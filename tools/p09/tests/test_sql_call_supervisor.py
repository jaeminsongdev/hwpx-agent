"""Deterministic bounded lifecycle fixtures, no real child/SQL/Windows changes."""
import json
import subprocess
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import sql_call_supervisor as subject


class SQLCallSupervisorTests(unittest.TestCase):
    def fixture(self, *, stop=None, actions=None, grace=.5, maximum=3, pressure=None,
            signal_error=None, observation_error=None, close_error=None, capture_error=None,
            stdout='{"fixture":true}', stderr="", exit_code=0, residual=0, accounting_error=None, decoder=json.loads,
            settling=False):
        clock = SimpleNamespace(now=1.0)
        trace = []
        row = {"system_cpu_percent": 10, "available_ram_percent": 40, "commit_used_percent": 30}
        if pressure:
            row.update(pressure)
        resources = SimpleNamespace(windows=object(), checkpoint_io=Mock(side_effect=ValueError(stop) if stop else None),
            sample=Mock(return_value=row), samples=[row], last_sample_at=1.0, lock=threading.Lock(), hot=0,
            thread=SimpleNamespace(is_alive=Mock(return_value=False)))
        event = SimpleNamespace(owner=True, closed=False, request=Mock(side_effect=signal_error))
        pending = list(["success"] if actions is None else actions)
        class Owned:
            def __init__(self, *args, **kwargs):
                self.checkpoint, self.returncode = kwargs["checkpoint"], None
                self.job = "exact-owned-fixture-job"
                observed = []
                def accounting(job):
                    if job != self.job:
                        raise AssertionError("OTHER_JOB_FORBIDDEN")
                    if accounting_error:
                        raise accounting_error
                    observed.append(True)
                    active = 1 if settling and len(observed) < 3 else residual
                    return {"active_processes": active if self.returncode is not None else 2}
                self.windows = SimpleNamespace(accounting=accounting)
                self.profile = {"owned_tree_empty": False, "cleanup_confirmed": False, "job_handle_closed": False}
                trace.append("created")
            def observe(self):
                self.checkpoint()
                if observation_error:
                    raise observation_error
                trace.append("observed")
            def poll(self):
                return self.returncode
            def wait(self, timeout):
                return self.returncode
            def kill(self):
                trace.append("forced")
                self.returncode = 125
            def close(self):
                trace.append("closed")
                self.profile.update(owned_tree_empty=True, cleanup_confirmed=True, job_handle_closed=True)
                if close_error:
                    self.profile["cleanup_confirmed"] = False
                    raise close_error
        class Capture:
            def __init__(self, owned, **kwargs):
                if capture_error:
                    raise capture_error
                self.owned = owned
            def communicate(self, timeout):
                clock.now += .3
                action = pending.pop(0) if pending else "timeout"
                if action == "timeout":
                    raise subprocess.TimeoutExpired("fixture", timeout)
                if isinstance(action, Exception):
                    raise action
                self.owned.returncode = exit_code
                return stdout, stderr
            def progress(self):
                return [], []
            def close(self):
                trace.append("pipes-closed")
        def sleep(seconds):
            clock.now += seconds
        result = subject.supervise_owned_call(["fixture"], resources, event, decoder,
            maximum_seconds=maximum, grace_seconds=grace, clock=lambda: clock.now,
            sleep=sleep, process_factory=Owned, capture_factory=Capture)
        return result, resources, event, trace

    def test_normal_terminal_is_accounted_without_cancellation_or_forced_kill(self):
        row, _, event, trace = self.fixture()
        self.assertEqual(row["state"], "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE")
        self.assertTrue(row["worker_terminal_before_forced_termination"])
        self.assertFalse(row["forced_termination"])
        self.assertTrue(row["pipe_cleanup_confirmed"])
        event.request.assert_not_called()
        self.assertNotIn("forced", trace)
        self.assertIsNone(row["backend_container_cleanup_confirmed"])
        self.assertFalse(row["full_SQL_wrapper_cancellation_and_container_cleanup_qualified"])
        self.assertTrue(row["pre_teardown_tree_observed"])
        self.assertEqual(row["pre_teardown_job_accounting"]["active_processes"], 0)

    def test_stop_sends_one_signal_and_allows_terminal_cleanup_before_kill(self):
        row, resources, event, trace = self.fixture(stop="STOP_FIXTURE")
        self.assertEqual(row["state"], "CANCELLED_OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE")
        self.assertEqual(row["cancel_reason"], "STOP_FIXTURE")
        event.request.assert_called_once()
        resources.checkpoint_io.assert_called_once()
        resources.sample.assert_called_once()
        self.assertNotIn("forced", trace)

    def test_cleanup_grace_expiry_force_kills_only_owned_tree_and_keeps_failure(self):
        row, _, event, trace = self.fixture(stop="STOP_FIXTURE", actions=["timeout"]*5)
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertEqual(row["grace_abort_reason"], "STOP_SQL_CALL_GRACE_TIME")
        self.assertTrue(row["forced_termination"])
        self.assertFalse(row["worker_terminal_before_forced_termination"])
        self.assertIn("forced", trace)
        event.request.assert_called_once()
        self.assertIsNone(row["backend_container_cleanup_confirmed"])

    def test_total_wall_time_transitions_to_cancel_then_graceful_terminal(self):
        row, _, event, _ = self.fixture(maximum=.25, actions=["timeout", "success"])
        self.assertEqual(row["cancel_reason"], "STOP_SQL_CALL_WALL_TIME")
        self.assertEqual(row["state"], "CANCELLED_OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE")
        event.request.assert_called_once()

    def test_low_RAM_or_high_commit_does_not_get_unchecked_cleanup_grace(self):
        for pressure in ({"available_ram_percent": 7.9}, {"commit_used_percent": 95}):
            row, _, event, _ = self.fixture(stop="STOP_FIXTURE", pressure=pressure)
            self.assertEqual(row["grace_abort_reason"], "STOP_SQL_CALL_GRACE_RESOURCE_PRESSURE")
            self.assertTrue(row["forced_termination"])
            event.request.assert_called_once()

    def test_live_job_memory_budget_cannot_be_relaxed_by_grace(self):
        row, _, event, _ = self.fixture(observation_error=ValueError("STOP_OWNED_JOB_MEMORY_BUDGET"), actions=["timeout"])
        self.assertEqual(row["grace_abort_reason"], "STOP_OWNED_JOB_MEMORY_BUDGET")
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertTrue(row["forced_termination"])
        event.request.assert_called_once()

    def test_signal_failure_cannot_claim_cooperative_termination(self):
        row, _, _, _ = self.fixture(stop="STOP_FIXTURE", signal_error=OSError("PRIVATE_FIXTURE"))
        self.assertFalse(row["signal_sent"])
        self.assertTrue(row["forced_termination"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_observation_failure_during_grace_is_not_ignored(self):
        row, _, _, _ = self.fixture(stop="STOP_FIXTURE", pressure={"available_ram_percent": float("nan")})
        self.assertEqual(row["grace_abort_reason"], "STOP_SQL_CALL_GRACE_OBSERVATION_INVALID")
        self.assertTrue(row["forced_termination"])

    def test_capture_initialization_failure_signals_before_owned_force_kill(self):
        row, _, event, trace = self.fixture(capture_error=ValueError("owned_pipe_scope_invalid"))
        event.request.assert_called_once()
        self.assertTrue(row["forced_termination"])
        self.assertFalse(row["pipe_cleanup_confirmed"])
        self.assertIn("closed", trace)

    def test_nonzero_worker_stderr_or_bad_protocol_cannot_be_accounted_success(self):
        for kwargs in ({"exit_code": 2}, {"stderr": "PRIVATE_FIXTURE"}, {"stdout": "PRIVATE_FIXTURE"}, {"stdout": "[]"}):
            row, _, _, _ = self.fixture(**kwargs)
            self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
            self.assertIsNone(row["worker_result"])
            self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_owned_cleanup_failure_overrides_terminal_success(self):
        row, _, _, _ = self.fixture(close_error=ValueError("OWNED_SQL_CLEANUP_FAILED"))
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertFalse(row["owned_job_profile"]["cleanup_confirmed"])

    def test_time_bounds_or_nonowner_event_cannot_launch_worker(self):
        factory = Mock()
        event = SimpleNamespace(owner=True, closed=False)
        for kwargs in ({"maximum_seconds": True}, {"maximum_seconds": 691}, {"grace_seconds": 136},
                {"grace_seconds": float("nan")}, {"grace_seconds": 0}):
            with self.assertRaises(ValueError):
                subject.supervise_owned_call([], object(), event, json.loads, process_factory=factory, **kwargs)
        with self.assertRaisesRegex(ValueError, "SQL_CALL_OWNER_OR_DECODER_SCOPE"):
            subject.supervise_owned_call([], object(), SimpleNamespace(owner=False, closed=False), json.loads,
                process_factory=factory)
        factory.assert_not_called()

    def test_nonfinite_or_regressing_clock_fails_closed(self):
        for now, previous in ((float("nan"), 1), (float("inf"), 1), (0, 1), (True, 0)):
            with self.assertRaisesRegex(ValueError, "SQL_CALL_CLOCK_INVALID"):
                subject.valid_clock(lambda: now, previous)

    def test_stale_alive_watcher_cannot_authorize_grace(self):
        resources = SimpleNamespace(thread=SimpleNamespace(is_alive=lambda: True), lock=threading.Lock(),
            samples=[{}], last_sample_at=1, sample=Mock())
        with self.assertRaisesRegex(ValueError, "STOP_SQL_CALL_GRACE_OBSERVATION_STALE"):
            subject.grace_resource_checkpoint(resources, 3.001)
        resources.sample.assert_not_called()

    def test_alive_watcher_reuses_fresh_sample_without_second_sampler(self):
        resources = SimpleNamespace(thread=SimpleNamespace(is_alive=lambda: True), lock=threading.Lock(),
            samples=[{"system_cpu_percent": 20, "available_ram_percent": 40, "commit_used_percent": 30}],
            last_sample_at=1, sample=Mock(), hot=0)
        subject.grace_resource_checkpoint(resources, 2)
        resources.sample.assert_not_called()

    def test_sustained_CPU_pressure_or_bad_sample_aborts_grace(self):
        resources = SimpleNamespace(thread=SimpleNamespace(is_alive=lambda: False), hot=4,
            sample=Mock(return_value={"system_cpu_percent": 98, "available_ram_percent": 40, "commit_used_percent": 30}))
        with self.assertRaisesRegex(ValueError, "STOP_SQL_CALL_GRACE_RESOURCE_PRESSURE"):
            subject.grace_resource_checkpoint(resources, 1)
        resources.sample.return_value = {"system_cpu_percent": 20, "available_ram_percent": 101, "commit_used_percent": 30}
        with self.assertRaisesRegex(ValueError, "STOP_SQL_CALL_GRACE_OBSERVATION_INVALID"):
            subject.grace_resource_checkpoint(resources, 1)

    def test_terminal_main_with_residual_children_is_forced_not_graceful_success(self):
        row, _, _, trace = self.fixture(residual=1)
        self.assertTrue(row["worker_terminal_before_forced_termination"])
        self.assertEqual(row["pre_teardown_job_accounting"]["active_processes"], 1)
        self.assertTrue(row["forced_termination"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertIn("forced", trace)
        self.assertLessEqual(row["terminal_tree_settle"]["polls_after_first"], 100)

    def test_terminal_job_counter_can_settle_to_zero_without_forcing_owned_children(self):
        row, _, _, trace = self.fixture(settling=True)
        self.assertEqual(row["state"], "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE")
        self.assertEqual(row["terminal_tree_settle"]["first_active_processes"], 1)
        self.assertEqual(row["pre_teardown_job_accounting"]["active_processes"], 0)
        self.assertEqual(row["terminal_tree_settle"]["polls_after_first"], 2)
        self.assertFalse(row["forced_termination"])
        self.assertNotIn("forced", trace)

    def test_pre_teardown_observation_failure_keeps_unknown_not_zero(self):
        row, _, _, trace = self.fixture(accounting_error=OSError("PRIVATE_FIXTURE"))
        self.assertIsNone(row["pre_teardown_job_accounting"])
        self.assertIsNone(row["forced_termination"])
        self.assertFalse(row["pre_teardown_tree_observed"])
        self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
        self.assertIn("closed", trace)
        self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_decoder_key_or_type_errors_are_closed_and_do_not_escape_cleanup(self):
        for error in (KeyError("PRIVATE_FIXTURE"), TypeError("PRIVATE_FIXTURE")):
            row, _, _, trace = self.fixture(decoder=Mock(side_effect=error))
            self.assertEqual(row["state"], "FAILED_NOT_ACCEPTED")
            self.assertIsNone(row["worker_result"])
            self.assertIn("closed", trace)
            self.assertNotIn("PRIVATE_FIXTURE", json.dumps(row))

    def test_non_dict_grace_sample_is_closed_observation_failure(self):
        resources = SimpleNamespace(thread=SimpleNamespace(is_alive=lambda: False), sample=lambda: None)
        with self.assertRaisesRegex(ValueError, "STOP_SQL_CALL_GRACE_OBSERVATION_INVALID"):
            subject.grace_resource_checkpoint(resources, 1)
