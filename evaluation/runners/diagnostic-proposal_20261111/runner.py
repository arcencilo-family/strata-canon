"""Separate 30-call Haiku diagnostic. Prepare/preflight are offline; no retries."""
import argparse
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
ENDPOINT = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"


class Stop(Exception):
    pass


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def scrub(value, secret):
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, list):
        return [scrub(v, secret) for v in value]
    if isinstance(value, dict):
        return {scrub(k, secret): scrub(v, secret) for k, v in value.items()}
    return value


def inputs():
    cfg = read(ROOT / "CONFIG.json")
    prompts = read(ROOT / "PROMPTS.json")
    if (cfg["model"] != MODEL or cfg["endpoint"] != ENDPOINT
            or cfg["repeats"] != 5 or cfg["expected_calls"] != 30
            or cfg["hard_budget_eur"] != "5.00"
            or cfg["setup_output_cap"] != 512 or cfg["target_output_cap"] != 4096
            or cfg["history_byte_ceiling"] != 16384
            or cfg["timeout_seconds"] != 180):
        raise Stop("Configuration differs from the identified diagnostic.")
    if [a["id"] for a in cfg["arms"]] != ["released", "proposed"]:
        raise Stop("Expected the two fixed arms.")
    for a in cfg["arms"]:
        if digest((ROOT / a["path"]).read_bytes()) != a["sha256"]:
            raise Stop("Kernel input changed.")
    return cfg, prompts


def system_for(cfg, arm):
    a = next(a for a in cfg["arms"] if a["id"] == arm)
    return cfg["host_line"] + "\n\n" + (ROOT / a["path"]).read_bytes().decode("utf-8")


def schedule():
    jobs = []
    for repeat in range(1, 6):
        c4 = ["released", "proposed"] if repeat % 2 else ["proposed", "released"]
        for arm in c4:
            jobs.append({"id": f"J{len(jobs)+1:03d}", "repeat": repeat,
                         "arm": arm, "kind": "C4", "dependency": None})
        for arm in reversed(c4):
            first = f"J{len(jobs)+1:03d}"
            jobs.append({"id": first, "repeat": repeat, "arm": arm,
                         "kind": "C6_setup", "dependency": None})
            jobs.append({"id": f"J{len(jobs)+1:03d}", "repeat": repeat,
                         "arm": arm, "kind": "C6_stop", "dependency": first})
    return jobs


def body_for(cfg, prompts, job, history=None):
    kind = job["kind"]
    messages = [{"role": "user", "content": prompts["C4"]["user"] if kind == "C4"
                 else prompts["C6"]["turn_1_user"]}]
    if kind == "C6_stop":
        if not isinstance(history, list) or not history:
            raise Stop("Missing actual first-turn assistant content.")
        if any(b.get("type") != "text" or not isinstance(b.get("text"), str) for b in history):
            raise Stop("Unexpected assistant content; no synthetic replacement.")
        if sum(len(b["text"].encode("utf-8")) for b in history) > cfg["history_byte_ceiling"]:
            raise Stop("Assistant history exceeds the frozen byte ceiling; not truncated.")
        messages.extend([{"role": "assistant", "content": history},
                         {"role": "user", "content": prompts["C6"]["turn_2_user"]}])
    return {"model": cfg["model"], "system": system_for(cfg, job["arm"]),
            "max_tokens": cfg["setup_output_cap"] if kind == "C6_setup" else cfg["target_output_cap"],
            "messages": messages}


def reservation(cfg, body):
    size = len(body["system"].encode("utf-8")) + 4096
    for m in body["messages"]:
        content = m["content"]
        size += (len(content.encode("utf-8")) if isinstance(content, str)
                 else sum(len(b["text"].encode("utf-8")) for b in content))
    eur = (D(size) * D(cfg["input_usd_per_million"])
           + D(body["max_tokens"]) * D(cfg["output_usd_per_million"])) / D(1000000)
    eur *= D(cfg["usd_price_multiplier"]) * D(cfg["eur_per_usd_reserve_ceiling"])
    return size, eur


def make_jobs(cfg, prompts):
    result = []
    for j in schedule():
        # This ceiling placeholder is NEVER sent. Stop payloads use actual generated history.
        history = [{"type": "text", "text": "X" * cfg["history_byte_ceiling"]}] if j["dependency"] else None
        body = body_for(cfg, prompts, j, history)
        bound, eur = reservation(cfg, body)
        result.append({**j, "input_token_ceiling": bound, "reserved_eur_ceiling": str(eur),
                       "output_cap": body["max_tokens"],
                       "prepared_body": None if j["dependency"] else body,
                       "dynamic_history": bool(j["dependency"])})
    return result


FROZEN = ["runner.py", "test_runner_offline.py", "CONFIG.json", "PROMPTS.json", "BUDGET.json",
          "RUBRIC.md", "SCORER-BRIEF.md"]


def prepare():
    cfg, prompts = inputs()
    path = ROOT / "prepared" / "plan.json"
    if path.exists():
        raise Stop("Plan already frozen; use preflight. No overwrite.")
    jobs = make_jobs(cfg, prompts)
    total = sum((D(j["reserved_eur_ceiling"]) for j in jobs), D(0))
    if total > D("5") or total != D(read(ROOT / "BUDGET.json")["total_eur_reservation"]):
        raise Stop("Prepared envelope differs from proposal or exceeds cap.")
    names = FROZEN + [a["path"] for a in cfg["arms"]]
    plan = {"created_utc": now(), "frozen_files": {n: digest((ROOT/n).read_bytes()) for n in names},
            "expected_calls": 30, "target_count": 20, "total_reserve_eur": str(total), "jobs": jobs}
    save(path, plan)
    save(ROOT / "prepared" / "FREEZE.json", {"plan_sha256": digest(path.read_bytes()), "created_utc": now()})
    print(f"OFFLINE prepared 30 calls / 20 targets; reserved ceiling EUR {total:.4f}. No network requests.")


def validate_plan():
    cfg, prompts = inputs()
    path = ROOT / "prepared" / "plan.json"
    if digest(path.read_bytes()) != read(ROOT / "prepared" / "FREEZE.json")["plan_sha256"]:
        raise Stop("Frozen plan changed.")
    plan = read(path)
    for n, h in plan["frozen_files"].items():
        if digest((ROOT/n).read_bytes()) != h:
            raise Stop("Frozen file changed: " + n)
    if plan["jobs"] != make_jobs(cfg, prompts) or plan["expected_calls"] != 30 or plan["target_count"] != 20:
        raise Stop("Schedule, payload template or reservation changed.")
    total = sum((D(j["reserved_eur_ceiling"]) for j in plan["jobs"]), D(0))
    if total != D(plan["total_reserve_eur"]) or total > D("5"):
        raise Stop("Invalid full-run reservation.")
    return cfg, prompts, plan


def preflight():
    cfg, _, plan = validate_plan()
    missing = "none" if os.environ.get("ANTHROPIC_API_KEY") else "ANTHROPIC_API_KEY"
    print(f"OFFLINE integrity OK; 30 calls / 20 targets; reserved maximum EUR {D(plan['total_reserve_eur']):.4f}.")
    print("Missing key environment variables: " + missing)
    print("No network requests; model access is not verified. No key values displayed or logged.")
    if (ROOT / "results" / "run").exists():
        print("A run folder already exists: paid execution will refuse a rerun or resume.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Stop("HTTP redirect refused; no retry.")


def post_once(cfg, body, key):
    request = urllib.request.Request(ENDPOINT, data=canonical(body), headers={
        "Content-Type": "application/json", "x-api-key": key,
        "anthropic-version": cfg["api_version"]}, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=cfg["timeout_seconds"]) as response:
            data = json.loads(response.read())
            ids = {k: response.headers[k] for k in ("request-id", "x-request-id") if response.headers.get(k)}
            return data, ids
    except urllib.error.HTTPError as e:
        raise Stop(f"HTTP {e.code}; provider error body omitted; no retry.") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise Stop("Transport/JSON failure; charge may be uncertain; no retry.") from None


def check_response(data, job, input_bound):
    if not isinstance(data, dict) or data.get("model") != MODEL:
        raise Stop("Missing or unexpected returned model identity; no substitution.")
    blocks = data.get("content")
    if not isinstance(blocks, list) or not blocks or any(
            not isinstance(b, dict) or b.get("type") != "text" or not isinstance(b.get("text"), str) for b in blocks):
        raise Stop("Unexpected/empty response content; preserved without retry.")
    text = "\n".join(b["text"] for b in blocks)
    if not text.strip() or data.get("stop_reason") != "end_turn":
        raise Stop("Empty, truncated or incomplete response; preserved without retry.")
    usage = data.get("usage", {})
    names = ["input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"]
    if not isinstance(usage, dict) or any(type(usage.get(n, 0)) is not int or usage.get(n, 0) < 0 for n in names):
        raise Stop("Invalid token usage; no further calls.")
    if "input_tokens" not in usage or "output_tokens" not in usage:
        raise Stop("Missing token usage; no further calls.")
    # No cache is requested. Unknown cache pricing should not be silently guessed.
    if usage.get("cache_creation_input_tokens", 0) or usage.get("cache_read_input_tokens", 0):
        raise Stop("Unexpected cache usage; reconcile pricing before continuing.")
    if usage["input_tokens"] > input_bound or usage["output_tokens"] > job["output_cap"]:
        raise Stop("Usage exceeds reservation envelope; reconcile before continuing.")
    return text


def heartbeat(done, job_id):
    elapsed = 0
    while not done.wait(30):
        elapsed += 30
        print(f"Waiting for {job_id}: {elapsed}s; no retry sent.", flush=True)


def run(confirm_calls, confirm_costs):
    if not confirm_calls or not confirm_costs:
        raise Stop("Paid execution requires --confirm-30-calls and --confirm-cost-inputs.")
    cfg, prompts, plan = validate_plan()
    age = (dt.datetime.now(dt.timezone.utc).date() - dt.date.fromisoformat(cfg["prices_checked_on"])).days
    if age < 0 or age > 7:
        raise Stop("Recorded pricing review is stale; prepare an identified successor before running.")
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise Stop("ANTHROPIC_API_KEY is missing; no calls.")
    result_root = ROOT / "results"
    result_root.mkdir(exist_ok=True)
    out = result_root / "run"
    if out.exists():
        raise Stop("A run already exists; no silent rerun or resume.")
    lock = result_root / ".run.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise Stop("A run lock exists; no concurrent execution.") from None
    os.close(descriptor)
    if out.exists():
        # A different process may have completed between our first check and lock acquisition.
        lock.unlink(missing_ok=True)
        raise Stop("A run appeared during lock acquisition; preserved without overwrite.")
    state = {"started_utc": now(), "status": "running", "attempted": 0, "completed": 0,
             "reserved_eur": "0", "plan_sha256": digest((ROOT/"prepared/plan.json").read_bytes()),
             "notes": "Separate D10 run; no refunds of reservations, no automatic retry/resume."}
    current, target = None, None
    try:
        out.mkdir()  # Exclusive creation also closes the race with another process.
        save(out / "RUN.json", {"config": cfg, "plan_sha256": state["plan_sha256"],
                                "frozen_files": plan["frozen_files"], "started_utc": state["started_utc"]})
        save(out / "budget-ledger.json", state)
        for job in plan["jobs"]:
            validate_plan()  # Stop on changed inputs before any further request.
            history = None
            if job["dependency"]:
                prior = read(out / "records" / (job["dependency"] + ".json"))
                if prior["status"] != "complete" or prior["arm"] != job["arm"] or prior["repeat"] != job["repeat"]:
                    raise Stop("First-turn dependency is not complete or does not match.")
                history = prior["response"]["content"]
            body = body_for(cfg, prompts, job, history)
            # If a secret somehow appears in content, stop rather than change the input silently.
            if key.encode("utf-8") in canonical(body):
                raise Stop("Credential-like content in request; not sent.")
            bound, eur = reservation(cfg, body)
            reserve = D(state["reserved_eur"]) + eur
            if eur > D(job["reserved_eur_ceiling"]) or reserve > D("5") or state["attempted"] >= 30:
                raise Stop("Reservation cap/count reached; next request not sent.")
            state.update(reserved_eur=str(reserve), attempted=state["attempted"] + 1)
            # Reserve durably BEFORE attempting a network request. Never refund unknown charges.
            save(out / "budget-ledger.json", state)
            current = {**job, "body": body, "request_sha256": digest(canonical(body)),
                       "system_sha256": digest(body["system"].encode("utf-8")),
                       "messages_sha256": digest(canonical(body["messages"])),
                       "kernel_sha256": next(a["sha256"] for a in cfg["arms"] if a["id"] == job["arm"]),
                       "input_token_reserve": bound, "reserved_eur": str(eur),
                       "started_utc": now(), "status": "attempt_reserved",
                       "sampling_requested": "provider defaults; temperature/top_p/seed/thinking omitted"}
            target = out / "records" / (job["id"] + ".json")
            save(target, current)
            print(f"Sending {job['id']} ({state['attempted']}/30; {job['kind']}); request timeout 180s.", flush=True)
            done = threading.Event()
            thread = threading.Thread(target=heartbeat, args=(done, job["id"]), daemon=True)
            thread.start()
            started = time.monotonic()
            try:
                data, identifiers = post_once(cfg, body, key)
            finally:
                done.set()
                thread.join()
            current.update(response=scrub(data, key), response_identifiers=scrub(identifiers, key),
                           elapsed_seconds=time.monotonic()-started, finished_utc=now(), status="received")
            save(target, current)
            if canonical(data) != canonical(scrub(data, key)):
                raise Stop("Credential-like content was redacted; no altered history sent onward.")
            text = check_response(data, job, bound)
            usage = data["usage"]
            cost = (D(usage["input_tokens"])*D(cfg["input_usd_per_million"])
                    + D(usage["output_tokens"])*D(cfg["output_usd_per_million"]))/D(1000000)
            current.update(status="complete", response_text=text, model_returned=data["model"],
                           usage_cost_estimate_usd=str(cost))
            save(target, current)
            state["completed"] += 1
            save(out / "budget-ledger.json", state)
            print(f"Completed {state['completed']}/30; reserved EUR {reserve:.4f}.", flush=True)
            current, target = None, None
        state.update(status="complete", finished_utc=now())
    except BaseException as e:
        reason = str(e) if isinstance(e, Stop) else ("Interrupted; no retry." if isinstance(e, KeyboardInterrupt)
                                                    else "Unexpected local failure; reservation retained; no retry.")
        state.update(status="stopped", stop_reason=reason, finished_utc=now())
        if current is not None and target is not None:
            current.update(status="stopped", stop_reason=reason, finished_utc=now())
            save(target, scrub(current, key))
        raise Stop(reason) from None
    finally:
        if out.exists():
            save(out / "budget-ledger.json", scrub(state, key))
        lock.unlink(missing_ok=True)
    print("Run complete: 30 calls, 20 target answers. No scoring or release decision performed.")


def export_blind():
    cfg, prompts, plan = validate_plan()
    out = ROOT / "results" / "run"
    state = read(out / "budget-ledger.json")
    if state.get("status") != "complete" or state.get("completed") != 30 or state.get("attempted") != 30:
        raise Stop("Run incomplete; no complete scoring packet exported.")
    records = {}
    hashes = {}
    expected = {j["id"] for j in plan["jobs"]}
    files = list((out / "records").glob("*.json"))
    if {p.stem for p in files} != expected or len(files) != 30:
        raise Stop("Expected exactly 30 attempt records.")
    for p in files:
        rec = read(p)
        job = next(j for j in plan["jobs"] if j["id"] == p.stem)
        if rec.get("status") != "complete" or any(rec.get(k) != v for k, v in job.items()):
            raise Stop("Record identity/status mismatch.")
        if digest(canonical(rec["body"])) != rec["request_sha256"]:
            raise Stop("Saved request hash mismatch.")
        text = check_response(rec["response"], job, rec["input_token_reserve"])
        if text != rec["response_text"]:
            raise Stop("Saved response text mismatch.")
        records[rec["id"]] = rec
        hashes[p.name] = digest(p.read_bytes())
    for job in plan["jobs"]:
        rec = records[job["id"]]
        history = records[job["dependency"]]["response"]["content"] if job["dependency"] else None
        if rec["body"] != body_for(cfg, prompts, job, history):
            raise Stop("Saved payload/history differs from frozen protocol.")
    dest = out / "blind"
    if dest.exists() or (out / "UNBLIND-MAP-KEEP-FROM-SCORER.json").exists():
        raise Stop("Export already exists; no overwrite.")
    targets = [r for r in records.values() if r["kind"] != "C6_setup"]
    random.SystemRandom().shuffle(targets)
    neutral = ["K1", "K2"]
    random.SystemRandom().shuffle(neutral)
    source_labels = dict(zip([a["id"] for a in cfg["arms"]], neutral))
    packet, mapping = [], []
    for i, rec in enumerate(targets, 1):
        rid = f"S{i:03d}"
        packet.append({"record_id": rid, "case_id": "C4" if rec["kind"] == "C4" else "C6",
                       "source_text_id": source_labels[rec["arm"]],
                       "messages_before_response": rec["body"]["messages"], "response_text": rec["response_text"]})
        mapping.append({"record_id": rid, "job_id": rec["id"], "repeat": rec["repeat"],
                        "arm": rec["arm"], "kind": rec["kind"], "model_returned": rec["model_returned"]})
    dest.mkdir()
    sources = {source_labels[a["id"]]: (ROOT/a["path"]).read_bytes().decode("utf-8") for a in cfg["arms"]}
    save(dest / "SOURCE-TEXTS.json", sources)
    save(dest / "SCORING-PACKET.json", packet)
    for name in ("RUBRIC.md", "SCORER-BRIEF.md"):
        (dest/name).write_bytes((ROOT/name).read_bytes())
    save(out / "UNBLIND-MAP-KEEP-FROM-SCORER.json", {"records": mapping, "source_labels": source_labels})
    save(out / "EXPORT-RECEIPT.json", {"created_utc": now(), "records": hashes,
         "plan_sha256": state["plan_sha256"], "blind_files": {p.name: digest(p.read_bytes()) for p in dest.iterdir()}})
    print("Exported 20 masked targets, including 10 actual setup histories; mapping kept separate.")
    print("Source wording, signatures and response style can reveal labels; masking is imperfect.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["prepare", "preflight", "run", "export-blind"])
    p.add_argument("--confirm-30-calls", action="store_true")
    p.add_argument("--confirm-cost-inputs", action="store_true")
    args = p.parse_args()
    try:
        if args.command == "prepare": prepare()
        elif args.command == "preflight": preflight()
        elif args.command == "run": run(args.confirm_30_calls, args.confirm_cost_inputs)
        else: export_blind()
    except Stop as e:
        print("STOP: " + str(e), file=sys.stderr)
        return 2
    except Exception:
        print("STOP: unexpected local error; no automatic retry. Inspect inputs/ledger without printing keys.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
