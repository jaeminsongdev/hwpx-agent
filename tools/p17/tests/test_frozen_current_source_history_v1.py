from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_history_v1 as history

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_current_source_history_v1.py"


class FrozenCurrentSourceHistoryV1Tests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        history.clear_cache()

    def test_v20_through_v39_are_verified_from_exact_history(self) -> None:
        v20 = history.verify_version(ROOT, 20)
        v39 = history.verify_version(ROOT, 39)
        self.assertEqual(v20["qualification_id"], history.qualification_id(20))
        self.assertEqual(v39["qualification_id"], history.qualification_id(39))
        self.assertEqual(history.EXPECTED_VERSIONS, tuple(range(20, 40)))
        self.assertEqual(len(history.verified_implementation_sources(ROOT, 20)), 118)
        self.assertEqual(len(history.verified_successors(ROOT, 20)), 25)
        self.assertEqual(len(history.verified_implementation_sources(ROOT, 39)), 7)
        self.assertEqual(len(history.verified_successors(ROOT, 39)), 26)
        self.assertFalse(v39["claims"]["actual_hangul"])
        self.assertFalse(v39["claims"]["production"])
        self.assertFalse(v39["claims"]["product_complete"])

    def test_contract_history_tamper_fails_closed(self) -> None:
        history.clear_cache()
        original = history.frozen.git_blob
        target = history.contract_relative(39)

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = history.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return raw + b"\n" if relative == target else raw

        try:
            with patch.object(history.frozen, "git_blob", side_effect=tampered):
                with self.assertRaisesRegex(
                    history.FrozenSourceHistoryError, "v39.contract.digest"
                ):
                    history.verify_version(ROOT, 20)
        finally:
            history.clear_cache()

    def test_source_history_tamper_fails_closed(self) -> None:
        history.clear_cache()
        original = history.frozen.git_blob
        target = "protocol/private/p06-table-formula-target-v2.json"

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = history.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return b"tampered" if relative == target else raw

        try:
            with patch.object(history.frozen, "git_blob", side_effect=tampered):
                with self.assertRaisesRegex(
                    history.FrozenSourceHistoryError, "implementation"
                ):
                    history.verify_version(ROOT, 39)
        finally:
            history.clear_cache()

    def test_invalid_version_fails_closed(self) -> None:
        for version in (True, 19, 40):
            with self.subTest(version=version):
                with self.assertRaisesRegex(
                    history.FrozenSourceHistoryError, "version"
                ):
                    history.verify_version(ROOT, version)

    def test_source_has_no_legacy_validator_import_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("current_workspace_source_qualification_v", source)
        self.assertNotIn("importlib", source)
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)


if __name__ == "__main__":
    unittest.main()
