from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.p17 import validate_durable_git_mirror_pull_contract as contract


ROOT = Path(__file__).resolve().parents[3]


class DurableGitMirrorPullContractTests(unittest.TestCase):
    def test_exact_current_pc_contract_and_receipt_pass_without_phase_promotion(self) -> None:
        document = contract.verify(ROOT)
        self.assertEqual(
            document["schema_version"], "hwpx-agent.durable-git-mirror-pull/v1"
        )
        self.assertTrue(document["evidence"]["actual_clean_advance"])
        self.assertTrue(document["evidence"]["actual_conflict_preservation"])
        self.assertFalse(document["evidence"]["actual_remote_network"])
        self.assertFalse(document["evidence"]["persistent_credential_custody"])
        self.assertFalse(document["evidence"]["production"])
        self.assertFalse(document["evidence"]["p17_06_complete"])
        self.assertFalse(document["evidence"]["product_complete"])

    def test_unearned_evidence_promotion_fails_closed(self) -> None:
        document = contract.load_unique(contract.CONTRACT)
        for claim in (
            "actual_remote_network",
            "persistent_credential_custody",
            "registered_host",
            "production",
            "actual_hangul",
            "p17_06_complete",
            "product_complete",
        ):
            tampered = copy.deepcopy(document)
            tampered["evidence"][claim] = True
            with self.assertRaises(contract.ContractError, msg=claim):
                contract.validate(tampered)

    def test_snapshot_replay_drift_and_rollback_tampering_fails_closed(self) -> None:
        document = contract.load_unique(contract.CONTRACT)
        mutations = (
            ("request", "observed_snapshot_sha256_bound", False),
            ("database", "exact_replay_creates_no_second_observation_or_conflict", False),
            ("database", "ahead_conflict_preserves_local_snapshot_and_plan", False),
            ("git", "access", "read_write"),
            ("git", "accepts_caller_command_or_reference", True),
            ("reconciliation", "git_database_drift", "rejected"),
            ("reconciliation", "blind_retry", True),
            ("rollback", "retained_observations_refuse_rollback", False),
            ("transport", "persistent_credential_custody", True),
        )
        for section, key, value in mutations:
            tampered = copy.deepcopy(document)
            tampered[section][key] = value
            with self.assertRaises(contract.ContractError, msg=f"{section}.{key}"):
                contract.validate(tampered)

    def test_receipt_check_claim_effect_and_source_tampering_fails_closed(self) -> None:
        receipt = contract.load_unique(contract.RECEIPT)
        checks = copy.deepcopy(receipt)
        checks["checks"] = checks["checks"][:-1]
        with self.assertRaisesRegex(contract.ContractError, "receipt.checks"):
            contract.validate_receipt(checks, ROOT)
        claim = copy.deepcopy(receipt)
        claim["claims"]["actual_remote_network"] = True
        with self.assertRaisesRegex(contract.ContractError, "receipt.claims"):
            contract.validate_receipt(claim, ROOT)
        effect = copy.deepcopy(receipt)
        effect["effect"]["conflict_count"] = 0
        with self.assertRaisesRegex(contract.ContractError, "receipt.effect"):
            contract.validate_receipt(effect, ROOT)
        source = copy.deepcopy(receipt)
        source["source_sha256"]["crates/local-sync/src/adapter.rs"] = "0" * 64
        with self.assertRaisesRegex(contract.ContractError, "receipt.sources.digest"):
            contract.validate_receipt(source, ROOT)

    def test_current_source_digest_drift_fails_closed(self) -> None:
        original = contract.digest_file

        def changed(path: Path) -> str:
            if path == ROOT / "crates/local-sync/src/adapter.rs":
                return "0" * 64
            return original(path)

        receipt = contract.load_unique(contract.RECEIPT)
        with patch.object(contract, "digest_file", side_effect=changed):
            with self.assertRaisesRegex(contract.ContractError, "receipt.sources.digest"):
                contract.validate_receipt(receipt, ROOT)

    def test_duplicate_key_and_non_object_documents_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(
                '{"schema_version":"a","schema_version":"b"}',
                encoding="utf-8",
            )
            with self.assertRaises(contract.ContractError):
                contract.load_unique(path)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(contract.ContractError):
                contract.load_unique(path)


if __name__ == "__main__":
    unittest.main()
