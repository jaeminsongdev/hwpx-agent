from __future__ import annotations

import copy
import unittest

from tools.p17 import validate_windows_credential_custody_contract as validator


class WindowsCredentialCustodyContractTests(unittest.TestCase):
    def test_current_contract_and_evidence_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertTrue(result["actual_current_pc_store_mechanism"])
        self.assertFalse(result["actual_remote_network"])
        self.assertFalse(result["p17_06_complete"])

    def test_contract_limit_dependency_and_gate_tampering_fail(self) -> None:
        contract, _ = validator.load_json_strict(
            validator.ROOT / validator.CONTRACT_RELATIVE, "contract"
        )
        for path, value in [
            (("platform", "maximum_secret_bytes"), 8192),
            (("dependencies", "keyring_core"), "latest"),
            (("retrieval", "product_write_or_delete_api"), True),
            (("gate_decision", "production"), True),
        ]:
            tampered = copy.deepcopy(contract)
            tampered[path[0]][path[1]] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_contract_document(tampered)

    def test_evidence_claim_privacy_and_cleanup_tampering_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        validator.validate_evidence_document(evidence, raw)
        mutations = [
            ("checks", "credential_deleted", False),
            ("privacy", "existing_credentials_enumerated", True),
            ("claims", "real_service_credential", True),
            ("claims", "actual_remote_network", True),
            ("claims", "p17_06_complete", True),
        ]
        for group, key, value in mutations:
            tampered = copy.deepcopy(evidence)
            tampered[group][key] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(tampered, raw)

    def test_raw_secret_or_target_in_evidence_fails(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for leaked in [b"Bearer aaa.bbb.ccc", b"hwpx-agent.remote-sync:raw:target"]:
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(evidence, raw + leaked)


if __name__ == "__main__":
    unittest.main()
