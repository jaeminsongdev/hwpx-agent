"""Whole source/inventory and explicit claim guards; NOT native protection acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p111_bytes", Path(__file__).parents[1] / "verify_review_mutation_protection_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ReviewMutationProtectionProgressTests(unittest.TestCase):
    def test_live_prior_raw_and_original_guard_inverse(self):
        result = M.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1806)
        self.assertEqual(result["unchanged_previous_source_files"], 967)
        self.assertEqual(len(result["whole_parent_preimages"]), 4)
        self.assertTrue(result["previous_unchanged_audit_passed_on_exact_parent_preimages"])

    def test_only_declared_parent_uses_whole_preimage(self):
        view = M.PreviousReadView(M.ROOT)
        for path in M.PARENTS:
            self.assertEqual(view / path, M.ROOT / (M.ARCHIVE + path))
        for path in (M.PREVIOUS, M.CURRENT, "PLANS.md", "not-a-parent"):
            self.assertEqual(view / path, M.ROOT / path)

    def test_previous_roots_restore_after_rejection(self):
        module, base = M.P110.ROOT, M.BASE.ROOT
        with patch.object(M.P110, "current", side_effect=ValueError("rejected")):
            with self.assertRaises(ValueError):
                M.previous_audit()
        self.assertIs(M.P110.ROOT, module)
        self.assertIs(M.BASE.ROOT, base)

    def test_declared_new_sources_exist_and_documents_use_the_actual_current_phase(self):
        for path in M.NEW_SOURCES:
            self.assertTrue((M.ROOT / path).is_file(), path)
        self.assertIn("implementation/p09/P09-111_REVIEW_MUTATION_PROTECTION_POLICY.md", M.NEW_SOURCES)
        self.assertIn("implementation/p09/P09-111_REVIEW_MUTATION_PROTECTION_REPORT.md", M.NEW_SOURCES)

    def test_all_four_whole_parents_allow_only_the_exact_single_addition(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "parent_whole_preimage_drift"):
                M.parent_inverses({p: {"path": p} for p in M.PARENTS})
        for path in M.PARENTS:
            current = (M.ROOT / path).read_bytes()
            expected = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
            self.assertEqual(M.restored_parent(path, current), expected)
            self.assertNotEqual(M.restored_parent(path, current + b"// unexpected change\n"), expected)
            for original, added in M.EDITS[path]:
                added = added.encode()
                for changed in (current.replace(added, b""), current + added):
                    with self.assertRaises(ValueError):
                        M.restored_parent(path, changed)

    @staticmethod
    def fixture():
        prior = {"previous_checkpoint": {"path": M.PREVIOUS, "bytes": 13390, "sha256": "x"}}
        data = {"inherited_checkpoint": prior["previous_checkpoint"], "current_source_files_count": 980,
                "qualification": {"P09_gate": "OPEN", "observed_review_mutation_ancestors_and_consumed_subtree_protection_enforced": True,
                                  **{k: False for k in M.FALSE_QUALIFICATIONS}}}
        required = {"source_delta": set(M.PARENTS + M.NEW_SOURCES), "source_archives_added": set(M.ARCHIVES),
                    "predecessor_receipts_added": set(M.PREDECESSORS), "current_executables": set(M.EXECUTABLES)}
        for key, paths in required.items():
            data[key] = [{"path": p, "bytes": 1, "sha256": "x"} for p in sorted(paths)]
        return data, prior

    def test_mock_complete_actual_scope(self):
        data, prior = self.fixture()
        with patch.object(M.BASE, "exact", return_value=True):
            counts = M.verify_current_manifest(data, prior)
        self.assertEqual(counts["source_delta"], 13)
        self.assertEqual(counts["source_archives_added"], 17)
        self.assertEqual(counts["predecessor_receipts_added"], 2)
        self.assertEqual(counts["current_executables"], len(M.EXECUTABLES))

    def test_mock_missing_duplicate_wrong_bytes_and_coverage_reject(self):
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
        for key, value in (("inherited_checkpoint", {}), ("current_source_files_count", 979)):
            changed = copy.deepcopy(data)
            changed[key] = value
            with self.assertRaises(ValueError):
                M.verify_current_manifest(changed, prior)

    def test_mock_missing_guard_or_unproven_product_promotion_reject(self):
        data, prior = self.fixture()
        for key in M.FALSE_QUALIFICATIONS + ("P09_gate", "observed_review_mutation_ancestors_and_consumed_subtree_protection_enforced"):
            changed = copy.deepcopy(data)
            changed["qualification"][key] = "PASS" if key == "P09_gate" else key != "observed_review_mutation_ancestors_and_consumed_subtree_protection_enforced"
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)

    def test_mock_foreign_duplicate_unfrozen_executables_reject(self):
        data, prior = self.fixture()
        for value in (data["current_executables"][1]["path"], "target/foreign.exe"):
            changed = copy.deepcopy(data)
            changed["current_executables"][0]["path"] = value
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)
        with patch.object(M, "EXECUTABLES", ()):
            with self.assertRaisesRegex(ValueError, "unfrozen_executable_inventory"):
                M.verify_current_manifest(data, prior)


if __name__ == "__main__":
    unittest.main()
