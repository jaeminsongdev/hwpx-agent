from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools/p14/validate_retention_local_mirror.py"
SPEC = importlib.util.spec_from_file_location("validate_retention_local_mirror", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = ROOT / "implementation/p14/postgres/p14-retention-local-mirror-v1.json"


class RetentionLocalMirrorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_json(CONTRACT_PATH)

    def validate_tampered(self, contract: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            MODULE.validate_contract(path, ROOT)

    def test_canonical_contract_is_valid(self) -> None:
        validated = MODULE.validate_contract(CONTRACT_PATH, ROOT)
        self.assertEqual(validated["state"], "pass")
        self.assertEqual(validated["function_count"], 18)
        self.assertEqual(validated["smoke_assertion_count"], 32)
        self.assertEqual(validated["regression_assertion_count"], 28)
        self.assertEqual(validated["source_file_count"], 9)

    def test_unknown_property_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["force_pass"] = True
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"state":"pass","state":"fail"}', encoding="utf-8")
            with self.assertRaises(MODULE.ContractError):
                MODULE.load_json(path)

    def test_image_pin_cannot_be_removed(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["container_image"] = "postgres:18.4-bookworm"
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_prerequisite_order_is_exact(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["prerequisites"].reverse()
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_migration_digest_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migration"]["up_sha256"] = "0" * 64
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_smoke_count_promotion_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["smoke_fixture"]["assertion_count"] = 33
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_legal_hold_race_protection_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["active_purge_blocks_new_hold"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_mirror_plan_binding_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["operation_plan_bound"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_conflict_choices_are_exact(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["conflict_resolutions"].append("overwrite_remote")
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_production_scope_cannot_be_promoted(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["production_service_qualified"] = True
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_hangul_dependency_cannot_be_invented(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["hangul_runtime_required"] = True
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_source_manifest_removal_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_files"].pop()
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_required_sql_tokens_are_fail_closed(self) -> None:
        up_sql = (
            ROOT / "migrations/postgres/0009_p14_retention_local_mirror.up.sql"
        ).read_text(encoding="utf-8")
        for token in [
            "RETENTION_PURGE_IN_PROGRESS",
            "artifact_referenced_outside_project_v1",
            "active_push_subject_sha256",
            "revision_commit_receipts AS receipt",
            "MIRROR_PLAN_MISMATCH",
        ]:
            with self.subTest(token=token), self.assertRaises(MODULE.ContractError):
                MODULE.require_tokens(up_sql.replace(token, "removed"), [token], "up")

    def test_security_definer_requires_fixed_search_path(self) -> None:
        sql = """
CREATE FUNCTION hwpx_agent.test_function()
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$ BEGIN END $$;
""" * 18
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(sql)

    def test_public_execute_grant_is_rejected(self) -> None:
        up_sql = (
            ROOT / "migrations/postgres/0009_p14_retention_local_mirror.up.sql"
        ).read_text(encoding="utf-8")
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(
                up_sql + "\nGRANT EXECUTE ON FUNCTION x() TO PUBLIC;\n"
            )

    def test_missing_public_revoke_is_rejected(self) -> None:
        up_sql = (
            ROOT / "migrations/postgres/0009_p14_retention_local_mirror.up.sql"
        ).read_text(encoding="utf-8")
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(
                up_sql.replace(
                    "REVOKE ALL ON FUNCTION hwpx_agent.protect_p14_09_identity() FROM PUBLIC;",
                    "-- missing trigger-function revoke",
                )
            )


if __name__ == "__main__":
    unittest.main()
