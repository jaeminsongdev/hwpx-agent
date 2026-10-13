"""Observe original driver call time and IO, including pre-receipt failures.

driver/reader의 검증·finish·자원 정책을 바꾸지 않는다. IO를 관측하는 subclass는
원래 생성자만 호출하며 실패를 성공으로 재분류하거나 종료 해시를 대신 실행하지 않는다.
"""
import math
import re
import subprocess
import time
from unittest.mock import patch

import conservative_maintenance as c


def closed_code(error):
    value = str(error) if isinstance(error, ValueError) else "SQL_ACCOUNTED_DRIVER_OPERATION_FAILED"
    allowed = (r"STOP_[A-Z_]+|OWNED_SQL_[A-Z_]+|CURRENT_COMPILER_[A-Z_]+|SQL_(?:ACCOUNTING|BUILD|RUNTIME)_[A-Z_]+"
        r"|sql_[a-z_]+|locked_original_[a-z_]+|adapter_[a-z_]+|crypto_[a-z_]+|original_[a-z_]+"
        r"|accepted_probe_build_missing|new_build_coverage_missing|build_receipt_outside_target"
        r"|fresh_adapter_receipt_required|corpus_selection_invalid|live_case_not_allowlisted|authority_case_not_allowlisted"
        r"|unit_build_missing|complete_executable_protection_missing|docker_not_available|bootstrap_[a-z_]+"
        r"|DEFERRED_ALREADY_SATURATED_SYSTEM|resource_stop")
    return value if len(value) <= 160 and re.fullmatch(allowed, value) else "SQL_ACCOUNTED_DRIVER_REDACTED_FAILURE"


def account_driver_call(driver, arguments, *, clock=time.monotonic):
    original_reader, readers = driver.LiveSQLReader, []
    started = clock()
    c.require(type(started) in (int, float) and math.isfinite(started), "SQL_ACCOUNTING_CLOCK_INVALID")
    row = {"schema_version": "hwpx-agent.p09-original-SQL-call-accounting/v1",
        "state": "FAILED_NOT_ACCEPTED", "driver_return_code": None, "driver_error_code": None,
        "reader_count": 0, "reader_IO": None, "source_final_hash_completed": False,
        "driver_call_wall_seconds": None, "includes_driver_admission_and_pre_hash": True,
        "includes_module_import_and_outer_supervision": False,
        "original_reader_finish_called_by_collector": False,
        "original_driver_or_resource_policy_modified": False,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "product_complete": False, "P09_gate": "OPEN"}

    class TrackedReader(original_reader):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            readers.append(self)

    try:
        with patch.object(driver, "LiveSQLReader", TrackedReader):
            code = driver.main(*arguments)
        c.require(type(code) is int and code in {0, 1}, "SQL_ACCOUNTING_DRIVER_EXIT_INVALID")
        row["driver_return_code"] = code
        row["state"] = "ORIGINAL_DRIVER_RETURNED_SUCCESS_NOT_FULL_PRODUCT_OR_GATE" if code == 0 else \
            "ORIGINAL_DRIVER_RETURNED_FAILURE"
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row["driver_error_code"] = closed_code(error)
        row["state"] = "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS"
    finally:
        row["reader_count"] = len(readers)
        if len(readers) == 1:
            try:
                row["reader_IO"] = readers[0].summary()
                row["source_final_hash_completed"] = readers[0].finished is True
            except (ValueError, OSError, KeyError, TypeError):
                row["accounting_error_code"] = "SQL_ACCOUNTING_IO_SUMMARY_UNAVAILABLE"
                row["state"] = "FAILED_NOT_ACCEPTED"
        elif len(readers) > 1:
            row["accounting_error_code"] = "SQL_ACCOUNTING_READER_INVENTORY_CHANGED"
            row["state"] = "FAILED_NOT_ACCEPTED"
        ended = clock()
        if type(ended) in (int, float) and math.isfinite(ended) and ended >= started:
            row["driver_call_wall_seconds"] = round(ended-started, 4)
        else:
            row["accounting_error_code"] = "SQL_ACCOUNTING_CLOCK_INVALID"
            row["state"] = "FAILED_NOT_ACCEPTED"
    return row
