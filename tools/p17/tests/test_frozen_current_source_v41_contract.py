from __future__ import annotations

import copy
from pathlib import Path
import unittest

from tools.p17 import validate_frozen_current_source_v41_contract as validator


ROOT = Path(__file__).resolve().parents[3]


class FrozenCurrentSourceV41ContractTests(unittest.TestCase):
    def test_private_contract_and_history_pass(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(contract["contract_id"], "p17.frozen-current-source.v41.v1")
        self.assertTrue(contract["claims"]["durable_push_current_pc_runtime_verified"])
        self.assertTrue(contract["claims"]["receipt_blob_verified"])
        self.assertFalse(contract["claims"]["durable_pull"])
        self.assertFalse(contract["claims"]["actual_remote_network"])
        self.assertFalse(contract["claims"]["product_complete"])

    def test_claim_runtime_and_source_tamper_fail_closed(self) -> None:
        contract = validator.load_contract(ROOT)
        promoted = copy.deepcopy(contract)
        promoted["claims"]["actual_remote_network"] = True
        with self.assertRaisesRegex(validator.FrozenSourceV41ContractError, "contract.claims"):
            validator.validate_document(ROOT, promoted)
        runtime = copy.deepcopy(contract)
        runtime["runtime_frozen_contract"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(validator.FrozenSourceV41ContractError, "contract.runtime"):
            validator.validate_document(ROOT, runtime)
        source = copy.deepcopy(contract)
        source["source_locks"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(validator.FrozenSourceV41ContractError, "source.digest"):
            validator.validate_document(ROOT, source)


if __name__ == "__main__":
    unittest.main()
