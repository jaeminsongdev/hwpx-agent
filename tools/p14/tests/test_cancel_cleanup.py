from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools/p14/validate_cancel_cleanup.py"
SPEC = importlib.util.spec_from_file_location("validate_cancel_cleanup", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = ROOT / "implementation/p14/postgres/p14-cancel-cleanup-v1.json"


class CancelCleanupContractTests(unittest.TestCase):
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
        self.assertEqual(validated["functions"], 13)
        self.assertEqual(validated["smoke_assertions"], 18)
        self.assertEqual(validated["regression_assertions"], 28)

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

    def test_smoke_promotion_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["smoke_fixture"]["assertion_count"] = 19
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_source_protection_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["source_artifact_protected"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_unknown_outcome_cannot_be_promoted_to_cancelled(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["started_effect_becomes_unknown"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_production_scope_cannot_be_promoted(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["production_service_qualified"] = True
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_source_manifest_removal_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_files"].pop()
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_frozen_artifact_successor_is_exact(self) -> None:
        replacements = MODULE.validate_frozen_artifact_qualification()
        self.assertEqual(
            replacements["crates/artifact-service/src/store.rs"],
            (
                "72d4a74d318743494cefb842554a671ae212f56133d0f9987395c2f3dcb2c4e2",
                "ff803fce425c82cf19ed10b0aaa8b6b377c6bc9525f77ec8d70fa2168509f672",
            ),
        )

    def test_unqualified_artifact_predecessor_is_rejected(self) -> None:
        with self.assertRaises(MODULE.ContractError):
            MODULE.require_source_digest_with_supersession(
                {
                    "path": "crates/artifact-service/src/store.rs",
                    "sha256": "0" * 64,
                },
                256 * 1024,
            )

    def test_required_sql_tokens_are_fail_closed(self) -> None:
        up_sql = (ROOT / "migrations/postgres/0008_p14_cancel_cleanup.up.sql").read_text(
            encoding="utf-8"
        )
        for token in [
            "SAFE_POINT_CANCELLATION_PENDING",
            "CLEANUP_SOURCE_PROTECTED",
            "CLEANUP_TARGET_REFERENCED",
            "FOR UPDATE OF task SKIP LOCKED",
            "storage_state = 'purging'",
            "CLEANUP_LEASE_MISMATCH",
        ]:
            with self.subTest(token=token), self.assertRaises(MODULE.ContractError):
                MODULE.require_tokens(up_sql.replace(token, "removed"), [token], "up")

    def test_security_definer_requires_fixed_search_path(self) -> None:
        sql = """
CREATE FUNCTION hwpx_agent.test_function()
RETURNS void LANGUAGE plpgsql SECURITY DEFINER AS $$ BEGIN END $$;
""" * 10
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(sql)

    def test_public_execute_grant_is_rejected(self) -> None:
        up_sql = (ROOT / "migrations/postgres/0008_p14_cancel_cleanup.up.sql").read_text(
            encoding="utf-8"
        )
        with self.assertRaises(MODULE.ContractError):
            MODULE.validate_security_definer_search_paths(
                up_sql + "\nGRANT EXECUTE ON FUNCTION x() TO PUBLIC;\n"
            )


if __name__ == "__main__":
    unittest.main()
