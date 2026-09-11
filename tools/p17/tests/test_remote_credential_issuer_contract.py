from __future__ import annotations

import copy
import unittest

from tools.p17 import validate_remote_credential_issuer_contract as validator


class RemoteCredentialIssuerContractTests(unittest.TestCase):
    def test_current_contract_evidence_dependencies_and_source_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["issuer_rust_tests"], 17)
        self.assertTrue(result["current_pc_independently_bound_tls_service"])
        self.assertTrue(result["pinned_loopback_tls_1_3"])
        self.assertFalse(result["external_independently_operated_issuer"])
        self.assertFalse(result["power_loss_durability"])
        self.assertFalse(result["p17_06_complete"])

    def test_contract_auth_state_transport_deployment_and_gate_tampering_fail(self) -> None:
        contract, _ = validator.load_json_strict(
            validator.ROOT / validator.CONTRACT_RELATIVE, "contract"
        )
        mutations = [
            (("authentication", "algorithm"), "any"),
            (("authentication", "exact_request_sha256_binding"), False),
            (("lifecycle", "invalid_state_rejected_before_signer"), False),
            (("response_signing", "returned_signature_reverified_with_pinned_public_key"), False),
            (("state_store", "fixed_sequence_only_final_slot"), False),
            (("state_store", "directory_fsync_or_power_loss_qualified"), True),
            (("state_store", "cross_system_transaction_claimed"), True),
            (("service_transport", "tls_version"), "1.2_or_newer"),
            (("service_transport", "actual_external_endpoint_tested"), True),
            (("deployment_qualification", "status"), "pass"),
            (("gate_decision", "external_independently_operated_issuer"), True),
            (("gate_decision", "real_client_assertion"), True),
            (("gate_decision", "production"), True),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                tampered = copy.deepcopy(contract)
                tampered[path[0]][path[1]] = value
                with self.assertRaises(validator.ContractError):
                    validator.validate_contract_document(tampered)

    def test_evidence_privacy_execution_deployment_and_nonclaim_tampering_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        mutations = [
            (("execution", "tests_passed"), 15),
            (("checks", "concurrent_32_writer_sequence_slot_single_winner"), False),
            (("checks", "real_pinned_client_to_issuer_server_loopback_interoperation"), False),
            (("privacy", "raw_client_assertion_recorded"), True),
            (("deployment_qualification", "status"), "pass"),
            (("claims", "external_independently_operated_issuer"), True),
            (("claims", "real_service_credential"), True),
            (("claims", "power_loss_durability_qualified"), True),
            (("claims", "product_complete"), True),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                tampered = copy.deepcopy(evidence)
                tampered[path[0]][path[1]] = value
                with self.assertRaises(validator.ContractError):
                    validator.validate_evidence_document(tampered, raw)
        for leaked in [
            b"Bearer aaa.bbb.ccc",
            b"-----BEGIN PRIVATE KEY-----",
            b"operation-tls-server-0001",
        ]:
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(evidence, raw + leaked)

    def test_source_auth_transition_store_tls_and_test_weakening_fail(self) -> None:
        source = (validator.ROOT / validator.ISSUER_SOURCE).read_text("utf-8")
        tests = (validator.ROOT / validator.ISSUER_TEST_SOURCE).read_text("utf-8")
        mutations = [
            (source.replace("UnparsedPublicKey::new(&ED25519", "DisabledVerifier::new(", 1), tests),
            (source.replace("claims.request_sha256 != request_sha256", "false", 1), tests),
            (source.replace("temporary.sync_all()", "Ok(())", 1), tests),
            (source.replace("fs::hard_link", "fs::rename", 1), tests),
            (
                source.replace(
                    'format!("{sequence:020}.json")',
                    'format!("{sequence:020}-{record_sha256}.json")',
                    1,
                ),
                tests,
            ),
            (source.replace("with_protocol_versions(&[&version::TLS13])", "", 1), tests),
            (
                source,
                tests.replace(
                    "fn durable_store_allows_only_one_writer_per_sequence_slot()",
                    "fn weakened_sequence_test()",
                    1,
                ),
            ),
            (
                source,
                tests.replace(
                    "fn independent_tls13_server_interoperates_with_pinned_client()",
                    "fn weakened_tls_test()",
                    1,
                ),
            ),
        ]
        for index, (mutated_source, mutated_tests) in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(validator.ContractError):
                    validator.validate_source_text(mutated_source, mutated_tests)

    def test_relative_path_escape_is_rejected(self) -> None:
        for value in ["../secret", "/absolute", "C:/secret", "a\\b", "a/./b"]:
            with self.subTest(value=value):
                with self.assertRaises(validator.ContractError):
                    validator.validate_relative(value)


if __name__ == "__main__":
    unittest.main()
