"""Bounded read-only review of ONE exact terminal flat prebody stop.

One original Guard; one root read + original final reread, no diagnostic retry,
Native input frame, PDH/process inventory, worker, acceptance or file writes.
Never prints full resource samples, path/handle/exception/command values.
"""
import argparse
import heapq
import json
import math
import time

import flat_current_queue_metadata_runtime as runtime

a = runtime.a
c = runtime.c
SELF = "tools/p09/review_flat_prebody_stop_v1.py"
TEST = "tools/p09/tests/test_review_flat_prebody_stop_v1.py"


def require(ok, code):
    if not ok:
        raise ValueError("STOP_REVIEW_" + code)


def finite(value, code, lower=0, upper=100):
    require(type(value) in (int, float) and math.isfinite(value)
            and lower <= value <= upper, code)
    return value


def count_high(samples, threshold):
    total = longest = streak = 0
    for row in samples:
        if row["system_cpu_percent"] >= threshold:
            total += 1
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0
    return dict(samples=total, longest_consecutive_samples=longest,
                full_high_load_duration_established=False)


def review(row):
    """Pure aggregate, never a runtime validator or retry authorization."""
    a.fields(row, dict(state="DEFERRED_NOT_STARTED", worker_created=False,
        product_body_observed=False, Native_source_frame_qualified=False,
        cleanup_confirmed=True, owned_tree_empty=True, accepted_count_delta=0,
        full249_current_qualified=False, signed16_current_qualified=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN"), "PREBODY_TERMINAL_ONLY")
    require(row["stop_reason"] in ("STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",
                                   "STOP_SYSTEM_COMMIT_PRESSURE"), "SUPPORTED_STOP")
    a.exact(row["source_freeze"], [], "NO_COMMITTED_FREEZE")
    a.exact(row["passed_test_names"], [], "NO_BODY_REPLAY")
    frame = row["source_frame"]
    handles = None
    if frame is not None:
        a.fields(frame, dict(frame_state="CLOSED", registered_live_frame=False,
            original_two_actual_per_case_byte_reads_retained=True, input_exclusions_added=False),
            "CLOSED_FRAME_ONLY")
        a.exact(frame["actual_byte_boundaries"], [], "NO_FINISHED_BYTE_PASS")
        h = frame["handles"]
        opened = h["input_lock_handles_opened"]
        require(type(opened) is int and opened >= 0, "OPENED_COUNT")
        a.fields(h, dict(input_lock_handles_closed=opened, input_lock_handles_remaining=0,
            input_lock_cleanup_confirmed=True, handle_close_failed_attempts=0,
            active_reader_bindings=0, active_byte_streams=0, byte_stream_identity_checks=0),
            "NO_LEAKS_OR_BYTE_WORK")
        diagnostic = h.get("native_acquisition_diagnostics")
        operations = None if diagnostic is None else {
            name: {k: v for k, v in values.items() if k in (
                "started", "completed", "failed", "elapsed_total_seconds", "elapsed_max_seconds")}
            for name, values in diagnostic["operations"].items()
            if name in ("open_with_pacing", "inspect_metadata")}
        handles = dict(opened=opened, closed=opened, remaining=0,
            frame_input_count=frame["input_count"], frame_input_bytes=frame["input_bytes"],
            native_open_pacing=h.get("native_open_pacing"), operations=operations,
            complete_byte_passes=0, causal_trigger_established=False)
    samples = row["samples"]
    require(type(samples) is list and 0 < len(samples) <= 4096, "BOUNDED_SAMPLES")
    hot = []
    available = []
    for sample in samples:
        finite(sample["system_cpu_percent"], "CPU")
        finite(sample["available_ram_percent"], "RAM")
        diagnostic = sample.get("serial_cpu_attribution", {})
        if diagnostic.get("available") is True:
            values = diagnostic["values"]
            entry = dict(time_utc=sample["time_utc"],
                PDH_interval_seconds=diagnostic["interval_seconds"],
                not_same_original_K32_interval=True)
            for name in ("MsMpEng", "System"):
                value = values[name]
                require(value["pid_stable"] is True, "STABLE_COUNTER_PID")
                entry[name + "_machine_CPU_percent"] = finite(value["machine_cpu_percent"], "COUNTER_CPU")
            available.append(entry)
    for sample in heapq.nlargest(3, samples, key=lambda x: x["system_cpu_percent"]):
        diagnostic = sample.get("serial_cpu_attribution", {})
        raw_breakdown = sample.get("existing_system_time_breakdown")
        breakdown = None if raw_breakdown is None else {
            k: v for k, v in raw_breakdown.items() if k in (
                "kernel_busy_machine_percent", "user_machine_percent",
                "extra_system_time_query", "original_K32_resource_CPU_replaced")}
        hot.append(dict(time_utc=sample["time_utc"], host_CPU_percent=sample["system_cpu_percent"],
            parent_machine_CPU_percent=sample.get("parent_cpu_machine_percent"),
            existing_system_time_breakdown=breakdown,
            diagnostic_available=diagnostic.get("available", False),
            diagnostic_reason=diagnostic.get("reason"),
            diagnostic_added_wall_seconds=diagnostic.get("added_wall_seconds"),
            hot_interval_process_attribution_established=False))
    probe = None
    attribution = row.get("serial_CPU_attribution")
    if attribution is not None:
        a.fields(attribution, dict(existing_observer_instances=1,
            second_sampler_thread_or_process=False, original_CPU_RAM_decisions_replaced=False),
            "ONE_ORIGINAL_OBSERVER")
        probes = attribution["probes"]
        require(type(probes) is list and len(probes) == 1, "ONE_PROBE")
        a.fields(probes[0], dict(query_remaining=False, cleanup_confirmed=True), "QUERY_CLOSED")
        probe = {k: v for k, v in probes[0].items() if k in (
            "collect_calls", "samples", "maximum_added_sample_seconds", "total_added_sample_seconds",
            "disabled_reason", "query_remaining", "cleanup_confirmed",
            "early_budget_checks", "early_budget_stops", "cost_checked_before_formatted_reads")}
    return dict(state="PASS_BOUNDED_READONLY_PREBODY_STOP_REVIEW_NOT_ACCEPTANCE_OR_RETRY",
        selected_test_index=row["selected_test_index"], stop_reason=row["stop_reason"],
        elapsed_seconds=row["elapsed_seconds"], sample_count=len(samples),
        host_CPU_max_percent=max(s["system_cpu_percent"] for s in samples),
        available_RAM_min_percent=min(s["available_ram_percent"] for s in samples),
        CPU_threshold_counts={str(x): count_high(samples, x) for x in (75, 90, 98)},
        hot_samples=hot, available_PDH_samples=len(available),
        last_available_PDH_sample=available[-1] if available else None,
        available_PDH_process_maxima={name: max((s[name + "_machine_CPU_percent"] for s in available),
            default=None) for name in ("MsMpEng", "System")},
        counters_not_causal_or_hot_interval_proof=True,
        closed_handles=handles, probe=probe, product_body_executed=False,
        accepted_count_delta=0, automatic_retry_authorized=False, PC_freeze_resolved=False,
        extra_sampler_query_or_child=False, secret_or_full_log_values_recorded=False)


def run(root_pin):
    require(type(root_pin) is dict, "EXACT_ROOT_PIN")
    runtime.base.scope.pins([root_pin])
    guard = None
    out = dict(state="FAILED_READONLY_STOP_REVIEW_NOT_ACCEPTED")
    try:
        guard = a.Guard()
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        q.pin(SELF); q.pin(TEST)
        row = a.read_exact(q, root_pin)
        out = review(row)
        q.finish()
        time.sleep(.5)
        guard.check(force=True)
        out.update(root_pin=root_pin, reviewer_code_pins=[q.snapshots[SELF], q.snapshots[TEST]],
            fresh_pins=len(q.snapshots), fresh_read_passes=q.read_passes,
            fresh_bytes_read=q.bytes_read, final_fresh_hashes=q.final_fresh_hashes,
            review_CPU_max_percent=max(s["system_cpu_percent"] for s in guard.samples),
            review_RAM_min_percent=min(s["available_ram_percent"] for s in guard.samples))
    except (ValueError, OSError, KeyError, TypeError, AttributeError):
        # Missing fields/resource stops are review failures, never acceptance.
        out = dict(state="FAILED_READONLY_STOP_REVIEW_NOT_ACCEPTED",
                   error_code="STOP_REVIEW_INCOMPLETE_OR_RESOURCE_GUARD")
    finally:
        if guard is not None:
            guard.close()
        out["review_cleanup_confirmed"] = bool(guard is not None and guard.cleanup)
    require(len(json.dumps(out).encode("utf-8")) <= 8192, "BOUNDED_OUTPUT")
    print(json.dumps(out))
    return 0 if out["state"].startswith("PASS_") and out["review_cleanup_confirmed"] else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    parser.add_argument("--run", type=int, required=True)
    parser.add_argument("--root-bytes", type=int, required=True)
    parser.add_argument("--root-sha256", required=True)
    args = parser.parse_args()
    require(type(args.case) is int and 116 <= args.case <= 249 and
            type(args.run) is int and 1 <= args.run <= 999, "ROOT_CURSOR")
    pin = dict(path=f"implementation/p09/evidence/p09-361-case{args.case}-current-runtime-run{args.run:03}.v1.json",
               bytes=args.root_bytes, sha256=args.root_sha256)
    raise SystemExit(run(pin))
