from __future__ import annotations

import copy
import unittest

from tools.p17 import validate_remote_credential_broker_contract as validator


class RemoteCredentialBrokerContractTests(unittest.TestCase):
    def test_current_contract_evidence_receipt_manifests_and_source_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["broker_rust_tests"], 13)
        self.assertTrue(result["current_pc_windows_issue_revoke"])
        self.assertTrue(result["pinned_loopback_tls"])
        self.assertFalse(result["external_issuer"])
        self.assertFalse(result["power_loss_durability"])
        self.assertFalse(result["p17_06_complete"])

    def test_contract_transport_ordering_atomicity_and_gate_tampering_fail(self) -> None:
        contract, _ = validator.load_json_strict(
            validator.ROOT / validator.CONTRACT_RELATIVE, "contract"
        )
        for path, value in [
            (("wire", "request_magic"), "HWPXRSQ1"),
            (("issuer_transport", "tls_version"), "1.2_or_newer"),
            (("broker", "pending_persisted_before_dispatch"), False),
            (("state_store", "cross_system_transaction_claimed"), True),
            (("state_store", "power_loss_durability_qualified"), True),
            (("windows_vault", "credential_enumeration"), True),
            (("issuer_transport", "client_assertion_signature_or_freshness_qualified"), True),
            (("gate_decision", "external_issuer"), True),
            (("gate_decision", "real_client_assertion"), True),
            (("gate_decision", "production"), True),
        ]:
            tampered = copy.deepcopy(contract)
            tampered[path[0]][path[1]] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_contract_document(tampered)

    def test_evidence_cleanup_privacy_and_nonclaim_tampering_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for group, key, value in [
            ("checks", "post_cleanup_absent", False),
            ("checks", "pending_persisted_before_dispatch", False),
            ("privacy", "existing_credentials_enumerated", True),
            ("claims", "power_loss_durability_qualified", True),
            ("claims", "external_issuer", True),
            ("claims", "real_service_credential", True),
            ("claims", "p17_06_complete", True),
            ("predecessor_evidence", "sha256", "0" * 64),
        ]:
            tampered = copy.deepcopy(evidence)
            tampered[group][key] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(validator.ROOT, tampered, raw)

    def test_receipt_digest_path_and_raw_secret_tampering_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for key, value in [
            ("receipt_sha256", "0" * 64),
            ("receipt_path", "../escape.json"),
            ("credential_target_sha256", "0" * 63),
        ]:
            tampered = copy.deepcopy(evidence)
            tampered["execution"][key] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(
                    validator.ROOT, tampered, validator.canonical(tampered)
                )
        for leaked in [
            b"Bearer aaa.bbb.ccc",
            b"hwpx-agent.remote-sync:raw:target",
            b"-----BEGIN PRIVATE KEY-----",
        ]:
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(validator.ROOT, evidence, raw + leaked)

    def test_source_recovery_wire_tls_or_windows_vault_weakening_fails(self) -> None:
        broker = (validator.ROOT / validator.BROKER_SOURCE).read_text("utf-8")
        wire = (validator.ROOT / validator.WIRE_SOURCE).read_text("utf-8")
        tls = (validator.ROOT / validator.TLS_SOURCE).read_text("utf-8")
        windows = (validator.ROOT / validator.WINDOWS_SOURCE).read_text("utf-8")
        tests = (
            validator.ROOT
            / "crates/windows-credential-custody/tests/windows_broker_tls.rs"
        ).read_text("utf-8")
        mutations = [
            (broker.replace("fs::hard_link", "fs::rename", 1), wire, tls, windows, tests),
            (broker.replace("temporary.sync_all()", "Ok(())", 1), wire, tls, windows, tests),
            (broker, wire.replace('b"HWPXCIQ1"', 'b"HWPXRSQ1"', 1), tls, windows, tests),
            (
                broker,
                wire,
                tls.replace("with_protocol_versions(&[&version::TLS13])", "", 1),
                windows,
                tests,
            ),
            (
                broker,
                wire,
                tls,
                windows.replace(
                    "impl CredentialVault for WindowsCredentialManagerVault",
                    "impl DisabledVault for WindowsCredentialManagerVault",
                    1,
                ),
                tests,
            ),
            (
                broker,
                wire,
                tls,
                windows,
                tests.replace(
                    "fn current_user_broker_pinned_tls_issue_and_revoke()",
                    "fn weakened_qualification()",
                    1,
                ),
            ),
        ]
        for index, values in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(validator.ContractError):
                    validator.validate_source_text(*values)


if __name__ == "__main__":
    unittest.main()
