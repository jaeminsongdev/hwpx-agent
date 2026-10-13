"""One live preservation check and seven verifier rejection/manifest tests; NOT native evidence."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p98_bytes", Path(__file__).parents[1] / "verify_review_delete_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ReviewDeleteProgressTests(unittest.TestCase):
    def test_live_whole_inherited_bytes_and_parent_inverses(self):
        result = M.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1269)
        self.assertEqual(result["unchanged_previous_source_files"], 825)
        self.assertEqual(len(result["whole_parent_preimages"]), 3)

    def test_forged_previous_checkpoint_is_rejected(self):
        with patch.object(M.BASE, "pin", return_value={"bytes": 15167, "sha256": "0" * 64}):
            with self.assertRaisesRegex(ValueError, "previous_checkpoint_drift"):
                M.inherited()

    def test_no_archive_fallback_for_official_or_captured_inputs(self):
        record = {"path": "not-a-source-parent", "bytes": 1, "sha256": "0" * 64}
        with patch.object(M.BASE, "exact", return_value=False) as check:
            self.assertFalse(M.exact_inherited(record, False))
            check.assert_called_once_with(record)

    def test_changed_parent_requires_exact_whole_archive(self):
        record = {"path": M.PARENTS[0], "bytes": 1, "sha256": "0" * 64}
        with patch.object(M.BASE, "exact", return_value=False):
            self.assertFalse(M.exact_inherited(record, True))

    @staticmethod
    def fixture():
        prior = {"previous_checkpoint": {"path": M.PREVIOUS, "bytes": 15167, "sha256": "x"}}
        data = {"inherited_checkpoint": prior["previous_checkpoint"], "current_source_files_count": 840,
                "qualification": {"P09_gate": "OPEN"}}
        for key in ("native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                    "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                    "execution_publication_authority", "full_typed_comment_compiler_route_connected", "P11_capability_qualified"):
            data["qualification"][key] = False
        for key, paths in M.REQUIRED_GROUPS.items():
            data[key] = [{"path": path, "bytes": 1, "sha256": "x"} for path in sorted(paths)]
        return data, prior

    def test_mocked_exact_declared_current_coverage(self):
        data, prior = self.fixture()
        with patch.object(M.BASE, "exact", return_value=True):
            self.assertEqual(M.verify_current_manifest(data, prior),
                             {"source_delta": 15, "source_archives_added": 9,
                              "predecessor_receipts_added": 2, "current_executables": 15})

    def test_mocked_missing_duplicate_and_raw_drift_reject(self):
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

    def test_mocked_rebind_and_wrong_count_reject(self):
        data, prior = self.fixture()
        for field, value in (("inherited_checkpoint", {}), ("current_source_files_count", 839)):
            changed = copy.deepcopy(data)
            changed[field] = value
            with self.assertRaises(ValueError):
                M.verify_current_manifest(changed, prior)

    def test_mocked_every_unproved_acceptance_and_gate_promotion_reject(self):
        data, prior = self.fixture()
        for field in data["qualification"]:
            changed = copy.deepcopy(data)
            changed["qualification"][field] = "PASS" if field == "P09_gate" else True
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)


if __name__ == "__main__":
    unittest.main()
