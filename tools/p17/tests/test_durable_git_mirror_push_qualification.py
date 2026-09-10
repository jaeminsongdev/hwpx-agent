from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_durable_git_mirror_push_v15 as qualification


ROOT = Path(__file__).resolve().parents[3]


class DurableGitMirrorPushQualificationTests(unittest.TestCase):
    def test_historical_qualification_uses_frozen_git_state(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(
            result["qualification_id"],
            "p17.durable-git-mirror-push.v1.20260910",
        )
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_exact_historical_runtime_qualification_is_preserved(self) -> None:
        result = qualification.verify(ROOT)
        self.assertEqual(result["runtime_source_count"], 39)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["check_count"], 27)
        self.assertTrue(result["receipt_blob_verified"])
        self.assertTrue(result["actual_authenticated_loopback"])
        self.assertFalse(result["actual_remote_network"])
        self.assertFalse(result["durable_pull"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])

    def test_qualification_contract_blob_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == qualification.CONTRACT_RELATIVE:
                return raw + b"\n"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenDurableGitPushV15Error, "json.bytes"
            ):
                qualification.verify(ROOT)

    def test_runtime_source_history_tamper_fails_closed(self) -> None:
        original = qualification.git_blob

        def tampered(
            root: Path, revision: str, relative: str, maximum: int = 4_000_000
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "crates/remote-sync-host/src/durable_git_push.rs":
                return b"tampered"
            return raw

        with patch.object(qualification, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                qualification.FrozenDurableGitPushV15Error, "runtime.bytes"
            ):
                qualification.verify(ROOT)


if __name__ == "__main__":
    unittest.main()
