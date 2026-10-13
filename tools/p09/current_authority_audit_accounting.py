"""Account the unchanged full-byte receipt audit; PARTIAL is never PASS."""
import contextlib
import json
import math
import re
import sys
import time
from unittest.mock import patch

import conservative_maintenance as c
import current_authority_sql_receipts as receipts
from sql_cooperative_cancel import cancellable_resource_type
from sql_owned_execution import DiscardBoundedSummary, scoped_path
from sql_container_ownership import unique_object

SELF_AUDIT = "tools/p09/verify_current_authority_sql_receipts.py"
SCHEMA = "hwpx-agent.p09-accounted-current-authority-audit/v1"
FIELDS = {"schema_version", "state", "original_return_code", "original_error_code", "original_receipt_path",
    "resource_count", "resource_stop_reason", "resource_stop_latched", "original_dependencies_restored",
    "original_argv_restored", "call_wall_seconds", "child_event_closed", "raw_stdout_stored"}


def closed_error(error):
    value = str(error) if isinstance(error, ValueError) else "CURRENT_AUTHORITY_CALL_OPERATION_FAILED"
    return value if len(value) <= 160 and re.fullmatch(
        r"CURRENT_AUTHORITY_[A-Z_]+|STOP_[A-Z_]+|SQL_CANCEL_[A-Z_]+|SQL_CALL_[A-Z_]+|OWNED_SQL_[A-Z_]+", value) \
        else "CURRENT_AUTHORITY_CALL_REDACTED_FAILURE"


def original_receipt_path(run, *, fresh=True):
    c.require(type(run) is int and 1 <= run < 100, "CURRENT_AUTHORITY_CALL_RUN_SCOPE")
    name = f"implementation/p09/evidence/p09-149-current-authority-SQL-receipts.actual-run{run:02}.v1.json"
    scoped_path(name, fresh=fresh)
    return name


def account_original_audit(audit, run, cancel, *, clock=time.monotonic):
    name = original_receipt_path(run)
    original, constructed, previous_argv = audit.SQLRuntimeResources, [], sys.argv
    derived = cancellable_resource_type(original, cancel)
    class TrackedResources(derived):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            constructed.append(self)
    started = clock()
    c.require(type(started) in (int, float) and math.isfinite(started), "CURRENT_AUTHORITY_CALL_CLOCK_INVALID")
    row = {"schema_version": SCHEMA, "state": "FAILED_NOT_ACCEPTED", "original_return_code": None,
        "original_error_code": None, "original_receipt_path": name, "resource_count": 0,
        "resource_stop_reason": None, "resource_stop_latched": None, "original_dependencies_restored": False,
        "original_argv_restored": False, "call_wall_seconds": None, "child_event_closed": False, "raw_stdout_stored": False}
    try:
        with patch.object(audit, "SQLRuntimeResources", TrackedResources), \
                patch.object(sys, "argv", [str(c.ROOT/SELF_AUDIT), "--audit", "--run", str(run)]), \
                contextlib.redirect_stdout(DiscardBoundedSummary()):
            code = audit.main()
        c.require(type(code) is int and code in {0, 3}, "CURRENT_AUTHORITY_CALL_EXIT_INVALID")
        row["original_return_code"] = code
        row["state"] = "ORIGINAL_AUTHORITY_AUDIT_EXIT_ACCOUNTED_NOT_SQL_OR_GATE"
    except (ValueError, OSError, KeyError, TypeError, KeyboardInterrupt) as error:
        row["state"], row["original_error_code"] = "FAILED_NOT_ACCEPTED", closed_error(error)
    finally:
        row["resource_count"] = len(constructed)
        row["original_dependencies_restored"] = audit.SQLRuntimeResources is original
        row["original_argv_restored"] = sys.argv is previous_argv
        if len(constructed) == 1:
            resource = constructed[0]
            row["resource_stop_latched"] = resource.stop.is_set()
            row["resource_stop_reason"] = closed_error(ValueError(resource.reason)) if resource.reason else None
        elif len(constructed) > 1:
            row["state"], row["original_error_code"] = "FAILED_NOT_ACCEPTED", "CURRENT_AUTHORITY_CALL_RESOURCE_INVENTORY_CHANGED"
        ended = clock()
        if type(ended) in (int, float) and math.isfinite(ended) and ended >= started:
            row["call_wall_seconds"] = round(ended-started, 4)
        else:
            row["state"], row["original_error_code"] = "FAILED_NOT_ACCEPTED", "CURRENT_AUTHORITY_CALL_CLOCK_INVALID"
    return row


def decode_worker(output, run):
    c.require(isinstance(output, str) and len(output.encode("utf-8")) <= 16384, "CURRENT_AUTHORITY_CALL_PROTOCOL_BUDGET")
    try:
        row = json.loads(output, object_pairs_hook=unique_object)
    except json.JSONDecodeError:
        raise ValueError("CURRENT_AUTHORITY_CALL_PROTOCOL_JSON") from None
    c.require(isinstance(row, dict) and set(row) == FIELDS and row["schema_version"] == SCHEMA
        and row["original_receipt_path"] == original_receipt_path(run, fresh=False)
        and row["state"] in {"FAILED_NOT_ACCEPTED", "ORIGINAL_AUTHORITY_AUDIT_EXIT_ACCOUNTED_NOT_SQL_OR_GATE"}
        and row["original_dependencies_restored"] is True and row["original_argv_restored"] is True
        and row["child_event_closed"] is True and row["raw_stdout_stored"] is False,
        "CURRENT_AUTHORITY_CALL_PROTOCOL_SCOPE")
    c.require(row["original_return_code"] is None or type(row["original_return_code"]) is int
        and row["original_return_code"] in {0, 3}, "CURRENT_AUTHORITY_CALL_PROTOCOL_EXIT")
    c.require(type(row["resource_count"]) is int and 0 <= row["resource_count"] <= 16
        and (row["resource_stop_latched"] is None or type(row["resource_stop_latched"]) is bool),
        "CURRENT_AUTHORITY_CALL_PROTOCOL_RESOURCE")
    for key in ("original_error_code", "resource_stop_reason"):
        value = row[key]
        c.require(value is None or isinstance(value, str) and closed_error(ValueError(value)) == value,
            "CURRENT_AUTHORITY_CALL_PROTOCOL_ERROR")
    value = row["call_wall_seconds"]
    c.require(value is None or type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "CURRENT_AUTHORITY_CALL_PROTOCOL_CLOCK")
    return row


def classify_original_receipt(original, returned):
    c.require(isinstance(original, dict) and original["schema_version"] == "hwpx-agent.p09-current-authority-SQL-receipt-audit/v1"
        and original["source_freeze_exact_after"] is True and original["resource_watcher_cleanup_confirmed"] is True
        and original["resource_stop_reason"] is None and original["actual_current_input_byte_binding_executed"] is True
        and original["full_current_authority_audit_executed"] is False
        and original["actual_SQL_Docker_Cargo_native_formatter_or_child_executed"] is False
        and original["new_git_started"] is False and original["system_or_Defender_or_WSL_settings_changed"] is False
        and original["product_complete"] is False
        and all(original[key] == "OPEN" for key in ("P09_gate", "A12_gate", "A13_gate")),
        "CURRENT_AUTHORITY_CALL_RECEIPT_FINAL_OR_SCOPE")
    rows = original["validated_current_cases"]
    seen = {(row["case"], row["input_mode"]) for row in rows}
    c.require(len(rows) == len(seen) and seen == set(receipts.CURRENT_RUNS)
        and all(row["component_only"] is True and type(row["SQL_checks"]) is int
            and row["SQL_checks"] == (27 if row["case"] == "approval" else 33)
            and row["receipt_pin"]["path"] == receipts.CURRENT_RUNS[(row["case"], row["input_mode"])] for row in rows),
        "CURRENT_AUTHORITY_CALL_RECEIPT_CASE_INVENTORY")
    missing = receipts.missing_replays({key: None for key in seen})
    c.require(original["missing_required_replays"] == missing and type(original["required_replay_count"]) is int
        and original["required_replay_count"] == 6 and original["all_six_current_replays_validated"] is (not missing),
        "CURRENT_AUTHORITY_CALL_RECEIPT_REPLAYS")
    summary = original["bounded_input_IO"]
    c.require(isinstance(summary, dict) and summary["finished"] is True
        and type(summary["bound_inputs"]) is int and type(summary["final_fresh_hashes"]) is int
        and summary["bound_inputs"] == summary["final_fresh_hashes"]
        and type(original["exact_union_input_count"]) is int and original["exact_union_input_count"] > 0
        and summary["bound_inputs"] >= original["exact_union_input_count"], "CURRENT_AUTHORITY_CALL_RECEIPT_IO")
    wanted = "PARTIAL_CURRENT_SQL_RECEIPT_AUDIT_REQUIRED_REPLAYS_MISSING" if missing else \
        "CURRENT_SQL_RECEIPT_AUDIT_SIX_REPLAYS_NOT_FULL_AUTHORITY_OR_GATE"
    c.require(original["state"] == wanted and type(returned) is int and returned == (3 if missing else 0),
        "CURRENT_AUTHORITY_CALL_RECEIPT_EXIT_STATE")
    return {"state": original["state"], "original_exit_code": returned,
        "validated_current_cases": rows, "missing_required_replays": missing, "required_replay_count": 6,
        "all_six_current_replays_validated": not missing, "exact_union_input_count": original["exact_union_input_count"],
        "bounded_input_IO": summary, "full_current_authority_audit_executed": False,
        "P09_gate": "OPEN", "product_complete": False}
