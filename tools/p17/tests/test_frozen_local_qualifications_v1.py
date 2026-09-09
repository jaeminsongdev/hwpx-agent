from __future__ import annotations

from pathlib import Path
import unittest
from unittest.mock import patch

from tools.p17 import frozen_local_qualifications_v1 as frozen_local

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools/p17/frozen_local_qualifications_v1.py"


class FrozenLocalQualificationsV1Tests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        frozen_local.clear_cache()

    def test_all_five_qualifications_verify_without_runtime_promotion(self) -> None:
        expected_counts = {
            "local_daemon": (10, 3),
            "local_mcp_plugin": (17, 3),
            "main_bound_plugin": (13, 3),
            "postgres_checkpoint_host": (29, 6),
            "widget_plugin_prepare": (17, 3),
        }
        for name, counts in expected_counts.items():
            with self.subTest(name=name):
                contract = frozen_local.verify(name, ROOT)
                sources = frozen_local.verified_sources(name, ROOT)
                self.assertEqual(
                    (len(sources["runtime_sources"]), len(sources["guard_sources"])),
                    counts,
                )
                self.assertFalse(contract["claims"].get("actual_hangul", False))
                self.assertFalse(contract["claims"].get("phase_complete", False))

    def test_contract_tamper_fails_closed(self) -> None:
        frozen_local.clear_cache()
        original = frozen_local.frozen.git_blob
        specification = frozen_local.QUALIFICATIONS["local_daemon"]
        target, _ = frozen_local.qualification_paths(specification)

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = frozen_local.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return raw + b"\n" if relative == target else raw

        try:
            with patch.object(frozen_local.frozen, "git_blob", side_effect=tampered):
                with self.assertRaisesRegex(
                    frozen_local.FrozenLocalQualificationError,
                    "local_daemon.contract.bytes",
                ):
                    frozen_local.verify("local_daemon", ROOT)
        finally:
            frozen_local.clear_cache()

    def test_runtime_source_tamper_fails_closed(self) -> None:
        frozen_local.clear_cache()
        original = frozen_local.frozen.git_blob
        target = "crates/local-companion-daemon/tests/sandbox.rs"

        def tampered(
            root: Path,
            revision: str,
            relative: str,
            maximum: int = frozen_local.frozen.MAX_BLOB_BYTES,
        ) -> bytes:
            raw = original(root, revision, relative, maximum)
            return b"tampered" if relative == target else raw

        try:
            with patch.object(frozen_local.frozen, "git_blob", side_effect=tampered):
                with self.assertRaisesRegex(
                    frozen_local.FrozenLocalQualificationError,
                    "local_daemon.runtime.bytes",
                ):
                    frozen_local.verify("local_daemon", ROOT)
        finally:
            frozen_local.clear_cache()

    def test_unknown_qualification_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            frozen_local.FrozenLocalQualificationError, "qualification.unknown"
        ):
            frozen_local.verify("unknown", ROOT)

    def test_source_has_no_mutable_qualifier_import_or_worktree_reader(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for forbidden in (
            "local_daemon_qualification",
            "local_mcp_plugin_qualification",
            "main_bound_plugin_qualification",
            "postgres_checkpoint_host_qualification",
            "widget_plugin_prepare_qualification",
            "read_bytes(",
            "read_text(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
