from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest

from tools.dev.git_batch import (
    GitBatchError,
    GitBatchReader,
    REPOSITORY_ENVIRONMENT_KEYS,
    sanitized_git_environment,
)


ROOT = Path(__file__).resolve().parents[3]


def head_revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class GitBatchReaderTests(unittest.TestCase):
    def test_batch_bytes_equal_direct_git_and_cache_reuses_process(self) -> None:
        revision = head_revision()
        expected = subprocess.run(
            ["git", "cat-file", "blob", f"{revision}:PLANS.md"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        with GitBatchReader(ROOT) as reader:
            first = reader.read_blob(revision, "PLANS.md")
            second = reader.read_blob(revision, "PLANS.md")
            stats = reader.stats
        self.assertEqual(first, expected)
        self.assertEqual(second, expected)
        self.assertEqual(stats.process_starts, 1)
        self.assertEqual(stats.object_queries, 1)
        self.assertEqual(stats.cache_hits, 1)
        self.assertEqual(stats.cache_entries, 1)
        self.assertEqual(stats.cached_bytes, len(expected))

    def test_distinct_objects_share_one_batch_process(self) -> None:
        revision = head_revision()
        with GitBatchReader(ROOT) as reader:
            plans = reader.read_blob(revision, "PLANS.md")
            lock = reader.read_blob(revision, "Cargo.lock")
            stats = reader.stats
        self.assertTrue(plans.startswith(b"# HWPX Agent"))
        self.assertIn(b"[[package]]", lock)
        self.assertEqual(stats.process_starts, 1)
        self.assertEqual(stats.object_queries, 2)

    def test_invalid_revision_path_missing_blob_and_limit_fail_closed(self) -> None:
        revision = head_revision()
        with GitBatchReader(ROOT) as reader:
            with self.assertRaisesRegex(GitBatchError, "revision"):
                reader.read_blob("HEAD", "PLANS.md")
            for invalid in ("../PLANS.md", "/PLANS.md", "a\\b", "a:b", "a\nb"):
                with self.subTest(invalid=invalid):
                    with self.assertRaisesRegex(GitBatchError, "path"):
                        reader.read_blob(revision, invalid)
            with self.assertRaisesRegex(GitBatchError, "blob.header"):
                reader.read_blob(revision, "definitely-missing")
        with GitBatchReader(ROOT, max_blob_bytes=32) as reader:
            with self.assertRaisesRegex(GitBatchError, "blob.size"):
                reader.read_blob(revision, "PLANS.md")

    def test_repository_selection_environment_is_removed(self) -> None:
        original = {key: os.environ.get(key) for key in REPOSITORY_ENVIRONMENT_KEYS}
        try:
            for key in REPOSITORY_ENVIRONMENT_KEYS:
                os.environ[key] = "untrusted"
            environment = sanitized_git_environment()
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        for key in REPOSITORY_ENVIRONMENT_KEYS:
            self.assertNotIn(key, environment)
        self.assertEqual(environment["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(environment["GIT_NO_REPLACE_OBJECTS"], "1")
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_debug_output_does_not_reveal_repository_path(self) -> None:
        with GitBatchReader(ROOT) as reader:
            rendered = repr(reader)
        self.assertNotIn(str(ROOT), rendered)
        self.assertIn("cache_entries=0", rendered)


if __name__ == "__main__":
    unittest.main()
