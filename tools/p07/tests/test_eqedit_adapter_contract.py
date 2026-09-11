from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools.p07 import validate_eqedit_adapter_contract as validator


class EqEditAdapterContractTests(unittest.TestCase):
    def test_repository_contract_passes_without_native_or_target_promotion(self) -> None:
        report = validator.validate()
        self.assertEqual(report["state"], "pass", report)
        self.assertEqual(report["source_locks"], 9)
        self.assertEqual(report["implementation_files"], 9)
        self.assertTrue(report["installed_source_qualified"])
        self.assertEqual(report["task"], "P07-04")
        self.assertEqual(report["direct_stage"], "unit_passed")
        self.assertFalse(report["actual_hwpx"])
        self.assertFalse(report["actual_hangul"])
        self.assertFalse(report["product_complete"])

    def test_source_implementation_migration_and_evidence_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            source = root / "implementation/p06/P06-07_TARGET_READBACK_REPORT.md"
            source.write_text(source.read_text(encoding="utf-8") + "\ntamper\n", encoding="utf-8")
            self.assertIn("source_lock_digest", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            implementation = root / "crates/equation-engine/src/eqedit.rs"
            implementation.write_text(
                implementation.read_text(encoding="utf-8").replace(
                    "RoundTripMismatch", "WeakenedRoundTrip"
                ),
                encoding="utf-8",
            )
            self.assertIn("implementation_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            (root / validator.MIGRATION).write_text("removed", encoding="utf-8")
            self.assertIn("migration_marker", validator.validate(root)["errors"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            evidence_path = root / validator.QUALIFICATION
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["installed_artifacts"][0]["sha256"] = "0" * 64
            evidence["observations"]["removed_legacy_commands"].pop()
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("qualification_artifacts", errors)
            self.assertIn("qualification_observations", errors)

    def test_duplicate_key_path_escape_and_profile_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            original = contract_path.read_text(encoding="utf-8")
            contract_path.write_text(
                original.replace("{\n", '{"schema_version":"duplicate",\n', 1),
                encoding="utf-8",
            )
            self.assertEqual(validator.validate(root)["errors"], ["contract_json_or_path"])

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["source_locks"][0]["path"] = "../outside.md"
            contract["parser_profile"]["adjacency"] = "implicit_multiplication"
            contract["compiler_profile"]["roundtrip"] = "unchecked"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("source_lock_path", errors)
            self.assertIn("source_lock_paths_exact", errors)
            self.assertIn("parser_profile", errors)
            self.assertIn("compiler_profile", errors)

    def test_limits_nonclaims_qualification_and_failure_policy_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            contract_path = root / validator.CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["default_limits"]["parse_depth"] = 0
            contract["qualification_boundary"]["new_engine_native_execution"] = True
            contract["semantic_corpus"]["native_roundtrip"] = True
            contract["not_claimed"]["new_engine_hangul_2020_execution"] = True
            contract["gate_decision"]["actual_hangul"] = True
            contract["failure_policy"].pop()
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("default_limits", errors)
            self.assertIn("qualification_boundary", errors)
            self.assertIn("semantic_corpus", errors)
            self.assertIn("not_claimed", errors)
            self.assertIn("gate_decision", errors)
            self.assertIn("failure_policy", errors)

        with tempfile.TemporaryDirectory() as directory:
            root = self.copy_tree(Path(directory))
            evidence_path = root / validator.QUALIFICATION
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence["claims"]["actual_hangul_engine_execution"] = True
            evidence["predecessor_fixture"]["new_engine_executed_in_predecessor"] = True
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            errors = validator.validate(root)["errors"]
            self.assertIn("qualification_claims", errors)
            self.assertIn("qualification_predecessor", errors)

    @staticmethod
    def copy_tree(destination: Path) -> Path:
        root = destination / "repo"
        paths = {
            validator.CONTRACT,
            validator.MIGRATION,
            *validator.EXPECTED_SOURCE_PATHS,
            *validator.IMPLEMENTATION_MARKERS,
        }
        for relative in paths:
            source = validator.ROOT / relative
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return root


if __name__ == "__main__":
    unittest.main()
