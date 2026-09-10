from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from tools.p17 import validate_frozen_durable_git_mirror_pull_v17_contract as validator


ROOT = Path(__file__).resolve().parents[3]


class FrozenDurableGitMirrorPullV17ContractTests(unittest.TestCase):
    def test_exact_private_contract_and_frozen_authority_pass(self) -> None:
        contract = validator.verify(ROOT)
        self.assertEqual(len(contract["source_locks"]), 6)
        self.assertTrue(contract["claims"]["durable_pull_current_pc_runtime_verified"])
        self.assertFalse(contract["claims"]["actual_remote_network"])
        self.assertFalse(contract["claims"]["product_complete"])

    def test_claim_and_qualification_tamper_fail_closed(self) -> None:
        contract = validator.load_unique(ROOT / validator.CONTRACT_RELATIVE)
        promoted = copy.deepcopy(contract)
        promoted["claims"]["production"] = True
        with self.assertRaisesRegex(validator.ContractError, "contract.claims"):
            validator.validate_document(promoted, ROOT)
        changed = copy.deepcopy(contract)
        changed["qualification"]["receipt_sha256"] = "0" * 64
        with self.assertRaisesRegex(validator.ContractError, "contract.qualification"):
            validator.validate_document(changed, ROOT)

    def test_source_and_duplicate_json_tamper_fail_closed(self) -> None:
        contract = validator.load_unique(ROOT / validator.CONTRACT_RELATIVE)
        changed = copy.deepcopy(contract)
        changed["source_locks"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(validator.ContractError, "contract.sources"):
            validator.validate_document(changed, ROOT)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(validator.ContractError, "contract.duplicate"):
                validator.load_unique(path)


if __name__ == "__main__":
    unittest.main()
