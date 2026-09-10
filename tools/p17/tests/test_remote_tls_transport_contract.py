from __future__ import annotations

import copy
import unittest

from tools.p17 import validate_remote_tls_transport_contract as validator


class RemoteTlsTransportContractTests(unittest.TestCase):
    def test_current_contract_evidence_manifests_and_source_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertTrue(result["current_pc_loopback_tls13"])
        self.assertFalse(result["actual_external_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["p17_06_complete"])

    def test_contract_dependency_trust_and_gate_tampering_fail(self) -> None:
        contract, _ = validator.load_json_strict(
            validator.ROOT / validator.CONTRACT_RELATIVE, "contract"
        )
        for path, value in [
            (("dependencies", "rustls"), "latest"),
            (("configuration", "dns_resolution"), True),
            (("tls", "custom_accept_all_verifier"), True),
            (("gate_decision", "actual_external_remote_network"), True),
            (("gate_decision", "production"), True),
        ]:
            tampered = copy.deepcopy(contract)
            tampered[path[0]][path[1]] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_contract_document(tampered)

    def test_evidence_check_cleanup_privacy_and_claim_tampering_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for group, key, value in [
            ("checks", "request_not_dispatched_on_wrong_pin_or_name", False),
            ("cleanup", "certificate_installed", True),
            ("privacy", "certificate_pin_recorded", True),
            ("claims", "real_service_certificate", True),
            ("claims", "actual_external_remote_network", True),
            ("claims", "p17_06_complete", True),
        ]:
            tampered = copy.deepcopy(evidence)
            tampered[group][key] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(tampered, raw)

    def test_permissive_verifier_or_pre_pin_dispatch_source_fails(self) -> None:
        source = (validator.ROOT / validator.SOURCE_RELATIVE).read_text("utf-8")
        tests = (validator.ROOT / validator.TEST_RELATIVE).read_text("utf-8")
        with self.assertRaises(validator.ContractError):
            validator.validate_source_text(source + "\n.dangerous()", tests)
        reordered = source.replace(
            "actual_leaf_sha256 != self.expected_leaf_sha256",
            "write_request(&mut stream, authorization_header, request);\n"
            "actual_leaf_sha256 != self.expected_leaf_sha256",
            1,
        )
        with self.assertRaises(validator.ContractError):
            validator.validate_source_text(reordered, tests)

    def test_raw_authorization_or_certificate_in_evidence_fails(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for leaked in (b"Bearer aaa.bbb.ccc", b"-----BEGIN CERTIFICATE-----"):
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(evidence, raw + leaked)


if __name__ == "__main__":
    unittest.main()
