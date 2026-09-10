from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_composed_source_v39 as chain
from tools.p17 import frozen_current_source_v12 as v12

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_composed_source_v39.py"


class FrozenComposedSourceV39Tests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        chain.clear_cache()

    def test_p15_and_v20_edges_compose_to_v39(self) -> None:
        target = chain.verified_target(
            ROOT,
            "tools/p15/validate_handler_contract.py",
            "4be508c7d4706388861c0ba0aead076ba36356a7302043441d4bf7877dcf5b45",
        )
        self.assertEqual(
            target,
            "86c044ee38112bca4540ec730a1e902d0156632cb1ef3d4f2fcb8bba3e8f3c6a",
        )

    def test_legacy_contract_states_compose_to_v39(self) -> None:
        target = chain.verified_target(
            ROOT,
            "crates/mcp-control-plane/src/handler.rs",
            "652c9d214590d60cc466769918b801eac89743a70db4a0eeef02677a3f4668ae",
        )
        self.assertEqual(
            target,
            "8ff8a1be4750b842558ea0c5047431d5cb5aa76fc8a5e0651525c3e107b9d99d",
        )

    def test_consecutive_qualification_states_compose_to_v39(self) -> None:
        target = chain.verified_target(
            ROOT,
            "Cargo.lock",
            "46b3259e3a1fd86f6d7f8c3c676c5dfc1e4144c2bde1b78e61a811a0a92b0d49",
        )
        self.assertEqual(
            target,
            "716028407f2ac804f0a57a4e6b85dd499736dc62c6df090bbad73081ae08726e",
        )

    def test_unqualified_predecessor_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            chain.FrozenComposedSourceError, "chain.unreachable"
        ):
            chain.verified_target(ROOT, "Cargo.toml", "0" * 64)

    def test_unreachable_path_does_not_discard_verified_replacements(self) -> None:
        replacements = v12.verified_replacements(
            ROOT,
            [
                {
                    "path": "deny.toml",
                    "sha256": (
                        "1b7f0c7a65ba80242847fbb24483fa82708f28b361e425c76c48233d52073ef3"
                    ),
                },
                {
                    "path": "docs/09_roadmap/P15_remote_mcp_control_plane.md",
                    "sha256": (
                        "a77298e3eaafc3c6a544e53ef3e79c90f6ecb984b01128a174d96ad3bcaa2b5b"
                    ),
                },
            ],
        )
        self.assertEqual(
            replacements,
            {
                "deny.toml": (
                    "1b7f0c7a65ba80242847fbb24483fa82708f28b361e425c76c48233d52073ef3",
                    "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
                )
            },
        )

    def test_exact_legacy_deny_transition_composes_to_v39(self) -> None:
        target = chain.verified_target(
            ROOT,
            "deny.toml",
            "1b7f0c7a65ba80242847fbb24483fa82708f28b361e425c76c48233d52073ef3",
        )
        self.assertEqual(
            target,
            "a939acc670946e472480d5dde52b0bc19caa326abd14418e90b522deb03025bd",
        )

    def test_source_has_no_worktree_or_mutable_qualifier_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("current_workspace_source_qualification", source)
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)

    def test_anchor_tamper_fails_closed(self) -> None:
        chain.clear_cache()
        original = chain.anchor.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = chain.anchor.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "Cargo.toml":
                return raw + b"\n"
            return raw

        try:
            with patch.object(chain.anchor, "git_blob", side_effect=tampered):
                with self.assertRaises(ValueError):
                    chain.verified_target(
                        ROOT,
                        "Cargo.toml",
                        "317b38412eaddc5c2a630ad753ac1370f38358aff619940b4537ed63f3a29c28",
                    )
        finally:
            chain.clear_cache()


if __name__ == "__main__":
    unittest.main()
