from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from tools.p17 import validate_frozen_current_source_v45_contract as validator


ROOT = Path(__file__).resolve().parents[3]


class FrozenCurrentSourceV45ContractTests(unittest.TestCase):
    def test_exact_private_contract_and_frozen_authority_pass(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(len(contract["source_locks"]), 8)
        self.assertTrue(
            contract["claims"]["exact_version_license_admission_current_pc_verified"]
        )
        self.assertFalse(contract["claims"]["global_isc_allowance"])
        self.assertFalse(contract["claims"]["real_service_certificate_verified"])
        self.assertFalse(contract["claims"]["real_service_credential_verified"])
        self.assertFalse(contract["claims"]["actual_external_remote_network"])
        self.assertFalse(contract["claims"]["product_complete"])

    def test_claim_and_qualification_tamper_fail_closed(self) -> None:
        contract = validator.load_unique(ROOT / validator.CONTRACT_RELATIVE)
        promoted = copy.deepcopy(contract)
        promoted["claims"]["real_service_certificate_verified"] = True
        with self.assertRaisesRegex(validator.ContractError, "contract.claims"):
            validator.validate_document(promoted, ROOT)
        global_allow = copy.deepcopy(contract)
        global_allow["claims"]["global_isc_allowance"] = True
        with self.assertRaisesRegex(validator.ContractError, "contract.claims"):
            validator.validate_document(global_allow, ROOT)
        changed = copy.deepcopy(contract)
        changed["qualification"]["claim_count"] = 74
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
