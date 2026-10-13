"""Bounded owned-call cancel/grace/teardown; never implies backend cleanup.

취소 유예 중에는 작업 admission을 재개하지 않는다. 기존 hard Job 제한과
host pressure 검사를 유지하며, 강제종료는 backend 정리 성공과 구분한다.
"""
import math
import re
import subprocess
import sys
import time

import conservative_maintenance as c
from bounded_process_progress import BoundedProcessCapture, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobProcess

MAX_CALL_SECONDS, MAX_GRACE_SECONDS = 690, 135
TERMINAL_TREE_SETTLE_SECONDS, TERMINAL_TREE_SETTLE_POLLS = 2, 100


def closed_error(error):
    value = str(error) if isinstance(error, ValueError) else "SQL_CALL_SUPERVISOR_OPERATION_FAILED"
    return value if len(value) <= 160 and re.fullmatch(
        r"SQL_CALL_[A-Z_]+|STOP_[A-Z_]+|OWNED_SQL_[A-Z_]+|live_progress_[a-z_]+|owned_pipe_[a-z_]+", value) \
        else "SQL_CALL_SUPERVISOR_REDACTED_FAILURE"


def valid_clock(clock, previous):
    now = clock()
    c.require(type(now) in (int, float) and math.isfinite(now) and now >= previous,
        "SQL_CALL_CLOCK_INVALID")
    return now


def grace_resource_checkpoint(resources, now):
    # stop 뒤 종료된 원래 watcher를 재시작하거나 두 sampler를 겹치지 않는다.
    if resources.thread.is_alive():
        with resources.lock:
            c.require(resources.samples and 0 <= now-resources.last_sample_at <= 2,
                "STOP_SQL_CALL_GRACE_OBSERVATION_STALE")
            row = dict(resources.samples[-1])
    else:
        row = resources.sample()
    c.require(isinstance(row, dict), "STOP_SQL_CALL_GRACE_OBSERVATION_INVALID")
    values = [row.get(key) for key in ("system_cpu_percent", "available_ram_percent", "commit_used_percent")]
    c.require(all(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100 for value in values),
        "STOP_SQL_CALL_GRACE_OBSERVATION_INVALID")
    cpu, ram, commit = values
    c.require(ram >= c.POLICY["stop_ram_min_percent"] and commit < c.POLICY["stop_commit_used_percent"]
        and not (cpu >= c.POLICY["emergency_cpu_percent"]
            and resources.hot >= c.POLICY["emergency_cpu_consecutive_samples"]),
        "STOP_SQL_CALL_GRACE_RESOURCE_PRESSURE")


def terminal_tree_accounting(owned, terminal, *, clock, sleep):
    started = previous = valid_clock(clock, 0)
    polls, first_active = 0, None
    while True:
        before = owned.windows.accounting(owned.job)
        c.require(isinstance(before, dict) and type(before.get("active_processes")) is int
            and 0 <= before["active_processes"] <= 16, "SQL_CALL_PRE_TEARDOWN_OBSERVATION_INVALID")
        if first_active is None:
            first_active = before["active_processes"]
        previous = valid_clock(clock, previous)
        if not terminal or before["active_processes"] == 0 or previous-started >= TERMINAL_TREE_SETTLE_SECONDS \
                or polls >= TERMINAL_TREE_SETTLE_POLLS:
            return before, {"first_active_processes": first_active, "polls_after_first": polls,
                "wall_seconds": round(previous-started, 4)}
        # 주 프로세스 종료 후 동일한 owned Job만 관측하며 작업을 재시작하지 않는다.
        sleep(.02)
        polls += 1


def supervise_owned_call(arguments, resources, event, decoder, *, maximum_seconds=MAX_CALL_SECONDS,
        grace_seconds=MAX_GRACE_SECONDS, clock=time.monotonic,
        sleep=time.sleep, process_factory=OwnedSQLJobProcess, capture_factory=BoundedProcessCapture):
    c.require(callable(decoder) and event.owner is True and event.closed is False, "SQL_CALL_OWNER_OR_DECODER_SCOPE")
    for value, maximum in ((maximum_seconds, MAX_CALL_SECONDS), (grace_seconds, MAX_GRACE_SECONDS)):
        c.require(type(value) in (int, float) and math.isfinite(value) and .25 <= value <= maximum,
            "SQL_CALL_TIME_SCOPE")
    started = valid_clock(clock, 0)
    previous, cancel_started, owned, capture = started, None, None, None
    row = {"state": "FAILED_NOT_ACCEPTED", "signal_sent": False, "cancel_reason": None,
        "grace_abort_reason": None, "grace_wall_seconds": None, "call_wall_seconds": None,
        "worker_terminal_before_forced_termination": None, "forced_termination": None,
        "pre_teardown_job_accounting": None, "pre_teardown_tree_observed": False,
        "terminal_tree_settle": None,
        "worker_exit_code": None, "worker_result": None, "owned_job_profile": None,
        "pipe_cleanup_confirmed": False, "backend_container_cleanup_confirmed": None,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "product_complete": False, "P09_gate": "OPEN"}

    def process_checkpoint():
        # cleanup 유예 한정: 새로운 작업 GO가 아니라 이미 취소된 owned tree 관측이다.
        if cancel_started is None:
            resources.checkpoint_io()

    def request_cancel(error, now):
        nonlocal cancel_started
        if cancel_started is None:
            row["cancel_reason"], cancel_started = closed_error(error), now
            try:
                event.request()
                row["signal_sent"] = True
            except (ValueError, OSError) as signal_error:
                row["grace_abort_reason"] = closed_error(signal_error)
                return False
        return True

    try:
        owned = process_factory(arguments, windows=resources.windows, allowed_executables=[sys.executable],
            cwd=c.ROOT, checkpoint=process_checkpoint)
        capture = capture_factory(owned, output_limit=MAX_OUTPUT, parse_markers=False)
        while True:
            try:
                previous = valid_clock(clock, previous)
                if cancel_started is None:
                    resources.checkpoint_io()
                    c.require(previous-started <= maximum_seconds, "STOP_SQL_CALL_WALL_TIME")
                else:
                    c.require(previous-cancel_started <= grace_seconds, "STOP_SQL_CALL_GRACE_TIME")
                    grace_resource_checkpoint(resources, previous)
                try:
                    output, errors = capture.communicate(timeout=.25)
                except subprocess.TimeoutExpired:
                    capture.progress()
                    owned.observe()
                    continue
                owned.observe()
                row["worker_exit_code"] = owned.returncode
                c.require(owned.returncode == 0 and not errors, "SQL_CALL_WORKER_EXIT_OR_STDERR")
                decoded = decoder(output)
                c.require(isinstance(decoded, dict), "SQL_CALL_WORKER_PROTOCOL")
                row["worker_result"] = decoded
                row["state"] = "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE"
                if cancel_started is not None:
                    row["state"] = "CANCELLED_OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE"
                break
            except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
                # 원래 Job memory stop을 유예로 우회하지 않는다.
                if cancel_started is not None:
                    row["grace_abort_reason"] = closed_error(error)
                    break
                if not request_cancel(error, previous):
                    break
                if row["cancel_reason"] == "STOP_OWNED_JOB_MEMORY_BUDGET":
                    row["grace_abort_reason"] = row["cancel_reason"]
                    break
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["error_code"] = closed_error(error)
        if hasattr(error, "owned_sql_job_profile"):
            row["owned_job_profile"] = dict(error.owned_sql_job_profile)
        # capture 초기화 실패에도 살아 있는 worker에 취소를 먼저 전달한다.
        if owned is not None:
            request_cancel(error, previous)
    finally:
        if owned is not None:
            try:
                terminal = owned.poll() is not None
                row["worker_terminal_before_forced_termination"] = terminal
                before, settled = terminal_tree_accounting(owned, terminal, clock=clock, sleep=sleep)
                row["pre_teardown_job_accounting"] = before
                row["terminal_tree_settle"] = settled
                row["pre_teardown_tree_observed"] = True
                row["forced_termination"] = not terminal or before["active_processes"] != 0
                if row["forced_termination"]:
                    owned.kill()
                owned.wait(timeout=2)
                row["worker_exit_code"] = owned.returncode
                if capture is not None:
                    capture.close()
                    row["pipe_cleanup_confirmed"] = True
            except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
                row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", closed_error(error)
            finally:
                try:
                    owned.close()
                except (ValueError, OSError, subprocess.SubprocessError) as error:
                    row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", closed_error(error)
                row["owned_job_profile"] = dict(owned.profile)
        try:
            ended = valid_clock(clock, previous)
            row["call_wall_seconds"] = round(ended-started, 4)
            if cancel_started is not None:
                row["grace_wall_seconds"] = round(ended-cancel_started, 4)
        except ValueError:
            row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "SQL_CALL_CLOCK_INVALID"
        profile = row["owned_job_profile"] or {}
        if not all(profile.get(key) is True for key in ("owned_tree_empty", "cleanup_confirmed", "job_handle_closed")) \
                or row["forced_termination"] is not False or not row["pre_teardown_tree_observed"] \
                or not row["pipe_cleanup_confirmed"]:
            row["state"] = "FAILED_NOT_ACCEPTED"
    return row
