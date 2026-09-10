from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_p14_cancel_successor_v1 as successor

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_p14_cancel_successor_v1.py"


def source_lock(digest: str = successor.P15_PREDECESSOR_SHA256) -> dict[str, str]:
    return {"path": successor.RELATIVE, "sha256": digest}


class FrozenP14CancelSuccessorV1Tests(unittest.TestCase):
    def test_exact_successor_is_bound_to_both_commits(self) -> None:
        self.assertEqual(
            successor.verified_replacement(ROOT, source_lock()),
            (successor.P15_PREDECESSOR_SHA256, successor.SUCCESSOR_SHA256),
        )

    def test_unqualified_predecessor_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            successor.FrozenP14CancelSuccessorError, "source_lock.identity"
        ):
            successor.verified_replacement(ROOT, source_lock("0" * 64))

    def test_successor_blob_tamper_fails_closed(self) -> None:
        original = successor.frozen.git_blob

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = successor.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            if (
                revision == successor.SUCCESSOR_COMMIT
                and relative == successor.RELATIVE
            ):
                return raw + b"\n"
            return raw

        with patch.object(successor.frozen, "git_blob", side_effect=tampered):
            with self.assertRaisesRegex(
                successor.FrozenP14CancelSuccessorError, "successor.bytes"
            ):
                successor.verified_replacement(ROOT, source_lock())

    def test_source_has_no_mutable_qualifier_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("current_workspace_source_qualification", source)
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)


if __name__ == "__main__":
    unittest.main()
