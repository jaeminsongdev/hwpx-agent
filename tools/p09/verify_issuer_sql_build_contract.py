"""Source/mocks or paced actual byte-binding audit; neither runs SQL/children."""
import argparse
import io
import json
from pathlib import Path
import re
import subprocess
import threading
import time
import unittest
from unittest.mock import patch

import conservative_maintenance as c
import issuer_sql_build_contract as subject
from build_current_issuer_probe import CurrentCompilerResources
from live_sql_evidence_reader import LiveSQLReader
from verify_sql_percentage_resources_light import SOURCES as SQL_SOURCES

SOURCES = list(dict.fromkeys(c.SOURCES+SQL_SOURCES+subject.SOURCES+subject.current.OWN_SOURCES
    +subject.compiler.SOURCES+subject.inputs.EXTRA+[
    "tools/p09/tests/test_owned_sql_job.py", "rust-toolchain.toml", subject.current.CANDIDATE_PIN["path"],
    "tools/p09/verify_live_sql_reader_light.py",
    "implementation/p09/source-archive/p09-149-pre-sql-source-union-repair/source-preimages.v1.json",
    "implementation/p09/source-archive/p09-149-pre-reader-mutation-error-code-repair/source-preimages.v1.json",
    subject.CURRENT_BUILD_PIN["path"]]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    kind = "actual-binding" if args.audit else "light-source"
    destination = c.ROOT/f"implementation/p09/evidence/p09-149-current-SQL-build-contract.{kind}-run{args.run:02}.v1.json"
    c.require(Path.cwd().resolve() == c.ROOT and not destination.exists() and destination.parent.is_dir()
        and not destination.parent.is_symlink() and not destination.parent.is_junction(), "SQL_BUILD_FRESH_RECEIPT_REQUIRED")
    resources = CurrentCompilerResources()
    started, reader = time.monotonic(), None
    row = {"schema_version": "hwpx-agent.p09-current-SQL-build-contract/v1", "state": "FAILED_NOT_ACCEPTED",
        "tests_run": 0, "tests_passed": 0, "failed_tests": [], "source_freeze": [], "source_freeze_exact_after": False,
        "resource_samples": resources.samples, "actual_current_input_byte_binding_executed": False,
        "actual_SQL_Docker_Cargo_native_or_child_run": False, "new_git_started": False,
        "system_or_Defender_or_WSL_settings_changed": False, "raw_logs_printed_or_saved": False,
        "P09_gate": "OPEN", "product_complete": False}
    try:
        resources.admit()
        reader = LiveSQLReader(resources)
        row["source_freeze"] = [reader.pin(name) for name in SOURCES]
        with patch.object(subprocess, "Popen", side_effect=AssertionError("SQL_BUILD_CHILD_FORBIDDEN")), \
                patch.object(subprocess, "run", side_effect=AssertionError("SQL_BUILD_CHILD_FORBIDDEN")), \
                patch.object(threading.Thread, "start", side_effect=AssertionError("SQL_BUILD_THREAD_FORBIDDEN")):
            if args.audit:
                build, executable, binding = subject.bind_probe_build(reader, c.ROOT/subject.CURRENT_BUILD_PIN["path"])
                row.update(actual_current_input_byte_binding_executed=True, build_binding=binding,
                    source_inventory=len(build["source_freeze"]), protected_inventory=len(build["protected_executables"]),
                    build_helper_inventory=len(build["build_helper_freeze"]), executable_pin=executable)
            else:
                from tests.test_issuer_sql_build_contract import IssuerSQLBuildContractTests
                from tests.test_sql_runtime_supervision import SQLRuntimeSupervisionTests
                from tests.test_live_sql_evidence_reader import LiveSQLReaderTests, LiveSQLReaderActualTests
                from tests.test_audit_evidence_io import AuditEvidenceIOTests
                from tests.test_sql_percentage_resources import SQLPercentageResourceTests
                from tests.test_sql_bounded_io_integration import SQLBoundedIOIntegrationTests
                from tests.test_sql_job_integration import SQLJobIntegrationTests
                suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in
                    (IssuerSQLBuildContractTests, SQLRuntimeSupervisionTests, LiveSQLReaderTests, LiveSQLReaderActualTests, AuditEvidenceIOTests,
                        SQLPercentageResourceTests, SQLBoundedIOIntegrationTests, SQLJobIntegrationTests)])
                result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
                failures = {getattr(test, "test_case", test).id() for test, _ in result.errors+result.failures+result.skipped}
                row.update(tests_run=result.testsRun, tests_passed=result.testsRun-len(failures),
                    failed_tests=sorted(name.split(".")[-1] for name in failures))
                c.require(result.testsRun == 83 and result.wasSuccessful() and not result.skipped,
                    "SQL_BUILD_CONTRACT_TEST_FAILED")
        reader.finish()
        row["source_freeze_exact_after"] = True
        row["state"] = "PASS_CURRENT_SQL_BUILD_BYTES_ONLY_NOT_SQL_PRODUCT_OR_GATE" if args.audit else \
            "PASS_CURRENT_SQL_BUILD_CONTRACT_SOURCE_MOCK_ONLY_NOT_SQL_PRODUCT_OR_GATE"
    except (ValueError, OSError, KeyError, TypeError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else "SQL_BUILD_OPERATION_FAILED"
        row["error_code"] = code if re.fullmatch(r"[A-Za-z0-9_]+", code) else "SQL_BUILD_REDACTED_FAILURE"
    finally:
        resources.done.set()
        if reader is not None:
            row["bounded_input_IO"] = reader.summary()
        row["resource_stop_reason"] = resources.reason
        if resources.stop.is_set():
            row["state"] = "FAILED_NOT_ACCEPTED"
        row["elapsed_seconds"] = round(time.monotonic()-started, 4)
        with destination.open("x", encoding="utf-8") as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({key: row[key] for key in ("state", "tests_run", "tests_passed", "failed_tests", "elapsed_seconds")}))
    return 0 if row["state"].startswith("PASS_") else 2


if __name__ == "__main__":
    raise SystemExit(main())
