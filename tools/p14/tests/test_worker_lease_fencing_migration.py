from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    ROOT / "tools" / "p14" / "validate_worker_lease_fencing_migration.py"
)
SPEC = importlib.util.spec_from_file_location(
    "validate_worker_lease_fencing_migration", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = (
    ROOT
    / "implementation"
    / "p14"
    / "postgres"
    / "p14-worker-lease-fencing-v1.json"
)


class WorkerLeaseFencingMigrationContractTests(unittest.TestCase):
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
        self.assertEqual(validated["smoke_assertions"], 20)
        self.assertEqual(validated["source_files"], 8)

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
        contract["smoke_fixture"]["assertion_count"] = 21
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_late_worker_requirement_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["late_worker_commit_rejected"] = False
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_retry_scope_cannot_be_promoted_into_p14_06(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["requirements"]["retry_or_requeue_implemented"] = True
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

    def test_up_sql_requires_worker_gate_expiry_and_public_revoke(self) -> None:
        up_sql = (
            ROOT
            / "migrations"
            / "postgres"
            / "0006_p14_worker_lease_fencing.up.sql"
        ).read_text(encoding="utf-8")
        for token in [
            "MESSAGE = 'JOB_WORKER_NOT_QUALIFIED'",
            "MESSAGE = 'JOB_LEASE_EXPIRED'",
            "REVOKE ALL ON TABLE hwpx_agent.worker_registrations FROM PUBLIC",
        ]:
            with self.subTest(token=token), self.assertRaises(MODULE.ContractError):
                MODULE.require_tokens(up_sql.replace(token, "removed"), [token], "up")

    def test_down_sql_requires_rollback_gate_and_v5_guard_restore(self) -> None:
        down_sql = (
            ROOT
            / "migrations"
            / "postgres"
            / "0006_p14_worker_lease_fencing.down.sql"
        ).read_text(encoding="utf-8")
        for token in [
            "hwpx_agent.allow_destructive_rollback",
            "CREATE OR REPLACE FUNCTION hwpx_agent.guard_job_state_machine_update()",
            "version > 6",
        ]:
            with self.subTest(token=token), self.assertRaises(MODULE.ContractError):
                MODULE.require_tokens(down_sql.replace(token, "removed"), [token], "down")


if __name__ == "__main__":
    unittest.main()
