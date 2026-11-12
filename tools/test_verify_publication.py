"""Offline regressions for source identity, including a refreshed-manifest bypass."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publication_verifier", SOURCE / "tools/verify_publication.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)
EXCERPT = "evaluation/comprehension/proposed/USE-FOR-COMPREHENSION.md"


class ProvenanceRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="strata-publication-integrity-")
        self.root = Path(self.temp.name) / "payload"
        shutil.copytree(SOURCE, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(mock.patch.object(verify, "ROOT", self.root))
        self.stack.enter_context(mock.patch.object(verify.reconstruction, "ROOT", self.root))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(mock.patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("Network forbidden")))

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def refresh_manifest(self):
        path = self.root / "PUBLICATION-MANIFEST.json"
        data = verify.load(path)
        data["files"] = {f.relative_to(self.root).as_posix(): verify.sha(f)
                         for f in self.root.rglob("*") if f.is_file() and f != path}
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def declare_modification(self, name, description):
        path = self.root / "evaluation/PROVENANCE.json"
        data = verify.load(path)
        data["modified_exports"][name] = description
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def relocate_signature(self):
        path = self.root / EXCERPT
        original = path.read_text(encoding="utf-8")
        signature = next(line for line in original.splitlines() if line.startswith("— Frank Böhm"))
        changed = original.replace("\n\n" + signature, "", 1).rstrip() + "\n" + signature + "\n"
        self.assertNotEqual(original, changed)
        path.write_text(changed, encoding="utf-8", newline="\n")

    def test_unmodified_publication_passes(self):
        self.refresh_manifest()
        verify.main()

    def test_relocated_excerpt_rejected_despite_updated_manifest_and_byte_identical_label(self):
        self.relocate_signature()
        self.declare_modification(EXCERPT, "byte-identical")
        self.refresh_manifest()
        with self.assertRaisesRegex(AssertionError, "Original-source hash mismatch"):
            verify.main()

    def test_any_claimed_byte_identical_export_is_checked_against_origin(self):
        name = "evaluation/runners/check-run_20261111/RUBRIC.md"
        path = self.root / name
        path.write_bytes(path.read_bytes() + b"\n")
        self.declare_modification(name, "byte-identical")
        self.refresh_manifest()
        with self.assertRaisesRegex(AssertionError, "Original-source hash mismatch"):
            verify.main()

    def test_reviewed_input_cannot_be_exempted_as_a_presentation_change(self):
        self.relocate_signature()
        self.declare_modification(EXCERPT, "Attribution relocated for presentation")
        self.refresh_manifest()
        with self.assertRaisesRegex(AssertionError, "Original-source hash mismatch"):
            verify.main()


if __name__ == "__main__":
    unittest.main()
