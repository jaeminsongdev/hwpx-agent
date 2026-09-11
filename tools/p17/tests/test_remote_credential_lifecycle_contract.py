from __future__ import annotations

import copy
import unittest

from tools.p17 import validate_remote_credential_lifecycle_contract as validator


class RemoteCredentialLifecycleContractTests(unittest.TestCase):
    def test_current_contract_evidence_manifests_and_source_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["rust_tests"], 15)
        self.assertFalse(result["actual_external_issuer"])
        self.assertFalse(result["actual_external_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["p17_06_complete"])

    def test_contract_policy_transition_durability_and_gate_tampering_fail(self) -> None:
        contract, _ = validator.load_json_strict(
            validator.ROOT / validator.CONTRACT_RELATIVE, "contract"
        )
        for path, value in [
            (("policy", "complete_policy_binding"), False),
            (("transitions", "refresh_token_modeled_or_stored"), True),
            (("jwt", "algorithm"), "HS256"),
            (("durability_boundary", "atomic_vault_and_state_adapter_implemented_here"), True),
            (("gate_decision", "actual_external_issuer"), True),
            (("gate_decision", "production"), True),
        ]:
            tampered = copy.deepcopy(contract)
            tampered[path[0]][path[1]] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_contract_document(tampered)

    def test_evidence_check_privacy_and_claim_tampering_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for group, key, value in [
            ("checks", "complete_policy_and_prior_state_binding", False),
            ("checks", "prior_token_and_jti_replay_rejected", False),
            ("checks", "prior_operation_id_reuse_rejected", False),
            ("privacy", "raw_access_token_recorded", True),
            ("claims", "real_service_credential", True),
            ("claims", "actual_external_remote_network", True),
            ("claims", "p17_06_complete", True),
        ]:
            tampered = copy.deepcopy(evidence)
            tampered[group][key] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(tampered, raw)

    def test_permissive_algorithm_or_secret_logging_source_fails(self) -> None:
        source = (validator.ROOT / validator.SOURCE_RELATIVE).read_text("utf-8")
        tests = (validator.ROOT / validator.TEST_RELATIVE).read_text("utf-8")
        for tampered in [
            source + '\nconst ALTERNATE: &str = "HS256";',
            source + '\nprintln!("credential");',
            source.replace("secret: Zeroizing<String>", "secret: String", 1),
            source.replace(
                "URL_SAFE_NO_PAD.encode(&decoded) != segment",
                "false",
                1,
            ),
        ]:
            with self.assertRaises(validator.ContractError):
                validator.validate_source_text(tampered, tests)

    def test_test_coverage_drift_fails(self) -> None:
        source = (validator.ROOT / validator.SOURCE_RELATIVE).read_text("utf-8")
        tests = (validator.ROOT / validator.TEST_RELATIVE).read_text("utf-8")
        tampered = tests.replace(
            "fn pending_binds_all_keys_and_lifetime_policy()",
            "fn pending_binding_weakened()",
            1,
        )
        with self.assertRaises(validator.ContractError):
            validator.validate_source_text(source, tampered)

    def test_raw_token_or_private_key_in_evidence_fails(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for leaked in (b"Bearer aaa.bbb.ccc", b"-----BEGIN PRIVATE KEY-----"):
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(evidence, raw + leaked)


if __name__ == "__main__":
    unittest.main()
