"""Low-cost semantic review of P340 post-product source-stop receipts.

This deliberately does not import the queue runtime, rescan its 1,658 inputs,
run tests, create workers, or promote runtime/Gate acceptance. It distinguishes
the actual child result in the parent sidecar from the outer frame result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT_RECEIPT = "implementation/p09/evidence/locked-r07/p340-case-111-run083.v1.json"
SIDECAR_RECEIPT = "implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json"
CASE_RECEIPT = "implementation/p09/evidence/locked-r07/cases/p340-case-111-run083.json"
SELF = "tools/p09/review_p340_post_product_stop.py"
TEST = "tools/p09/tests/test_review_p340_post_product_stop.py"
TEST_NAME = (
    "actual_import::policy_product::changed_head_provider_and_trusted_input_access_"
    "deny_without_source_or_policy_write"
)
STOP = "STOP_SUSTAINED_SYSTEM_CPU"


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("P340_POST_PRODUCT_STOP_" + code)


def pins(rows):
    require(type(rows) is list, "PIN_LIST")
    result = {}
    for row in rows:
        require(type(row) is dict and set(row) == {"path", "bytes", "sha256"}, "PIN_SHAPE")
        require(type(row["bytes"]) is int and row["bytes"] >= 0, "PIN_BYTES")
        require(isinstance(row["path"], str) and isinstance(row["sha256"], str), "PIN_FIELDS")
        require(row["path"] not in result, "DUPLICATE_PIN")
        result[row["path"]] = row
    return result


def validate(root, body, actual_sidecar_pin=None):
    require(root["schema_version"] == "hwpx-agent.p09-preserved106-fixed-runtime-queue/v24"
            and root["state"] == "FAILED_NOT_ACCEPTED"
            and root["error_code"] == root["resource_stop_reason"] == STOP
            and root["selected_test_index"] == 111
            and root["source_attempted"] is True and root["source_qualified"] is False
            and root["actual_product_child_executed"] is False
            and root.get("source_frame") is None,
            "OUTER_STOP_REMAINS_UNACCEPTED")
    recorded_sidecar = root["terminal_parent_failure_sidecar_pin"]
    require(root["case_receipt_path"] == CASE_RECEIPT
            and recorded_sidecar["path"] == SIDECAR_RECEIPT
            and set(recorded_sidecar) == {"path", "bytes", "sha256"},
            "EXACT_CASE_AND_SIDECAR_PATHS")
    if actual_sidecar_pin is not None:
        require(recorded_sidecar == actual_sidecar_pin, "SIDECAR_RECEIPT_PIN_MATCH")
    require(body["schema_version"] == "hwpx-agent.p09-locked-r07-parent-candidate/v1"
            and body["state"] == "STOPPED_NOT_ACCEPTED"
            and body["operation_phase"] == "final_source_freeze"
            and body["resource_stop_reason"] == body["stop_reason"] == STOP
            and body["actual_product_child_executed"] is True
            and body["exit_code"] == 0
            and body["selected_test_names"] == body["passed_test_names"] == [TEST_NAME]
            and body["terminal_summary"] ==
            {"passed": 1, "failed": 0, "ignored": 0, "measured": 0, "filtered_out": 248},
            "SIDECAR_PRODUCT_RESULT_AND_STOP")
    require(body["cleanup_confirmed"] is True and body["owned_tree_empty"] is True
            and body["worker_created"] is True and body["job_assigned"] is True,
            "OWNED_CLEANUP")
    require(body["test_arguments"] == [TEST_NAME, "--exact", "--test-threads=1",
                "--format=pretty", "--color=never"]
            and body["binding"] == root["binding"]
            and body["task"] == body["minimal_worker_task"] == "p204-r07-case-111-tests"
            and body["minimal_owned_worker_path"] == "tools/p09/minimal_r07_worker.py"
            and body["capture"] == dict(error_code=None, per_stream_limit_bytes=32768,
                complete_streams=True, raw_logs_saved=False)
            and all(body[k] is True for k in ("writer_authorized", "owned_limits_verified",
                "actual_job_membership_checked"))
            and body["job_final"]["active_processes"] == 0
            and body["job_final"]["owned_processes"] == [],
            "SEMANTIC_PRODUCT_CHILD_BODY_COMPLETE")
    limits = body["owned_limits_readback"]
    require(limits["verified"] is True and limits["cpu_hard_cap_machine_percent"] == 6.25
            and limits["affinity_mask"] == 1 and limits["priority_class"] == 16384
            and limits["active_process_limit"] == 16 and limits["kill_on_close"] is True
            and limits["breakaway_disabled"] is True,
            "ORIGINAL_JOB_LIMIT_VALUES")
    source = pins(body["source_freeze"])
    frame = root["terminal_source_frame"]
    require(len(source) == 1658 and frame["frame_state"] == "CLOSED"
            and frame["registered_live_frame"] is False
            and frame["input_count"] == len(source)
            and frame["input_bytes"] == sum(row["bytes"] for row in source.values()),
            "SOURCE_FRAME_CLOSED_NOT_COMMITTED")
    boundaries = frame["actual_byte_boundaries"]
    require(type(boundaries) is list and len(boundaries) == 1
            and boundaries[0]["role"] == "before"
            and pins(boundaries[0]["actual_byte_pins"]) == source,
            "EXACT_COMPLETE_BEFORE_BOUNDARY")
    readers = body["owned_source_reader_passes"]
    require(type(readers) is list and len(readers) == 2
            and readers[0]["read_passes"] == len(source)
            and readers[0]["bytes_read"] == frame["input_bytes"]
            and readers[1]["read_passes"] == 727
            and readers[1]["read_passes"] < len(source)
            and readers[1]["bytes_read"] < frame["input_bytes"],
            "PARTIAL_FINAL_SOURCE_BOUNDARY")
    require(all(row["original_owned_read_operations_preserved"] is True
                and row["read_rates_by_kind"] == {"binary": 1048576, "other": 2097152}
                for row in readers), "SOURCE_READ_POLICY_RETAINED")
    require(all(row["P09_gate"] == row["A12_gate"] == row["A13_gate"] == "OPEN"
                and row["product_complete"] is False
                and row["PC_freeze_resolved"] is False for row in (root, body)),
            "NO_GATE_OR_FREEZE_PROMOTION")
    return {
        "state": "PASS_SEMANTIC_STOP_REVIEW_NOT_SOURCE_CLOSURE_OR_RUNTIME_ACCEPTANCE",
        "selected_index": 111,
        "outer_frame_product_child_flag": False,
        "embedded_parent_actual_product_child_executed": True,
        "product_test": {"name": TEST_NAME, "passed": 1, "failed": 0, "filtered_out": 248},
        "semantic_body_capture_complete": True,
        "source_closure": "INCOMPLETE: second reader stopped at 727 of 1658",
        "accepted_count_delta": 0,
        "runtime_accepted": False,
        "P09_gate": "OPEN",
        "rescan_or_product_execution_performed": False,
    }


def read_json(root: Path, relative: str):
    raw = (root / relative).read_bytes()
    return json.loads(raw), {"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root_doc, root_pin = read_json(args.root, ROOT_RECEIPT)
    body_doc, body_pin = read_json(args.root, SIDECAR_RECEIPT)
    result = validate(root_doc, body_doc, body_pin)
    print(json.dumps({**result, "reviewed_receipts": [root_pin, body_pin]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
