"""Read-only review of a completed child whose current Native frame stopped.

Never closes a source frame, runs a product, rewrites failed receipts, substitutes
for the whole current-epoch acceptor, or advances the queue. Output is a closed
allowlist: no complete pins, resources, logs or process commands are serialized.
Caller must bind the receipt bytes/code through its guarded fresh reader.
"""
import json
import math
import re

SELF = "tools/p09/review_flat_completed_body_stop_v1.py"
TEST = "tools/p09/tests/test_review_flat_completed_body_stop_v1.py"
PASS = "PASS_COMPLETED_CHILD_WITH_STOPPED_NATIVE_REVIEW_ONLY_NOT_RUNTIME_OR_ACCEPTANCE"


def require(ok, code):
    if not ok:
        raise ValueError("FLAT_COMPLETED_STOP_" + code)


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def pins(rows):
    require(type(rows) is list and rows, "WHOLE_INPUT_PINS")
    result = {}
    for row in rows:
        require(type(row) is dict and set(row) == {"path", "bytes", "sha256"}, "PIN_SHAPE")
        name = row["path"]
        require(type(name) is str and name and "\\" not in name and
                not name.startswith("/") and ":" not in name and
                all(x not in ("", ".", "..") for x in name.split("/")), "PIN_DIRECT_NAME")
        require(integer(row["bytes"]) and type(row["sha256"]) is str and
                re.fullmatch("[0-9a-f]{64}", row["sha256"]), "PIN_BYTES_HASH")
        require(name not in result, "DUPLICATE_PIN")
        result[name] = row
    return result


def review(row, root_pin, *, case, index, prior_count):
    """Positive proves only completed child + preserved failed parent/cleanup."""
    require(type(row) is dict and type(root_pin) is dict and
            set(root_pin) == {"path", "bytes", "sha256"}, "RECEIPT_SHAPE")
    require(integer(index, 129) and index <= 249 and integer(prior_count, 1) and
            type(case) is str and re.fullmatch("[A-Za-z0-9_:]+", case), "EXPECTED_CASE")
    require(re.fullmatch(
        r"implementation/p09/evidence/p09-361-case" + str(index) +
        r"-current-runtime-run[0-9]{3}\.v1\.json", root_pin["path"]) and
        integer(root_pin["bytes"], 1) and
        re.fullmatch("[0-9a-f]{64}", root_pin["sha256"]), "EXACT_RECEIPT_PIN")
    expected = dict(state="STOPPED_NOT_ACCEPTED", operation_phase="final_source_freeze",
        selected_test_index=index, prior_queue_cases=prior_count, accepted_count_delta=0,
        maximum_seconds=1200, product_body_observed=True, actual_product_child_executed=True,
        cleanup_confirmed=True, owned_tree_empty=True, worker_created=True, job_assigned=True,
        writer_authorized=True, Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False, closing_error_code=None,
        full249_current_qualified=False, signed16_current_qualified=False,
        product_complete=False, P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
        PC_freeze_resolved=False)
    for name, value in expected.items():
        require(type(row.get(name)) is type(value) and row[name] == value, "FAILED_PARENT_" + name.upper())
    require(type(row.get("exit_code")) is int and row["exit_code"] == 0, "CHILD_EXIT")
    require(row.get("selected_test_names") == row.get("passed_test_names") == [case], "ONE_EXACT_CHILD")
    require(row.get("terminal_summary") == dict(passed=1, failed=0, ignored=0,
        measured=0, filtered_out=248), "COMPLETE_TERMINAL")
    require(type(row.get("stop_reason")) is str and
            re.fullmatch("[A-Z0-9_]{1,256}", row["stop_reason"]), "PRESERVED_STOP_REASON")
    capture = row.get("capture_diagnostics")
    require(type(capture) is dict and capture.get("error_code") is None and
            capture.get("complete_streams") is True and
            capture.get("raw_log_content_included") is False and
            type(capture.get("per_stream_limit_bytes")) is int and
            capture["per_stream_limit_bytes"] == 32768, "COMPLETE_BOUNDED_CAPTURE")
    received, buffered = capture.get("received_bytes"), capture.get("buffered_bytes")
    require(type(received) is dict and type(buffered) is dict and
            set(received) == set(buffered) == {"stdout", "stderr"} and
            received == buffered and all(integer(v) and v <= 32768 for v in received.values()),
            "ALL_CAPTURE_BYTES")
    limits = row.get("owned_limits_readback") or {}
    require(limits.get("verified") is True and
            limits.get("cpu_hard_cap_machine_percent") == 6.25 and
            limits.get("affinity_mask") == 1 and limits.get("priority_class") == 16384 and
            limits.get("active_process_limit") == 16 and limits.get("kill_on_close") is True and
            limits.get("breakaway_disabled") is True, "ORIGINAL_JOB_LIMITS")
    job = row.get("job_final") or {}
    require(type(job.get("active_processes")) is int and job["active_processes"] == 0 and
            job.get("owned_processes") == [], "EMPTY_REAL_JOB")
    required = pins(row.get("source_freeze"))
    frame = row.get("source_frame") or {}
    require(frame.get("frame_state") == "CLOSED" and frame.get("registered_live_frame") is False and
            frame.get("original_two_actual_per_case_byte_reads_retained") is True and
            frame.get("serialized_pin_reused_as_live_handle") is False and
            frame.get("input_exclusions_added") is False and
            integer(frame.get("input_count"), 1) and frame["input_count"] == len(required) and
            frame.get("input_bytes") == sum(p["bytes"] for p in required.values()), "FULL_CLOSED_NOT_COMMITTED_FRAME")
    bounds = frame.get("actual_byte_boundaries")
    require(type(bounds) is list and len(bounds) == 1 and bounds[0].get("role") == "before" and
            pins(bounds[0].get("actual_byte_pins")) == required, "EXACT_COMPLETE_BEFORE_NOT_AFTER")
    diagnostics = bounds[0].get("reader_diagnostics") or {}
    require(diagnostics.get("read_passes") == len(required) and
            diagnostics.get("bytes_read") == frame["input_bytes"] and
            diagnostics.get("original_owned_read_operations_preserved") is True and
            diagnostics.get("extra_sampler_or_native_query_started") is False, "COMPLETE_ORIGINAL_BEFORE_READ")
    handles = frame.get("handles") or {}
    require(integer(handles.get("input_lock_handles_opened"), len(required)) and
            handles["input_lock_handles_opened"] == handles.get("input_lock_handles_closed") and
            handles.get("input_lock_cleanup_confirmed") is True and
            handles.get("maximum_lock_seconds") == 600, "ALL_ORIGINAL_HELD_HANDLES_CLOSED")
    for key in ("input_lock_handles_remaining", "active_reader_bindings", "active_byte_streams",
                "handle_close_failed_attempts", "probe_handles_remaining", "probe_handle_close_failed_attempts"):
        require(type(handles.get(key)) is int and handles[key] == 0, "NO_REMAINING_" + key.upper())
    require(row.get("accepted_count_delta") == 0, "NEVER_ACCEPTED")
    return dict(state=PASS, root_pin=root_pin, selected_test_index=index,
        selected_test_name=case, prior_accepted_count=prior_count, accepted_count_delta=0,
        semantic_child_passes=1, complete_before_input_count=len(required),
        complete_before_bytes=frame["input_bytes"], original_failed_receipt_preserved=True,
        original_after_source_complete=False, current_Native_frame_qualified=False,
        original_product_body_reexecution_allowed=False, independent_full_source_closing_required=True,
        current_epoch_acceptance_qualified=False, queue_cursor_advanced=False,
        source_reads_or_deadlines_relaxed=False, P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN")


def compact(row, proof):
    """Bounded diagnostic after review; no full resources/pins/diffs/log strings."""
    require(proof.get("state") == PASS and proof.get("accepted_count_delta") == 0, "REVIEW_BEFORE_OUTPUT")
    resource_fields = ("system_cpu_percent", "available_ram_percent", "commit_used_percent",
        "parent_cpu_machine_percent", "parent_private_mib", "active_processes", "owned_job_cpu_machine_percent")
    # 모든 기존 표본을 검사하되 전체 표본 배열/복사본을 새로 만들지 않는다.
    count = 0
    peak = None
    minimum_ram = 100
    tail = []
    for group in (row.get("samples", []), row.get("post_Job_cleanup_resource_samples", [])):
        require(type(group) is list, "RESOURCE_SAMPLE_LIST")
        for sample in group:
            cpu, ram = sample.get("system_cpu_percent"), sample.get("available_ram_percent")
            require(type(cpu) in (int, float) and math.isfinite(cpu) and 0 <= cpu <= 100 and
                    type(ram) in (int, float) and math.isfinite(ram) and 0 <= ram <= 100, "RESOURCE_VALUES")
            safe = {k: sample[k] for k in resource_fields if k in sample}
            count += 1
            minimum_ram = min(minimum_ram, ram)
            if peak is None or cpu > peak["system_cpu_percent"]:
                peak = safe
            tail.append(safe)
            if len(tail) > 4:
                del tail[0]
    require(count > 0, "RESOURCE_SAMPLES")
    result = dict(proof, stop_reason=row["stop_reason"], original_runtime_state=row["state"],
        elapsed_seconds=row.get("elapsed_seconds"), resource_count=count, peak_resource_sample=peak,
        available_RAM_min_percent=minimum_ram,
        resource_tail=tail, current_after_byte_boundary_complete=False,
        causal_trigger_or_PC_freeze_fix_established=False,
        complete_source_pins_or_resources_or_logs_or_process_commands_printed=False)
    encoded = json.dumps(result, ensure_ascii=True)
    require(len(encoded.encode("utf-8")) <= 8192, "CLOSED_OUTPUT_LIMIT")
    return result
