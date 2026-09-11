from __future__ import annotations

import copy
import unittest

from tools.p17 import validate_remote_credential_broker_v2_contract as validator


class RemoteCredentialBrokerV2ContractTests(unittest.TestCase):
    def test_successor_contract_evidence_predecessors_and_source_pass(self) -> None:
        result = validator.verify()
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["concurrent_writers"], 32)
        self.assertEqual(result["expected_winners"], 1)
        self.assertFalse(result["external_issuer"])
        self.assertFalse(result["power_loss_durability"])
        self.assertFalse(result["p17_06_complete"])

    def test_contract_publication_migration_and_nonclaims_tampering_fail(self) -> None:
        contract, _ = validator.load_json_strict(
            validator.ROOT / validator.CONTRACT_RELATIVE, "contract"
        )
        for path, value in [
            (("predecessor", "sha256"), "0" * 64),
            (("migration", "automatic_v1_directory_migration"), True),
            (("state_store_successor", "record_sha256_in_filename"), True),
            (("state_store_successor", "one_publication_slot_per_sequence"), False),
            (("state_store_successor", "power_loss_durability_qualified"), True),
            (("concurrency_qualification", "expected_winners"), 2),
            (("gate_decision", "external_issuer"), True),
            (("gate_decision", "product_complete"), True),
        ]:
            tampered = copy.deepcopy(contract)
            tampered[path[0]][path[1]] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_contract_document(tampered)

    def test_evidence_concurrency_privacy_and_nonclaim_tampering_fail(self) -> None:
        evidence, _ = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        for group, key, value in [
            ("predecessor_evidence", "sha256", "0" * 64),
            ("state_store", "one_publication_slot_per_sequence", False),
            ("qualification", "conflicts", 30),
            ("qualification", "synthetic_file_state_only", False),
            ("privacy", "existing_credentials_enumerated", True),
            ("claims", "power_loss_durability_qualified", True),
            ("claims", "production", True),
        ]:
            tampered = copy.deepcopy(evidence)
            tampered[group][key] = value
            with self.assertRaises(validator.ContractError):
                validator.validate_evidence_document(
                    tampered, validator.canonical(tampered)
                )

    def test_noncanonical_duplicate_and_path_escape_fail(self) -> None:
        evidence, raw = validator.load_json_strict(
            validator.ROOT / validator.EVIDENCE_RELATIVE, "evidence"
        )
        with self.assertRaises(validator.ContractError):
            validator.validate_evidence_document(evidence, raw + b" ")
        with self.assertRaises(validator.ContractError):
            validator.validate_relative("../escape.json")
        duplicate = b'{"schema_version":"one","schema_version":"two"}'
        temporary = self.id().replace(".", "-") + ".json"
        path = validator.ROOT / "target" / temporary
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(duplicate)
        try:
            with self.assertRaises(validator.ContractError):
                validator.load_json_strict(path, "duplicate")
        finally:
            path.unlink(missing_ok=True)

    def test_source_slot_sync_hard_link_and_concurrency_weakening_fail(self) -> None:
        source = (validator.ROOT / validator.BROKER_SOURCE).read_text("utf-8")
        mutations = [
            source.replace(
                'self.root.join(format!("{sequence:020}.json"))',
                'self.root.join(format!("{sequence:020}-{record_sha256}.json"))',
                1,
            ),
            source.replace("temporary.sync_all()", "Ok(())", 1),
            source.replace("fs::hard_link(&temporary_path, &final_path)", "fs::rename(&temporary_path, &final_path)", 1),
            source.replace("const WRITERS: usize = 32;", "const WRITERS: usize = 1;", 1),
            source.replace("assert_eq!(completed, 1);", "assert!(completed > 0);", 1),
        ]
        for index, mutated in enumerate(mutations):
            with self.subTest(index=index):
                with self.assertRaises(validator.ContractError):
                    validator.validate_source_text(mutated)


if __name__ == "__main__":
    unittest.main()
