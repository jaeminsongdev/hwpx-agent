from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.p17 import validate_frozen_current_source_v40_contract as validator

ROOT = Path(__file__).resolve().parents[3]


class FrozenCurrentSourceV40ContractTests(unittest.TestCase):
    def test_private_contract_and_historical_state_verify(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(contract["contract_id"], "p17.frozen-current-source.v40.v1")
        self.assertEqual(len(contract["source_locks"]), 8)
        self.assertTrue(
            contract["claims"]["historical_v40_committed_source_state_verified"]
        )
        self.assertFalse(contract["claims"]["receipt_blob_verified"])
        self.assertFalse(contract["claims"]["actual_hangul"])
        self.assertFalse(contract["claims"]["p17_06_complete"])

    def test_claim_promotion_tamper_fails_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["claims"]["actual_hangul"] = True
        with self.assertRaisesRegex(
            validator.FrozenSourceV40ContractError, "contract.claims"
        ):
            validator.validate_document(ROOT, contract)

    def test_qualification_identity_tamper_fails_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["qualification"]["qualification_commit"] = "0" * 40
        with self.assertRaisesRegex(
            validator.FrozenSourceV40ContractError, "contract.qualification"
        ):
            validator.validate_document(ROOT, contract)

    def test_overlap_tamper_fails_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["qualification"]["intentional_overlap"] = []
        with self.assertRaisesRegex(
            validator.FrozenSourceV40ContractError, "contract.qualification"
        ):
            validator.validate_document(ROOT, contract)

    def test_source_lock_tamper_and_duplicate_member_fail_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["source_locks"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            validator.FrozenSourceV40ContractError, "source.digest"
        ):
            validator.validate_document(ROOT, contract)
        with self.assertRaisesRegex(
            validator.FrozenSourceV40ContractError, "contract.duplicate"
        ):
            json.loads(
                '{"claims":{},"claims":{}}',
                object_pairs_hook=validator.unique_object,
            )


if __name__ == "__main__":
    unittest.main()
