"""Byte/inventory tamper tests, NOT SQL/native/table-output acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("p103_bytes", Path(__file__).parents[1] / "verify_review_table_context_progress.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ReviewTableContextProgressTests(unittest.TestCase):
    def test_live_unchanged_prior_audit_and_whole_parent_inverses(self):
        result = M.inherited()
        self.assertEqual(result["inherited_raw_pin_entries"], 1479)
        self.assertEqual(result["unchanged_previous_source_files"], 886)
        self.assertEqual(len(result["whole_parent_preimages"]), 4)
        self.assertTrue(result["previous_unchanged_audit_passed_on_exact_parent_preimages"])

    def test_only_four_parents_route_to_prior_preimages(self):
        view = M.PreviousReadView(M.ROOT)
        for path in M.PARENTS:
            self.assertEqual(view / path, M.ROOT / (M.ARCHIVE + path))
        for path in (M.PREVIOUS, M.CURRENT, "PLANS.md", "not-a-parent"):
            self.assertEqual(view / path, M.ROOT / path)

    def test_prior_roots_restore_on_audit_failure(self):
        module, base = M.P102.ROOT, M.BASE.ROOT
        with patch.object(M.P102, "current", side_effect=ValueError("rejected")):
            with self.assertRaises(ValueError):
                M.previous_audit()
        self.assertIs(M.P102.ROOT, module)
        self.assertIs(M.BASE.ROOT, base)

    def test_exact_preimage_required_and_undeclared_original_edits_not_removed(self):
        with patch.object(M.BASE, "exact", return_value=False):
            with self.assertRaisesRegex(ValueError, "parent_whole_preimage_drift"):
                M.parent_inverses({p: {"path": p} for p in M.PARENTS})
        path = M.PARENTS[2]
        current = (M.ROOT / path).read_bytes()
        expected = (M.ROOT / (M.ARCHIVE + path)).read_bytes()
        self.assertEqual(M.restored_parent(path, current), expected)
        tampered = current.replace(b"require_template_profile(&template, &template_pagination)?;", b"// bypassed original guard", 1)
        self.assertNotEqual(M.restored_parent(path, tampered), expected)
        with self.assertRaises(ValueError):
            M.restored_parent(path, current.replace(b"// END source-bound review context.\n\n", b""))

    @staticmethod
    def fixture():
        prior = {"previous_checkpoint": {"path": M.PREVIOUS, "bytes": 14128, "sha256": "x"}}
        data = {"inherited_checkpoint": prior["previous_checkpoint"], "current_source_files_count": 900,
                "qualification": {"P09_gate": "OPEN", **{k: False for k in M.FALSE_QUALIFICATIONS}}}
        required = {"source_delta": set(M.PARENTS + M.NEW_SOURCES),
                    "source_archives_added": {M.ARCHIVE + p for p in M.PARENTS} | M.FAILURE_ARCHIVES,
                    "predecessor_receipts_added": set(M.PREDECESSORS)}
        for key, paths in required.items():
            data[key] = [{"path": p, "bytes": 1, "sha256": "x"} for p in sorted(paths)]
        data["current_executables"] = [{"path": p, "bytes": 1, "sha256": "x"} for p in M.EXECUTABLES]
        return data, prior

    def test_mock_complete_manifest_coverage(self):
        data, prior = self.fixture()
        with patch.object(M.BASE, "exact", return_value=True):
            self.assertEqual(M.verify_current_manifest(data, prior),
                             {"source_delta": 14, "source_archives_added": 13,
                              "predecessor_receipts_added": 2, "current_executables": len(M.EXECUTABLES)})

    def test_mock_missing_duplicate_raw_drift_rebinding_and_count_reject(self):
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
        for key, value in (("inherited_checkpoint", {}), ("current_source_files_count", 896)):
            changed = copy.deepcopy(data)
            changed[key] = value
            with self.assertRaises(ValueError):
                M.verify_current_manifest(changed, prior)

    def test_mock_every_unsupported_qualification_promotion_rejects(self):
        data, prior = self.fixture()
        for key in data["qualification"]:
            changed = copy.deepcopy(data)
            changed["qualification"][key] = "PASS" if key == "P09_gate" else True
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)

    def test_mock_executable_scope_or_duplicate_identity_rejects(self):
        data, prior = self.fixture()
        for value in (data["current_executables"][1]["path"], "target/foreign.exe"):
            changed = copy.deepcopy(data)
            changed["current_executables"][0]["path"] = value
            with patch.object(M.BASE, "exact", return_value=True):
                with self.assertRaises(ValueError):
                    M.verify_current_manifest(changed, prior)


if __name__ == "__main__":
    unittest.main()
