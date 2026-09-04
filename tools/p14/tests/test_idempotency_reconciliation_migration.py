from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p14" / "validate_idempotency_reconciliation_migration.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_idempotency_reconciliation_migration", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = (
    ROOT
    / "implementation"
    / "p14"
    / "postgres"
    / "p14-idempotency-reconciliation-v2.json"
)


class IdempotencyReconciliationMigrationContractTests(unittest.TestCase):
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
        self.assertEqual(validated["migration_functions"], 11)
        self.assertEqual(validated["smoke_assertions"], 28)
        self.assertEqual(validated["source_files"], 6)

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

    def test_image_digest_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["container_image"] = "postgres:18.4-bookworm"
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_prerequisite_order_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["prerequisites"].reverse()
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_migration_digest_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migration"]["up_sha256"] = "0" * 64
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_smoke_assertion_promotion_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["smoke_fixture"]["assertion_count"] = 29
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_production_scope_cannot_be_promoted(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["production_service_qualified"] = True
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_head_lock_requirement_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["branch_head_lock_closes_no_effect_toctou"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_late_commit_fence_requirement_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["late_commit_requires_current_fence_authorization"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_all_v7_commits_must_remain_idempotency_bound(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["all_v7_revision_commits_require_bound_idempotency"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_attempt_commit_capability_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["attempt_scoped_unpredictable_commit_capability"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_source_lock_removal_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_files"].pop()
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_source_path_escape_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_files"][0]["path"] = "../outside"
        with self.assertRaises((MODULE.ContractError, FileNotFoundError)):
            self.validate_tampered(contract)

    def test_up_sql_requires_lock_oracles_and_v2_functions(self) -> None:
        up_sql = (
            ROOT
            / "migrations"
            / "postgres"
            / "0007_p14_idempotency_reconciliation.up.sql"
        ).read_text(encoding="utf-8")
        for token in [
            "FOR SHARE;",
            "CREATE TABLE hwpx_agent.idempotency_commit_authorizations (",
            "CREATE FUNCTION hwpx_agent.commit_idempotent_revision_cas_v2(",
            "CREATE TRIGGER revision_commit_receipts_idempotency_v2_guard",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED'",
            "MESSAGE = 'IDEMPOTENCY_COMMIT_CAPABILITY_MISMATCH'",
            "JOIN hwpx_agent.revision_commit_receipts AS commit_receipt",
            "CREATE FUNCTION hwpx_agent.reconcile_idempotent_job_v2(",
            "MESSAGE = 'IDEMPOTENCY_NO_EFFECT_ORACLE_FAILED'",
        ]:
            with self.subTest(token=token), self.assertRaises(MODULE.ContractError):
                MODULE.require_tokens(up_sql.replace(token, "removed"), [token], "up")

    def test_unbound_revision_commit_fallback_is_rejected(self) -> None:
        up_sql = (
            ROOT
            / "migrations"
            / "postgres"
            / "0007_p14_idempotency_reconciliation.up.sql"
        ).read_text(encoding="utf-8")
        unsafe = up_sql.replace(
            "IF NOT FOUND THEN\n        RAISE EXCEPTION USING\n"
            "            ERRCODE = '42501', MESSAGE = "
            "'IDEMPOTENCY_COMMIT_AUTHORIZATION_REQUIRED';",
            "IF NOT FOUND THEN\n        RETURN NEW;",
            1,
        )
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_commit_authorization_guard(unsafe)

    def test_down_sql_requires_data_and_later_version_guards(self) -> None:
        down_sql = (
            ROOT
            / "migrations"
            / "postgres"
            / "0007_p14_idempotency_reconciliation.down.sql"
        ).read_text(encoding="utf-8")
        for token in [
            "hwpx_agent.allow_destructive_rollback",
            "rollback refuses remaining version 2 data",
            "version > 7",
            "DELETE FROM hwpx_agent.schema_versions WHERE version = 7",
        ]:
            with self.subTest(token=token), self.assertRaises(MODULE.ContractError):
                MODULE.require_tokens(down_sql.replace(token, "removed"), [token], "down")

    def test_security_definer_requires_fixed_search_path(self) -> None:
        sql = """
CREATE FUNCTION hwpx_agent.test_function()
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$ BEGIN END $$;
""" * 15
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(sql)

    def test_public_execute_grant_is_rejected(self) -> None:
        up_sql = (
            ROOT
            / "migrations"
            / "postgres"
            / "0007_p14_idempotency_reconciliation.up.sql"
        ).read_text(encoding="utf-8")
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(
                up_sql + "\nGRANT EXECUTE ON FUNCTION x() TO PUBLIC;\n"
            )


if __name__ == "__main__":
    unittest.main()
