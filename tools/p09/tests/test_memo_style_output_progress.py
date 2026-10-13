"""Verifier rejection checks, not HWPX/native semantic proof."""
import importlib.util
import copy
from pathlib import Path
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("p96", Path(__file__).resolve().parents[1] / "verify_memo_style_output_progress.py")
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class PreservationTests(unittest.TestCase):
    def test_current_whole_parent_preimages_are_exact(self):
        result = VERIFIER.previous()
        self.assertEqual(result["previous_raw_pin_entries"], 1183)
        self.assertEqual(result["unchanged_previous_source_files"], 797)
        self.assertEqual(len(result["whole_parent_preimages"]), 6)
        self.assertTrue(result["parent_inverse_exact"])

    def test_previous_checkpoint_cannot_be_refreshed_to_claim_preservation(self):
        original = VERIFIER.BASE.pin

        def altered(path):
            record = original(path)
            return {**record, "sha256": "0" * 64} if path == VERIFIER.PREVIOUS else record

        with mock.patch.object(VERIFIER.BASE, "pin", altered):
            with self.assertRaisesRegex(ValueError, "previous_checkpoint_drift"):
                VERIFIER.previous()

    def test_native_cached_source_pin_drift_is_not_accepted_as_an_archived_parent(self):
        original = VERIFIER.BASE.pin

        def altered(path):
            record = original(path)
            return {**record, "sha256": "0" * 64} if path.endswith("/OWPML/Class/Head/MemoShapeType.cpp") else record

        with mock.patch.object(VERIFIER.BASE, "pin", altered):
            with self.assertRaisesRegex(ValueError, "previous_raw_pin_not_preserved"):
                VERIFIER.previous()


class CurrentManifestTests(unittest.TestCase):
    """Manifest scope rejection only; mocking byte checks is not live preservation evidence."""
    def setUp(self):
        self.inherited = {"previous_checkpoint": {
            "path": VERIFIER.PREVIOUS, "bytes": 253422,
            "sha256": "9f21a4848e38c89b6ef5858cb0fe668d7a67ca6bb0abdd765cb9fd46d2d65f99",
        }}
        self.data = {
            "inherited_checkpoint": copy.deepcopy(self.inherited["previous_checkpoint"]),
            "current_source_files_count": 815,
            "qualification": {"P09_gate": "OPEN", **{key: False for key in (
                "native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                "execution_publication_authority",
            )}},
            **{key: [{"path": path, "bytes": 1, "sha256": "0" * 64} for path in sorted(paths)]
               for key, paths in VERIFIER.REQUIRED_GROUPS.items()},
        }

    def verify_scope(self, data):
        with mock.patch.object(VERIFIER.BASE, "exact", return_value=True):
            return VERIFIER.verify_current_manifest(data, self.inherited)

    def test_complete_declared_scope_requires_all_four_groups(self):
        self.assertEqual(self.verify_scope(self.data), {
            "source_delta": 18, "source_archives_added": 10,
            "predecessor_receipts_added": 2, "current_executables": 9,
        })

    def test_omitted_or_substituted_source_archive_predecessor_or_executable_is_rejected(self):
        for key in VERIFIER.REQUIRED_GROUPS:
            for mode in ("omit", "substitute"):
                with self.subTest(key=key, mode=mode):
                    data = copy.deepcopy(self.data)
                    if mode == "omit":
                        data[key].pop()
                    else:
                        data[key][0]["path"] = "unrelated-valid-looking-file"
                    with self.assertRaisesRegex(ValueError, "current_group_coverage_drift"):
                        self.verify_scope(data)

    def test_inherited_checkpoint_cannot_be_rebound(self):
        for key, value in (("path", "another-checkpoint"), ("bytes", 1), ("sha256", "0" * 64)):
            with self.subTest(key=key):
                data = copy.deepcopy(self.data)
                data["inherited_checkpoint"][key] = value
                with self.assertRaisesRegex(ValueError, "inherited_checkpoint_binding_drift"):
                    self.verify_scope(data)

    def test_coverage_counts_or_unproven_acceptance_cannot_be_promoted(self):
        data = copy.deepcopy(self.data)
        data["current_source_files_count"] = 814
        with self.assertRaisesRegex(ValueError, "current_source_coverage_drift"):
            self.verify_scope(data)
        for key in self.data["qualification"]:
            with self.subTest(key=key):
                data = copy.deepcopy(self.data)
                data["qualification"][key] = "CLOSED" if key == "P09_gate" else True
                with self.assertRaises(ValueError):
                    self.verify_scope(data)

    def test_duplicate_or_byte_drifted_entry_is_rejected(self):
        for key in VERIFIER.REQUIRED_GROUPS:
            with self.subTest(key=key):
                data = copy.deepcopy(self.data)
                data[key].append(copy.deepcopy(data[key][0]))
                with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                    self.verify_scope(data)
        with mock.patch.object(VERIFIER.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                VERIFIER.verify_current_manifest(self.data, self.inherited)


if __name__ == "__main__":
    unittest.main()
