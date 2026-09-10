from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v41 as frozen


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_current_source_v41.py"


class FrozenCurrentSourceV41Tests(unittest.TestCase):
    def test_exact_historical_qualification_passes_without_phase_promotion(self) -> None:
        result = frozen.verify(ROOT)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["implementation_source_count"], 20)
        self.assertEqual(result["runtime_qualification_source_count"], 6)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 59)
        self.assertEqual(
            result["intentional_overlap"],
            ["crates/artifact-service/src/store/postgres_repository.rs"],
        )
        self.assertTrue(result["receipt_blob_verified"])
        self.assertTrue(result["durable_push_runtime_verified"])
        self.assertFalse(result["durable_pull"])
        self.assertFalse(result["actual_remote_network"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])
        self.assertFalse(result["mutable_worktree_sources_read"])

    def test_contract_and_runtime_history_tamper_fail_closed(self) -> None:
        original = frozen.git_blob

        def tampered(root: Path, revision: str, relative: str, maximum: int = 4_000_000) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == frozen.CONTRACT_RELATIVE:
                return raw + b"\n"
            return raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenSourceV41Error, "json.bytes"):
                frozen.verify(ROOT)

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(root: Path, revision: str, relative: str, maximum: int = 4_000_000) -> bytes:
            raw = original(root, revision, relative, maximum)
            if relative == "crates/remote-sync-host/src/durable_git_push.rs":
                return b"tampered"
            return raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenSourceV41Error, "implementation.bytes"):
                frozen.verify(ROOT)

    def test_source_has_no_mutable_qualification_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn(
            "from tools.p17 import current_workspace_source_qualification_v41",
            source,
        )
        self.assertNotIn(
            "from tools.p17 import durable_git_mirror_push_qualification",
            source,
        )
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)
        self.assertIn("frozen_current_source_v40", source)
        self.assertIn("frozen_durable_git_mirror_push_v15", source)


if __name__ == "__main__":
    unittest.main()
