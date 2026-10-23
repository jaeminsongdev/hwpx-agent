from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from tools.p17 import validate_frozen_current_source_v48_contract as validator


ROOT = Path(__file__).resolve().parents[3]


class FrozenCurrentSourceV48ContractTests(unittest.TestCase):
    def test_exact_private_contract_and_frozen_authority_pass(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(len(contract["source_locks"]), 4)
        self.assertTrue(contract["claims"]["credential_issuer_component_verified"])
        self.assertTrue(contract["claims"]["broker_fixed_sequence_slot_verified"])
        self.assertEqual(contract["claims"]["broker_concurrent_writers_verified"], 32)
        self.assertTrue(
            contract["claims"]["independently_bound_tls_issuer_current_pc_verified"]
        )
        self.assertFalse(
            contract["claims"]["actual_external_independently_operated_issuer"]
        )
        self.assertFalse(contract["claims"]["external_signer_hsm_kms_verified"])
        self.assertFalse(contract["claims"]["real_client_assertion_verified"])
        self.assertFalse(contract["claims"]["real_service_credential_verified"])
        self.assertFalse(contract["claims"]["windows_power_loss_durability_verified"])
        self.assertFalse(contract["claims"]["product_complete"])

    def test_claim_and_qualification_tamper_fail_closed(self) -> None:
        contract = validator.load_unique(ROOT / validator.CONTRACT_RELATIVE)
        for key in (
            "actual_external_independently_operated_issuer",
            "external_signer_hsm_kms_verified",
            "real_client_assertion_verified",
            "real_service_credential_verified",
            "windows_power_loss_durability_verified",
            "production",
        ):
            promoted = copy.deepcopy(contract)
            promoted["claims"][key] = True
            with self.assertRaisesRegex(validator.ContractError, "contract.claims"):
                validator.validate_document(promoted, ROOT)
        changed = copy.deepcopy(contract)
        changed["qualification"]["claim_count"] += 1
        with self.assertRaisesRegex(validator.ContractError, "contract.qualification"):
            validator.validate_document(changed, ROOT)

    def test_source_and_duplicate_json_tamper_fail_closed(self) -> None:
        contract = validator.load_unique(ROOT / validator.CONTRACT_RELATIVE)
        changed = copy.deepcopy(contract)
        changed["source_locks"][0]["bytes"] += 1
        with self.assertRaisesRegex(validator.ContractError, "contract.sources"):
            validator.validate_document(changed, ROOT)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"scope":"a","scope":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(validator.ContractError, "contract.duplicate"):
                validator.load_unique(path)


if __name__ == "__main__":
    unittest.main()
