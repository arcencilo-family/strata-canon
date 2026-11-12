"""Offline fixtures only, never model evidence; all network access is blocked."""
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
spec = importlib.util.spec_from_file_location("diagnostic_runner", HERE / "runner.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
SECRET = "OFFLINE_SENTINEL_NOT_A_REAL_KEY"


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="strata-diagnostic-offline-")
        self.base = Path(self.tmp.name)
        self.root = self.base / "diagnostic"
        self.root.mkdir()
        for name in r.FROZEN:
            shutil.copyfile(HERE/name, self.root/name)
        cfg = r.read(self.root/"CONFIG.json")
        for a in cfg["arms"]:
            target = self.root/a["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(HERE/a["path"], target)
        cfg["prices_checked_on"] = r.dt.datetime.now(r.dt.timezone.utc).date().isoformat()
        r.save(self.root/"CONFIG.json", cfg)
        self.patches = [mock.patch.object(r, "ROOT", self.root),
                        mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": SECRET}),
                        mock.patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden"))]
        for p in self.patches: p.start()
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.calls = []
        r.prepare()

    def tearDown(self):
        self.redirect.__exit__(None, None, None)
        for p in reversed(self.patches): p.stop()
        self.tmp.cleanup()

    def fake(self, cfg, body, key):
        self.calls.append(body)
        # Assert durable accounting exists before transport receives any request.
        state = r.read(self.root/"results/run/budget-ledger.json")
        self.assertEqual(state["attempted"], len(self.calls))
        self.assertGreater(r.D(state["reserved_eur"]), 0)
        return {"model": r.MODEL, "stop_reason": "end_turn",
                "content": [{"type": "text", "text": f"OFFLINE FIXTURE {len(self.calls)}; not model evidence."}],
                "usage": {"input_tokens": 100, "output_tokens": 20}}, {"request-id": "offline"}

    def run_fake(self, effect=None):
        with mock.patch.object(r, "post_once", side_effect=effect or self.fake) as transport:
            r.run(True, True)
        return transport

    def test_schedule_envelope_and_no_sampling_overrides(self):
        cfg, prompts, plan = r.validate_plan()
        self.assertEqual(len(plan["jobs"]), 30)
        self.assertEqual(sum(j["kind"] != "C6_setup" for j in plan["jobs"]), 20)
        self.assertEqual(r.D(plan["total_reserve_eur"]), r.D("2.438055"))
        for j in plan["jobs"]:
            body = j["prepared_body"]
            if body:
                self.assertEqual(set(body), {"model", "system", "max_tokens", "messages"})
                self.assertEqual(len(body["messages"]), 1)
            else:
                self.assertTrue(j["dependency"])
        self.assertEqual(prompts["C4"]["user"].count("?"), 1)
        kinds = [j["kind"] for j in plan["jobs"]]
        self.assertEqual(kinds[:6], ["C4", "C4", "C6_setup", "C6_stop", "C6_setup", "C6_stop"])
        self.assertEqual([j["arm"] for j in plan["jobs"][:2]], ["released", "proposed"])
        self.assertEqual([j["arm"] for j in plan["jobs"][6:8]], ["proposed", "released"])

    def test_offline_preflight_never_sends(self):
        r.preflight()
        self.assertIn("Missing key environment variables: none", self.output.getvalue())
        self.assertNotIn(SECRET, self.output.getvalue())

    def test_confirmation_and_missing_key_prevent_run(self):
        with self.assertRaises(r.Stop): r.run(False, True)
        with self.assertRaises(r.Stop): r.run(True, False)
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            with self.assertRaises(r.Stop): r.run(True, True)
        self.assertFalse((self.root/"results/run").exists())

    def test_changed_input_and_plan_rejected(self):
        path = self.root/"PROMPTS.json"
        original = path.read_bytes()
        path.write_bytes(original+b" ")
        with self.assertRaises(r.Stop): r.validate_plan()
        path.write_bytes(original)
        path = self.root/"prepared/plan.json"
        path.write_bytes(path.read_bytes()+b" ")
        with self.assertRaises(r.Stop): r.validate_plan()

    def test_complete_run_exact_history_export_and_no_rerun(self):
        self.run_fake()
        self.assertEqual(len(self.calls), 30)
        state = r.read(self.root/"results/run/budget-ledger.json")
        self.assertEqual(state["status"], "complete")
        self.assertLessEqual(r.D(state["reserved_eur"]), r.D("2.438055"))
        cfg, prompts, plan = r.validate_plan()
        for j, body in zip(plan["jobs"], self.calls):
            if j["dependency"]:
                prior = r.read(self.root/"results/run/records"/(j["dependency"]+".json"))
                self.assertEqual(body["messages"][1]["content"], prior["response"]["content"])
                self.assertEqual(body["messages"][2]["content"], prompts["C6"]["turn_2_user"])
                self.assertEqual(len(body["messages"]), 3)
            else:
                self.assertEqual(len(body["messages"]), 1)
        r.export_blind()
        out = self.root/"results/run"
        packet = r.read(out/"blind/SCORING-PACKET.json")
        self.assertEqual(len(packet), 20)
        self.assertEqual(sum(x["case_id"] == "C6" for x in packet), 10)
        self.assertEqual({p.name for p in (out/"blind").iterdir()},
                         {"SCORING-PACKET.json", "SOURCE-TEXTS.json", "RUBRIC.md", "SCORER-BRIEF.md"})
        for x in packet:
            self.assertNotIn("arm", x)
            self.assertNotIn("model", x)
            self.assertNotIn("repeat", x)
        for p in out.rglob("*.json"):
            self.assertNotIn(SECRET, p.read_text(encoding="utf-8"))
        with self.assertRaises(r.Stop): r.run(True, True)
        with self.assertRaises(r.Stop): r.export_blind()

    def test_uncertain_charge_stops_once(self):
        with mock.patch.object(r, "post_once", side_effect=r.Stop("fixture timeout")) as send:
            with self.assertRaises(r.Stop): r.run(True, True)
        self.assertEqual(send.call_count, 1)
        state = r.read(self.root/"results/run/budget-ledger.json")
        self.assertEqual((state["attempted"], state["completed"], state["status"]), (1, 0, "stopped"))
        self.assertGreater(r.D(state["reserved_eur"]), 0)
        with self.assertRaises(r.Stop): r.export_blind()

    def test_truncated_response_preserved_without_retry(self):
        def truncated(*args):
            data, ids = self.fake(*args)
            data["stop_reason"] = "max_tokens"
            return data, ids
        with self.assertRaises(r.Stop): self.run_fake(truncated)
        self.assertEqual(len(self.calls), 1)
        rec = r.read(self.root/"results/run/records/J001.json")
        self.assertEqual(rec["status"], "stopped")
        self.assertIn("response", rec)

    def test_oversize_setup_history_stops_before_second_send(self):
        def oversized(*args):
            data, ids = self.fake(*args)
            if len(self.calls) == 3:
                data["content"][0]["text"] = "X" * 16385
            return data, ids
        with self.assertRaises(r.Stop): self.run_fake(oversized)
        self.assertEqual(len(self.calls), 3)
        state = r.read(self.root/"results/run/budget-ledger.json")
        self.assertEqual(state["attempted"], 3)

    def test_secret_response_redacted_and_not_sent_as_history(self):
        def secret(*args):
            data, ids = self.fake(*args)
            data["content"][0]["text"] = SECRET
            return data, ids
        with self.assertRaises(r.Stop): self.run_fake(secret)
        self.assertEqual(len(self.calls), 1)
        for p in (self.root/"results/run").rglob("*.json"):
            self.assertNotIn(SECRET, p.read_text(encoding="utf-8"))

    def test_missing_usage_wrong_model_and_cache_stop(self):
        cfg, _, plan = r.validate_plan()
        job = plan["jobs"][0]
        base = {"model": r.MODEL, "stop_reason": "end_turn", "content": [{"type": "text", "text": "fixture"}],
                "usage": {"input_tokens": 100, "output_tokens": 10}}
        for change in [{"model": "another-model"}, {"usage": {}},
                       {"usage": {"input_tokens": 100, "output_tokens": 10, "cache_creation_input_tokens": 10}}]:
            with self.subTest(change=change):
                with self.assertRaises(r.Stop): r.check_response({**base, **change}, job, 1000)

    def test_interrupt_keeps_reserved_attempt(self):
        with mock.patch.object(r, "post_once", side_effect=KeyboardInterrupt):
            with self.assertRaises(r.Stop): r.run(True, True)
        state = r.read(self.root/"results/run/budget-ledger.json")
        self.assertEqual(state["attempted"], 1)
        self.assertGreater(r.D(state["reserved_eur"]), 0)
        self.assertFalse((self.root/"results/.run.lock").exists())

    def test_per_send_budget_guard(self):
        cfg, prompts, plan = r.validate_plan()
        original = r.reservation
        def inflated(*args):
            bound, _ = original(*args)
            return bound, r.D("6")
        # Isolate the last-moment cap guard; validation separately rejects forged schedules.
        with mock.patch.object(r, "validate_plan", return_value=(cfg, prompts, plan)):
            with mock.patch.object(r, "reservation", side_effect=inflated):
                with mock.patch.object(r, "post_once") as send:
                    with self.assertRaises(r.Stop): r.run(True, True)
                    send.assert_not_called()
        self.assertEqual(r.read(self.root/"results/run/budget-ledger.json")["attempted"], 0)

    def test_preexisting_lock_blocks(self):
        (self.root/"results").mkdir()
        (self.root/"results/.run.lock").write_text("fixture")
        with self.assertRaises(r.Stop): r.run(True, True)
        self.assertFalse((self.root/"results/run").exists())

    def test_changed_record_blocks_export(self):
        self.run_fake()
        path = self.root/"results/run/records/J004.json"
        rec = r.read(path)
        rec["body"]["messages"][1]["content"][0]["text"] = "tampered history"
        r.save(path, rec)
        with self.assertRaises(r.Stop): r.export_blind()

    def test_run_created_during_lock_acquisition_is_preserved(self):
        original = r.os.open
        ledger = self.root/"results/run/budget-ledger.json"
        def acquire(*args, **kwargs):
            descriptor = original(*args, **kwargs)
            ledger.parent.mkdir()
            ledger.write_text('OFFLINE EXISTING LEDGER', encoding='utf-8')
            return descriptor
        with mock.patch.object(r.os, "open", side_effect=acquire):
            with self.assertRaises(r.Stop): r.run(True, True)
        self.assertEqual(ledger.read_text(encoding='utf-8'), 'OFFLINE EXISTING LEDGER')
        self.assertFalse((self.root/"results/.run.lock").exists())


if __name__ == "__main__":
    unittest.main()
