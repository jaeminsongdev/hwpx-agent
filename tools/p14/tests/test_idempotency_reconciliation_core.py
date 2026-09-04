from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tools" / "p14" / "validate_idempotency_reconciliation_core.py"
SPEC = importlib.util.spec_from_file_location(
    "validate_idempotency_reconciliation_core", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT_PATH = (
    ROOT / "implementation" / "p14" / "p14-idempotency-reconciliation-core-v1.json"
)


class IdempotencyReconciliationCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = MODULE.load_json(CONTRACT_PATH)

    def validate_tampered(self, contract: dict[str, object]) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            MODULE.validate_contract(path, ROOT)

    def test_canonical_contract_is_valid(self) -> None:
        result = MODULE.validate_contract(CONTRACT_PATH, ROOT)
        self.assertEqual(result, {"state": "pass", "source_files": 7, "rust_tests": 10})

    def test_unknown_key_is_rejected(self) -> None:
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

    def test_source_digest_drift_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_files"][3]["sha256"] = "0" * 64
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_source_escape_is_rejected(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["source_files"][0]["path"] = "../Cargo.toml"
        with self.assertRaises(MODULE.ContractError):
            self.validate_tampered(contract)

    def test_retry_or_production_scope_cannot_be_promoted(self) -> None:
        for key in [
            "trusted_reconciliation_oracle_qualified",
            "postgres_migration_qualified",
            "production_service_qualified",
        ]:
            with self.subTest(key=key):
                contract = copy.deepcopy(self.contract)
                contract["requirements"][key] = True
                with self.assertRaises(MODULE.ContractError):
                    self.validate_tampered(contract)


if __name__ == "__main__":
    unittest.main()
