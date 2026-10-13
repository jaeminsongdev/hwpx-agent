"""Whole-byte/inventory claim guards; not native/SQL/full rich comment acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p106_bytes", Path(__file__).parents[1] / "verify_filled_review_table_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FilledReviewTableProgressTests(unittest.TestCase):
    def test_live_prior_raw_and_whole_parent_inverse(self):
        result = M.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1644)
        self.assertEqual(result["unchanged_previous_source_files"], 921)
        self.assertEqual(len(result["whole_parent_preimages"]), 1)
        self.assertTrue(result["previous_unchanged_audit_passed_on_exact_parent_preimages"])

    def test_only_declared_parent_uses_preimage(self):
        view = M.PreviousReadView(M.ROOT)
        for path in M.PARENTS:
            self.assertEqual(view / path, M.ROOT / (M.ARCHIVE + path))
        for path in (M.PREVIOUS, M.CURRENT, "PLANS.md", "not-a-parent"):
            self.assertEqual(view / path, M.ROOT / path)

    def test_roots_restore_on_prior_failure(self):
        module, base = M.P105.ROOT, M.BASE.ROOT
        with patch.object(M.P105, "current", side_effect=ValueError("rejected")):
            with self.assertRaises(ValueError):
                M.previous_audit()
        self.assertIs(M.P105.ROOT, module)
        self.assertIs(M.BASE.ROOT, base)

    def test_whole_preimage_and_exact_single_addition_required(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "parent_whole_preimage_drift"):
                M.parent_inverses({p: {"path": p} for p in M.PARENTS})
        path = M.PARENTS[0]
        current = (M.ROOT / path).read_bytes()
        expected = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
        self.assertEqual(M.restored_parent(path, current), expected)
        self.assertNotEqual(M.restored_parent(path, current + b"// unexpected change\n"), expected)
        for change in (current.replace(b"pub mod filled_output;\n", b""), current + b"pub mod filled_output;\n"):
            with self.assertRaises(ValueError):
                M.restored_parent(path, change)

    @staticmethod
    def fixture():
        prior = {"previous_checkpoint": {"path": M.PREVIOUS, "bytes": 9161, "sha256": "x"}}
        data = {"inherited_checkpoint": prior["previous_checkpoint"], "current_source_files_count": 932,
                "qualification": {"P09_gate": "OPEN", "actual_new_table_typed_cells_source_output": True,
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
                             {"source_delta": 11, "source_archives_added": 4,
                              "predecessor_receipts_added": 2, "current_executables": 22})

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
        for key, value in (("inherited_checkpoint", {}), ("current_source_files_count", 931)):
            changed = copy.deepcopy(data)
            changed[key] = value
            with self.assertRaises(ValueError):
                M.verify_current_manifest(changed, prior)

    def test_mock_unproven_claims_or_missing_output_reject(self):
        data, prior = self.fixture()
        for key in M.FALSE_QUALIFICATIONS + ("P09_gate", "actual_new_table_typed_cells_source_output"):
            changed = copy.deepcopy(data)
            changed["qualification"][key] = ("PASS" if key == "P09_gate" else key != "actual_new_table_typed_cells_source_output")
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)

    def test_mock_foreign_duplicate_and_unfrozen_executables_reject(self):
        data, prior = self.fixture()
        for value in (data["current_executables"][1]["path"], "target/foreign.exe"):
            changed = copy.deepcopy(data)
            changed["current_executables"][0]["path"] = value
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)
        with patch.object(M, "EXECUTABLES", []):
            with self.assertRaisesRegex(ValueError, "unfrozen_executable_inventory"):
                M.verify_current_manifest(data, prior)


if __name__ == "__main__":
    unittest.main()
