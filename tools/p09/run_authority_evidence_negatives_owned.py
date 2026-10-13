"""Run the original 20 evidence-negative tests in one bounded owned tree, including rustfmt."""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
from bounded_process_progress import BoundedProcessCapture, MAX_OUTPUT
from owned_sql_job import OwnedSQLJobProcess
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher
from live_sql_evidence_reader import LiveSQLReader
from verify_issuer_sql_build_contract import SOURCES as CONTRACT_SOURCES

SELF = "tools/p09/run_authority_evidence_negatives_owned.py"
SOURCES = list(dict.fromkeys(CONTRACT_SOURCES+[SELF,
    "tools/p09/tests/test_authority_sql_current_audit.py", "tools/p09/verify_formula_issuer_authority_current.py",
    "tools/p09/verify_formula_issuer_live_current.py", "tools/p09/bounded_audit_tools.py",
    "tools/p09/bounded_container_absence.py", "tools/p09/run_formula_issuer_corpus_unit_probe.py",
    "crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs",
    "implementation/p09/source-archive/p09-148-pre-live-authority/source-preimages.v1.json",
    "target/p09-121-resource-optimized/p143-issuer-product-build-r14.json",
    "implementation/p09/evidence/p09-77-document-import-active-security.source-progress.v1.json",
    "implementation/p09/evidence/p09-148-owned-absence-run01.v1.json",
    *[f"implementation/p09/evidence/p09-148-authority-consumer-run{n:02}.v1.json" for n in range(1, 11)]]))


def worker():
    from tests.test_authority_sql_current_audit import AuthorityCurrentAudit, AuthorityTimeoutAudit, OwnedAbsenceAudit
    import verify_formula_issuer_authority_current as audit
    c.require(Path.cwd().resolve() == c.ROOT, "AUTH_NEGATIVE_WORKER_ROOT")
    profiles = []
    original = audit.run_audit_tool
    def tracked(task, *args, **kwargs):
        c.require(task == "rustfmt-stdin", "AUTH_NEGATIVE_FORMATTER_SCOPE")
        result = original(task, *args, **kwargs)
        profiles.append(result.audit_limits)
        return result
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (AuthorityCurrentAudit, AuthorityTimeoutAudit, OwnedAbsenceAudit)])
    with patch.object(audit, "run_audit_tool", side_effect=tracked):
        checked = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    failed = {getattr(test, "test_case", test).id() for test, _ in checked.errors+checked.failures+checked.skipped}
    codes = []
    for _, trace in checked.errors+checked.failures:
        match = re.search(r"(?:ValueError|AssertionError): ([A-Za-z0-9_]+)\s*$", trace)
        codes.append(match.group(1) if match else "AUTH_NEGATIVE_TEST_FAILED")
    accepted = checked.testsRun == 20 and checked.wasSuccessful() and not checked.skipped and bool(profiles)
    accepted = accepted and all(row.get("cleanup_confirmed") is True
        and row.get("owned_tree_empty") is True for row in profiles)
    row = {"state": "PASS_ORIGINAL_AUTHORITY_EVIDENCE_NEGATIVES_ONLY" if accepted else "FAILED_NOT_ACCEPTED",
        "tests_run": checked.testsRun, "tests_passed": checked.testsRun-len(failed),
        "failed_tests": sorted(name.split(".")[-1] for name in failed), "failure_codes": sorted(set(codes)),
        "actual_formatter_calls": len(profiles), "formatter_owned_profiles": profiles}
    print(json.dumps(row))
    return 0 if accepted else 2


def main(run):
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-authority-evidence-negatives.actual-run{run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "AUTH_NEGATIVE_FRESH_RECEIPT")
    resources, reader, owned, capture = SQLRuntimeResources(), None, None, None
    started = time.monotonic()
    row = {"schema_version": "hwpx-agent.p09-owned-authority-evidence-negatives/v1", "state": "FAILED_NOT_ACCEPTED",
        "source_freeze": [], "source_freeze_exact_after": False, "resource_samples": resources.samples,
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "actual_formatter_calls": 0,
        "maximum_worker_seconds": 90, "owned_job_profile": None, "pipe_cleanup_confirmed": False,
        "actual_SQL_Docker_Cargo_or_native_executed": False, "full_current_authority_audit_executed": False,
        "new_git_started": False, "system_or_Defender_or_WSL_settings_changed": False,
        "raw_logs_printed_or_saved": False, "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        resources.start()
        owned = OwnedSQLJobProcess([sys.executable, str(c.ROOT/SELF), "--worker"], windows=resources.windows,
            allowed_executables=[sys.executable], cwd=c.ROOT, checkpoint=resources.checkpoint_io)
        capture = BoundedProcessCapture(owned, output_limit=MAX_OUTPUT, parse_markers=False)
        deadline = time.monotonic()+90
        while True:
            resources.checkpoint_io()
            remaining = deadline-time.monotonic()
            c.require(remaining > 0, "STOP_AUTH_NEGATIVE_WORKER_TIME")
            try:
                output, errors = capture.communicate(timeout=min(.25, remaining))
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        c.require(not errors and len(output.encode()) <= MAX_OUTPUT, "AUTH_NEGATIVE_OUTPUT_SCOPE")
        result = json.loads(output)
        c.require(set(result) == {"state", "tests_run", "tests_passed", "failed_tests", "failure_codes",
            "actual_formatter_calls", "formatter_owned_profiles"}, "AUTH_NEGATIVE_PROTOCOL_SCOPE")
        row.update(result)
        row["exit_code"] = owned.returncode
        c.require(owned.returncode == 0 and result["state"] == "PASS_ORIGINAL_AUTHORITY_EVIDENCE_NEGATIVES_ONLY"
            and result["tests_run"] == result["tests_passed"] == 20 and not result["failed_tests"]
            and result["actual_formatter_calls"] >= 1, "AUTH_NEGATIVE_NOT_ACCEPTED")
        row["state"] = "PASS_20_ORIGINAL_EVIDENCE_NEGATIVES_NOT_CURRENT_SQL_PRODUCT_OR_GATE"
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["state"] = "FAILED_NOT_ACCEPTED"
        code = str(error) if isinstance(error, ValueError) else "AUTH_NEGATIVE_OPERATION_FAILED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "AUTH_NEGATIVE_REDACTED_FAILURE"
        if hasattr(error, "owned_sql_job_profile"):
            row["owned_job_profile"] = dict(error.owned_sql_job_profile)
    finally:
        if owned is not None:
            try:
                owned.kill()
                owned.wait(timeout=2)
                if capture is not None:
                    capture.close()
                    row["pipe_cleanup_confirmed"] = True
            except (ValueError, OSError, subprocess.SubprocessError):
                row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "AUTH_NEGATIVE_PIPE_OR_TERMINATE_FAILED"
            finally:
                try:
                    owned.close()
                except (ValueError, OSError, subprocess.SubprocessError):
                    row["state"], row["cleanup_error_code"] = "FAILED_NOT_ACCEPTED", "AUTH_NEGATIVE_JOB_CLEANUP_FAILED"
                row["owned_job_profile"] = dict(owned.profile)
        if reader is not None and not reader.finished:
            try:
                reader.finish()
                row["source_freeze_exact_after"] = True
            except (ValueError, OSError):
                row["state"], row["final_freshness_error_code"] = "FAILED_NOT_ACCEPTED", "AUTH_NEGATIVE_FINAL_FRESHNESS_FAILED"
        finish_watcher(resources, row)
        if resources.reason:
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["resource_stop_reason"] = resources.reason
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in
            ("state", "tests_run", "tests_passed", "failed_tests", "actual_formatter_calls", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        raise SystemExit(worker())
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    raise SystemExit(main(parser.parse_args().run))
