from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p14" / "validate_job_state_machine_migration.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_job_state_machine_migration", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = (
    ROOT / "implementation" / "p14" / "postgres" / "p14-job-state-machine-v1.json"
)


class JobStateMachineMigrationContractTests(unittest.TestCase):
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
        self.assertEqual(validated["smoke_assertions_per_run"], 30)

    def test_unknown_property_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["force_pass"] = True
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"contract_id":"a","contract_id":"b"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.load_json(path)

    def test_image_digest_cannot_be_weakened(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["database"]["container_image"] = "postgres:18.4-bookworm"
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_migration_digest_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["migration"]["up_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_prerequisite_order_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["prerequisites"].reverse()
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_smoke_assertion_promotion_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["smoke_fixture"]["assertions_per_run"] = 31
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_transition_invariant_weakening_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["invariants"]["terminal_state_immutable"] = False
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_identity_invariant_weakening_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["invariants"]["job_spec_and_attempt_identity_immutable"] = False
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_later_phase_scope_promotion_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["scope"]["p14_06_capability_matching_expiry_fencing_qualified"] = True
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_source_lock_removal_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_locks"].pop()
        with self.assertRaises(ValueError):
            self.validate_tampered(contract)

    def test_up_sql_requires_exact_stage_edges_and_qualified_artifacts(self) -> None:
        up_sql = (
            ROOT / "migrations" / "postgres" / "0005_p14_job_state_machine.up.sql"
        ).read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.validate_up_sql(
                up_sql.replace("ROW('staged', 'executing')", "ROW('staged', 'validating')")
            )
        with self.assertRaises(ValueError):
            MODULE.validate_up_sql(
                up_sql.replace("artifact.validation_state = 'verified'", "true")
            )
        with self.assertRaises(ValueError):
            MODULE.validate_up_sql(
                up_sql.replace("MESSAGE = 'JOB_SPEC_IMMUTABLE'", "MESSAGE = 'WEAK'")
            )

    def test_up_sql_requires_consistency_trigger_and_public_revoke(self) -> None:
        up_sql = (
            ROOT / "migrations" / "postgres" / "0005_p14_job_state_machine.up.sql"
        ).read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.validate_up_sql(
                up_sql.replace(
                    "CREATE CONSTRAINT TRIGGER jobs_state_machine_consistency",
                    "CREATE CONSTRAINT TRIGGER disabled_consistency",
                )
            )
        with self.assertRaises(ValueError):
            MODULE.validate_up_sql(
                up_sql.replace(
                    "REVOKE ALL ON FUNCTION hwpx_agent.commit_job_success(",
                    "-- revoke removed ",
                )
            )

    def test_down_sql_requires_explicit_and_later_version_gates(self) -> None:
        down_sql = (
            ROOT / "migrations" / "postgres" / "0005_p14_job_state_machine.down.sql"
        ).read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            MODULE.validate_down_sql(
                down_sql.replace(
                    "hwpx_agent.allow_destructive_rollback", "disabled.rollback.gate"
                )
            )
        with self.assertRaises(ValueError):
            MODULE.validate_down_sql(down_sql.replace("version > 5", "version > 999"))


if __name__ == "__main__":
    unittest.main()
