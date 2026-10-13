"""Closed-task, pipe and mock Job boundaries; no tool/child process execution."""
import ast
import io
import json
from pathlib import Path
import subprocess
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import bounded_audit_tools as subject


class Input(io.BytesIO):
    def close(self):
        if not self.closed:
            self.written = self.getvalue()
        super().close()


class BoundedAuditToolsTests(unittest.TestCase):
    def environment(self):
        kernel = SimpleNamespace(**{name: Mock(return_value=True) for name in
            ("AssignProcessToJobObject", "TerminateJobObject", "CloseHandle", "ReleaseMutex")})
        kernel.CreateMutexW = Mock(return_value=101)
        windows = SimpleNamespace(k=kernel, job=Mock(return_value=102), cpu_rate=625, memory_limit=10485760,
            accounting=Mock(return_value={"active_processes": 0, "peak_job_private_mib": 5.0,
                "peak_job_private_percent": 0.1}),
            sample=Mock(return_value={"system_cpu_percent": 10, "available_ram_percent": 40,
                "commit_used_percent": 50}))
        process = SimpleNamespace(_handle=103, stdin=Input(), stdout=io.BufferedReader(io.BytesIO()),
            stderr=io.BufferedReader(io.BytesIO()), returncode=0,
            poll=Mock(return_value=0), wait=Mock(return_value=0), kill=Mock())
        capture = SimpleNamespace(communicate=Mock(return_value=("formatted\n", "")), check=Mock(), close=Mock())
        return windows, process, capture

    def run_fixture(self, windows, process, capture, checkpoint=None):
        with patch.object(subject, "Windows", return_value=windows), \
                patch.object(subject.ctypes, "get_last_error", return_value=0), \
                patch.object(subject.subprocess, "Popen", return_value=process) as launch, \
                patch.object(subject, "AuditToolCapture", return_value=capture) as pipes:
            result = subject.run_audit_tool("rustfmt-stdin", "fn main() {}\n", checkpoint)
        return result, launch, pipes

    def test_closed_tasks_and_exact_readonly_arguments(self):
        self.assertEqual(set(subject.TASKS), {"rustfmt-stdin", "rust-input-inventory"})
        self.assertEqual(subject.TASKS["rustfmt-stdin"], ("rustfmt", ["--edition", "2024", "--emit", "stdout"]))
        self.assertEqual(subject.TASKS["rust-input-inventory"], ("rg", ["--threads", "1", "--files",
            "crates", "protocol/generated/rust", "tools/xtask", "-g", "*.rs", "-g", "Cargo.toml"]))
        for task in ("cargo", "docker", "arbitrary", [], None):
            with self.assertRaisesRegex(ValueError, "^audit_tool_task_scope$"):
                subject.payload_for(task, None)

    def test_utf8_input_budget_and_inventory_cannot_accept_input(self):
        self.assertEqual(subject.payload_for("rustfmt-stdin", "한글"), "한글".encode())
        self.assertEqual(subject.payload_for("rust-input-inventory", None), b"")
        for value in ("x"*(subject.INPUT_LIMIT+1), "한"*(subject.INPUT_LIMIT//3+1)):
            with self.assertRaisesRegex(ValueError, "^audit_tool_input_budget$"):
                subject.payload_for("rustfmt-stdin", value)
        with self.assertRaisesRegex(ValueError, "^audit_tool_input_encoding$"):
            subject.payload_for("rustfmt-stdin", "\ud800")
        with self.assertRaises(ValueError):
            subject.payload_for("rust-input-inventory", "ignored-input")

    def test_capture_preserves_utf8_and_legacy_universal_newlines(self):
        _, process, _ = self.environment()
        process.stdout = io.BufferedReader(io.BytesIO("한글\r\nnext\rlast\n".encode()))
        capture = subject.AuditToolCapture(process, b"GO\n0\n")
        try:
            self.assertEqual(capture.communicate(1), ("한글\nnext\nlast\n", ""))
            self.assertEqual(process.stdin.written, b"GO\n0\n")
        finally:
            capture.close()

    def test_capture_hard_output_budget_is_not_truncated_or_accepted(self):
        capture = subject.AuditToolCapture.__new__(subject.AuditToolCapture)
        capture.lock, capture.error = threading.Lock(), None
        capture.buffers = {"stdout": bytearray(), "stderr": bytearray()}
        for name, limit in subject.OUTPUT_LIMITS.items():
            capture.error = None
            capture._accept(name, b"x"*(limit+1))
            self.assertEqual(len(capture.buffers[name]), 0)
            with self.assertRaisesRegex(ValueError, "^audit_tool_output_budget$"):
                capture.check()

    def test_bad_output_encoding_and_failed_writer_fail_closed(self):
        _, process, _ = self.environment()
        process.stdout = io.BufferedReader(io.BytesIO(b"\xff"))
        capture = subject.AuditToolCapture(process, b"GO\n0\n")
        try:
            with self.assertRaisesRegex(ValueError, "^audit_tool_output_encoding$"):
                capture.communicate(1)
        finally:
            capture.close()
        _, process, _ = self.environment()
        process.stdin.write = Mock(return_value=0)
        capture = subject.AuditToolCapture(process, b"GO\n0\n")
        try:
            with self.assertRaisesRegex(ValueError, "^audit_tool_pipe_write_failed$"):
                capture.communicate(1)
        finally:
            capture.close()

    def test_job_assignment_precedes_writer_authorization(self):
        windows, process, capture = self.environment()
        order = []
        windows.k.AssignProcessToJobObject.side_effect = lambda *args: order.append("assign") or True
        def pipes(child, request):
            self.assertEqual(order, ["checkpoint", "assign", "checkpoint"])
            self.assertEqual(request, b"P149_AUDIT_GO\n13\nfn main() {}\n")
            return capture
        with patch.object(subject, "Windows", return_value=windows), \
                patch.object(subject.ctypes, "get_last_error", return_value=0), \
                patch.object(subject.subprocess, "Popen", return_value=process), \
                patch.object(subject, "AuditToolCapture", side_effect=pipes):
            result = subject.run_audit_tool("rustfmt-stdin", "fn main() {}\n", lambda: order.append("checkpoint"))
        self.assertEqual(result.stdout, "formatted\n")
        self.assertTrue(result.audit_limits["owned_tree_empty"])
        self.assertEqual(result.audit_limits["job_private_peak_mib"], 5.0)
        windows.k.TerminateJobObject.assert_called_once_with(102, 1)

    def test_assignment_failure_never_starts_writer_or_tool(self):
        windows, process, capture = self.environment()
        windows.k.AssignProcessToJobObject.return_value = False
        process.poll.return_value = None
        with self.assertRaisesRegex(ValueError, "^audit_tool_job_assignment_failed$"):
            self.run_fixture(windows, process, capture)
        capture.communicate.assert_not_called()
        process.kill.assert_called_once()
        self.assertTrue(process.stdin.closed)

    def test_resource_preflight_refuses_before_starting_owned_worker(self):
        windows, process, capture = self.environment()
        windows.sample.return_value["available_ram_percent"] = 7
        with self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$"):
            self.run_fixture(windows, process, capture)
        windows.job.assert_not_called()
        capture.communicate.assert_not_called()

    def test_timeout_and_output_overflow_stop_only_owned_job(self):
        windows, process, capture = self.environment()
        with patch.object(subject.time, "monotonic", side_effect=[0, 0, 11, 11, 11]):
            with self.assertRaisesRegex(ValueError, "^audit_tool_command_timeout$"):
                self.run_fixture(windows, process, capture)
        windows.k.TerminateJobObject.assert_called_once()
        windows, process, capture = self.environment()
        capture.communicate.side_effect = subprocess.TimeoutExpired("fixture", 0.25)
        capture.check.side_effect = [None, ValueError("audit_tool_output_budget")]
        with self.assertRaisesRegex(ValueError, "^audit_tool_output_budget$"):
            self.run_fixture(windows, process, capture)
        windows.k.TerminateJobObject.assert_called_once()

    def test_cleanup_failure_cannot_return_tool_success(self):
        windows, process, capture = self.environment()
        windows.k.TerminateJobObject.return_value = False
        with self.assertRaisesRegex(ValueError, "^audit_tool_cleanup_not_confirmed$"):
            self.run_fixture(windows, process, capture)
        self.assertEqual(windows.k.CloseHandle.call_count, 2)
        capture.close.assert_called_once()

    def test_initial_checkpoint_and_missing_worker_go_start_nothing(self):
        with patch.object(subject, "Windows") as setup:
            with self.assertRaisesRegex(ValueError, "^fixture_stop$"):
                subject.run_audit_tool("rustfmt-stdin", "x", Mock(side_effect=ValueError("fixture_stop")))
        setup.assert_not_called()
        with patch.object(subject, "Windows"), \
                patch.object(subject.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"wrong\n"))), \
                patch.object(subject.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "^audit_tool_worker_not_authorized$"):
                subject.worker("rustfmt-stdin")
        launch.assert_not_called()

    def test_worker_has_no_output_capture_installation_or_source_write_commands(self):
        tree = ast.parse(Path(subject.__file__).read_text(encoding="utf-8"))
        worker = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "worker")
        launches = [node for node in ast.walk(worker) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == "Popen"]
        self.assertEqual(len(launches), 1)
        self.assertFalse({"stdout", "stderr", "shell", "capture_output"}.intersection(
            keyword.arg for keyword in launches[0].keywords))
        self.assertFalse(any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"write_text", "write_bytes", "unlink", "rmdir"} for node in ast.walk(tree)))
        self.assertIn('RUSTUP_AUTO_INSTALL="0"', Path(subject.__file__).read_text(encoding="utf-8"))

    def test_only_exact_sibling_rustup_symlink_is_allowed_and_invocation_name_retained(self):
        invoked = Path("C:/fixture/rustfmt.exe").absolute()
        for target, accepted in ((Path("C:/fixture/rustup.exe").absolute(), True),
                (Path("C:/foreign/rustup.exe").absolute(), False),
                (Path("C:/fixture/other.exe").absolute(), False)):
            def resolved(path):
                return target if path == invoked else path
            with patch.object(subject.shutil, "which", return_value=str(invoked)), \
                    patch.object(Path, "is_file", return_value=True), \
                    patch.object(Path, "is_junction", return_value=False), \
                    patch.object(Path, "is_symlink", lambda path: path == invoked), \
                    patch.object(Path, "resolve", resolved):
                if accepted:
                    self.assertEqual(subject.executable_for("rustfmt-stdin"), str(invoked))
                else:
                    with self.assertRaisesRegex(ValueError, "^audit_tool_executable_scope$"):
                        subject.executable_for("rustfmt-stdin")

    def test_preflight_failure_retains_observation_without_inventing_job_peak(self):
        windows, process, capture = self.environment()
        windows.sample.return_value["available_ram_percent"] = 7
        with self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$") as caught:
            self.run_fixture(windows, process, capture)
        profile = caught.exception.audit_limits
        self.assertEqual(profile["operation_phase"], "preflight")
        self.assertEqual(profile["system_first"]["available_ram_percent"], 7)
        self.assertFalse(profile["worker_created"])
        self.assertTrue(profile["no_owned_worker_started"])
        self.assertTrue(profile["owned_tree_empty"])
        self.assertIsNone(profile["job_private_peak_mib"])
        self.assertFalse(profile["job_accounting_observed"])
        windows.job.assert_not_called()

    def test_running_resource_failure_keeps_job_profile_after_cleanup_and_redacts_fields(self):
        windows, process, capture = self.environment()
        windows.sample.side_effect = [dict(windows.sample.return_value),
            dict(windows.sample.return_value),
            {"system_cpu_percent": 100, "available_ram_percent": 7, "commit_used_percent": 97}]
        active = {"active_processes": 2, "peak_job_private_mib": 6,
            "peak_job_private_percent": 0.2, "job_cpu_seconds": 0.25,
            "owned_processes": [{"pid": 77, "role": "C:/fixture-private-output/do-not-record.exe",
                "memory_observed": True, "private_mib": 4, "command_line": "fixture-private-output"}],
            "raw_output": "fixture-private-output"}
        empty = {"active_processes": 0, "peak_job_private_mib": 6, "peak_job_private_percent": 0.2}
        windows.accounting.side_effect = [active, active, empty]
        capture.communicate.side_effect = subprocess.TimeoutExpired("fixture", 0.25)
        with self.assertRaisesRegex(ValueError, "^STOP_LOW_AVAILABLE_RAM$") as caught:
            self.run_fixture(windows, process, capture)
        profile = caught.exception.audit_limits
        self.assertTrue(profile["worker_created"] and profile["job_assigned"] and profile["writer_authorized"])
        self.assertEqual(profile["job_last_active"]["active_processes"], 2)
        self.assertEqual(profile["job_last_active"]["job_cpu_seconds"], 0.25)
        self.assertEqual(profile["job_private_peak_mib"], 6)
        self.assertEqual(profile["job_last"]["active_processes"], 0)
        self.assertTrue(profile["owned_tree_empty"] and profile["cleanup_confirmed"])
        self.assertEqual(profile["system_last"]["commit_used_percent"], 97)
        self.assertNotIn("fixture-private-output", json.dumps(profile))
        windows.k.TerminateJobObject.assert_called_once()

    def test_pre_go_rechecks_resources_and_never_authorizes_on_emergency(self):
        for changes, code in (({"available_ram_percent": 7}, "STOP_LOW_AVAILABLE_RAM"),
                ({"commit_used_percent": 97}, "STOP_SYSTEM_COMMIT_PRESSURE"),
                ({"available_ram_percent": float("nan")}, "STOP_RESOURCE_OBSERVATION_INVALID")):
            with self.subTest(code=code):
                windows, process, capture = self.environment()
                stable = dict(windows.sample.return_value)
                windows.sample.side_effect = [stable, stable | changes]
                with self.assertRaisesRegex(ValueError, "^"+code+"$") as caught:
                    self.run_fixture(windows, process, capture)
                profile = caught.exception.audit_limits
                self.assertEqual(profile["operation_phase"], "pre_go")
                self.assertTrue(profile["worker_created"] and profile["job_assigned"])
                self.assertFalse(profile["writer_authorized"])
                self.assertTrue(profile["owned_tree_empty"] and profile["cleanup_confirmed"])
                capture.communicate.assert_not_called()
                windows.k.TerminateJobObject.assert_called_once()

    def test_fast_completion_checks_global_and_owned_budgets_before_success(self):
        scenarios = (({"available_ram_percent": 7}, {}, "STOP_LOW_AVAILABLE_RAM"),
            ({"commit_used_percent": 97}, {}, "STOP_SYSTEM_COMMIT_PRESSURE"),
            ({"system_cpu_percent": float("nan")}, {}, "STOP_RESOURCE_OBSERVATION_INVALID"),
            ({}, {"peak_job_private_percent": 7.1}, "STOP_OWNED_JOB_MEMORY_BUDGET"))
        for changes, job_changes, code in scenarios:
            with self.subTest(code=code):
                windows, process, capture = self.environment()
                stable = dict(windows.sample.return_value)
                windows.sample.side_effect = [stable, stable, stable | changes]
                windows.accounting.return_value.update(job_changes)
                with self.assertRaisesRegex(ValueError, "^"+code+"$") as caught:
                    self.run_fixture(windows, process, capture)
                profile = caught.exception.audit_limits
                self.assertTrue(profile["writer_authorized"])
                self.assertTrue(profile["owned_tree_empty"] and profile["cleanup_confirmed"])
                self.assertEqual(profile["system_sample_count"], 3)
                capture.communicate.assert_called_once()
                windows.k.TerminateJobObject.assert_called_once()
        windows, process, capture = self.environment()
        windows.sample.return_value["system_cpu_percent"] = 60
        result, _, _ = self.run_fixture(windows, process, capture)
        self.assertEqual(result.audit_limits["system_sample_count"], 3)
        self.assertEqual(result.stdout, "formatted\n")  # No CPU35 admission gate.
        windows, process, capture = self.environment()
        windows.sample.return_value["system_cpu_percent"] = 100
        capture.communicate.side_effect = [subprocess.TimeoutExpired("fixture", 0.25), ("formatted\n", "")]
        with self.assertRaisesRegex(ValueError, "^STOP_SUSTAINED_SYSTEM_CPU$") as caught:
            self.run_fixture(windows, process, capture)
        self.assertEqual(caught.exception.audit_limits["system_sample_count"], 4)
        self.assertTrue(caught.exception.audit_limits["owned_tree_empty"])

    def test_cleanup_failure_retains_profile_but_never_confirms_successful_cleanup(self):
        windows, process, capture = self.environment()
        windows.k.TerminateJobObject.return_value = False
        with self.assertRaisesRegex(ValueError, "^audit_tool_cleanup_not_confirmed$") as caught:
            self.run_fixture(windows, process, capture)
        profile = caught.exception.audit_limits
        self.assertFalse(profile["cleanup_confirmed"])
        self.assertTrue(profile["owned_tree_empty"])
        self.assertTrue(profile["job_accounting_observed"])
        self.assertEqual(profile["failure_code"], "audit_tool_cleanup_not_confirmed")

    def test_checkpoint_failure_profile_cannot_persist_raw_exception_text(self):
        with patch.object(subject, "Windows") as setup:
            with self.assertRaises(ValueError) as caught:
                subject.run_audit_tool("rustfmt-stdin", "x",
                    Mock(side_effect=ValueError("fixture-private-output-do-not-record")))
        setup.assert_not_called()
        self.assertEqual(caught.exception.audit_limits["failure_code"], "audit_tool_failure")
        self.assertNotIn("fixture-private-output", json.dumps(caught.exception.audit_limits))
        self.assertTrue(caught.exception.audit_limits["no_owned_worker_started"])

    def test_verifier_main_timing_includes_source_freezes_and_final_resource_sample(self):
        path = Path(subject.__file__).with_name("verify_bounded_audit_tools_light.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        start = main.body[0]
        self.assertIsInstance(start, ast.Assign)
        self.assertEqual(start.targets[0].id, "main_started")
        assigned = [(index, node.targets[0].slice.value) for index, node in enumerate(main.body)
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].slice, ast.Constant)]
        order = dict((key, index) for index, key in assigned)
        self.assertLess(order["self_resource_after"], order["elapsed_seconds"])
        self.assertIn("excludes_python_startup_and_receipt_write", path.read_text(encoding="utf-8"))
        self.assertIn('getattr(error, "audit_limits", None)', path.read_text(encoding="utf-8"))
        self.assertIn('r"audit_tool_[a-z_]+|STOP_[A-Z_]+"', path.read_text(encoding="utf-8"))
        self.assertNotIn('r"[A-Za-z_]+"', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
