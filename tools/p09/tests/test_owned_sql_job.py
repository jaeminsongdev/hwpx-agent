"""Closed Job launcher mock boundaries and small real Python process-tree smokes."""
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import conservative_maintenance as c
import owned_sql_job as subject
from bounded_process_progress import BoundedProcessCapture, bounded_observation_run


class OwnedSQLJobMockTests(unittest.TestCase):
    def fixture(self):
        process = SimpleNamespace(_handle=1, pid=123, returncode=None,
            stdin=io.StringIO(), stdout=io.BytesIO(), stderr=io.BytesIO())
        process.poll = Mock(side_effect=lambda: process.returncode)
        process.kill = Mock(side_effect=lambda: setattr(process, "returncode", 1))
        process.wait = Mock(side_effect=lambda timeout: process.returncode)
        def membership(handle, job, pointer):
            pointer._obj.value = 1
            return True
        kernel = SimpleNamespace(AssignProcessToJobObject=Mock(return_value=True),
            IsProcessInJob=Mock(side_effect=membership), TerminateJobObject=Mock(return_value=True),
            CloseHandle=Mock(return_value=True))
        windows = SimpleNamespace(k=kernel, job=Mock(return_value=7),
            verify_job_limits=Mock(return_value={"verified": True}))
        windows.accounting = Mock(side_effect=lambda job: {"active_processes":
            0 if kernel.TerminateJobObject.called else 1, "peak_job_private_percent": 1})
        return windows, process

    def launch(self, windows, checkpoint, **kwargs):
        return subject.OwnedSQLJobProcess([sys.executable, "-c", "pass"], windows=windows,
            allowed_executables=[sys.executable], cwd=c.ROOT, checkpoint=checkpoint, **kwargs)

    def test_readback_assignment_membership_checkpoints_precede_GO_and_env_is_exact(self):
        windows, process = self.fixture()
        events = []
        windows.verify_job_limits.side_effect = lambda job: events.append("readback") or {"verified": True}
        windows.k.AssignProcessToJobObject.side_effect = lambda job, handle: events.append("assign") or True
        checkpoint = Mock(side_effect=lambda: events.append("checkpoint"))
        env = {"P149_TEST_ONLY": "fixed-not-secret"}
        with patch.object(subject.subprocess, "Popen", return_value=process) as popen:
            owned = self.launch(windows, checkpoint, env=env)
        self.assertEqual(events, ["checkpoint", "readback", "assign", "checkpoint", "checkpoint"])
        self.assertEqual(process.stdin.getvalue(), subject.TOKEN+"\n")
        self.assertIs(popen.call_args.kwargs["env"], env)
        self.assertTrue(owned.profile["job_assigned"] and owned.profile["target_authorized"])
        owned.close()
        self.assertTrue(owned.profile["cleanup_confirmed"])
        self.assertTrue(owned.profile["owned_tree_empty"])
        owned.close()
        windows.k.CloseHandle.assert_called_once_with(7)

    def test_initial_checkpoint_and_readback_failure_never_start_worker(self):
        for phase in ("checkpoint", "readback"):
            windows, process = self.fixture()
            checkpoint = Mock()
            if phase == "checkpoint":
                checkpoint.side_effect = ValueError("fixture-stop")
            else:
                windows.verify_job_limits.side_effect = ValueError("fixture-readback")
            with patch.object(subject.subprocess, "Popen", return_value=process) as popen:
                with self.assertRaises(ValueError) as caught:
                    self.launch(windows, checkpoint)
            popen.assert_not_called()
            profile = caught.exception.owned_sql_job_profile
            self.assertFalse(profile["worker_created"] or profile["target_authorized"])
            self.assertTrue(profile["cleanup_confirmed"])

    def test_assignment_membership_and_post_assignment_checkpoint_failure_never_GO(self):
        for phase in ("assign", "membership", "checkpoint", "interrupt"):
            windows, process = self.fixture()
            checkpoint = Mock()
            if phase == "assign":
                windows.k.AssignProcessToJobObject.return_value = False
            elif phase == "membership":
                windows.k.IsProcessInJob.side_effect = None
                windows.k.IsProcessInJob.return_value = False
            elif phase == "interrupt":
                checkpoint.side_effect = [None, KeyboardInterrupt()]
            else:
                checkpoint.side_effect = [None, ValueError("fixture-stop")]
            sent = []
            process.stdin.write = Mock(side_effect=lambda text: sent.append(text) or len(text))
            with patch.object(subject.subprocess, "Popen", return_value=process):
                with self.assertRaises((ValueError, KeyboardInterrupt)) as caught:
                    self.launch(windows, checkpoint)
            self.assertEqual(sent, [])
            self.assertFalse(caught.exception.owned_sql_job_profile["target_authorized"])
            self.assertTrue(caught.exception.owned_sql_job_profile["cleanup_confirmed"])

    def test_owned_memory_observation_invalid_and_stop_do_not_authorize(self):
        for value in (7, True, float("nan"), float("inf"), -1, "7"):
            windows, process = self.fixture()
            def accounting(job):
                return {"active_processes": 0 if windows.k.TerminateJobObject.called else 1,
                    "peak_job_private_percent": value}
            windows.accounting.side_effect = accounting
            sent = []
            process.stdin.write = Mock(side_effect=lambda text: sent.append(text) or len(text))
            with patch.object(subject.subprocess, "Popen", return_value=process), self.assertRaises(ValueError):
                self.launch(windows, Mock())
            self.assertEqual(sent, [])

    def test_cleanup_failure_cannot_report_success_or_pass_on_second_close(self):
        for failure in ("terminate", "close", "wait", "accounting"):
            windows, process = self.fixture()
            with patch.object(subject.subprocess, "Popen", return_value=process):
                owned = self.launch(windows, Mock())
            if failure == "terminate":
                windows.k.TerminateJobObject.return_value = False
            elif failure == "close":
                windows.k.CloseHandle.return_value = False
            elif failure == "wait":
                process.wait.side_effect = subprocess.TimeoutExpired("fixture", 2)
            else:
                windows.accounting.side_effect = ValueError("fixture")
            with self.assertRaises(ValueError):
                owned.close()
            self.assertFalse(owned.profile["cleanup_confirmed"])
            with self.assertRaisesRegex(ValueError, "^OWNED_SQL_PREVIOUS_CLEANUP_FAILED$"):
                owned.close()

    def test_argument_scope_budget_and_executable_allowlist_reject_before_job(self):
        windows, _ = self.fixture()
        for args in ([], [123], [sys.executable, "bad\0arg"], [sys.executable, "x"*13000],
                ["not-allowlisted.exe"], [sys.executable, "\ud800"]):
            with self.assertRaises(ValueError):
                subject.OwnedSQLJobProcess(args, windows=windows, allowed_executables=[sys.executable],
                    cwd=c.ROOT, checkpoint=Mock())
        windows.job.assert_not_called()


class OwnedSQLJobActualTests(unittest.TestCase):
    def launch(self, code):
        windows = c.Windows()
        def checkpoint():
            row = windows.sample()
            _, reason = c.decision(row, 0)
            c.require(reason is None and row["system_cpu_percent"] < c.POLICY["emergency_cpu_percent"],
                reason or "DEFERRED_ALREADY_SATURATED_SYSTEM")
            c.require(row["available_ram_percent"] >= c.POLICY["start_ram_min_percent"],
                "STOP_LOW_AVAILABLE_RAM")
        # Three checkpoint calls can be close enough to have no GetSystemTimes delta.
        def paced_checkpoint():
            time.sleep(.05)
            checkpoint()
        owned = subject.OwnedSQLJobProcess([sys.executable, "-c", code], windows=windows,
            allowed_executables=[sys.executable], cwd=c.ROOT, checkpoint=paced_checkpoint,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        capture_holder = []
        def cleanup():
            try:
                owned.kill()
                owned.wait(timeout=2)
                for capture in capture_holder:
                    capture.close()
            finally:
                owned.close()
                self.owned_job_profiles = getattr(self, "owned_job_profiles", [])+[dict(owned.profile)]
        self.addCleanup(cleanup)
        return owned, capture_holder

    def test_actual_complete_unicode_stdin_and_exit_are_preserved(self):
        text = "가나다\n"*12000
        owned, holder = self.launch("import sys,hashlib;data=sys.stdin.read();print(hashlib.sha256(data.encode('utf-8')).hexdigest())")
        capture = BoundedProcessCapture(owned, input_text=text, parse_markers=False)
        holder.append(capture)
        output, errors = capture.communicate(timeout=5)
        self.assertEqual(output.strip(), hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertEqual(errors, "")
        self.assertEqual(owned.returncode, 0)
        self.assertTrue(owned.profile["limits_readback"]["verified"])

    def test_actual_timeout_kills_worker_target_and_grandchild(self):
        code = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);print('READY',flush=True);time.sleep(30)"
        owned, holder = self.launch(code)
        capture = BoundedProcessCapture(owned, parse_markers=False)
        holder.append(capture)
        deadline = time.monotonic()+4
        info = owned.observe()
        while info["active_processes"] < 3 and time.monotonic() < deadline:
            time.sleep(.05)
            info = owned.observe()
        self.assertGreaterEqual(info["active_processes"], 3)
        self.assertLess(info["peak_job_private_percent"], 7)
        with self.assertRaises(subprocess.TimeoutExpired):
            owned.wait(timeout=.05)


class OwnedSQLFactoryActualTests(unittest.TestCase):
    def test_primary_and_observer_kernel_budget_and_cleanup(self):
        windows = c.Windows()
        def checkpoint():
            time.sleep(.05)
            row = windows.sample()
            _, reason = c.decision(row, 0)
            c.require(reason is None and row["system_cpu_percent"] < c.POLICY["emergency_cpu_percent"]
                and row["available_ram_percent"] >= c.POLICY["start_ram_min_percent"],
                reason or "DEFERRED_RESOURCE_PRESSURE")
        factory = subject.OwnedSQLJobFactory(windows=windows, allowed_executables=[sys.executable],
            checkpoint=checkpoint, record=lambda profiles: setattr(self, "owned_job_profiles", profiles))
        holder = []
        def cleanup():
            try:
                if factory.processes:
                    primary = factory.processes[0]
                    if not primary.closed:
                        primary.kill()
                        primary.wait(timeout=2)
                for capture in holder:
                    capture.close()
            finally:
                factory.close()
        self.addCleanup(cleanup)
        flags = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS
        primary = factory([sys.executable, "-c", "import time;print('READY',flush=True);time.sleep(10)"],
            cwd=c.ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", creationflags=flags)
        capture = BoundedProcessCapture(primary, parse_markers=False)
        holder.append(capture)
        result = bounded_observation_run([sys.executable, "-c", "print('[]')"], cwd=c.ROOT,
            creationflags=flags, process_factory=factory)
        self.assertEqual((result.returncode, result.stdout), (0, "[]\n"))
        self.assertEqual(len(factory.processes), 2)
        observer = factory.processes[1]
        self.assertTrue(observer.closed)
        limits = [child.profile["limits_readback"] for child in factory.processes]
        self.assertTrue(all(row["verified"] and row["affinity_mask"] == 1 for row in limits))
        self.assertLessEqual(sum(row["job_private_limit_mib"] for row in limits), windows.memory_limit/1048576)
        self.assertLessEqual(limits[0]["job_private_limit_mib"], windows.total_ram*0.07/1048576)
        self.assertLessEqual(limits[1]["job_private_limit_mib"], windows.total_ram*0.01/1048576)
        self.assertIsNone(primary.poll())


if __name__ == "__main__":
    unittest.main()
