from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import validate_git_mirror_effect_contract as contract  # noqa: E402


class GitMirrorEffectContractTests(unittest.TestCase):
    def test_current_contract_and_sources_pass(self) -> None:
        document = contract.verify()
        self.assertEqual(document["schema_version"], "hwpx-agent.git-mirror-effect/v1")

    def test_claim_promotion_tampering_fails_closed(self) -> None:
        document = contract.load_unique(contract.CONTRACT)
        for claim in (
            "actual_remote_network",
            "actual_postgresql_state_machine",
            "authenticated_host_dispatch",
            "persistent_credential_custody",
            "production",
            "p17_06_complete",
        ):
            tampered = copy.deepcopy(document)
            tampered["evidence"][claim] = True
            with self.assertRaises(contract.ContractError, msg=claim):
                contract.validate(tampered)

    def test_cas_recovery_and_bound_tampering_fails_closed(self) -> None:
        document = contract.load_unique(contract.CONTRACT)
        mutations = (
            ("publish", "old_oid_compare_and_swap", False),
            ("publish", "blind_retry", True),
            ("plan", "canonical_max_bytes", 4097),
            ("state", "tree_contains_only_state", False),
            ("repository_admission", "repository_hooks", True),
        )
        for section, key, value in mutations:
            tampered = copy.deepcopy(document)
            tampered[section][key] = value
            message = f"{section}.{key}"
            with self.assertRaises(contract.ContractError, msg=message):
                contract.validate(tampered)

    def test_duplicate_key_and_non_object_contracts_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "contract.json"
            path.write_text(
                '{"schema_version":"a","schema_version":"b"}', encoding="utf-8"
            )
            with self.assertRaises(contract.ContractError):
                contract.load_unique(path)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(contract.ContractError):
                contract.load_unique(path)


if __name__ == "__main__":
    unittest.main()
