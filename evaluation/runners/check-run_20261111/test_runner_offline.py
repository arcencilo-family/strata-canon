"""Offline protocol tests: fake transport only, never a model API."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("strata_runner", HERE / "runner.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class OfflineRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="strata-offline-")
        self.root = Path(self.temp.name)
        self.assertTrue(self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
        for name in ["runner.py", "study.json", "cases.json", "RUBRIC.md", "SCORER-BRIEF.md"]:
            shutil.copyfile(HERE / name, self.root / name)
        shutil.copytree(HERE / "artifacts", self.root / "artifacts")
        cfg = r.read(self.root / "study.json")
        cfg["prices_checked_on"] = r.dt.datetime.now(r.dt.timezone.utc).date().isoformat()
        r.save(self.root / "study.json", cfg)
        (self.root / "results").mkdir()
        self.patch = mock.patch.object(r, "ROOT", self.root)
        self.patch.start()
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.network = mock.patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden in offline tests"))
        self.network.start()
        self.keys = mock.patch.dict(os.environ, {"OPENAI_API_KEY": "SENTINEL_OPENAI_SECRET",
                                                "ANTHROPIC_API_KEY": "SENTINEL_ANTHROPIC_SECRET",
                                                "XAI_API_KEY": "SENTINEL_XAI_SECRET"})
        self.keys.start()

    def tearDown(self):
        self.keys.stop()
        self.network.stop()
        self.stdout.__exit__(None, None, None)
        self.patch.stop()
        self.temp.cleanup()

    def fixture(self, model, body, key, timeout):
        self.calls.append((model["family"], body))
        text = "OFFLINE FIXTURE, not model evidence. SENTINEL_OPENAI_SECRET"
        if model["api"] == "messages":
            return {"model": model["model"], "content": [{"type": "text", "text": text}],
                    "stop_reason": "end_turn", "usage": {"input_tokens": 30, "output_tokens": 20}}, {}
        return {"model": model["model"], "status": "completed", "incomplete_details": None,
                "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}],
                "usage": {"input_tokens": 30, "output_tokens": 20}}, {}

    def prepare(self):
        self.calls = []
        r.prepare()

    def test_exact_plan_and_defaults(self):
        self.prepare()
        cfg, plan = r.validate_plan()
        self.assertEqual(len(plan["jobs"]), 42)
        self.assertLessEqual(r.D(plan["total_reserve_eur"]), r.D(5))
        self.assertEqual(len({(j["family"], j["arm"], j["case_id"]) for j in plan["jobs"]}), 42)
        for j in plan["jobs"]:
            self.assertEqual(j["system"].split("\n\n", 1)[0], cfg["host_line"])
            self.assertNotIn("temperature", j["body"])
            self.assertNotIn("top_p", j["body"])
            self.assertNotIn("reasoning", j["body"])
            self.assertNotIn("previous_response_id", j["body"])
            self.assertNotIn("tools", j["body"])

    def test_no_paid_run_without_confirmation(self):
        self.prepare()
        with self.assertRaises(r.Stop): r.run(False, False)
        self.assertFalse((self.root / "results/run").exists())

    def test_frozen_input_change_blocks(self):
        self.prepare()
        with (self.root / "RUBRIC.md").open("a", encoding="utf-8") as f: f.write("changed")
        with self.assertRaises(r.Stop): r.validate_plan()

    def test_full_fake_run_redaction_and_blinding(self):
        self.prepare()
        with mock.patch.object(r, "post_once", side_effect=self.fixture): r.run(True, True)
        self.assertEqual(len(self.calls), 42)
        state = r.read(self.root / "results/run/budget-ledger.json")
        self.assertEqual(state["completed"], 42)
        r.export_blind()
        packet = r.read(self.root / "results/run/blind/SCORING-PACKET.json")
        self.assertEqual(len(packet), 42)
        self.assertTrue(all(set(row) == {"record_id", "case_id", "user", "response_text"} for row in packet))
        for f in (self.root / "results/run").rglob("*.json"):
            text = f.read_text(encoding="utf-8")
            self.assertNotIn("SENTINEL_OPENAI_SECRET", text)
            self.assertNotIn("SENTINEL_ANTHROPIC_SECRET", text)
            self.assertNotIn("SENTINEL_XAI_SECRET", text)
        with self.assertRaises(r.Stop): r.run(True, True)

    def test_uncertain_charge_stops_no_retry(self):
        self.prepare()
        with mock.patch.object(r, "post_once", side_effect=r.Stop("fixture transport failure")) as send:
            with self.assertRaises(r.Stop): r.run(True, True)
        self.assertEqual(send.call_count, 1)
        state = r.read(self.root / "results/run/budget-ledger.json")
        self.assertEqual(state["attempted"], 1)
        self.assertGreater(r.D(state["reserved_eur"]), 0)
        self.assertEqual(state["status"], "stopped")
        with self.assertRaises(r.Stop): r.export_blind()

    def test_pre_send_cap_blocks_next_request(self):
        self.prepare()
        cfg, plan = r.validate_plan()
        plan["jobs"][0]["reserved_eur"] = "4"
        plan["jobs"][1]["reserved_eur"] = "4"
        # Isolate the per-send budget guard; production validate_plan also rejects this forged envelope.
        with mock.patch.object(r, "validate_plan", return_value=(cfg, plan)):
            with mock.patch.object(r, "post_once", side_effect=self.fixture):
                with self.assertRaises(r.Stop): r.run(True, True)
        self.assertEqual(len(self.calls), 1)
        state = r.read(self.root / "results/run/budget-ledger.json")
        self.assertEqual(state["attempted"], 1)
        self.assertEqual(state["reserved_eur"], "4")

    def test_truncated_response_preserved_and_stops(self):
        self.prepare()
        def truncated(model, body, key, timeout):
            data, info = self.fixture(model, body, key, timeout)
            data["status"] = "incomplete"
            data["incomplete_details"] = {"reason": "max_output_tokens"}
            return data, info
        with mock.patch.object(r, "post_once", side_effect=truncated):
            with self.assertRaises(r.Stop): r.run(True, True)
        self.assertEqual(len(self.calls), 1)
        rec = r.read(self.root / "results/run/records/J001.json")
        self.assertIn("response", rec)
        self.assertEqual(rec["status"], "stopped")


if __name__ == "__main__":
    unittest.main()
