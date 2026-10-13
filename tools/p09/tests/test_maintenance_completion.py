"""Mock Cargo-supervisor barriers; no actual Cargo/worker or filesystem receipts."""
import contextlib
import ctypes
import io
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as subject
import bounded_process_progress


class Receipt:
    def open(self, mode, encoding):
        if mode != "x" or encoding != "utf-8":
            raise ValueError("fixture_receipt_scope")
        owner = self
        class Sink(io.StringIO):
            def close(self):
                owner.saved = json.loads(self.getvalue())
                super().close()
        return Sink()


class MaintenanceCompletionTests(unittest.TestCase):
    def environment(self):
        kernel = SimpleNamespace(**{name: Mock(return_value=True) for name in
            ("AssignProcessToJobObject", "TerminateJobObject", "CloseHandle", "ReleaseMutex")})
        kernel.CreateMutexW = Mock(return_value=101)
        kernel.OpenProcess = Mock(return_value=103)
        windows = SimpleNamespace(k=kernel, total_ram=32*1024**3, memory_limit=1024**2,
            processors=16, cpu_rate=625, job=Mock(return_value=102),
            verify_job_limits=Mock(return_value={"verified": True}),
            sample=Mock(return_value={"system_cpu_percent": 60, "available_ram_percent": 40,
                "commit_used_percent": 30}),
            accounting=Mock(return_value={"active_processes": 0, "job_cpu_seconds": .1,
                "peak_job_private_percent": .1, "peak_job_private_mib": 1}))
        process = SimpleNamespace(pid=104, stdin=io.BytesIO(), stdout=io.BytesIO(), stderr=io.BytesIO(),
            returncode=0, poll=Mock(return_value=0), wait=Mock(return_value=0), kill=Mock())
        process.stdin.write = Mock(wraps=process.stdin.write)
        capture = SimpleNamespace(communicate=Mock(return_value=("", "")), progress=Mock(), close=Mock(),
            lock=threading.Lock(), buffers={"stderr": bytearray(
                b"   Compiling domain-ir v0.1.0 (D:/private-fixture-never-saved)\n")})
        return windows, process, capture

    def run_fixture(self, windows, process, capture, pins=None):
        receipt = Receipt()
        with patch.object(subject, "Windows", return_value=windows), \
                patch.object(subject.ctypes, "get_last_error", return_value=0), \
                patch.object(subject.time, "sleep"), \
                patch.object(subject, "pins", pins or Mock(return_value=[])), \
                patch.object(subject.subprocess, "Popen", return_value=process) as launch, \
                patch.object(bounded_process_progress, "BoundedProcessCapture", return_value=capture) as bounded, \
                contextlib.redirect_stdout(io.StringIO()):
            code = subject.run("domain-check", receipt, 30)
        return code, receipt.saved, launch, bounded

    def test_success_reads_limits_before_assignment_and_go_and_observes_final_resources(self):
        windows, process, capture = self.environment()
        order = []
        windows.verify_job_limits.side_effect = lambda handle: order.append("readback") or {"verified": True}
        windows.k.AssignProcessToJobObject.side_effect = lambda *args: order.append("assign") or True
        original_write = process.stdin.write
        process.stdin.write = Mock(side_effect=lambda data: order.append("go") or original_write(data))
        code, row, launch, _ = self.run_fixture(windows, process, capture)
        self.assertEqual((code, row["state"]), (0, "PASS_SCOPED_NOT_GATE"))
        self.assertEqual(order, ["readback", "assign", "go"])
        process.stdin.write.assert_called_once_with(b"P149_GO\n")
        self.assertTrue(row["worker_created"] and row["job_assigned"] and row["writer_authorized"])
        self.assertTrue(row["cleanup_confirmed"] and row["owned_tree_empty"])
        self.assertTrue(row["owned_limits_readback"]["verified"])
        self.assertGreaterEqual(windows.sample.call_count, 5)
        self.assertEqual(launch.call_count, 1)
        capture.communicate.assert_called_once()

    def test_pre_go_resource_emergency_never_sends_authorization(self):
        for changes, reason in (({"available_ram_percent": 7}, "STOP_LOW_AVAILABLE_RAM"),
                ({"commit_used_percent": 97}, "STOP_SYSTEM_COMMIT_PRESSURE")):
            with self.subTest(reason=reason):
                windows, process, capture = self.environment()
                stable = dict(windows.sample.return_value)
                windows.sample.side_effect = [stable, stable, stable | changes]
                code, row, launch, bounded = self.run_fixture(windows, process, capture)
                self.assertEqual(code, 2)
                self.assertEqual(row["stop_reason"], reason)
                self.assertFalse(row["heavy_work_started"] or row["writer_authorized"])
                self.assertTrue(row["cleanup_confirmed"] and row["owned_tree_empty"])
                self.assertEqual(launch.call_count, 1)
                bounded.assert_not_called()
                process.stdin.write.assert_not_called()

    def test_fast_completion_rejects_final_global_or_owned_memory_emergency(self):
        for changes, owned, reason in (({"available_ram_percent": 7}, False, "STOP_LOW_AVAILABLE_RAM"),
                ({"commit_used_percent": 97}, False, "STOP_SYSTEM_COMMIT_PRESSURE"),
                ({}, True, "STOP_OWNED_JOB_MEMORY_BUDGET")):
            with self.subTest(reason=reason):
                windows, process, capture = self.environment()
                stable = dict(windows.sample.return_value)
                windows.sample.side_effect = [stable, stable, stable, stable | changes]
                if owned:
                    info = dict(windows.accounting.return_value)
                    windows.accounting.side_effect = [info, info | {"peak_job_private_percent": 7.1}, info]
                code, row, _, _ = self.run_fixture(windows, process, capture)
                self.assertEqual((code, row["stop_reason"]), (2, reason))
                self.assertTrue(row["heavy_work_started"] and row["cleanup_confirmed"] and row["owned_tree_empty"])
                capture.communicate.assert_called_once()
                self.assertEqual(row["last_cargo_announcement"]["announcement"],
                    {"stage": "compiling", "package": "domain-ir"})
                self.assertEqual(row["samples"][-1]["cargo_announcement"], row["last_cargo_announcement"])
                self.assertFalse(row["last_cargo_announcement"]["process_or_compiler_phase_attribution_verified"])
                self.assertEqual(row["cargo_announcement_at_cleanup"], row["last_cargo_announcement"])
                self.assertNotIn("private-fixture", json.dumps(row))

    def test_source_change_is_rejected_after_successful_exit(self):
        windows, process, capture = self.environment()
        changed = Mock(side_effect=[[{"path": "fixture.rs", "bytes": 1, "sha256": "a"*64}],
            [{"path": "fixture.rs", "bytes": 1, "sha256": "b"*64}]])
        code, row, _, _ = self.run_fixture(windows, process, capture, changed)
        self.assertEqual((code, row["stop_reason"]), (2, "SOURCE_DRIFT_AFTER_RUN"))
        self.assertTrue(row["cleanup_confirmed"] and row["owned_tree_empty"])

        windows, process, capture = self.environment()
        process.returncode = 101
        capture.communicate.return_value = ("", "error[E0308]: private-fixture-not-for-receipt\n"
            "  --> crates/domain-ir/src/document_graph.rs:12:3\n")
        code, row, _, _ = self.run_fixture(windows, process, capture)
        self.assertEqual((code, row["stop_reason"]), (2, "OWNED_COMMAND_FAILED"))
        self.assertEqual(row["compiler_error_codes"], ["E0308"])
        self.assertEqual(row["compiler_diagnostic_locations"],
            [{"path": "crates/domain-ir/src/document_graph.rs", "line": 12, "column": 3}])
        self.assertNotIn("private-fixture", json.dumps(row))

    def test_cleanup_failure_cannot_return_pass_even_with_empty_tree(self):
        for operation in ("TerminateJobObject", "CloseHandle", "ReleaseMutex"):
            with self.subTest(operation=operation):
                windows, process, capture = self.environment()
                if operation == "CloseHandle":
                    windows.k.CloseHandle.side_effect = lambda handle: handle != 102
                else:
                    getattr(windows.k, operation).return_value = False
                code, row, _, _ = self.run_fixture(windows, process, capture)
                self.assertEqual((code, row["state"], row["stop_reason"]),
                    (2, "STOPPED_NOT_ACCEPTED", "OWNED_CLEANUP_NOT_CONFIRMED"))
                self.assertFalse(row["cleanup_confirmed"])
                self.assertTrue(row["owned_tree_empty"])

    def test_kernel_readback_mismatch_blocks_worker_and_checks_all_required_limits(self):
        windows, process, capture = self.environment()
        windows.verify_job_limits.side_effect = ValueError("OWNED_LIMIT_READBACK_MISMATCH")
        code, row, launch, _ = self.run_fixture(windows, process, capture)
        self.assertEqual((code, row["stop_reason"]), (2, "OWNED_LIMIT_READBACK_MISMATCH"))
        launch.assert_not_called()
        process.stdin.write.assert_not_called()
        for mismatch in ("memory", "affinity", "priority", "active", "kill", "breakaway", "rate", "rate_flags"):
            raw_windows = subject.Windows.__new__(subject.Windows)
            raw_windows.memory_limit, raw_windows.mask, raw_windows.cpu_rate = 1024**2, 1, 625
            def query(job, kind, pointer, size, returned):
                value = pointer._obj
                if kind == 9:
                    value.job_memory = raw_windows.memory_limit
                    value.basic.affinity, value.basic.priority, value.basic.active_limit = 1, 0x4000, 16
                    value.basic.flags = 0x2238
                    if mismatch == "memory": value.job_memory += 4096
                    if mismatch == "affinity": value.basic.affinity = 2
                    if mismatch == "priority": value.basic.priority = 0x20
                    if mismatch == "active": value.basic.active_limit = 17
                    if mismatch == "kill": value.basic.flags &= ~0x2000
                    if mismatch == "breakaway": value.basic.flags |= 0x800
                else:
                    value.rate, value.flags = 625, 5
                    if mismatch == "rate": value.rate = 626
                    if mismatch == "rate_flags": value.flags = 1
                return True
            raw_windows.k = SimpleNamespace(QueryInformationJobObject=query)
            with self.subTest(mismatch=mismatch), self.assertRaisesRegex(ValueError, "^OWNED_LIMIT_READBACK_MISMATCH$"):
                raw_windows.verify_job_limits(102)

    def test_admission_refuses_low_ram_before_creating_job(self):
        windows, process, capture = self.environment()
        windows.sample.return_value["available_ram_percent"] = 7
        code, row, launch, _ = self.run_fixture(windows, process, capture)
        self.assertEqual((code, row["state"]), (2, "DEFERRED_NOT_STARTED"))
        self.assertFalse(row["worker_created"] or row["heavy_work_started"])
        launch.assert_not_called()
        windows.job.assert_not_called()

    def test_worker_keeps_exact_check_scope_profiles_and_disables_auto_install(self):
        windows, _, _ = self.environment()
        windows.k.GetCurrentProcess = Mock(return_value=1)
        def member(current, job, pointer):
            pointer._obj.value = True
            return True
        windows.k.IsProcessInJob = member
        with patch.object(subject, "Windows", return_value=windows), \
                patch.object(subject.sys, "stdin", io.StringIO("P149_GO\n")), \
                patch.object(subject.shutil, "which", return_value="C:/fixture/cargo.exe"), \
                patch.object(subject.subprocess, "call", return_value=0) as cargo:
            self.assertEqual(subject.worker("domain-check"), 0)
        args = cargo.call_args.args[0]
        self.assertEqual(args[1:7], ["check", "-p", "domain-ir", "--lib", "--test", "document_graph"])
        self.assertIn("--locked", args)
        self.assertIn("--offline", args)
        self.assertIn("--color=never", args)
        self.assertNotIn("--workspace", args)
        env = cargo.call_args.kwargs["env"]
        self.assertEqual(env["RUSTUP_AUTO_INSTALL"], "0")
        self.assertEqual(env["CARGO_BUILD_JOBS"], "1")
        self.assertEqual(env["CARGO_PROFILE_DEV_DEBUG_ASSERTIONS"], "true")
        self.assertEqual(env["CARGO_PROFILE_DEV_OVERFLOW_CHECKS"], "true")
        self.assertEqual(env["CARGO_PROFILE_TEST_OPT_LEVEL"], "0")
        self.assertEqual(env["CARGO_PROFILE_TEST_DEBUG"], "line-tables-only")
        self.assertEqual(env["CARGO_PROFILE_TEST_DEBUG_ASSERTIONS"], "true")
        self.assertEqual(env["CARGO_PROFILE_TEST_OVERFLOW_CHECKS"], "true")
        self.assertEqual(env["CARGO_PROFILE_TEST_CODEGEN_UNITS"], "16")
        self.assertEqual(env["RUST_TEST_THREADS"], "1")

    def test_cargo_announcements_are_closed_complete_snapshots_not_compiler_proof(self):
        capture = SimpleNamespace(lock=threading.Lock(), buffers={"stderr": bytearray()})
        snapshot = lambda: subject.cargo_announcement_snapshot(capture)
        for chunk in (b" Comp", b"iling domain-ir v0.1.0 (D:/private-path)", b"\r"):
            capture.buffers["stderr"].extend(chunk)
            self.assertIsNone(snapshot()["announcement"])
        capture.buffers["stderr"].extend(b"\n")
        original = snapshot()
        self.assertEqual(original["announcement"], {"stage": "compiling", "package": "domain-ir"})
        capture.buffers["stderr"].extend(b" Checking private-package v1.2.3 (/private-token)\n")
        current = snapshot()
        self.assertEqual(current["announcement"], {"stage": "checking", "package": None})
        self.assertFalse(current["process_or_compiler_phase_attribution_verified"])
        self.assertNotIn("private", json.dumps(current))
        self.assertEqual(original["announcement"], {"stage": "compiling", "package": "domain-ir"})
        capture.buffers["stderr"].extend(b" Finished private-profile [private-flags] in 1s\n")
        self.assertEqual(snapshot()["announcement"], {"stage": "build_finished", "package": None})
        for bad in (b"private-token\n", b" Compiling domain-ir v1.0 extra-secret\n",
                b"\x1b[31m Compiling domain-ir v1.0\n", b" Compiling domain-ir v1.0\x00\n"):
            capture.buffers["stderr"] = bytearray(bad)
            self.assertIsNone(snapshot()["announcement"])
        capture.buffers["stderr"] = bytearray(b"x" * (subject.POLICY["output_limit_bytes_per_stream"]+1))
        with self.assertRaisesRegex(ValueError, "^CARGO_DIAGNOSTIC_BUFFER_LIMIT$"):
            snapshot()


if __name__ == "__main__":
    unittest.main()
