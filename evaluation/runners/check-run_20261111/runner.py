"""42 stateless text calls; stdlib only. Offline prepare/preflight; explicit paid-run gate."""
import argparse
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parent
ENDPOINTS = {
    "openai": "https://api.openai.com/v1/responses",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "xai": "https://api.x.ai/v1/responses",
}


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


def scrub(value, secrets):
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[REDACTED]")
        return value
    if isinstance(value, list):
        return [scrub(x, secrets) for x in value]
    if isinstance(value, dict):
        return {scrub(k, secrets): scrub(v, secrets) for k, v in value.items()}
    return value


def configuration():
    cfg = read(ROOT / "study.json")
    cases = read(ROOT / cfg["case_file"])
    if len(cases) != 7 or len(cfg["models"]) != 3 or len(cfg["arms"]) != 2:
        raise Stop("Expected exactly 7 cases, 3 families, and 2 arms.")
    if {m["family"] for m in cfg["models"]} != set(ENDPOINTS):
        raise Stop("This frozen runner requires OpenAI, Anthropic and xAI; no silent substitution.")
    if D(cfg["hard_budget_eur"]) != D("5.00") or cfg["expected_calls"] != 42:
        raise Stop("The accepted cap and count are EUR 5 and 42 calls.")
    if cfg["max_output_tokens"] != 4096:
        raise Stop("Output cap differs from the prepared protocol.")
    if digest((ROOT / cfg["case_file"]).read_bytes()) != cfg["case_sha256"]:
        raise Stop("Case bytes changed.")
    for arm in cfg["arms"]:
        if digest((ROOT / arm["path"]).read_bytes()) != arm["sha256"]:
            raise Stop("A kernel artifact changed.")
    for model in cfg["models"]:
        if model["endpoint"] != ENDPOINTS[model["family"]]:
            raise Stop("Non-frozen endpoint refused.")
        for key in ("input_usd_per_million", "output_usd_per_million"):
            if D(model[key]) <= 0:
                raise Stop("Invalid price.")
    return cfg, cases


def body_for(model, system, user, cap):
    if model["api"] == "messages":
        return {"model": model["model"], "max_tokens": cap, "system": system,
                "messages": [{"role": "user", "content": user}]}
    return {"model": model["model"], "max_output_tokens": cap, "store": False,
            "input": [{"role": "system", "content": system},
                      {"role": "user", "content": user}]}


def reservation(cfg, model, system, user):
    # No tokenizer or count-token call: one token per UTF-8 byte plus a large framing allowance.
    input_bound = len(system.encode("utf-8")) + len(user.encode("utf-8")) + 4096
    usd = (D(input_bound) * D(model["input_usd_per_million"])
           + D(cfg["max_output_tokens"]) * D(model["output_usd_per_million"])) / D(1000000)
    eur = usd * D(cfg["usd_price_safety_multiplier"]) * D(cfg["eur_per_usd_reserve_ceiling"])
    return input_bound, eur


def prepare():
    cfg, cases = configuration()
    destination = ROOT / "prepared" / "plan.json"
    if destination.exists():
        raise Stop("Frozen plan already exists. Do not overwrite it; use preflight.")
    jobs = []
    for mi, model in enumerate(cfg["models"]):
        for ci, case in enumerate(cases):
            arms = cfg["arms"] if (mi + ci) % 2 == 0 else list(reversed(cfg["arms"]))
            for arm in arms:
                kernel = (ROOT / arm["path"]).read_bytes().decode("utf-8")
                system = cfg["host_line"] + "\n\n" + kernel
                body = body_for(model, system, case["user"], cfg["max_output_tokens"])
                bound, euro = reservation(cfg, model, system, case["user"])
                jobs.append({"id": f"J{len(jobs)+1:03d}", "family": model["family"],
                             "model_requested": model["model"], "arm": arm["id"],
                             "case_id": case["id"], "endpoint": model["endpoint"],
                             "kernel_sha256": arm["sha256"], "system": system,
                             "system_sha256": digest(system.encode("utf-8")),
                             "user": case["user"], "user_sha256": digest(case["user"].encode("utf-8")),
                             "body": body, "request_sha256": digest(canonical(body)),
                             "input_token_reserve": bound, "reserved_eur": str(euro)})
    total = sum((D(j["reserved_eur"]) for j in jobs), D(0))
    if len(jobs) != 42 or total > D(cfg["hard_budget_eur"]):
        raise Stop("All-call conservative envelope would exceed EUR 5; no run prepared.")
    files = ["study.json", "cases.json", "runner.py", "RUBRIC.md", "SCORER-BRIEF.md",
             "artifacts/Strata-0-3_AI-Kernel_1.0.0_RELEASED.md",
             "artifacts/Strata-0-3_AI-Kernel_1.1.0_TEST.md"]
    frozen = {name: digest((ROOT / name).read_bytes()) for name in files}
    plan = {"created_utc": now(), "call_count": 42, "total_reserve_eur": str(total),
            "frozen_files": frozen, "sampling": "temperature/top_p/seed/reasoning omitted; provider defaults",
            "output_cap": cfg["max_output_tokens"], "jobs": jobs}
    for job in jobs:
        save(ROOT / "prepared" / "requests" / (job["id"] + ".json"), job["body"])
    save(destination, plan)
    print(f"OFFLINE prepared 42 requests; worst-case reserved envelope EUR {total:.4f}; no API calls.")


def validate_plan():
    cfg, cases = configuration()
    path = ROOT / "prepared" / "plan.json"
    plan = read(path)
    for name, expected in plan["frozen_files"].items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise Stop("Frozen input, runner, or rubric changed: " + name)
    expected_jobs = {(m["family"], a["id"], c["id"])
                     for m in cfg["models"] for a in cfg["arms"] for c in cases}
    if len(plan["jobs"]) != 42 or {(j["family"], j["arm"], j["case_id"]) for j in plan["jobs"]} != expected_jobs:
        raise Stop("Plan does not contain the exact 42 distinct cells.")
    for job in plan["jobs"]:
        model = next(m for m in cfg["models"] if m["family"] == job["family"])
        arm = next(a for a in cfg["arms"] if a["id"] == job["arm"])
        case = next(c for c in cases if c["id"] == job["case_id"])
        system = cfg["host_line"] + "\n\n" + (ROOT / arm["path"]).read_bytes().decode("utf-8")
        bound, euro = reservation(cfg, model, system, case["user"])
        if (job["system"] != system or job["user"] != case["user"]
                or job["body"] != body_for(model, system, case["user"], cfg["max_output_tokens"])
                or job["endpoint"] != model["endpoint"] or job["model_requested"] != model["model"]
                or job["input_token_reserve"] != bound or D(job["reserved_eur"]) != euro):
            raise Stop("Plan prompt, provider, or reservation differs from frozen inputs.")
        if digest(canonical(job["body"])) != job["request_sha256"]:
            raise Stop("Plan request changed.")
        if read(ROOT / "prepared" / "requests" / (job["id"] + ".json")) != job["body"]:
            raise Stop("Prepared request file changed.")
        if digest(job["system"].encode()) != job["system_sha256"] or digest(job["user"].encode()) != job["user_sha256"]:
            raise Stop("Prompt changed.")
    total = sum((D(j["reserved_eur"]) for j in plan["jobs"]), D(0))
    if total != D(plan["total_reserve_eur"]) or total > D("5"):
        raise Stop("Budget envelope invalid.")
    return cfg, plan


def preflight():
    cfg, plan = validate_plan()
    missing = [m["key_env"] for m in cfg["models"] if not os.environ.get(m["key_env"])]
    print(f"OFFLINE integrity OK; 42 cells; reserved maximum EUR {D(plan['total_reserve_eur']):.4f}.")
    print("Missing key environment variables: " + (", ".join(missing) if missing else "none"))
    print("No key values read into logs; no network requests. Model access is not verified.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Stop("HTTP redirect refused.")


def post_once(model, body, key, timeout):
    headers = {"Content-Type": "application/json"}
    if model["api"] == "messages":
        headers.update({"x-api-key": key, "anthropic-version": model["api_version"]})
    else:
        headers["Authorization"] = "Bearer " + key
    request = urllib.request.Request(model["endpoint"], data=canonical(body), headers=headers, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
            data = json.loads(response.read())
            # Only allowlisted identifiers, never arbitrary request/response headers.
            info = {k: response.headers[k] for k in ("request-id", "x-request-id") if response.headers.get(k)}
            return data, info
    except urllib.error.HTTPError as error:
        raise Stop(f"HTTP {error.code}; response body omitted; no retry.") from None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise Stop("Transport/JSON failure; charge may be uncertain; no retry.") from None


def extract(data, api):
    if api == "messages":
        text = "\n".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        finish = data.get("stop_reason")
        ok = finish == "end_turn"
    else:
        text = "\n".join(c.get("text", "") for b in data.get("output", [])
                         if b.get("type") == "message" for c in b.get("content", [])
                         if c.get("type") == "output_text")
        finish = data.get("status")
        ok = finish == "completed" and not data.get("incomplete_details")
    return text, finish, bool(ok and text.strip())


def usage_counts(data, api):
    u = data.get("usage", {})
    if not isinstance(u.get("input_tokens"), int) or not isinstance(u.get("output_tokens"), int):
        raise Stop("Missing token usage; no further calls.")
    ins = u["input_tokens"]
    if api == "messages":
        ins += int(u.get("cache_read_input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0))
    return ins, u["output_tokens"]


def run(confirm_calls, confirm_costs):
    if not confirm_calls or not confirm_costs:
        raise Stop("Paid execution requires --confirm-42-calls and --confirm-cost-inputs after Frank confirms keys/budget.")
    cfg, plan = validate_plan()
    age = (dt.datetime.now(dt.timezone.utc).date() - dt.date.fromisoformat(cfg["prices_checked_on"])).days
    if age < 0 or age > cfg["price_review_valid_days"]:
        raise Stop("Pricing review is out of date; prepare an explicitly identified successor protocol.")
    keys = {m["family"]: os.environ.get(m["key_env"], "") for m in cfg["models"]}
    if not all(keys.values()):
        raise Stop("A required key environment variable is absent; no calls.")
    secrets = list(keys.values())
    out = ROOT / "results" / "run"
    if out.exists():
        raise Stop("A run already exists; no silent rerun/resume or additional billed attempts.")
    lock = ROOT / "results" / ".run.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise Stop("A run lock exists; investigate before any paid action.") from None
    os.close(descriptor)
    state = {"started_utc": now(), "status": "running", "attempted": 0, "completed": 0,
             "reserved_eur": "0", "plan_sha256": digest((ROOT / "prepared/plan.json").read_bytes()),
             "notes": "Reservations never refunded; uncertain charges stop the campaign; no automatic retries."}
    try:
        out.mkdir()
        save(out / "run.json", {"config": cfg, "plan_sha256": state["plan_sha256"],
                                "frozen_files": plan["frozen_files"], "started_utc": state["started_utc"]})
        models = {m["family"]: m for m in cfg["models"]}
        for job in plan["jobs"]:
            reserve = D(state["reserved_eur"]) + D(job["reserved_eur"])
            if reserve > D("5") or state["attempted"] >= 42:
                raise Stop("Hard reservation cap/count reached; no next request sent.")
            model = models[job["family"]]
            # Persist the full worst-case reservation BEFORE the only send attempt.
            state.update(reserved_eur=str(reserve), attempted=state["attempted"] + 1)
            save(out / "budget-ledger.json", state)
            record = {**job, "started_utc": now(), "status": "attempt_reserved",
                      "sampling_requested": "provider defaults; temperature/top_p/seed/reasoning omitted",
                      "output_cap": cfg["max_output_tokens"]}
            target = out / "records" / (job["id"] + ".json")
            save(target, scrub(record, secrets))
            start = time.monotonic()
            try:
                data, info = post_once(model, job["body"], keys[job["family"]], cfg["timeout_seconds"])
                text, finish, valid = extract(data, model["api"])
                record.update(response=data, response_text=text, response_identifiers=info,
                              model_returned=data.get("model"), finish=finish, status="received",
                              finished_utc=now(), elapsed_seconds=time.monotonic() - start)
                save(target, scrub(record, secrets))
                ins, outs = usage_counts(data, model["api"])
                if ins < 0 or outs < 0 or ins > job["input_token_reserve"] or outs > cfg["max_output_tokens"]:
                    raise Stop("Usage exceeds conservative envelope; stop and reconcile billing.")
                if not data.get("model"):
                    raise Stop("Response omitted exact model identity; no further calls.")
                if not valid:
                    raise Stop("Truncated, empty, or otherwise incomplete response; preserved without retry.")
                actual = (D(ins) * D(model["input_usd_per_million"]) + D(outs) * D(model["output_usd_per_million"])) / D(1000000)
                record.update(status="complete", usage_cost_estimate_usd=str(actual))
                save(target, scrub(record, secrets))
                state["completed"] += 1
                save(out / "budget-ledger.json", state)
                print(f"Completed {state['completed']}/42; reserved EUR {reserve:.4f}.")
            except Stop as error:
                record.update(status="stopped", stop_reason=str(error), finished_utc=now())
                save(target, scrub(record, secrets))
                raise
        state.update(status="complete", finished_utc=now())
    except (Stop, KeyboardInterrupt) as error:
        state.update(status="stopped", stop_reason=str(error) if isinstance(error, Stop) else "Interrupted; no retry.", finished_utc=now())
        raise Stop(state["stop_reason"]) from None
    except Exception:
        state.update(status="stopped", stop_reason="Unexpected local failure; charges reserved; no retry.", finished_utc=now())
        raise Stop(state["stop_reason"]) from None
    finally:
        if out.exists():
            save(out / "budget-ledger.json", scrub(state, secrets))
        lock.unlink(missing_ok=True)


def export_blind():
    validate_plan()
    out = ROOT / "results" / "run"
    state = read(out / "budget-ledger.json")
    if state.get("status") != "complete" or state.get("completed") != 42:
        raise Stop("Run incomplete; do not present a 42-response scorer packet.")
    dest = out / "blind"
    if dest.exists():
        raise Stop("Scoring packet already exists; do not overwrite.")
    records = [read(f) for f in sorted((out / "records").glob("*.json"))]
    if len(records) != 42 or any(x.get("status") != "complete" for x in records):
        raise Stop("Expected exactly 42 complete records.")
    random.SystemRandom().shuffle(records)
    packet, mapping = [], []
    for i, record in enumerate(records, 1):
        rid = f"S{i:03d}"
        packet.append({"record_id": rid, "case_id": record["case_id"], "user": record["user"],
                       "response_text": record["response_text"]})
        mapping.append({"record_id": rid, "job_id": record["id"], "arm": record["arm"],
                        "family": record["family"], "model_requested": record["model_requested"],
                        "model_returned": record["model_returned"]})
    dest.mkdir()
    save(dest / "SCORING-PACKET.json", packet)
    save(out / "UNBLIND-MAP-KEEP-FROM-SCORER.json", mapping)
    for name in ("RUBRIC.md", "SCORER-BRIEF.md"):
        (dest / name).write_bytes((ROOT / name).read_bytes())
    print("Exported 42 shuffled responses with arm/provider/model labels removed; arm inference from text remains possible.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "preflight", "run", "export-blind"])
    parser.add_argument("--confirm-42-calls", action="store_true")
    parser.add_argument("--confirm-cost-inputs", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "prepare": prepare()
        elif args.command == "preflight": preflight()
        elif args.command == "run": run(args.confirm_42_calls, args.confirm_cost_inputs)
        else: export_blind()
    except Stop as error:
        print("STOP: " + str(error), file=sys.stderr)
        return 2
    except Exception:
        # Do not print exception objects/tracebacks that could contain credential-bearing headers.
        print("STOP: unexpected local error; no automatic retry. Inspect local inputs and ledger without printing keys.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
