from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_durable_git_mirror_pull_v17 as frozen


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_durable_git_mirror_pull_v17.py"


class FrozenDurableGitMirrorPullV17Tests(unittest.TestCase):
    def test_exact_historical_runtime_qualification_passes(self) -> None:
        result = frozen.verify(ROOT)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["runtime_source_count"], 48)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["check_count"], 20)
        self.assertTrue(result["receipt_blob_verified"])
        self.assertTrue(result["actual_authenticated_loopback"])
        self.assertTrue(result["durable_pull"])
        self.assertFalse(result["actual_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_qualification_contract_blob_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return raw + b"\n" if relative == frozen.CONTRACT_RELATIVE else raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenDurableGitPullV17Error, "json.bytes"):
                frozen.verify(ROOT)

    def test_runtime_source_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "crates/remote-sync-host/src/durable_git_pull.rs":
                return b"tampered"
            return raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                frozen.FrozenDurableGitPullV17Error, "runtime.bytes"
            ):
                frozen.verify(ROOT)

    def test_receipt_claim_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == frozen.RECEIPT_RELATIVE:
                return raw.replace(b'"actual_remote_network":false', b'"actual_remote_network":true ')
            return raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                frozen.FrozenDurableGitPullV17Error, "json.digest"
            ):
                frozen.verify(ROOT)

    def test_source_has_no_mutable_qualification_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("durable_git_mirror_pull_qualification as", source)
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)
        self.assertIn("frozen_current_source_v41", source)


if __name__ == "__main__":
    unittest.main()
