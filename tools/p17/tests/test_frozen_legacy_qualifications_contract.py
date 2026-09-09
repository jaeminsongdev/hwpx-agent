from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from tools.p17 import validate_frozen_legacy_qualifications_contract as validator

ROOT = Path(__file__).resolve().parents[3]


class FrozenLegacyQualificationsContractTests(unittest.TestCase):
    def test_private_contract_and_all_historical_readers_verify(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(contract["contract_id"], "p17.frozen-legacy-qualifications.v1")
        self.assertEqual(contract["coverage"]["current_p17_test_count"], 199)
        self.assertEqual(contract["coverage"]["current_error_count"], 0)
        self.assertFalse(contract["claims"]["receipt_blobs_verified"])
        self.assertFalse(contract["claims"]["actual_hangul"])
        self.assertFalse(contract["claims"]["production"])

    def test_claim_promotion_tamper_fails_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["claims"]["actual_hangul"] = True
        with self.assertRaisesRegex(
            validator.FrozenLegacyContractError, "contract.claims"
        ):
            validator.validate_document(ROOT, contract)

    def test_coverage_tamper_fails_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["coverage"]["current_error_count"] = 1
        with self.assertRaisesRegex(
            validator.FrozenLegacyContractError, "contract.coverage"
        ):
            validator.validate_document(ROOT, contract)

    def test_source_and_duplicate_member_tamper_fail_closed(self) -> None:
        contract = copy.deepcopy(validator.load_contract(ROOT))
        contract["source_locks"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            validator.FrozenLegacyContractError, "source.digest"
        ):
            validator.validate_document(ROOT, contract)
        with self.assertRaisesRegex(
            validator.FrozenLegacyContractError, "contract.duplicate"
        ):
            json.loads(
                '{"claims":{},"claims":{}}', object_pairs_hook=validator.unique_object
            )


if __name__ == "__main__":
    unittest.main()
