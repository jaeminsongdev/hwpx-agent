from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v40 as frozen

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_current_source_v40.py"


class FrozenCurrentSourceV40Tests(unittest.TestCase):
    def test_exact_historical_qualification_passes_without_product_promotion(
        self,
    ) -> None:
        result = frozen.verify(ROOT)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["qualification_id"], frozen.QUALIFICATION_ID)
        self.assertEqual(result["implementation_source_count"], 9)
        self.assertEqual(result["source_successor_count"], 28)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 53)
        self.assertEqual(result["intentional_overlap"], ["Cargo.lock"])
        self.assertTrue(result["receipt_reference_bound"])
        self.assertFalse(result["receipt_blob_verified"])
        self.assertFalse(result["mutable_worktree_sources_read"])
        self.assertFalse(result["actual_hangul"])
        self.assertFalse(result["production"])
        self.assertFalse(result["product_complete"])

    def test_qualification_contract_blob_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return raw + b"\n" if relative == frozen.CONTRACT_RELATIVE else raw

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenSourceV40Error, "json.bytes"):
                frozen.verify(ROOT)

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob
        target = "crates/remote-sync-host/src/git_mirror.rs"

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return (
                b"tampered"
                if revision == frozen.BASE_COMMIT and relative == target
                else raw
            )

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                frozen.FrozenSourceV40Error, "implementation.bytes"
            ):
                frozen.verify(ROOT)

    def test_successor_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return (
                b"tampered"
                if revision == frozen.BASE_COMMIT and relative == "Cargo.lock"
                else raw
            )

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                frozen.FrozenSourceV40Error, "implementation.bytes|successor.history"
            ):
                frozen.verify(ROOT)

    def test_guard_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob
        target = "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V40.md"

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return (
                b"tampered"
                if revision == frozen.QUALIFICATION_COMMIT and relative == target
                else raw
            )

        with patch.object(frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(frozen.FrozenSourceV40Error, "guard.bytes"):
                frozen.verify(ROOT)

    def test_unbounded_or_ambiguous_git_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(frozen.FrozenSourceV40Error, "revision"):
            frozen.git_blob(ROOT, "HEAD", frozen.CONTRACT_RELATIVE)
        for relative in ("../contract.json", "/contract.json", "a\\b", "a//b", "a:b"):
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(frozen.FrozenSourceV40Error, "path"):
                    frozen.git_blob(ROOT, frozen.QUALIFICATION_COMMIT, relative)

    def test_source_has_no_mutable_qualification_or_worktree_file_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn(
            "from tools.p17 import current_workspace_source_qualification_v40", source
        )
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)
        self.assertIn("frozen_current_source_v39", source)


if __name__ == "__main__":
    unittest.main()
