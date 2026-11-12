"""Explicitly approved one-off continuation. Preserves the stopped run and its reservation."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("frozen_strata_runner", ROOT / "runner.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def h(path):
    return base.digest(path.read_bytes())


def prepare():
    base.ROOT = ROOT
    cfg, plan = base.validate_plan()
    dest = ROOT / "prepared" / "continuation-01.json"
    if dest.exists():
        raise base.Stop("Continuation is already prepared; use preflight.")
    prior = ROOT / "results" / "run"
    ledger = base.read(prior / "budget-ledger.json")
    records = [base.read(f) for f in sorted((prior / "records").glob("*.json"))]
    completed = [r for r in records if r.get("status") == "complete"]
    failed = [r for r in records if r.get("status") != "complete"]
    if (ledger.get("status") != "stopped" or ledger.get("attempted") != 22
            or ledger.get("completed") != 21 or len(completed) != 21 or len(failed) != 1
            or failed[0]["id"] != "J022" or "response" in failed[0]):
        raise base.Stop("Original run differs from the specifically approved incident.")
    done = {r["id"] for r in completed}
    remaining = [j for j in plan["jobs"] if j["id"] not in done]
    total = base.D(ledger["reserved_eur"]) + sum((base.D(j["reserved_eur"]) for j in remaining), base.D(0))
    if len(remaining) != 21 or remaining[0]["id"] != "J022" or total > base.D("5"):
        raise base.Stop("Continuation count or campaign budget differs from approval.")
    frozen = {"continuation.py": h(ROOT / "continuation.py"),
              "prepared/plan.json": h(ROOT / "prepared/plan.json"),
              "results/run/budget-ledger.json": h(prior / "budget-ledger.json"),
              "results/run/run.json": h(prior / "run.json")}
    for f in sorted((prior / "records").glob("*.json")):
        frozen[f.relative_to(ROOT).as_posix()] = h(f)
    approval = {"prepared_utc": base.now(), "authorization": "Frank approved the proposed controlled continuation in the Codex chat after the incident report.",
                "original_attempted": 22, "original_completed": 21, "original_reserved_eur": ledger["reserved_eur"],
                "job_ids": [j["id"] for j in remaining], "successful_original_job_ids": sorted(done),
                "additional_attempts_maximum": 21, "campaign_attempts_maximum": 43,
                "combined_reserve_maximum_eur": str(total), "hard_budget_eur": "5.00",
                "failed_attempt_policy": "J022's first attempt/uncertain charge stays preserved and fully reserved. Exactly one new attempt is permitted; any further failure stops.",
                "protocol": "Same frozen prompts, models, sampling defaults and 180-second timeout. Chronological interruption disclosed. No successful output rerun or replaced.",
                "frozen_original_and_continuation_files": frozen}
    base.save(dest, approval)
    print(f"OFFLINE continuation prepared: 21 missing slots; combined reservation EUR {total:.4f}; no API calls.")


def validate():
    base.ROOT = ROOT
    cfg, plan = base.validate_plan()
    approval = base.read(ROOT / "prepared/continuation-01.json")
    for rel, expected in approval["frozen_original_and_continuation_files"].items():
        if h(ROOT / rel) != expected:
            raise base.Stop("Preserved original or continuation code changed: " + rel)
    prior = ROOT / "results/run"
    ledger = base.read(prior / "budget-ledger.json")
    originals = [base.read(f) for f in sorted((prior / "records").glob("*.json"))]
    done = sorted(r["id"] for r in originals if r.get("status") == "complete")
    if (len(originals) != 22 or ledger.get("attempted") != 22 or ledger.get("completed") != 21
            or done != approval["successful_original_job_ids"] or len(done) != 21
            or approval["original_reserved_eur"] != ledger["reserved_eur"]
            or approval["campaign_attempts_maximum"] != 43
            or approval["additional_attempts_maximum"] != 21):
        raise base.Stop("Continuation no longer matches the approved incident/counts.")
    jobs = [j for j in plan["jobs"] if j["id"] in approval["job_ids"]]
    expected = [j["id"] for j in plan["jobs"] if j["id"] not in done]
    if ([j["id"] for j in jobs] != approval["job_ids"] or len(jobs) != 21
            or approval["job_ids"] != expected or jobs[0]["id"] != "J022"):
        raise base.Stop("Continuation schedule changed.")
    total = base.D(approval["original_reserved_eur"]) + sum((base.D(j["reserved_eur"]) for j in jobs), base.D(0))
    if total != base.D(approval["combined_reserve_maximum_eur"]) or total > base.D("5"):
        raise base.Stop("Campaign budget invalid.")
    return cfg, plan, approval, jobs


def preflight():
    cfg, _, approval, jobs = validate()
    families = {j["family"] for j in jobs}
    missing = [m["key_env"] for m in cfg["models"] if m["family"] in families and not os.environ.get(m["key_env"])]
    print("OFFLINE continuation integrity OK; 21 answers preserved; 21 missing slots; 43 maximum total attempts.")
    print(f"Combined conservative reservation EUR {base.D(approval['combined_reserve_maximum_eur']):.4f}; cap EUR 5.00.")
    print("Missing required environment variables: " + (", ".join(missing) if missing else "none"))
    print("No network requests; no key values displayed; original run unchanged.")


def execute(confirmed):
    if not confirmed:
        raise base.Stop("Execution requires --confirm-approved-continuation.")
    cfg, plan, approval, jobs = validate()
    age = (base.dt.datetime.now(base.dt.timezone.utc).date() - base.dt.date.fromisoformat(cfg["prices_checked_on"])).days
    if age < 0 or age > cfg["price_review_valid_days"]:
        raise base.Stop("Price review expired; no new call.")
    models = {m["family"]: m for m in cfg["models"]}
    families = {j["family"] for j in jobs}
    keys = {f: os.environ.get(models[f]["key_env"], "") for f in families}
    if not all(keys.values()):
        raise base.Stop("Required key environment variable missing; no calls.")
    secrets = list(keys.values())
    out = ROOT / "results" / "continuation-01"
    if out.exists():
        raise base.Stop("Continuation already exists. No rerun/resume or extra attempt authorized.")
    lock = ROOT / "results" / ".run.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise base.Stop("Run lock exists; investigate before new calls.") from None
    os.close(fd)
    state = {"started_utc": base.now(), "status": "running", "additional_attempted": 0,
             "additional_completed": 0, "campaign_attempted": approval["original_attempted"],
             "campaign_completed": approval["original_completed"],
             "reserved_eur": approval["original_reserved_eur"],
             "continuation_plan_sha256": h(ROOT / "prepared/continuation-01.json")}
    try:
        out.mkdir()
        base.save(out / "run.json", {"approval": approval, "config": cfg,
                                     "original_plan_sha256": h(ROOT / "prepared/plan.json"),
                                     "started_utc": state["started_utc"]})
        for job in jobs:
            reserve = base.D(state["reserved_eur"]) + base.D(job["reserved_eur"])
            if reserve > base.D("5") or state["campaign_attempted"] >= 43 or state["additional_attempted"] >= 21:
                raise base.Stop("Approved campaign count/budget exhausted; next request not sent.")
            model = models[job["family"]]
            state.update(reserved_eur=str(reserve), additional_attempted=state["additional_attempted"] + 1,
                         campaign_attempted=state["campaign_attempted"] + 1)
            base.save(out / "budget-ledger.json", state)
            rec = {**job, "status": "attempt_reserved", "started_utc": base.now(),
                   "sampling_requested": "provider defaults; temperature/top_p/seed/reasoning omitted",
                   "output_cap": cfg["max_output_tokens"], "approved_continuation": True,
                   "original_failed_attempt_preserved": job["id"] == "J022"}
            target = out / "records" / (job["id"] + ".json")
            base.save(target, base.scrub(rec, secrets))
            start = time.monotonic()
            try:
                data, info = base.post_once(model, job["body"], keys[job["family"]], cfg["timeout_seconds"])
                text, finish, valid = base.extract(data, model["api"])
                rec.update(response=data, response_text=text, response_identifiers=info,
                           model_returned=data.get("model"), finish=finish, status="received",
                           finished_utc=base.now(), elapsed_seconds=time.monotonic() - start)
                base.save(target, base.scrub(rec, secrets))
                ins, outs = base.usage_counts(data, model["api"])
                if ins < 0 or outs < 0 or ins > job["input_token_reserve"] or outs > cfg["max_output_tokens"]:
                    raise base.Stop("Usage exceeds reserve; stop and reconcile billing.")
                if not data.get("model") or not valid:
                    raise base.Stop("Incomplete response or missing model ID; saved; no retry.")
                actual = (base.D(ins) * base.D(model["input_usd_per_million"]) + base.D(outs) * base.D(model["output_usd_per_million"])) / base.D(1000000)
                rec.update(status="complete", usage_cost_estimate_usd=str(actual))
                base.save(target, base.scrub(rec, secrets))
                state.update(additional_completed=state["additional_completed"] + 1,
                             campaign_completed=state["campaign_completed"] + 1)
                base.save(out / "budget-ledger.json", state)
                print(f"Completed {state['campaign_completed']}/42; campaign reserved EUR {reserve:.4f}.")
            except base.Stop as error:
                rec.update(status="stopped", stop_reason=str(error), finished_utc=base.now())
                base.save(target, base.scrub(rec, secrets))
                raise
        state.update(status="complete", finished_utc=base.now())
    except (base.Stop, KeyboardInterrupt) as error:
        state.update(status="stopped", finished_utc=base.now(),
                     stop_reason=str(error) if isinstance(error, base.Stop) else "Interrupted; no further retry.")
        raise base.Stop(state["stop_reason"]) from None
    except Exception:
        state.update(status="stopped", finished_utc=base.now(), stop_reason="Unexpected local failure; charge reserved; no retry.")
        raise base.Stop(state["stop_reason"]) from None
    finally:
        if out.exists():
            base.save(out / "budget-ledger.json", base.scrub(state, secrets))
        lock.unlink(missing_ok=True)


def export_blind():
    _, plan, approval, _ = validate()
    out = ROOT / "results" / "continuation-01"
    ledger = base.read(out / "budget-ledger.json")
    if ledger.get("status") != "complete" or ledger.get("campaign_completed") != 42:
        raise base.Stop("Continuation incomplete; no complete scorer packet.")
    records = []
    for job in plan["jobs"]:
        folder = "run" if job["id"] in approval["successful_original_job_ids"] else "continuation-01"
        source = ROOT / "results" / folder / "records" / (job["id"] + ".json")
        record = base.read(source)
        if record.get("status") != "complete":
            raise base.Stop("Missing selected response; no substitute or cherry-picking.")
        records.append((source, record))
    dest = out / "blind"
    if dest.exists():
        raise base.Stop("Scoring packet exists; do not overwrite.")
    random.SystemRandom().shuffle(records)
    packet, mapping = [], []
    for i, (source, rec) in enumerate(records, 1):
        rid = f"S{i:03d}"
        packet.append({"record_id": rid, "case_id": rec["case_id"], "user": rec["user"], "response_text": rec["response_text"]})
        mapping.append({"record_id": rid, "job_id": rec["id"], "arm": rec["arm"],
                        "family": rec["family"], "model_requested": rec["model_requested"],
                        "model_returned": rec["model_returned"], "source": source.relative_to(ROOT).as_posix(),
                        "source_sha256": h(source), "continued": "continuation-01" in source.parts})
    dest.mkdir()
    base.save(dest / "SCORING-PACKET.json", packet)
    base.save(out / "UNBLIND-MAP-KEEP-FROM-SCORER.json", mapping)
    for name in ("RUBRIC.md", "SCORER-BRIEF.md"):
        (dest / name).write_bytes((ROOT / name).read_bytes())
    (dest / "PROTOCOL-DEVIATION.md").write_text(
        "One request had no saved response after a transport failure. Frank authorized one replacement request "
        "and completion of unattempted cells, retaining all previously completed answers. The original failed "
        "attempt and possible charge are preserved and reserved. Maximum attempts: 43 for 42 responses. "
        "The interruption introduces a time gap; no successful output was rerun or selected. Cell identities "
        "and mapping are withheld until initial scoring. Label masking is not guaranteed blinding.\n", encoding="utf-8")
    print("Exported 42 responses, with the approved interruption disclosed; labels masked and unblind map kept separate.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "preflight", "run", "export-blind"])
    parser.add_argument("--confirm-approved-continuation", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "prepare": prepare()
        elif args.command == "preflight": preflight()
        elif args.command == "run": execute(args.confirm_approved_continuation)
        else: export_blind()
    except base.Stop as error:
        print("STOP: " + str(error), file=sys.stderr)
        return 2
    except Exception:
        print("STOP: unexpected local error; original run preserved; no automatic retry.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
