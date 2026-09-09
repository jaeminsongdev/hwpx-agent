from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_source_successor_pairs_v1 as pairs

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_source_successor_pairs_v1.py"


def locks(relative: str) -> list[dict[str, str]]:
    contract = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    return contract["source_locks"]


class FrozenSourceSuccessorPairsV1Tests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        pairs.clear_cache()

    def test_v12_pair_is_verified_without_current_source_read(self) -> None:
        replacements = pairs.v12_replacements(
            ROOT, locks("implementation/p15/p15-inspector-staging-contract-v1.json")
        )
        self.assertEqual(
            replacements["deny.toml"],
            (
                "1b7f0c7a65ba80242847fbb24483fa82708f28b361e425c76c48233d52073ef3",
                "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
            ),
        )

    def test_p15_context_pair_is_verified_across_exact_history(self) -> None:
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

    def test_v12_successor_tamper_fails_closed(self) -> None:
        original = pairs.frozen.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = pairs.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if revision == pairs.V12_BASE_COMMIT and relative == "deny.toml":
                return b"tampered"
            return raw

        with patch.object(pairs.frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                pairs.FrozenSuccessorPairError, "v12.successor.history"
            ):
                pairs.v12_replacements(
                    ROOT,
                    locks("implementation/p15/p15-inspector-staging-contract-v1.json"),
                )

    def test_unknown_p15_context_fails_closed(self) -> None:
        with self.assertRaisesRegex(pairs.FrozenSuccessorPairError, "context.unknown"):
            pairs.p15_context_replacements(
                ROOT, [{"path": "x", "sha256": "0" * 64}], "unknown"
            )

    def test_source_has_no_mutable_qualifier_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("frozen_current_source_v12", source)
        self.assertNotIn("frozen_p15_source_v1", source)
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)


if __name__ == "__main__":
    unittest.main()
