from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "security_checks.py"
SPEC = importlib.util.spec_from_file_location("security_checks", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("unable to load security checks")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def result(
    exit_code: int,
    *,
    stdout: str = "",
    stderr: str = "",
    timed_out: bool = False,
    cleanup_succeeded: bool = True,
) -> dict[str, object]:
    return {
        "command": ["pnpm", "audit"],
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": timed_out,
        "cleanup_succeeded": cleanup_succeeded,
    }


class SecurityCaptureTests(unittest.TestCase):
    def test_evidence_runs_are_unique_and_no_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(MODULE, "EVIDENCE", Path(temporary)):
                first_id, first_root = MODULE.create_evidence_run()
                second_id, second_root = MODULE.create_evidence_run()
                self.assertTrue(first_root.is_dir())
                self.assertTrue(second_root.is_dir())
        self.assertNotEqual(first_id, second_id)
        self.assertNotEqual(first_root, second_root)
        self.assertEqual(first_root.parent, second_root.parent)

    def test_resolved_command_does_not_mutate_input(self) -> None:
        command = ["pnpm", "audit"]
        MODULE.resolved_command(command)
        self.assertEqual(command, ["pnpm", "audit"])

    def test_capture_timeout_terminates_owned_process(self) -> None:
        captured = MODULE.capture(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            timeout_seconds=0.1,
        )
        self.assertEqual(captured["exit_code"], 124)
        self.assertTrue(captured["timed_out"])
        self.assertTrue(captured["cleanup_succeeded"])

    def test_transient_registry_failure_retries_then_requires_success(self) -> None:
        responses = [
            result(23, stderr="The operation was aborted due to timeout"),
            result(0),
        ]
        with (
            mock.patch.object(MODULE, "capture", side_effect=responses) as capture,
            mock.patch.object(MODULE.time, "sleep"),
        ):
            captured = MODULE.capture_pnpm_audit()
        self.assertEqual(captured["exit_code"], 0)
        self.assertEqual(captured["attempt_count"], 2)
        self.assertTrue(captured["attempt_history"][0]["transient_failure"])
        self.assertEqual(capture.call_count, 2)

    def test_vulnerability_failure_is_not_retried(self) -> None:
        with mock.patch.object(MODULE, "capture", return_value=result(1)) as capture:
            captured = MODULE.capture_pnpm_audit()
        self.assertEqual(captured["exit_code"], 1)
        self.assertEqual(captured["attempt_count"], 1)
        self.assertFalse(captured["attempt_history"][0]["transient_failure"])
        capture.assert_called_once()

    def test_valid_vulnerability_json_overrides_network_marker_text(self) -> None:
        vulnerability = result(
            1,
            stdout='{"auditReportVersion":2,"vulnerabilities":{"sample":"ETIMEDOUT"},"metadata":{}}',
        )
        with mock.patch.object(MODULE, "capture", return_value=vulnerability) as capture:
            captured = MODULE.capture_pnpm_audit()
        self.assertEqual(captured["exit_code"], 1)
        self.assertEqual(captured["attempt_count"], 1)
        self.assertFalse(captured["attempt_history"][0]["transient_failure"])
        capture.assert_called_once()

    def test_cleanup_failure_is_not_retried(self) -> None:
        failed_cleanup = result(125, timed_out=True, cleanup_succeeded=False)
        with mock.patch.object(MODULE, "capture", return_value=failed_cleanup) as capture:
            captured = MODULE.capture_pnpm_audit()
        self.assertEqual(captured["exit_code"], 125)
        self.assertEqual(captured["attempt_count"], 1)
        self.assertFalse(captured["attempt_history"][0]["transient_failure"])
        capture.assert_called_once()

    def test_transient_exhaustion_remains_failed(self) -> None:
        responses = [result(124, timed_out=True) for _ in range(MODULE.PNPM_AUDIT_ATTEMPTS)]
        with (
            mock.patch.object(MODULE, "capture", side_effect=responses),
            mock.patch.object(MODULE.time, "sleep"),
        ):
            captured = MODULE.capture_pnpm_audit()
        self.assertEqual(captured["exit_code"], 124)
        self.assertEqual(captured["attempt_count"], MODULE.PNPM_AUDIT_ATTEMPTS)
        self.assertTrue(all(item["transient_failure"] for item in captured["attempt_history"]))


if __name__ == "__main__":
    unittest.main()
