from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.p08 import validate_object_target_batch_tooling as validator


FILES = [
    validator.ENGINE,
    validator.WRAPPER,
    validator.BUNDLE_GENERATOR,
    validator.INSERT_GENERATOR,
    validator.ORACLE,
    validator.GITIGNORE,
]


def copy_files(root: Path) -> None:
    for relative in FILES:
        source = validator.ROOT / relative
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())


class ObjectTargetBatchToolingTests(unittest.TestCase):
    def test_current_tooling_covers_all_direct_rows_with_bounded_restart(self) -> None:
        value = validator.validate()
        self.assertEqual(value["state"], "pass", value)
        self.assertEqual(value["direct_feature_count"], 41)
        self.assertEqual(value["representative_retry_count"], 3)
        self.assertTrue(value["bounded_session_restart"])
        self.assertEqual(value["actual_hangul_2020"], "not_run")
        self.assertFalse(value["p08_complete"])

    def test_missing_feature_and_unbounded_com_creation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.ENGINE
            text = target.read_text(encoding="utf-8")
            text = text.replace("'OBJ-041', 'OBJ-031'", "'OBJ-031'")
            text += "\n$extra = New-Object -ComObject $ProgId\n"
            target.write_text(text, encoding="utf-8")
            value = validator.validate(root)
            self.assertIn("expected_feature_order", value["errors"])
            self.assertIn("bounded_com_creation_paths", value["errors"])

    def test_target_and_security_identity_drift_fail_closed(self) -> None:
        for needle, expected in [
            (validator.HWP_SHA256, "hwp_identity_pin"),
            (validator.SECURITY_MODULE_SHA256, "security_module_pin"),
            (validator.MANIFEST_SHA256, "manifest_pin"),
        ]:
            with self.subTest(needle=needle), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                copy_files(root)
                target = root / validator.ENGINE
                target.write_text(
                    target.read_text(encoding="utf-8").replace(needle, "0" * 64),
                    encoding="utf-8",
                )
                self.assertIn(expected, validator.validate(root)["errors"])

    def test_private_evidence_and_retry_controls_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.GITIGNORE
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "/implementation/p08/evidence/private/\n", ""
                ),
                encoding="utf-8",
            )
            self.assertIn("private_evidence_ignore", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.ENGINE
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "@('OBJ-002', 'OBJ-024', 'OBJ-010')", "@('OBJ-002')"
                ),
                encoding="utf-8",
            )
            self.assertIn("representative_retry_set", validator.validate(root)["errors"])

    def test_document_must_be_active_before_each_open(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.ENGINE
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "        [void]$document.SetActive_XHwpDocument()\n", "", 1
                ),
                encoding="utf-8",
            )
            self.assertIn("active_document_before_open", validator.validate(root)["errors"])

    def test_stable_case_ids_are_unique_without_positional_renumbering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.ENGINE
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "$seenCaseIds.ContainsKey($caseId)", "$false"
                ),
                encoding="utf-8",
            )
            self.assertIn("unique_case_id_guard", validator.validate(root)["errors"])

    def test_first_open_failure_aborts_instead_of_cycling_all_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.ENGINE
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "$index -eq 0 -and $caseFailed -and",
                    "$false -and $caseFailed -and",
                ),
                encoding="utf-8",
            )
            self.assertIn("first_open_fail_fast_guard", validator.validate(root)["errors"])

    def test_wrapper_preserves_partial_failure_trace_and_cleans_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.WRAPPER
            text = target.read_text(encoding="utf-8")
            text = text.replace("if (-not $child.HasExited)", "if ($false)")
            text = text.replace("@($engineValue.cases).Count -le 41", "$false")
            text = text.replace("engine_stderr_error_code", "engine_error_hidden")
            target.write_text(text, encoding="utf-8")
            value = validator.validate(root)
            self.assertIn("interrupted_worker_cleanup", value["errors"])
            self.assertIn("failed_trace_case_bound", value["errors"])
            self.assertIn("sanitized_engine_error_projection", value["errors"])

    def test_oracle_asset_path_and_namespace_guards_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_files(root)
            target = root / validator.ORACLE
            text = target.read_text(encoding="utf-8")
            text = text.replace(
                "source_inventory != target_inventory",
                "source_inventory == target_inventory",
            ).replace("source.tag != target.tag", "source.tag == target.tag")
            target.write_text(text, encoding="utf-8")
            value = validator.validate(root)
            self.assertIn("oracle_resource_inventory_guard", value["errors"])
            self.assertIn("oracle_namespace_guard", value["errors"])


if __name__ == "__main__":
    unittest.main()
