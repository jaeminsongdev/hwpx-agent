from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import validate_durable_git_mirror_push_contract as contract  # noqa: E402


class DurableGitMirrorPushContractTests(unittest.TestCase):
    def test_current_contract_and_sources_pass(self) -> None:
        document = contract.verify()
        self.assertEqual(
            document["schema_version"], "hwpx-agent.durable-git-mirror-push/v1"
        )

    def test_unearned_evidence_promotion_fails_closed(self) -> None:
        document = contract.load_unique(contract.CONTRACT)
        for claim in (
            "actual_remote_network",
            "durable_pull",
            "production",
            "actual_hangul",
            "p17_06_complete",
        ):
            tampered = copy.deepcopy(document)
            tampered["evidence"][claim] = True
            with self.assertRaises(contract.ContractError, msg=claim):
                contract.validate(tampered)

    def test_plan_fence_recovery_and_git_cas_tampering_fails_closed(self) -> None:
        document = contract.load_unique(contract.CONTRACT)
        mutations = (
            ("database", "plan_persisted_before_git_effect", False),
            ("database", "canonical_plan_max_bytes", 4097),
            ("database", "monotonic_fencing_token", False),
            ("database", "branch_head_reserved_while_executing", False),
            ("git", "old_oid_compare_and_swap", False),
            ("git", "accepts_caller_command_or_reference", True),
            ("recovery", "committed_git_finalizes_database_exactly_once", False),
            ("recovery", "blind_retry", True),
            ("transport", "arbitrary_host_configuration", True),
        )
        for section, key, value in mutations:
            tampered = copy.deepcopy(document)
            tampered[section][key] = value
            with self.assertRaises(contract.ContractError, msg=f"{section}.{key}"):
                contract.validate(tampered)

    def test_duplicate_key_and_non_object_contracts_fail_closed(self) -> None:
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
