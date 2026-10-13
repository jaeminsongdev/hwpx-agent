"""Connect original SQL calls, durable ownership and parent-only fallback.

기존 driver의 main/SQL/보안/finish/정리 조건은 바꾸지 않는다. host tree 정리와
backend 정리를 구분하며, 이 연결부의 성공을 full SQL 취소 qualification으로 쓰지 않는다.
"""
import contextlib
import json
import math
from pathlib import Path
import re
import subprocess
from unittest.mock import patch

import conservative_maintenance as c
import sql_container_ownership as ownership
from sql_cancelled_call import account_cancellable_driver_call
from sql_call_accounting import closed_code
from sql_parent_cleanup import OwnedCleanupCommand, cleanup_from_intent

BUILD = "target/p09-149-current-issuer-build/current-issuer-build-r4.json"
MISSING_BUILD = "target/p09-121-resource-optimized/p149-sql-accounting-known-missing-input.json"
COMPONENT_STATE = "PASS_ORIGINAL_SIGNATURE_CONSUMER_SQL22_COMPONENT_NOT_NATIVE_OR_GATE"
WORKER_FIELDS = {"schema_version", "case", "parent_nonce", "receipt_path", "accounted_call",
    "journal_write_count", "journal_pin", "journal_fsync_before_delegate_completed",
    "original_factory_restored", "child_event_closed"}
SCHEMA = "hwpx-agent.p09-journalled-original-SQL-worker/v1"


def closed_error(error):
    value = str(error) if isinstance(error, ValueError) else "SQL_EXECUTION_OPERATION_FAILED"
    return value if len(value) <= 160 and re.fullmatch(
        r"SQL_(?:EXECUTION|OWNED|CALL|CANCEL)[A-Z_]*|STOP_[A-Z_]+|OWNED_SQL_[A-Z_]+", value) \
        else "SQL_EXECUTION_REDACTED_FAILURE"


def scoped_path(name, *, fresh=False):
    path = c.ROOT/name
    c.require(path.is_absolute() and path.resolve().is_relative_to(c.ROOT.resolve()), "SQL_EXECUTION_PATH_SCOPE")
    for ancestor in (path, *path.parents):
        c.require(not ancestor.is_symlink() and not ancestor.is_junction(), "SQL_EXECUTION_PATH_LINK")
        if ancestor == c.ROOT:
            break
    c.require(not fresh or not path.exists(), "SQL_EXECUTION_FRESH_PATH_REQUIRED")
    return path


def call_arguments(case, mode, receipt_run, source_index, input_mode, expected):
    c.require(case in ownership.CASES and mode in {"product", "missing-input"}, "SQL_EXECUTION_CASE_OR_MODE_SCOPE")
    c.require(type(receipt_run) is int and type(source_index) is int and 0 <= source_index < 36,
        "SQL_EXECUTION_SELECTION_SCOPE")
    c.require((input_mode, expected) in {("original", "unchanged"), ("numeric_derivative", "changed")},
        "SQL_EXECUTION_REQUIRED_CASE_SCOPE")
    if mode == "missing-input":
        c.require(receipt_run == 91 and source_index == 0 and input_mode == "original",
            "SQL_EXECUTION_MISSING_FIXTURE_SCOPE")
        build = MISSING_BUILD
        scoped_path(build, fresh=True)
    else:
        c.require(1 <= receipt_run <= 90, "SQL_EXECUTION_PRODUCT_RECEIPT_SCOPE")
        build = BUILD
    prefix = "p09-146-corpus" if case == "approval" else "p09-148-authority"
    receipt = f"implementation/p09/evidence/{prefix}-consumer-run{receipt_run:02}.v1.json"
    scoped_path(build)
    scoped_path(receipt, fresh=True)
    return (build, receipt, source_index, input_mode, expected, case)


class DiscardBoundedSummary:
    """원래 main의 짧은 summary만 버린다. 임의 로그를 축적하거나 저장하지 않는다."""
    def __init__(self):
        self.bytes_written = 0

    def write(self, value):
        c.require(isinstance(value, str), "SQL_EXECUTION_SUMMARY_TYPE")
        self.bytes_written += len(value.encode("utf-8"))
        c.require(self.bytes_written <= 4096, "SQL_EXECUTION_SUMMARY_BUDGET")
        return len(value)

    def flush(self):
        pass


def journalled_driver_call(driver, arguments, cancel, nonce, case):
    ownership.uuid_value(nonce)
    c.require(case in ownership.CASES and len(arguments) == 6 and arguments[5] == case,
        "SQL_EXECUTION_DRIVER_ARGUMENT_SCOPE")
    original, recorded = driver.OwnedSQLJobFactory, []

    def writer(intent):
        c.require(not recorded, "SQL_EXECUTION_DUPLICATE_CONTAINER_GO")
        checked = ownership.write_intent(intent)
        recorded.append(checked)
        return checked

    derived = ownership.journalled_factory_type(original, nonce, case, writer=writer)
    # 같은 args/env와 원래 main을 유지한다. 모든 예외에서도 세 dependency가 복구된다.
    with patch.object(driver, "OwnedSQLJobFactory", derived), contextlib.redirect_stdout(DiscardBoundedSummary()):
        accounted = account_cancellable_driver_call(driver, arguments, cancel)
    return {"schema_version": SCHEMA, "case": case, "parent_nonce": nonce, "receipt_path": arguments[1],
        "accounted_call": accounted, "journal_write_count": len(recorded),
        "journal_pin": recorded[0]["journal_pin"] if recorded else None,
        "journal_fsync_before_delegate_completed": True if recorded else None,
        "original_factory_restored": driver.OwnedSQLJobFactory is original,
        "child_event_closed": False}


def decode_worker(output, nonce, case, receipt_path):
    c.require(isinstance(output, str) and len(output.encode("utf-8")) <= 65536, "SQL_EXECUTION_PROTOCOL_BUDGET")
    try:
        row = json.loads(output, object_pairs_hook=ownership.unique_object)
    except json.JSONDecodeError:
        raise ValueError("SQL_EXECUTION_PROTOCOL_JSON") from None
    c.require(isinstance(row, dict) and set(row) == WORKER_FIELDS and row["schema_version"] == SCHEMA
        and row["case"] == case and row["parent_nonce"] == nonce and row["receipt_path"] == receipt_path
        and row["original_factory_restored"] is True and row["child_event_closed"] is True,
        "SQL_EXECUTION_PROTOCOL_BINDING")
    count = row["journal_write_count"]
    c.require(type(count) is int and count in {0, 1} and isinstance(row["accounted_call"], dict),
        "SQL_EXECUTION_PROTOCOL_INVENTORY")
    if count == 0:
        c.require(row["journal_pin"] is None and row["journal_fsync_before_delegate_completed"] is None,
            "SQL_EXECUTION_PROTOCOL_NO_INTENT")
    else:
        pin = row["journal_pin"]
        c.require(isinstance(pin, dict) and set(pin) == {"path", "bytes", "sha256"}
            and pin["path"] == ownership.journal_path(nonce).relative_to(c.ROOT).as_posix()
            and type(pin["bytes"]) is int and 0 < pin["bytes"] <= ownership.MAX_JOURNAL_BYTES
            and isinstance(pin["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"])
            and row["journal_fsync_before_delegate_completed"] is True, "SQL_EXECUTION_PROTOCOL_INTENT")
    validate_accounting(row["accounted_call"])
    return row


def validate_accounting(row):
    """자식 stdout을 임의 JSON/로그 저장 통로로 사용하지 않는다."""
    base = {"schema_version", "state", "driver_return_code", "driver_error_code", "reader_count", "reader_IO",
        "source_final_hash_completed", "driver_call_wall_seconds", "includes_driver_admission_and_pre_hash",
        "includes_module_import_and_outer_supervision", "original_reader_finish_called_by_collector",
        "original_driver_or_resource_policy_modified", "full_SQL_wrapper_cancellation_and_container_cleanup_qualified",
        "product_complete", "P09_gate", "cooperative_resource_count", "cooperative_resource_stop_reason",
        "cooperative_resource_stop_latched", "original_resource_type_inherited", "original_driver_dependencies_restored"}
    c.require(isinstance(row, dict) and base <= set(row)
        and set(row) <= base | {"accounting_error_code", "cooperative_error_code"}
        and row["schema_version"] == "hwpx-agent.p09-original-SQL-call-accounting/v1"
        and row["state"] in {"FAILED_NOT_ACCEPTED", "ORIGINAL_DRIVER_RETURNED_FAILURE",
            "ORIGINAL_DRIVER_EXCEPTION_PRESERVED_NOT_SUCCESS", "ORIGINAL_DRIVER_RETURNED_SUCCESS_NOT_FULL_PRODUCT_OR_GATE"}
        and row["P09_gate"] == "OPEN", "SQL_EXECUTION_ACCOUNTING_PROTOCOL")
    for key in ("driver_error_code", "cooperative_resource_stop_reason", "accounting_error_code", "cooperative_error_code"):
        value = row.get(key)
        constants = {"SQL_ACCOUNTED_DRIVER_OPERATION_FAILED", "SQL_CANCELLED_CALL_RESOURCE_INVENTORY_CHANGED",
            "SQL_CANCELLED_CALL_STOP_RETURNED_SUCCESS", "SQL_CANCELLED_CALL_RESOURCE_OBSERVATION_INVALID"}
        c.require(value is None or isinstance(value, str) and len(value) <= 160
            and (value in constants or closed_code(ValueError(value)) == value),
            "SQL_EXECUTION_ACCOUNTING_ERROR_SCOPE")
    c.require(row["driver_return_code"] is None or type(row["driver_return_code"]) is int
        and row["driver_return_code"] in {0, 1}, "SQL_EXECUTION_ACCOUNTING_EXIT_SCOPE")
    for key in ("reader_count", "cooperative_resource_count"):
        c.require(type(row[key]) is int and 0 <= row[key] <= 16, "SQL_EXECUTION_ACCOUNTING_COUNT_SCOPE")
    for key in ("includes_driver_admission_and_pre_hash", "original_driver_dependencies_restored"):
        c.require(row[key] is True, "SQL_EXECUTION_ACCOUNTING_DEPENDENCY_SCOPE")
    for key in ("includes_module_import_and_outer_supervision", "original_reader_finish_called_by_collector",
            "original_driver_or_resource_policy_modified", "full_SQL_wrapper_cancellation_and_container_cleanup_qualified",
            "product_complete"):
        c.require(row[key] is False, "SQL_EXECUTION_ACCOUNTING_SCOPE_UPGRADE")
    for key in ("cooperative_resource_stop_latched", "original_resource_type_inherited"):
        c.require(row[key] is None or type(row[key]) is bool, "SQL_EXECUTION_ACCOUNTING_RESOURCE_SCOPE")
    wall = row["driver_call_wall_seconds"]
    c.require(wall is None or type(wall) in (int, float) and math.isfinite(wall) and wall >= 0,
        "SQL_EXECUTION_ACCOUNTING_CLOCK_SCOPE")
    c.require(type(row["source_final_hash_completed"]) is bool, "SQL_EXECUTION_ACCOUNTING_FINAL_SCOPE")
    if row["reader_IO"] is not None:
        summary = row["reader_IO"]
        keys = {"read_passes", "bytes_read", "bound_inputs", "final_fresh_hashes", "finished", "chunk_bytes",
            "parse_budget_bytes", "read_bytes_per_second", "maximum_scope_seconds"}
        c.require(isinstance(summary, dict) and set(summary) == keys
            and all(type(summary[key]) is int and summary[key] >= 0 for key in keys-{"finished"})
            and type(summary["finished"]) is bool and summary["finished"] == row["source_final_hash_completed"],
            "SQL_EXECUTION_ACCOUNTING_IO_SCOPE")
    else:
        c.require(row["source_final_hash_completed"] is False, "SQL_EXECUTION_ACCOUNTING_FINAL_WITHOUT_IO")


def host_tree_closed(parent):
    profile = parent.get("owned_job_profile") or {}
    final = profile.get("last_job_accounting") or {}
    return (profile.get("limits_readback") or {}).get("verified") is True \
        and all(profile.get(key) is True for key in ("owned_tree_empty", "cleanup_confirmed", "job_handle_closed")) \
        and type(final.get("active_processes")) is int and final["active_processes"] == 0


def parent_cleanup_from_loaded_intent(checked, parent, resources, docker):
    # 이미 fresh-read한 같은 intent로 actor를 만든다. 파일을 다시 읽어 다른 runUUID를
    # 선택하지 않는다. 삭제 직전의 Docker identity/격리 재검사는 기존 actor가 수행한다.
    command = OwnedCleanupCommand(checked["intent"], parent, resources, docker)
    row = cleanup_from_intent(checked["intent"], command)
    row["journal_pin"] = checked["journal_pin"]
    return row


def finalize_owned_call(parent, nonce, case, arguments, resources, reader, docker):
    """실패/강제종료 뒤에도 유효한 own intent만 정리한다. 성공으로 재분류하지 않는다."""
    row = {"state": "FAILED_NOT_ACCEPTED", "supervisor": parent, "parent_nonce": nonce, "case": case,
        "journal_pin": None, "fallback_cleanup": None, "original_receipt_pin": None,
        "original_receipt_summary": None, "backend_container_cleanup_confirmed": None,
        "full_SQL_wrapper_cancellation_and_container_cleanup_qualified": False,
        "product_complete": False, "P09_gate": "OPEN"}
    intent = None
    try:
        c.require(host_tree_closed(parent), "SQL_EXECUTION_HOST_TREE_NOT_CLOSED")
        path = ownership.journal_path(nonce)
        if path.exists():
            checked = ownership.load_intent(nonce, case)
            intent, row["journal_pin"] = checked["intent"], checked["journal_pin"]
            reported = parent.get("worker_result") or {}
            if reported.get("journal_write_count") == 1:
                c.require(reported.get("journal_pin") == checked["journal_pin"], "SQL_EXECUTION_INTENT_BYTE_DRIFT")
            # stop된 work reader에 cleanup을 의존시키지 않는다. adapter 자체의 fresh
            # grace host 검사/hard Job/15초 budget은 계속 적용한다.
            c.require(docker is not None, "SQL_EXECUTION_CLEANUP_DOCKER_MISSING")
            row["fallback_cleanup"] = parent_cleanup_from_loaded_intent(checked, parent, resources, docker)
            row["backend_container_cleanup_confirmed"] = row["fallback_cleanup"]["backend_container_cleanup_confirmed"]
            c.require(row["backend_container_cleanup_confirmed"] is True, "SQL_EXECUTION_BACKEND_CLEANUP_UNVERIFIED")
            c.require(reader.pin(checked["journal_pin"]["path"]) == checked["journal_pin"],
                "SQL_EXECUTION_INTENT_BYTE_DRIFT")
        worker = parent.get("worker_result")
        c.require(isinstance(worker, dict), "SQL_EXECUTION_WORKER_RESULT_MISSING")
        worker = decode_worker(json.dumps(worker), nonce, case, arguments[1])
        c.require(parent["state"] == "OWNED_CALL_TERMINAL_ACCOUNTED_NOT_SQL_OR_GATE"
            and parent.get("forced_termination") is False and parent.get("parent_event_closed") is True,
            "SQL_EXECUTION_LIFECYCLE_NOT_ACCEPTED")
        accounted = worker["accounted_call"]
        c.require(accounted.get("original_driver_dependencies_restored") is True
            and not accounted.get("accounting_error_code") and not accounted.get("cooperative_error_code"),
            "SQL_EXECUTION_DRIVER_ACCOUNTING_UNVERIFIED")
        c.require((worker["journal_write_count"] == 1) == (intent is not None)
            and worker["journal_pin"] == row["journal_pin"], "SQL_EXECUTION_INTENT_INVENTORY_DRIFT")
        receipt = scoped_path(arguments[1])
        if receipt.exists():
            pin = reader.pin(arguments[1])
            original = reader.json(arguments[1])
            c.require(isinstance(original, dict) and original.get("live_case") == case
                and type(original.get("source_index")) is int and original["source_index"] == arguments[2]
                and original.get("input_mode") == arguments[3] and original.get("expected_formula_outcome") == arguments[4],
                "SQL_EXECUTION_RECEIPT_SELECTION_DRIFT")
            if intent is not None:
                c.require(original.get("run_id") == intent["run_id"]
                    and original.get("container_name") == intent["container_name"]
                    and original.get("image") == intent["image_pin"], "SQL_EXECUTION_RECEIPT_IDENTITY_DRIFT")
            row["original_receipt_pin"] = pin
            row["original_receipt_summary"] = {key: original.get(key) for key in (
                "state", "container_removed", "source_freeze_exact_after", "protected_executables_exact_after",
                "resource_watcher_cleanup_confirmed", "resource_stop_reason", "actual_SQL_executed",
                "actual_Rust_DB_adapter_executed", "original_product_consumer_executed")}
        if accounted.get("driver_return_code") != 0:
            row["state"] = "ORIGINAL_DRIVER_FAILURE_ACCOUNTED_NOT_SQL_OR_GATE"
        else:
            original = row["original_receipt_summary"] or {}
            c.require(intent is not None and accounted.get("state") == "ORIGINAL_DRIVER_RETURNED_SUCCESS_NOT_FULL_PRODUCT_OR_GATE"
                and accounted.get("reader_count") == 1 and accounted.get("cooperative_resource_count") == 1
                and accounted.get("original_resource_type_inherited") is True
                and accounted.get("cooperative_resource_stop_latched") is False
                and accounted.get("cooperative_resource_stop_reason") is None
                and accounted.get("source_final_hash_completed") is True and original.get("state") == COMPONENT_STATE
                and all(original.get(key) is True for key in ("container_removed", "source_freeze_exact_after",
                    "protected_executables_exact_after", "resource_watcher_cleanup_confirmed", "actual_SQL_executed",
                    "actual_Rust_DB_adapter_executed", "original_product_consumer_executed"))
                and original.get("resource_stop_reason") is None, "SQL_EXECUTION_ORIGINAL_SUCCESS_UNVERIFIED")
            row["state"] = "ORIGINAL_SQL_COMPONENT_ACCOUNTED_NOT_FULL_WRAPPER_OR_GATE"
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        row["state"], row["error_code"] = "FAILED_NOT_ACCEPTED", closed_error(error)
    return row
