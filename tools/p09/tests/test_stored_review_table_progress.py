"""Whole-byte/inventory tests, not durable SQL/native/atomic publication."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p105_bytes", Path(__file__).parents[1] / "verify_stored_review_table_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class StoredReviewTableProgressTests(unittest.TestCase):
    def test_live_prior_raw_and_whole_parent_inverses(self):
        result = M.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1617)
        self.assertEqual(result["unchanged_previous_source_files"], 909)
        self.assertEqual(len(result["whole_parent_preimages"]), 2)
        self.assertTrue(result["previous_unchanged_audit_passed_on_exact_parent_preimages"])

    def test_only_declared_parents_use_preimages(self):
        view = M.PreviousReadView(M.ROOT)
        for path in M.PARENTS:
            self.assertEqual(view / path, M.ROOT / (M.ARCHIVE + path))
        for path in (M.PREVIOUS, M.CURRENT, "PLANS.md", "not-a-parent"):
            self.assertEqual(view / path, M.ROOT / path)

    def test_roots_restore_on_prior_failure(self):
        module, base = M.P104.ROOT, M.BASE.ROOT
        with patch.object(M.P104, "current", side_effect=ValueError("rejected")):
            with self.assertRaises(ValueError):
                M.previous_audit()
        self.assertIs(M.P104.ROOT, module)
        self.assertIs(M.BASE.ROOT, base)

    def test_exact_preimage_required_no_original_verification_removed(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "parent_whole_preimage_drift"):
                M.parent_inverses({p: {"path": p} for p in M.PARENTS})
        path = M.PARENTS[0]
        current = (M.ROOT / path).read_bytes()
        expected = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
        self.assertEqual(M.restored_parent(path, current), expected)
        changed = current.replace(b"let fresh = self.source.fresh_source(provider, now)?;", b"// bypassed", 1)
        self.assertNotEqual(M.restored_parent(path, changed), expected)
        with self.assertRaises(ValueError):
            M.restored_parent(path, current.replace(b"pub mod table_output;\n", b""))

    @staticmethod
    def fixture():
        prior = {"previous_checkpoint": {"path": M.PREVIOUS, "bytes": 19684, "sha256": "x"}}
        data = {"inherited_checkpoint": prior["previous_checkpoint"], "current_source_files_count": 922,
                "qualification": {"P09_gate": "OPEN", "stored_source_and_template_table_output_authenticated": True,
                                  **{k: False for k in M.FALSE_QUALIFICATIONS}}}
        required = {"source_delta": set(M.PARENTS + M.NEW_SOURCES), "source_archives_added": set(M.ARCHIVES),
                    "predecessor_receipts_added": set(M.PREDECESSORS), "current_executables": set(M.EXECUTABLES)}
        for key, paths in required.items():
            data[key] = [{"path": p, "bytes": 1, "sha256": "x"} for p in sorted(paths)]
        return data, prior

    def test_mock_complete_scope(self):
        data, prior = self.fixture()
        with patch.object(M.BASE, "exact", return_value=True):
            self.assertEqual(M.verify_current_manifest(data, prior),
                             {"source_delta": 13, "source_archives_added": 6,
                              "predecessor_receipts_added": 2, "current_executables": 6})

    def test_mock_missing_duplicate_raw_and_wrong_coverage_reject(self):
        data, prior = self.fixture()
        for key in ("source_delta", "source_archives_added", "predecessor_receipts_added", "current_executables"):
            for variant in ("missing", "duplicate", "raw"):
                changed = copy.deepcopy(data)
                if variant == "missing":
                    changed[key].pop()
                if variant == "duplicate":
                    changed[key].append(changed[key][0])
                with patch.object(M.BASE, "exact", return_value=variant != "raw"):
                    with self.assertRaises(ValueError):
                        M.verify_current_manifest(changed, prior)
        for key, value in (("inherited_checkpoint", {}), ("current_source_files_count", 921)):
            changed = copy.deepcopy(data)
            changed[key] = value
            with self.assertRaises(ValueError):
                M.verify_current_manifest(changed, prior)

    def test_mock_unproven_claims_or_missing_authentication_reject(self):
        data, prior = self.fixture()
        for key in M.FALSE_QUALIFICATIONS + ("P09_gate", "stored_source_and_template_table_output_authenticated"):
            changed = copy.deepcopy(data)
            changed["qualification"][key] = ("PASS" if key == "P09_gate" else key != "stored_source_and_template_table_output_authenticated")
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)

    def test_mock_foreign_and_duplicate_executables_reject(self):
        data, prior = self.fixture()
        for value in (data["current_executables"][1]["path"], "target/foreign.exe"):
            changed = copy.deepcopy(data)
            changed["current_executables"][0]["path"] = value
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)


if __name__ == "__main__":
    unittest.main()

