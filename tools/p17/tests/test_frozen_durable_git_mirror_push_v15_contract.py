from __future__ import annotations

import copy
from pathlib import Path
import unittest

from tools.p17 import validate_frozen_durable_git_mirror_push_v15_contract as validator


ROOT = Path(__file__).resolve().parents[3]


class FrozenDurableGitMirrorPushV15ContractTests(unittest.TestCase):
    def test_private_contract_and_history_pass(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(
            contract["contract_id"],
            "p17.frozen-durable-git-mirror-push.v15.v1",
        )
        self.assertTrue(contract["claims"]["receipt_blob_verified"])
        self.assertFalse(contract["claims"]["actual_remote_network"])
        self.assertFalse(contract["claims"]["durable_pull"])
        self.assertFalse(contract["claims"]["product_complete"])

    def test_claim_and_source_lock_tamper_fail_closed(self) -> None:
        contract = validator.load_contract(ROOT)
        promoted = copy.deepcopy(contract)
        promoted["claims"]["actual_remote_network"] = True
        with self.assertRaisesRegex(
            validator.FrozenDurableGitPushV15ContractError,
            "contract.claims",
        ):
            validator.validate_document(ROOT, promoted)
        source_tamper = copy.deepcopy(contract)
        source_tamper["source_locks"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            validator.FrozenDurableGitPushV15ContractError,
            "source.digest",
        ):
            validator.validate_document(ROOT, source_tamper)


if __name__ == "__main__":
    unittest.main()
