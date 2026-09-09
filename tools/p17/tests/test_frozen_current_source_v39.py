from __future__ import annotations

from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from tools.p17 import frozen_current_source_v39 as frozen

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_current_source_v39.py"


class FrozenCurrentSourceV39Tests(unittest.TestCase):
    def test_exact_historical_qualification_passes_without_runtime_promotion(
        self,
    ) -> None:
        result = frozen.verify(ROOT)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["qualification_id"], frozen.QUALIFICATION_ID)
        self.assertEqual(result["implementation_source_count"], 7)
        self.assertEqual(result["source_successor_count"], 26)
        self.assertEqual(result["guard_source_count"], 3)
        self.assertEqual(result["claim_count"], 45)
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
            with self.assertRaisesRegex(frozen.FrozenSourceV39Error, "json.bytes"):
                frozen.verify(ROOT)

    def test_implementation_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob
        target = "protocol/private/p06-table-formula-target-v2.json"

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
                frozen.FrozenSourceV39Error, "implementation.bytes"
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
                frozen.FrozenSourceV39Error, "successor.history"
            ):
                frozen.verify(ROOT)

    def test_guard_history_tamper_fails_closed(self) -> None:
        original = frozen.git_blob
        target = "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V39.md"

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
            with self.assertRaisesRegex(frozen.FrozenSourceV39Error, "guard.bytes"):
                frozen.verify(ROOT)

    def test_unbounded_or_ambiguous_git_inputs_are_rejected(self) -> None:
        with self.assertRaisesRegex(frozen.FrozenSourceV39Error, "revision"):
            frozen.git_blob(ROOT, "HEAD", frozen.CONTRACT_RELATIVE)
        for relative in ("../contract.json", "/contract.json", "a\\b", "a//b", "a:b"):
            with self.subTest(relative=relative):
                with self.assertRaisesRegex(frozen.FrozenSourceV39Error, "path"):
                    frozen.git_blob(ROOT, frozen.QUALIFICATION_COMMIT, relative)

    def test_git_execution_disables_replace_refs_lazy_fetch_and_locks(self) -> None:
        completed = subprocess.CompletedProcess(["git"], 0, stdout=b"", stderr=b"")
        injected = {key: "unexpected" for key in frozen.REPOSITORY_ENVIRONMENT_KEYS}
        with patch.dict(frozen.os.environ, injected):
            with patch.object(frozen.subprocess, "run", return_value=completed) as run:
                self.assertEqual(frozen.git_output(ROOT, ["version"], 0, "git"), b"")
        environment = run.call_args.kwargs["env"]
        for key in frozen.REPOSITORY_ENVIRONMENT_KEYS:
            self.assertNotIn(key, environment)
        self.assertEqual(environment["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(environment["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_source_has_no_mutable_validator_or_worktree_file_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("importlib", source)
        self.assertNotIn(
            "from tools.p17 import current_workspace_source_qualification_v39", source
        )
        self.assertNotIn("read_bytes(", source)
        self.assertNotIn("read_text(", source)


if __name__ == "__main__":
    unittest.main()
