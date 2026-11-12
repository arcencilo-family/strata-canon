"""Offline payload integrity and exact evaluation reconstruction. No model calls."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reconstruction", ROOT / "tools/reconstruct_evaluation.py")
reconstruction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reconstruction)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_origins(root, provenance):
    modifications = provenance["modified_exports"]
    assert set(modifications).issubset(provenance["origins"]), "Modified export has no source identity"
    reviewed_inputs = {"evaluation/comprehension/brief.md",
                       "evaluation/comprehension/proposed/USE-FOR-COMPREHENSION.md"}
    for name, origin in provenance["origins"].items():
        path = root / name
        assert path.is_file(), "Missing source export: " + name
        declaration = modifications.get(name, "byte-identical").strip()
        assert declaration, "Empty transformation declaration: " + name
        # A literal byte-identical declaration never grants an exemption. Actual
        # comprehension inputs stay exact even if someone labels a change otherwise.
        if name in reviewed_inputs or declaration.casefold() == "byte-identical":
            assert sha(path) == origin, "Original-source hash mismatch: " + name
        else:
            assert sha(path) != origin, "Unnecessary modified-export declaration: " + name


def main():
    receipt = load(ROOT / "PUBLICATION-MANIFEST.json")
    actual = {f.relative_to(ROOT).as_posix() for f in ROOT.rglob("*")
              if f.is_file() and ".git" not in f.relative_to(ROOT).parts}
    assert actual == set(receipt["files"]) | {"PUBLICATION-MANIFEST.json"}, "Unexpected or missing payload file"
    for name, expected in receipt["files"].items():
        assert sha(ROOT / name) == expected, "Changed payload: " + name
    provenance = load(ROOT / "evaluation/PROVENANCE.json")
    verify_origins(ROOT, provenance)
    names = {"Stratum-0_Primitives.md", "Stratum-1_Minimal-Dynamics.md", "Stratum-2_Orientation.md",
             "Stratum-3_Operational-Permissions.md", "Strata-0-3_AI-Kernel.md", "CANON-MANIFEST.md"}
    assert {f.name for f in (ROOT / "canon").iterdir()} == names
    manifest = (ROOT / "canon/CANON-MANIFEST.md").read_text(encoding="utf-8")
    rows = re.findall(r"\| `([^`]+\.md)` \| [^|]+ \| (\d+) \| `([A-F0-9]{64})` \|", manifest)
    assert len(rows) == 5
    for name, count, expected in rows:
        f = ROOT / "canon" / name
        assert f.stat().st_size == int(count) and sha(f) == expected, "Canon receipt mismatch: " + name
    kernel = (ROOT / "canon/Strata-0-3_AI-Kernel.md").read_text(encoding="utf-8")
    assert "TEST ARTIFACT" not in kernel and "candidate-id:" not in kernel
    assert kernel.count("Offered by Frank Böhm, Arcencilo Family Project.") == 1
    assert kernel.rfind("## Authorship") > kernel.rfind("### Boundary of Stratum 3")
    assert "Frank Böhm" not in kernel.split("## Use", 1)[1].split("## Stratum 0", 1)[0]
    forbidden = [r"(?i)(?:[A-Z]:[\\/]+Users[\\/]|/home/|/mnt/c/Users/|THE-VAULT)",
                 r"(?i)(?:sk-(?:proj-|ant-|live-)?[A-Za-z0-9_-]{18,}|xai-[A-Za-z0-9_-]{18,}|github_pat_[A-Za-z0-9_]{15,}|ghp_[A-Za-z0-9]{20,})"]
    for name in actual:
        f = ROOT / name
        content = f.read_text(encoding="utf-8")
        if name != "tools/verify_publication.py":
            assert not any(re.search(pattern, content) for pattern in forbidden), "Export scan finding: " + name
        if f.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", content):
                target = target.split("#", 1)[0]
                if target and "://" not in target and not target.startswith("mailto:"):
                    assert (f.parent / unquote(target.strip("<>"))).exists(), "Broken local link: " + name
    all_rows = {}
    for study, count, complete in [("initial-42", 43, 42), ("diagnostic-30", 30, 30)]:
        folder = ROOT / "evaluation/data" / study
        calls = reconstruction.records(study)
        assert len(calls) == count and sum(x["status"] == "complete" for x in calls) == complete
        assert len({(x["phase"], x["id"]) for x in calls}) == count
        bodies = { (x["phase"], x["id"]): reconstruction.request(study, x, calls) for x in calls }
        for body in bodies.values():
            assert "Authorization" not in body and "x-api-key" not in body
        inputs = reconstruction.scorer_inputs(study, calls)
        for name, value in inputs.items():
            proof = provenance["reconstructed_inputs"][study][name]
            assert hashlib.sha256(reconstruction.historical_bytes(value, proof)).hexdigest().upper() == proof["sha256"]
        packet = inputs["SCORING-PACKET.json"]
        scores = load(folder / "SCORING-INITIAL.json")["scores"]
        targets = 42 if study == "initial-42" else 20
        by_id = {x["record_id"]: x for x in packet}
        assert len(packet) == len(scores) == len(by_id) == targets
        assert {x["record_id"] for x in scores} == set(by_id)
        for score in scores:
            assert score["evidence_quote"] in by_id[score["record_id"]]["response_text"]
        mapping = load(folder / "score-map.json")
        if isinstance(mapping, dict):
            mapping = mapping["records"]
        for m in mapping:
            selected = [x for x in calls if x["id"] == m["job_id"] and x["status"] == "complete"]
            assert len(selected) == 1 and m["arm"] == selected[0]["arm"]
            assert by_id[m["record_id"]]["response_text"] == selected[0]["response_text"]
        all_rows[study] = calls
    diagnostic = all_rows["diagnostic-30"]
    lookup = {x["id"]: x for x in diagnostic}
    assert sum(x["kind"] == "C6_setup" for x in diagnostic) == 10
    assert sum(x["kind"] == "C6_stop" for x in diagnostic) == 10
    for rec in diagnostic:
        if rec["kind"] == "C6_stop":
            prior = lookup[rec["dependency"]]
            body = reconstruction.request("diagnostic-30", rec, diagnostic)
            assert "\n".join(b["text"] for b in body["messages"][1]["content"]) == prior["response_text"]
            assert rec["arm"] == prior["arm"] and rec["repeat"] == prior["repeat"]
    supplement = load(ROOT / "evaluation/data/diagnostic-30/SCORING-CONTEXT-SUPPLEMENT.json")
    packet = {x["record_id"]: x for x in reconstruction.scorer_inputs("diagnostic-30", diagnostic)["SCORING-PACKET.json"]}
    assert len(supplement["c4_targets"]) == 10
    for score in supplement["c4_targets"]:
        for quote in score["supplement"]["evidence_quotes"]:
            assert quote in packet[score["record_id"]]["response_text"]
    print("OFFLINE OK: canon and payload hashes; links and export scan; 73 exact request reconstructions / 72 answers; historical scorer inputs; scores and stop histories.")
    print("Package integrity only; not alignment, behavioral validation or release authorization.")


if __name__ == "__main__":
    main()
