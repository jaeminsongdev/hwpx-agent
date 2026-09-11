from __future__ import annotations

import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.dev.run import (
    BoundedJournal,
    DevRunError,
    execute,
    prepare_environment,
    redact,
    validate_command,
    validate_name,
)


ROOT = Path(__file__).resolve().parents[3]


class DevRunTests(unittest.TestCase):
    def test_redaction_covers_credentials_and_workspace(self) -> None:
        source = (
            f"{ROOT} Authorization=abc Bearer xyz password:hello "
            "https://user:pass@example.invalid/path api_key=qwerty "
            "{\"token\":\"json-secret\"}"
        )
        rendered = redact(source, ROOT)
        for secret in (
            "abc",
            "xyz",
            "hello",
            "user:pass",
            "qwerty",
            "json-secret",
            str(ROOT),
        ):
            self.assertNotIn(secret, rendered)
        self.assertIn("<workspace>", rendered)
        self.assertIn("<redacted>", rendered)

    def test_names_and_commands_are_bounded(self) -> None:
        self.assertEqual(validate_name("p07-focused"), "p07-focused")
        for invalid in ("", "../run", "a b", "."):
            with self.subTest(invalid=invalid):
                with self.assertRaises(DevRunError):
                    validate_name(invalid)
        with self.assertRaisesRegex(DevRunError, "run.command"):
            validate_command([])
        with self.assertRaisesRegex(DevRunError, "run.command"):
            validate_command(["python", "a\0b"])

    def test_sccache_is_applied_only_to_cargo_without_existing_wrapper(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch(
            "tools.dev.run.shutil.which", return_value="sccache"
        ):
            cargo = prepare_environment(["cargo", "test"], use_sccache=True)
            python = prepare_environment(["python", "-V"], use_sccache=True)
        self.assertEqual(cargo.sccache, "enabled")
        self.assertEqual(cargo.values["RUSTC_WRAPPER"], "sccache")
        self.assertEqual(cargo.values["CARGO_INCREMENTAL"], "0")
        self.assertEqual(python.sccache, "disabled")
        self.assertNotIn("RUSTC_WRAPPER", python.values)
        with patch.dict(os.environ, {"RUSTC_WRAPPER": "custom"}, clear=True):
            existing = prepare_environment(["cargo", "test"], use_sccache=True)
        self.assertEqual(existing.sccache, "existing")
        self.assertEqual(existing.values["RUSTC_WRAPPER"], "custom")

    def test_journal_truncates_events_and_writes_terminal_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "run"
            journal = BoundedJournal(
                directory,
                run_id="a" * 32,
                max_log_bytes=1_048_576,
                max_event_bytes=4_096,
            )
            journal.emit("output", 1, stream="stdout", message="x" * 20_000)
            journal.finish(
                {
                    "schema": "hwpx-agent.dev-run-summary/v1",
                    "status": "passed",
                }
            )
            event = json.loads(journal.events_path.read_text(encoding="utf-8"))
            event_bytes = journal.events_path.stat().st_size
            summary = json.loads(journal.summary_path.read_text(encoding="utf-8"))
        self.assertTrue(event["message_truncated"])
        self.assertLessEqual(event_bytes, 4_096)
        self.assertEqual(summary["status"], "passed")

    def test_execute_streams_both_channels_and_persists_only_redacted_output(self) -> None:
        script = (
            "import sys; "
            "print('token=topsecret'); "
            "print('password:alsosecret', file=sys.stderr); "
            "raise SystemExit(3)"
        )
        with tempfile.TemporaryDirectory() as temporary, patch(
            "tools.dev.run.sys.stdout", new_callable=io.StringIO
        ), patch("tools.dev.run.sys.stderr", new_callable=io.StringIO):
            result = execute(
                [sys.executable, "-c", script],
                name="runner-test",
                log_root=Path(temporary),
                heartbeat_seconds=1.0,
                use_sccache=False,
            )
            events = result.directory.joinpath("events.jsonl").read_text(encoding="utf-8")
            summary = json.loads(
                result.directory.joinpath("summary.json").read_text(encoding="utf-8")
            )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.exit_code, 3)
        self.assertNotIn("topsecret", events)
        self.assertNotIn("alsosecret", events)
        self.assertIn("<redacted>", events)
        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["exit_code"], 3)


if __name__ == "__main__":
    unittest.main()
