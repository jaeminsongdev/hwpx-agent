"""Whole prior-view audit and mock manifest rejection, NOT SQL/native acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p102_bytes", Path(__file__).parents[1] / "verify_review_paragraph_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ReviewParagraphProgressTests(unittest.TestCase):
    def test_live_prior_audit_and_whole_parent_transforms(self):
        result = M.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1421)
        self.assertEqual(result["unchanged_previous_source_files"], 871)
        self.assertTrue(result["previous_unchanged_audit_passed_on_exact_parent_preimages"])

    def test_previous_read_view_routes_only_six_declared_parents(self):
        view = M.PreviousReadView(M.ROOT)
        for path in M.PARENTS:
            self.assertEqual(view / path, M.ROOT / (M.ARCHIVE + path))
        for path in (M.PREVIOUS, M.CURRENT, "PLANS.md", "not-a-parent"):
            self.assertEqual(view / path, M.ROOT / path)

    def test_predecessor_roots_restore_on_failure(self):
        original_module, original_base = M.P101.ROOT, M.BASE.ROOT
        with patch.object(M.P101, "current", side_effect=ValueError("rejected")):
            with self.assertRaises(ValueError):
                M.previous_audit()
        self.assertIs(M.P101.ROOT, original_module)
        self.assertIs(M.BASE.ROOT, original_base)

    def test_parents_require_exact_whole_preimage(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "parent_whole_preimage_drift"):
                M.parent_inverses({p: {"path": p} for p in M.PARENTS})

    @staticmethod
    def fixture():
        prior = {"previous_checkpoint": {"path": M.PREVIOUS, "bytes": 5919, "sha256": "x"}}
        data = {"inherited_checkpoint": prior["previous_checkpoint"], "current_source_files_count": 890,
                "qualification": {"P09_gate": "OPEN"}}
        for key in ("native_executed", "actual_SQL_executed", "SQL_failure_root_cause_proven",
                    "original_atomic_oracle_verified", "full_comment_product_acceptance",
                    "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                    "execution_publication_authority", "new_table_insertion_implemented",
                    "native_caret_or_visual_coordinates_verified", "full_typed_comment_compiler_route_connected"):
            data["qualification"][key] = False
        for key, paths in M.REQUIRED_GROUPS.items():
            data[key] = [{"path": p, "bytes": 1, "sha256": "x"} for p in sorted(paths)]
        return data, prior

    def test_mock_complete_declared_coverage(self):
        data, prior = self.fixture()
        with patch.object(M.BASE, "exact", return_value=True):
            self.assertEqual(M.verify_current_manifest(data, prior),
                             {"source_delta": 19, "source_archives_added": 15,
                              "predecessor_receipts_added": 2, "current_executables": 22})

    def test_mock_missing_duplicate_and_raw_drift_reject(self):
        data, prior = self.fixture()
        for variant in ("missing", "duplicate", "raw"):
            changed = copy.deepcopy(data)
            if variant == "missing":
                changed["source_delta"].pop()
            if variant == "duplicate":
                changed["source_delta"].append(changed["source_delta"][0])
            with patch.object(M.BASE, "exact", return_value=variant != "raw"):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)

    def test_mock_rebinding_and_wrong_source_count_reject(self):
        data, prior = self.fixture()
        for field, value in (("inherited_checkpoint", {}), ("current_source_files_count", 889)):
            changed = copy.deepcopy(data)
            changed[field] = value
            with self.assertRaises(ValueError):
                M.verify_current_manifest(changed, prior)

    def test_mock_every_unsupported_acceptance_promotion_reject(self):
        data, prior = self.fixture()
        for field in data["qualification"]:
            changed = copy.deepcopy(data)
            changed["qualification"][field] = "PASS" if field == "P09_gate" else True
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)


if __name__ == "__main__":
    unittest.main()
