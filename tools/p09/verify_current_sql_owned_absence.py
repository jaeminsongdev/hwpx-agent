"""Bounded current-r4 independent absence; no creation/exec/removal/image pull."""
import argparse
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import current_sql_owned_absence as subject
from bounded_process_progress import bounded_observation_run
from owned_sql_job import OwnedSQLJobProcess
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher, local_docker_environment
from sql_owned_execution import scoped_path
from live_sql_evidence_reader import LiveSQLReader
from run_current_authority_audit_owned import SOURCES as AUDIT_SOURCES
from qualify_sql_runtime_environment import SOURCES as READY_SOURCES

SOURCES = list(dict.fromkeys(AUDIT_SOURCES+READY_SOURCES+["tools/p09/current_sql_owned_absence.py",
    "tools/p09/verify_current_sql_owned_absence.py", "tools/p09/tests/test_current_sql_owned_absence.py",
    "tools/p09/bounded_container_absence.py", "tools/p09/tests/test_bounded_container_absence.py", subject.AUDIT_PIN["path"],
    "implementation/p09/source-archive/p09-149-pre-current-absence-AST-composition/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-current-absence-response-diagnostics/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-current-absence-template-flush-adapter/source-preimages.v1.json"]))


def query(docker, references, resources, row):
    arguments, holders, started = subject.query_arguments(docker, references), [], time.monotonic()
    def checkpoint():
        c.require(time.monotonic()-started <= 15, "STOP_CURRENT_ABSENCE_QUERY_SCOPE")
        resources.checkpoint_io()
    def factory(actual, **kwargs):
        c.require(actual == arguments and kwargs.get("cwd") == c.ROOT
            and kwargs.get("stdin") == kwargs.get("stdout") == kwargs.get("stderr") == subprocess.PIPE
            and kwargs.get("creationflags") == subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,
            "CURRENT_ABSENCE_LAUNCH_SCOPE")
        owned = OwnedSQLJobProcess(actual, windows=resources.windows, allowed_executables=[docker],
            cwd=c.ROOT, checkpoint=checkpoint, env=local_docker_environment())
        holders.append(owned)
        return owned
    row["query_attempted"] = True
    try:
        result = bounded_observation_run(arguments, cwd=c.ROOT, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS, process_factory=factory)
    except subprocess.TimeoutExpired:
        raise ValueError("CURRENT_ABSENCE_QUERY_TIMEOUT") from None
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        if hasattr(error, "owned_sql_job_profile") and not holders:
            row["owned_host_job_profiles"].append(dict(error.owned_sql_job_profile))
        raise
    finally:
        row["owned_host_job_profiles"].extend(dict(owned.profile) for owned in holders)
        row["query_wall_seconds"] = round(time.monotonic()-started, 4)
    c.require(len(holders) == 1 and all(holders[0].profile.get(key) is True for key in
        ("cleanup_confirmed", "owned_tree_empty", "job_handle_closed"))
        and (holders[0].profile.get("limits_readback") or {}).get("verified") is True
        and type((holders[0].profile.get("last_job_accounting") or {}).get("active_processes")) is int
        and holders[0].profile["last_job_accounting"]["active_processes"] == 0,
        "CURRENT_ABSENCE_OWNED_QUERY_TEARDOWN_FAILED")
    checkpoint()
    row["inspect_exit_code"] = result.returncode
    row["query_response_diagnostics"] = subject.response_diagnostics(result, references)
    return subject.validate_response(result, references)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--actual", action="store_true")
    args = parser.parse_args()
    c.require(Path.cwd().resolve() == c.ROOT, "CURRENT_ABSENCE_ROOT")
    kind = "actual" if args.actual else "light"
    destination = scoped_path(f"implementation/p09/evidence/p09-149-current-SQL-absence.{kind}-run{args.run:02}.v1.json", fresh=True)
    resources, reader, started = SQLRuntimeResources(), None, time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-current-owned-SQL-absence/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "current_original_targets": [],
        "independent_absence_checks": [], "query_attempted": False, "query_wall_seconds": None,
        "inspect_exit_code": None, "query_response_diagnostics": None,
        "owned_host_job_profiles": [], "current_original_absence_confirmed": False,
        "all_six_current_replays_qualified": False, "full_current_authority_audit_executed": False,
        "container_created_executed_removed_or_pulled": False, "SQL_Cargo_native_or_formatter_executed": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        if args.actual:
            descriptors, references = subject.bind_inputs(reader)
            row["current_original_targets"] = descriptors
            docker = shutil.which("docker")
            c.require(docker is not None and Path(docker).is_file()
                and not Path(docker).is_symlink() and not Path(docker).is_junction(), "CURRENT_ABSENCE_DOCKER_MISSING_OR_LINK")
            resources.start()
            row["independent_absence_checks"] = query(docker, references, resources, row)
            row["current_original_absence_confirmed"] = True
            row["state"] = "PASS_THREE_CURRENT_ORIGINAL_CONTAINERS_SIX_REFERENCES_ABSENT_NOT_SQL_OR_GATE"
        else:
            from tests.test_current_authority_sql_receipts import CurrentAuthoritySQLReceiptTests
            from tests.test_bounded_container_absence import BoundedContainerAbsenceTests
            from tests.test_current_sql_owned_absence import CurrentSQLOwnedAbsenceTests
            from tests.test_sql_runtime_readiness import SQLRuntimeReadinessTests
            suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(kind) for kind in
                (CurrentAuthoritySQLReceiptTests, BoundedContainerAbsenceTests, CurrentSQLOwnedAbsenceTests, SQLRuntimeReadinessTests))
            with patch("subprocess.Popen", side_effect=AssertionError("CURRENT_ABSENCE_LIGHT_CHILD_FORBIDDEN")), \
                    patch("subprocess.run", side_effect=AssertionError("CURRENT_ABSENCE_LIGHT_CHILD_FORBIDDEN")), \
                    patch("threading.Thread.start", side_effect=AssertionError("CURRENT_ABSENCE_LIGHT_THREAD_FORBIDDEN")):
                checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
            failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
            row.update(tests_run=checked.testsRun, tests_passed=checked.testsRun-len(failed),
                failed_tests=sorted(name.split(".")[-1] for name in failed))
            c.require(checked.testsRun == 62 and checked.wasSuccessful() and not checked.skipped,
                "CURRENT_ABSENCE_LIGHT_TEST_FAILED")
            row["state"] = "PASS_CURRENT_ABSENCE_AND_READINESS_CONTRACT_ONLY_NOT_SQL_OR_GATE"
        reader.finish()
        row["source_freeze_exact_after"] = True
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "CURRENT_ABSENCE_OPERATION_FAILED"
        row["state"] = "FAILED_NOT_ACCEPTED"
        row["error_code"] = code if len(code) <= 160 and re.fullmatch(r"[A-Za-z_]+", code) else "CURRENT_ABSENCE_REDACTED_FAILURE"
    finally:
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "CURRENT_ABSENCE_FINAL_FRESHNESS_FAILED"
        finish_watcher(resources, row)
        if resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({"state": row["state"], "tests_run": row["tests_run"], "tests_passed": row["tests_passed"],
            "failed_tests": row["failed_tests"], "targets": len(row["current_original_targets"]),
            "absence_checks": len(row["independent_absence_checks"]), "elapsed_seconds": row["elapsed_seconds"]}))
    return 0 if row["state"].startswith("PASS_") and row["source_freeze_exact_after"] \
        and row.get("resource_watcher_cleanup_confirmed") is True and row["resource_stop_reason"] is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
