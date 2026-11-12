"""Offline fixtures only: continuation must preserve originals and cap total attempts/charges."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("continuation_test_target", HERE / "continuation.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
b = c.base


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="strata-continuation-offline-")
        self.root = Path(self.tmp.name)
        self.assertTrue(self.root.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()))
        for name in ["runner.py", "continuation.py", "study.json", "cases.json", "RUBRIC.md", "SCORER-BRIEF.md"]:
            shutil.copyfile(HERE / name, self.root / name)
        shutil.copytree(HERE / "artifacts", self.root / "artifacts")
        cfg = b.read(self.root / "study.json")
        cfg["prices_checked_on"] = b.dt.datetime.now(b.dt.timezone.utc).date().isoformat()
        b.save(self.root / "study.json", cfg)
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(mock.patch.object(c, "ROOT", self.root))
        self.stack.enter_context(mock.patch.object(b, "ROOT", self.root))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(mock.patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden")))
        self.stack.enter_context(mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "FAKE_ANTHROPIC_SECRET", "XAI_API_KEY": "FAKE_XAI_SECRET"}))
        b.prepare()
        _, plan = b.validate_plan()
        prior = self.root / "results/run"
        prior.mkdir(parents=True)
        b.save(prior / "run.json", {"offline_fixture": True})
        self.reservation = sum((b.D(j["reserved_eur"]) for j in plan["jobs"][:22]), b.D(0))
        for job in plan["jobs"][:22]:
            rec = {**job, "status": "complete" if job["id"] != "J022" else "stopped"}
            if rec["status"] == "complete":
                rec.update(response_text="OFFLINE ORIGINAL FIXTURE", model_returned=job["model_requested"])
            b.save(prior / "records" / (job["id"] + ".json"), rec)
        b.save(prior / "budget-ledger.json", {"status": "stopped", "attempted": 22, "completed": 21, "reserved_eur": str(self.reservation)})
        self.originals = {f: c.h(f) for f in prior.rglob("*.json")}
        c.prepare()
        self.calls = []

    def tearDown(self):
        self.stack.close()
        self.tmp.cleanup()

    def transport(self, model, body, key, timeout):
        self.calls.append((model["family"], body))
        if model["api"] == "messages":
            return {"model": model["model"], "content": [{"type": "text", "text": "OFFLINE NEW FIXTURE"}], "stop_reason": "end_turn", "usage": {"input_tokens": 30, "output_tokens": 20}}, {}
        return {"model": model["model"], "status": "completed", "incomplete_details": None, "output": [{"type": "message", "content": [{"type": "output_text", "text": "OFFLINE NEW FIXTURE"}]}], "usage": {"input_tokens": 30, "output_tokens": 20}}, {}

    def test_exact_missing_slots_and_budget(self):
        _, _, a, jobs = c.validate()
        self.assertEqual([j["id"] for j in jobs], [f"J{i:03d}" for i in range(22, 43)])
        self.assertEqual(len(jobs), 21)
        self.assertLess(b.D(a["combined_reserve_maximum_eur"]), b.D("5"))
        self.assertGreater(b.D(a["combined_reserve_maximum_eur"]), self.reservation)

    def test_success_preserves_originals_and_exports_42(self):
        with mock.patch.object(b, "post_once", side_effect=self.transport): c.execute(True)
        self.assertEqual(len(self.calls), 21)
        for f, h in self.originals.items(): self.assertEqual(c.h(f), h)
        ledger = b.read(self.root / "results/continuation-01/budget-ledger.json")
        self.assertEqual(ledger["campaign_attempted"], 43)
        self.assertEqual(ledger["campaign_completed"], 42)
        c.export_blind()
        packet = b.read(self.root / "results/continuation-01/blind/SCORING-PACKET.json")
        self.assertEqual(len(packet), 42)
        self.assertEqual(sum(x["response_text"] == "OFFLINE ORIGINAL FIXTURE" for x in packet), 21)
        self.assertTrue(all(set(x) == {"record_id", "case_id", "user", "response_text"} for x in packet))
        with self.assertRaises(b.Stop): c.execute(True)

    def test_second_failure_stops_without_retry(self):
        with mock.patch.object(b, "post_once", side_effect=b.Stop("offline timeout")) as send:
            with self.assertRaises(b.Stop): c.execute(True)
        self.assertEqual(send.call_count, 1)
        ledger = b.read(self.root / "results/continuation-01/budget-ledger.json")
        self.assertEqual(ledger["campaign_attempted"], 23)
        self.assertGreater(b.D(ledger["reserved_eur"]), self.reservation)
        for f, h in self.originals.items(): self.assertEqual(c.h(f), h)
        with self.assertRaises(b.Stop): c.export_blind()

    def test_modified_original_blocks_and_execution_needs_flag(self):
        with self.assertRaises(b.Stop): c.execute(False)
        target = self.root / "results/run/records/J001.json"
        target.write_text("{}", encoding="utf-8")
        with self.assertRaises(b.Stop): c.validate()


if __name__ == "__main__":
    unittest.main()
