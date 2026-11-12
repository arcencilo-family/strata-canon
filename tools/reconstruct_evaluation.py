"""Reconstruct archived request bodies and scorer inputs offline from shared source data."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def historical_bytes(value, proof):
    data = encoded(value)
    return data.replace(b"\n", b"\r\n") if proof["newline"] == "CRLF" else data


def records(study):
    return [json.loads(s) for s in (ROOT / "evaluation/data" / study / "attempts.jsonl").read_text(encoding="utf-8").splitlines()]


def request(study, rec, rows):
    runners = ROOT / "evaluation/runners"
    common = runners / "check-run_20261111"
    initial = load(common / "study.json")
    arm = next(a for a in initial["arms"] if a["id"] == rec["arm"])
    kernel = (common / arm["path"]).read_bytes().decode("utf-8")
    messages = []
    if study == "initial-42":
        user = next(c["user"] for c in load(common / "cases.json") if c["id"] == rec["case_id"])
        host = initial["host_line"]
        messages = [{"role": "user", "content": user}]
    else:
        diagnostic = runners / "diagnostic-proposal_20261111"
        cfg = load(diagnostic / "CONFIG.json")
        prompts = load(diagnostic / "PROMPTS.json")
        host = cfg["host_line"]
        user = prompts["C4"]["user"] if rec["kind"] == "C4" else prompts["C6"]["turn_1_user"]
        messages = [{"role": "user", "content": user}]
        if rec["kind"] == "C6_stop":
            prior = next(r for r in rows if r["id"] == rec["dependency"] and r["status"] == "complete")
            content = prior.get("assistant_content", [{"type": "text", "text": prior["response_text"]}])
            messages.extend([{"role": "assistant", "content": content},
                             {"role": "user", "content": prompts["C6"]["turn_2_user"]}])
    system = host + "\n\n" + kernel
    if rec["family"] == "anthropic":
        body = {"model": rec["model_requested"], "max_tokens": rec["output_cap"], "system": system, "messages": messages}
    else:
        body = {"model": rec["model_requested"], "max_output_tokens": rec["output_cap"], "store": False,
                "input": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    assert hashlib.sha256(canonical(body)).hexdigest().upper() == rec["request_sha256"], "Request reconstruction mismatch"
    return body


def scorer_inputs(study, rows):
    folder = ROOT / "evaluation/data" / study
    mapping = load(folder / "score-map.json")
    entries = mapping if isinstance(mapping, list) else mapping["records"]
    packet = []
    for item in entries:
        rec = next(r for r in rows if r["id"] == item["job_id"] and r["status"] == "complete")
        body = request(study, rec, rows)
        if study == "initial-42":
            user = body["messages"][0]["content"] if "messages" in body else body["input"][1]["content"]
            packet.append({"record_id": item["record_id"], "case_id": rec["case_id"], "user": user,
                           "response_text": rec["response_text"]})
        else:
            packet.append({"record_id": item["record_id"], "case_id": "C4" if rec["kind"] == "C4" else "C6",
                           "source_text_id": mapping["source_labels"][rec["arm"]],
                           "messages_before_response": body["messages"], "response_text": rec["response_text"]})
    result = {"SCORING-PACKET.json": packet}
    if study != "initial-42":
        common = ROOT / "evaluation/runners/check-run_20261111"
        cfg = load(common / "study.json")
        result["SOURCE-TEXTS.json"] = {mapping["source_labels"][a["id"]]: (common / a["path"]).read_bytes().decode("utf-8")
                                      for a in cfg["arms"]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", choices=["initial-42", "diagnostic-30"])
    parser.add_argument("--output", type=Path, required=True, help="New directory outside this repository")
    args = parser.parse_args()
    dest = args.output.resolve()
    if dest.is_relative_to(ROOT):
        parser.error("Choose a new output directory outside the repository payload.")
    rows = records(args.study)
    bodies = [(r, request(args.study, r, rows)) for r in rows]
    inputs = scorer_inputs(args.study, rows)
    provenance = load(ROOT / "evaluation/PROVENANCE.json")
    for name, value in inputs.items():
        proof = provenance["reconstructed_inputs"][args.study][name]
        assert hashlib.sha256(historical_bytes(value, proof)).hexdigest().upper() == proof["sha256"]
    dest.mkdir(parents=True, exist_ok=False)
    for rec, body in bodies:
        (dest / (rec["phase"] + "-" + rec["id"] + "-request.json")).write_bytes(encoded(body))
    for name, value in inputs.items():
        (dest / name).write_bytes(historical_bytes(value, provenance["reconstructed_inputs"][args.study][name]))
    runner = "check-run_20261111" if args.study == "initial-42" else "diagnostic-proposal_20261111"
    for name in ["RUBRIC.md", "SCORER-BRIEF.md"]:
        (dest / name).write_bytes((ROOT / "evaluation/runners" / runner / name).read_bytes())
    if args.study == "initial-42":
        (dest / "PROTOCOL-DEVIATION.md").write_bytes((ROOT / "evaluation/data/initial-42/PROTOCOL-DEVIATION.md").read_bytes())
    print(f"Reconstructed {len(bodies)} request bodies and scorer inputs; historical hashes matched. No network requests.")


if __name__ == "__main__":
    main()
