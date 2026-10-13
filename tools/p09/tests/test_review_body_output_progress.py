"""Byte-audit and manifest-scope rejection tests, not native comment acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("p97", Path(__file__).resolve().parents[1] / "verify_review_body_output_progress.py")
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class InheritanceTests(unittest.TestCase):
    def test_complete_declared_raw_inheritance_and_four_parent_inverses(self):
        result = AUDIT.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1222)
        self.assertEqual(result["unchanged_previous_source_files"], 811)
        self.assertEqual(len(result["whole_parent_preimages"]), 4)
        self.assertTrue(result["parent_inverse_exact"])

    def test_previous_whole_checkpoint_cannot_be_refreshed(self):
        original = AUDIT.BASE.pin
        def changed(path):
            record = original(path)
            return {**record, "sha256": "0" * 64} if path == AUDIT.PREVIOUS else record
        with mock.patch.object(AUDIT.BASE, "pin", changed):
            with self.assertRaisesRegex(ValueError, "previous_checkpoint_drift"):
                AUDIT.inherited()

    def test_official_bytes_cannot_fall_back_to_an_unrelated_parent_archive(self):
        original = AUDIT.BASE.pin
        def changed(path):
            record = original(path)
            return {**record, "sha256": "0" * 64} if path.endswith("/OWPML/Class/Head/MemoShapeType.cpp") else record
        with mock.patch.object(AUDIT.BASE, "pin", changed):
            with self.assertRaisesRegex(ValueError, "inherited_pin_drift"):
                AUDIT.inherited()

    def test_modified_original_patch_cannot_lose_its_whole_preimage(self):
        original = AUDIT.BASE.exact
        def changed(record, path=None):
            return False if path == AUDIT.ARCHIVE + AUDIT.PARENTS[0] else original(record, path)
        with mock.patch.object(AUDIT.BASE, "exact", changed):
            with self.assertRaisesRegex(ValueError, "inherited_pin_drift"):
                AUDIT.inherited()


class CurrentScopeTests(unittest.TestCase):
    """Mocked raw checks only isolate scope rules; live --current performs actual hashing."""
    def setUp(self):
        self.prior = {"previous_checkpoint": {
            "path": AUDIT.PREVIOUS, "bytes": 12952,
            "sha256": "4aebe074bef35ecca8e5a322b308837f15228f48046a2d3381f1ee8966dc0f13",
        }}
        self.data = {"inherited_checkpoint": copy.deepcopy(self.prior["previous_checkpoint"]),
                     "current_source_files_count": 828,
                     "qualification": {"P09_gate": "OPEN", **{key: False for key in (
                         "native_executed", "actual_SQL_executed", "full_comment_product_acceptance",
                         "native_author_time_state_binding", "product_complete", "P10_new_implementation",
                         "execution_publication_authority", "full_typed_comment_compiler_route_connected",
                     )}},
                     **{key: [{"path": path, "bytes": 1, "sha256": "0" * 64} for path in sorted(paths)]
                        for key, paths in AUDIT.REQUIRED_GROUPS.items()}}

    def scoped(self, data):
        with mock.patch.object(AUDIT.BASE, "exact", return_value=True):
            return AUDIT.verify_current_manifest(data, self.prior)

    def test_required_full_delta_scope(self):
        self.assertEqual(self.scoped(self.data), {"source_delta": 17, "source_archives_added": 14,
                                                "predecessor_receipts_added": 2, "current_executables": 14})

    def test_omitted_substituted_or_duplicate_pin_in_every_group_is_rejected(self):
        for key in AUDIT.REQUIRED_GROUPS:
            for mode in ("omit", "substitute", "duplicate"):
                with self.subTest(key=key, mode=mode):
                    data = copy.deepcopy(self.data)
                    if mode == "omit": data[key].pop()
                    elif mode == "substitute": data[key][0]["path"] = "another-valid-file"
                    else: data[key].append(copy.deepcopy(data[key][0]))
                    with self.assertRaises(ValueError): self.scoped(data)
        with mock.patch.object(AUDIT.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "current_raw_pin_drift"):
                AUDIT.verify_current_manifest(self.data, self.prior)

    def test_inherited_binding_or_coverage_count_cannot_change(self):
        for key, value in (("path", "another-checkpoint"), ("bytes", 1), ("sha256", "0" * 64)):
            data = copy.deepcopy(self.data)
            data["inherited_checkpoint"][key] = value
            with self.assertRaisesRegex(ValueError, "inherited_checkpoint_binding_drift"):
                self.scoped(data)
        self.data["current_source_files_count"] = 827
        with self.assertRaisesRegex(ValueError, "current_source_coverage_drift"):
            self.scoped(self.data)

    def test_unproved_native_or_full_product_acceptance_never_promoted(self):
        for key in self.data["qualification"]:
            data = copy.deepcopy(self.data)
            data["qualification"][key] = "CLOSED" if key == "P09_gate" else True
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.scoped(data)


if __name__ == "__main__": unittest.main()
