from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_source_successor_pairs_v1 as pairs

ROOT = Path(__file__).resolve().parents[3]
PATH = ROOT / "tools/p17/frozen_p15_source_v1.py"
SPEC = importlib.util.spec_from_file_location("frozen_p15_source_v1_test", PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def locks(relative: str) -> list[dict[str, str]]:
    contract = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    return contract["source_locks"]


class FrozenP15SourceV1Tests(unittest.TestCase):
    def test_quota_context_admits_exact_policy_successor(self) -> None:
        replacements = MODULE.verified_replacements(
            ROOT,
            locks("implementation/p15/p15-quota-contract-v1.json"),
            "p15_quota",
        )
        self.assertEqual(
            replacements["crates/mcp-control-plane/src/policy.rs"],
            (
                "32513728470e18608d1eeff419e83ece628d6a9c4dd2a948c1c95012e97412ac",
                "b0b566a3bd753f9463c16bc384f73bdb1d91cde58a09c92c977ceb4348a79d53",
            ),
        )

    def test_handler_context_admits_exact_auth_validator_successor(self) -> None:
        replacements = pairs.p15_context_replacements(
            ROOT,
            locks("implementation/p15/p15-handler-contract-v1.json"),
            "p15_handler",
        )
        self.assertEqual(
            replacements["tools/p15/validate_auth_tenant.py"],
            (
                "c8b55055d720b3a76d0cc92f6d0bb2e24caa8f9e076c00e1e4bef3d7b394fb47",
                "c805d097d92c6e41d8434de8d62aed3fd88bf95cfc81a2fab4cc3d389ccfb86a",
            ),
        )

    def test_history_mismatch_fails_closed(self) -> None:
        with patch.object(MODULE, "git_blob_digest", return_value="0" * 64):
            with self.assertRaisesRegex(
                MODULE.FrozenP15SourceError, "context.identity"
            ):
                MODULE.verified_replacements(
                    ROOT,
                    locks("implementation/p15/p15-quota-contract-v1.json"),
                    "p15_quota",
                )

    def test_unknown_context_fails_closed(self) -> None:
        with self.assertRaisesRegex(MODULE.FrozenP15SourceError, "context.unknown"):
            MODULE.verified_replacements(ROOT, [], "unknown")


if __name__ == "__main__":
    unittest.main()
