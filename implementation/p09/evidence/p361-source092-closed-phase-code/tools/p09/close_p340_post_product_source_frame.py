"""Close the original P340 case111 source frame without replaying its product test.

The output is an independent source-only candidate, not a queue acceptance. It
uses the P340 early-source guard, Native locks, two real byte boundaries, held
identity checks, and cleanup contract. A separate compound step is required to
advance the P340 cursor.
"""
from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path, PurePosixPath
import sys
import time
import unittest
from unittest.mock import patch

import review_p340_post_product_stop as review


SELF = "tools/p09/close_p340_post_product_source_frame.py"
TEST = "tools/p09/tests/test_close_p340_post_product_source_frame.py"
SOURCE_DIR = "implementation/p09/evidence/p09-361-post-product-source"
ROOT_PIN = dict(path=review.ROOT_RECEIPT, bytes=1066545,
                sha256="7312357110f497ed7e9104df3c641d8224430667caa960053209f18f7648ff8a")
BODY_PIN = dict(path=review.SIDECAR_RECEIPT, bytes=565807,
                sha256="b8495d04c9444875cd500d2941c5b055fab1bab630325cbefb327f9f79ec1e72")
EXTRAS = (review.SELF, review.TEST, SELF, TEST)
SCHEMA = "hwpx-agent.p09-post-product-source-frame/v1"
PASS = "PASS_INDEPENDENT_P340_CASE111_SOURCE_FRAME_NOT_RUNTIME_OR_GATE"
ORIGINAL_ACQUISITION_RATE = 14
LEGACY_ACQUISITION_RATE = 5
ACQUISITION_RATE = 9
ORIGINAL_OPEN_CEILING = 20
CONTRACT_COUNT = 29
FROZEN_MUTABLE_PINS = (
    dict(path="crates/product-cli/src/lib.rs", bytes=26524,
         sha256="0018013e7d6929533f8b072b2ee7702f195d9af4a568001935f3ee2e5e07c70d"),
    dict(path="tools/p09/resume_preserved106_queue_runtime.py", bytes=179934,
         sha256="417e8f7f1b736c07387324bb6829ed22d176ae8e8498f2977738101d32438c95"),
    dict(path="tools/p09/tests/test_preserved106_queue_runtime.py", bytes=137611,
         sha256="8ebe6bc796214808f8f67c49e59c51845af6e1c7173699f8af7f0f7241e425ac"),
)
DRIFT_ERROR = "P340_POST_PRODUCT_SOURCE_FROZEN_MUTABLE_INPUT_DRIFT"
ARCHIVED_SCHEMA = "hwpx-agent.p09-post-product-source-frame/v2"
ARCHIVED_KIND = "ARCHIVED_ORIGINAL_SOURCE_AND_CURRENT_OBSERVATIONS_NOT_CURRENT_PRODUCT_QUALIFICATION"
ARCHIVED_CONTRACT_COUNT = 44
ARCHIVE_BINDINGS = tuple(dict(logical_pin=pin, archive_pin=dict(pin, path=(
    "implementation/p09/evidence/p361-v24-product-source/" if index == 0 else
    "implementation/p09/evidence/p361-v24-candidate-code/") + pin["path"]))
    for index, pin in enumerate(FROZEN_MUTABLE_PINS))


def archived_scope(original, extras, observations):
    """과거의 논리 원본과 현재 물리 경로를 구분하고 전체 원본 바이트를 보존한다."""
    require(len(original) == 1658 and set(extras) == set(EXTRAS)
            and not set(original) & set(extras), "ARCHIVED_FULL_ORIGINAL_AND_CONTROLLER_SCOPE")
    require(all(original.get(row["path"]) == row for row in FROZEN_MUTABLE_PINS)
            and set(observations) == {row["path"] for row in FROZEN_MUTABLE_PINS}
            and all(observations[name]["path"] == name for name in observations),
            "ARCHIVED_EXACT_THREE_LOGICAL_ORIGINALS_AND_CURRENT_PATHS")
    relocated = dict(original)
    for row in ARCHIVE_BINDINGS:
        logical = row["logical_pin"]["path"]
        archive = row["archive_pin"]
        require(archive["path"] not in relocated and archive["path"] not in extras,
                "ARCHIVED_DESTINATION_DISJOINT")
        relocated.pop(logical)
        relocated[archive["path"]] = dict(archive)
    result = {**relocated, **extras, **observations}
    require(len(relocated) == 1658 and len(result) == 1665
            and sum(row["bytes"] for row in relocated.values()) ==
                sum(row["bytes"] for row in original.values()), "LOSSLESS_ORIGINAL_PLUS_SEVEN_CURRENT_INPUTS")
    return result


def required_from_document(doc, body, extras, observations=None):
    original = pins(body["source_freeze"])
    if doc["schema_version"] == SCHEMA:
        require(observations is None, "LEGACY_NO_ARCHIVED_PROJECTION")
        return {**original, **extras}
    require(doc["schema_version"] == ARCHIVED_SCHEMA and observations is not None
            and doc["source_archive_bindings"] == list(ARCHIVE_BINDINGS)
            and pins(doc["current_observed_source_pins"]) == observations
            and doc["source_kind"] == ARCHIVED_KIND
            and doc["current_product_source_qualified"] is False
            and doc["original_runtime_file_identities_reused"] is False,
            "EXPLICIT_ARCHIVED_BYTES_NOT_CURRENT_PRODUCT_OR_OLD_HANDLES")
    return archived_scope(original, extras, observations)


def directory_count(required):
    return len({parent.as_posix() for name in required for parent in PurePosixPath(name).parents})


def archived_preflight(reader, original, extras):
    for row in ARCHIVE_BINDINGS:
        require(original.get(row["logical_pin"]["path"]) == row["logical_pin"],
                "ARCHIVED_EXACT_FROZEN_PREIMAGE")
        require(reader.pin(row["archive_pin"]["path"]) == row["archive_pin"],
                "ARCHIVED_EXACT_PHYSICAL_BYTES")
    observations = {row["path"]: reader.pin(row["path"]) for row in FROZEN_MUTABLE_PINS}
    return archived_scope(original, extras, observations), observations


class SourceProgress:
    """기존 감시기 표본만 최대45초 간격으로 알린다. 새 조회/스레드는 없다."""
    def __init__(self, owner, stream=None, clock=time.monotonic):
        self.owner=owner;self.stream=sys.stderr if stream is None else stream;self.clock=clock
        self.next_emit=0.0;self.emitted=0;self.output_errors=0

    def emit(self, stage, held_count, *, force=False):
        try:
            now=self.clock()
            if not force and now<self.next_emit:return
            self.next_emit=now+45.0
            with self.owner.lock:
                sample=dict(self.owner.samples[-1]) if self.owner.samples else {}
            fields=("time_utc","system_cpu_percent","parent_cpu_machine_percent",
                    "available_ram_percent","own_private_bytes","audited_logical_read_bytes")
            row=dict(progress_stage=stage,held_handle_count=held_count,
                     existing_watcher_sample={key:sample.get(key) for key in fields},
                     new_native_query_or_sampler_started=False,progress_is_acceptance_evidence=False)
            print(json.dumps(row),file=self.stream,flush=True)
            self.emitted+=1
        except (OSError,ValueError,TypeError,AttributeError,RuntimeError):
            # 진단 출력 실패가 원 Native 반환/예외 또는 cleanup을 대체하지 않는다.
            self.output_errors+=1

    def summary(self):
        return dict(emitted_rows=self.emitted,output_errors=self.output_errors,
            interval_seconds=45.0,existing_watcher_samples_only=True,
            new_native_query_or_sampler_or_thread_started=False,
            original_native_return_and_exceptions_retained=True,
            original_guards_or_deadlines_or_pacer_credit_modified=False,
            diagnostic_output_not_acceptance_evidence=True)


def frozen_mutable_preflight(reader, original):
    """고비용 Native 획득 전에 자주 변경되는 세 원본을 실제 reader로 대조한다.

    이 조기 검사는 전체 두 경계 hash/lock/identity 검사를 대체하지 않는다.
    과거 pin을 현재 값으로 갱신하거나 archive 경로를 원본처럼 가장하지 않는다.
    """
    require(all(original.get(pin["path"]) == pin for pin in FROZEN_MUTABLE_PINS),
            "EXACT_FROZEN_MUTABLE_PREIMAGES")
    actual = [reader.pin(pin["path"]) for pin in FROZEN_MUTABLE_PINS]
    rows = pins(actual)
    require(set(rows) == {pin["path"] for pin in FROZEN_MUTABLE_PINS},
            "PREFLIGHT_ORIGINAL_PATHS_NOT_ARCHIVE_SUBSTITUTION")
    mismatches = [dict(expected=pin, actual=rows[pin["path"]])
                  for pin in FROZEN_MUTABLE_PINS if rows[pin["path"]] != pin]
    return dict(checked_input_count=3, actual_pins=actual, mismatches=mismatches,
                frozen_inputs_match=not mismatches, native_acquisition_started=False,
                full_source_qualification=False, product_child_replayed=False,
                original_pin_values_modified=False)


def validate_drift_preflight(doc):
    row = doc.get("frozen_mutable_input_preflight")
    require(type(row) is dict, "DRIFT_PREFLIGHT_REQUIRED")
    actual = pins(row.get("actual_pins"))
    require(set(actual) == {pin["path"] for pin in FROZEN_MUTABLE_PINS},
            "DRIFT_PREFLIGHT_EXACT_THREE_ORIGINAL_PATHS")
    mismatches = [dict(expected=pin, actual=actual[pin["path"]])
                  for pin in FROZEN_MUTABLE_PINS if actual[pin["path"]] != pin]
    require(bool(mismatches) and row == dict(
        checked_input_count=3, actual_pins=list(actual.values()), mismatches=mismatches,
        frozen_inputs_match=False, native_acquisition_started=False,
        full_source_qualification=False, product_child_replayed=False,
        original_pin_values_modified=False), "EXACT_RECORDED_FROZEN_DRIFT_NO_ACCEPTANCE")
    return True


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("P340_POST_PRODUCT_SOURCE_" + code)


def pins(rows):
    require(type(rows) is list, "PIN_LIST")
    result = {}
    for row in rows:
        require(type(row) is dict and set(row) == {"path", "bytes", "sha256"}
                and type(row["bytes"]) is int and row["bytes"] >= 0
                and isinstance(row["path"], str) and isinstance(row["sha256"], str), "PIN_SHAPE")
        require(row["path"] not in result, "DUPLICATE_PIN")
        result[row["path"]] = row
    return result


def validate_frame(frame, required, *, archived=False):
    total = sum(row["bytes"] for row in required.values())
    n = len(required)
    require(type(archived) is bool, "EXACT_ARCHIVED_FRAME_PROFILE")
    expected = 1665 if archived else 1662
    directories = directory_count(required) if archived else 308
    require(n == expected and frame["frame_state"] == "COMMITTED"
            and frame["registered_live_frame"] is False
            and frame["input_count"] == n and frame["input_bytes"] == total
            and frame["original_owned_cleanup_confirmed_before_release"] is True
            and frame["original_two_actual_per_case_byte_reads_retained"] is True
            and all(frame[k] is False for k in
                    ("serialized_pin_reused_as_live_handle", "input_exclusions_added", "security_sandbox_claimed")),
            "FULL_LIVE_FRAME_NOT_CACHE_OR_REDUCED")
    boundaries = frame["actual_byte_boundaries"]
    require(type(boundaries) is list and len(boundaries) == 2
            and [row["role"] for row in boundaries] == ["before", "after"], "TWO_BOUNDARIES")
    for row in boundaries:
        diag = row["reader_diagnostics"]
        require(pins(row["actual_byte_pins"]) == required
                and diag["read_passes"] == n and diag["bytes_read"] == total
                and diag["read_rates_by_kind"] == {"binary": 1048576, "other": 2097152}
                and diag["original_owned_read_operations_preserved"] is True
                and diag["extra_sampler_or_native_query_started"] is False,
                "COMPLETE_ACTUAL_BYTE_BOUNDARY")
    handles = frame["handles"]
    duplicate = handles["borrowed_byte_streams"]
    require(handles["input_lock_handles_opened"] == handles["input_lock_handles_closed"] == n + directories
            and handles["input_lock_handles_remaining"] == handles["active_reader_bindings"] ==
            handles["active_byte_streams"] == 0
            and handles["input_lock_cleanup_confirmed"] is True
            and handles["handle_close_failed_attempts"] == 0
            and handles["byte_stream_identity_checks"] == 2 * n
            and handles["separate_pathname_reopens"] == 0
            and duplicate["duplicate_handles_opened"] == duplicate["duplicate_handles_closed"] ==
            duplicate["shared_offset_resets"] == 2 * n
            and duplicate["duplicate_handles_remaining"] == duplicate["duplicate_close_failed_attempts"] == 0
            and duplicate["active_borrow_binding"] is False
            and duplicate["byte_stream_pathname_reopens"] == 0
            and duplicate["original_pre_read_stream_identity_check_retained"] is True
            and duplicate["original_held_handles_closed_by_borrower"] is False,
            "ALL_NATIVE_AND_BORROWED_HANDLES_CLOSED")
    require(handles["maximum_lock_seconds"] == 600
            and handles["native_open_pacing"]["maximum_opens_per_second"] == 20
            and handles["file_write_or_delete_operation_executed"] is False
            and handles["native_open_backpressure"]["original_hard_resource_decisions_unmodified"] is True
            and handles["native_open_backpressure"]["original_IO_deadline_unmodified"] is True
            and handles["native_open_backpressure"]["original_read_checks_skipped"] is False,
            "ORIGINAL_NATIVE_LIMITS_AND_READ_GUARDS")
    pressure = handles["acquisition_phase_pressure"]
    selected_rate = ACQUISITION_RATE if archived else LEGACY_ACQUISITION_RATE
    density_baseline = ORIGINAL_OPEN_CEILING if archived else ORIGINAL_ACQUISITION_RATE
    require(pressure["acquisition_maximum_reservations_per_second"] == selected_rate
            and pressure["original_global_and_byte_reservation_ceiling_per_second"] == ORIGINAL_OPEN_CEILING
            and pressure["acquisition_used"] is True and pressure["acquisition_complete"] is True
            and pressure["acquisition_reservations"] == n + directories
            and pressure["restored_original_rate"] == ORIGINAL_OPEN_CEILING
            and pressure["same_original_pacer"] is True
            and pressure["clock_and_sleeper_and_checkpoint_retained"] is True
            and pressure["clock_previous_credit_or_reservation_counter_reset"] is False
            and pressure["extra_sampler_or_thread_started"] is False
            and pressure["original_CPU_RAM600_and_all_byte_identity_guards_preserved"] is True
            and pressure["cleanup_callback_wrapped"] is False
            and pressure["nominal_acquisition_density_reduction_percent"] ==
                100.0 * (1.0 - selected_rate / density_baseline)
            and pressure["CPU_or_PC_freeze_improvement_established"] is False,
            "LOWER_ACQUISITION_PACING_ONLY_NO_GUARD_RELAXATION")
    require(frame["held_identity_after_owned_cleanup"] == dict(
        held_identity_checks_complete=True, separate_pathname_reopens=0,
        regular_file_count=n, directory_count=directories), "POST_CLEANUP_HELD_IDENTITIES")


def validate_path_guard(rows, n):
    require(type(rows) is list and len(rows) == 2, "TWO_PATH_GUARD_BOUNDARIES")
    for row in rows:
        require(row["native_metadata_queries_attempted"] == row["fresh_held_metadata_queries"] == n
                and row["original_path_guard_predicates"] == 3 * n
                and row["original_reader_root_restored"] is True
                and row["active_path_guard_adapter"] is False
                and row["pathname_metadata_probes"] == 0
                and row["original_stream_identity_check_retained"] is True
                and row["metadata_reused_between_source_requests"] is False
                and row["added_native_queries_recorded_separately_from_original_lock_checks"] is True
                and row["kernel_call_reduction_or_CPU_freeze_improvement_claimed"] is False,
                "ALL_CURRENT_INPUT_GUARDS_FRESH_AND_RESTORED")


def validate_acquisition(handles, regular_count, directory_count):
    row = handles["native_acquisition_diagnostics"]
    total = regular_count + directory_count
    require(row["take_attempts"] == row["take_completed"] == total
            and row["take_failed"] == 0 and row["active_take"] is False
            and row["input_kinds"] == dict(
                directory=dict(started=directory_count, completed=directory_count, failed=0),
                regular=dict(started=regular_count, completed=regular_count, failed=0))
            and row["last_attempt"] == dict(ordinal=total, kind="regular",
                last_native_operation="inspect_metadata", completed=True),
            "COMPLETE_NATIVE_ACQUISITION_DIAGNOSTICS")
    require(set(row["operations"]) == {"open_with_pacing", "inspect_metadata"},
            "BOUNDED_NATIVE_OPERATION_SET")
    for op in row["operations"].values():
        require(op["started"] == op["completed"] == total and op["failed"] == 0
                and all(type(op[key]) is int and op[key] >= 0 for key in ("measured", "unknown"))
                and op["measured"] + op["unknown"] == total
                and type(op["elapsed_total_seconds"]) in (int, float)
                and math.isfinite(op["elapsed_total_seconds"])
                and op["elapsed_total_seconds"] >= 0,
                "NATIVE_ACQUISITION_TIMING_ACCOUNTING")
        require((op["measured"] == 0 and op["elapsed_max_seconds"] is None
                 and op["elapsed_total_seconds"] == 0)
                or (op["measured"] > 0 and type(op["elapsed_max_seconds"]) in (int, float)
                    and math.isfinite(op["elapsed_max_seconds"])
                    and 0 <= op["elapsed_max_seconds"] <= op["elapsed_total_seconds"]),
                "NATIVE_ACQUISITION_MAX_DURATION")
    expected_flags = dict(bounded_aggregate_not_per_input_trace=True,
        open_elapsed_includes_original_pacer_and_pressure_wait=True,
        inspect_elapsed_covers_original_metadata_bundle=True,
        original_native_methods_and_arguments_retained=True,
        original_take_guard_and_identity_checks_retained=True,
        original_pacer_clock_sleeper_checkpoint_and_credit_retained=True,
        diagnostic_clock_failures_do_not_mask_original_return_or_exception=True,
        cleanup_callback_or_close_wrapped=False,
        extra_sampler_or_thread_or_native_query_started=False,
        path_or_handle_or_exception_values_recorded=False,
        CPU_cause_or_PC_freeze_improvement_claimed=False)
    require(all(row[name] is value for name, value in expected_flags.items()),
            "NATIVE_ACQUISITION_ORIGINAL_GUARDS")


def source_budget(required, *, archived=False, acquisition_rate=None):
    require(type(archived) is bool and len(required) == (1665 if archived else 1662),
            "BUDGET_FULL_INPUT_SCOPE")
    directories = directory_count(required) if archived else 308
    binary = sum(pin["bytes"] for path, pin in required.items() if path.lower().endswith(".exe"))
    other = sum(pin["bytes"] for path, pin in required.items() if not path.lower().endswith(".exe"))
    require(binary > 0 and other > 0, "BUDGET_BINARY_AND_OTHER_INPUTS")
    acquisitions = len(required) + directories
    selected_rate = (ACQUISITION_RATE if archived else LEGACY_ACQUISITION_RATE)
    if acquisition_rate is not None:
        require(archived and type(acquisition_rate) is int
                and 1 <= acquisition_rate <= ORIGINAL_ACQUISITION_RATE,
                "BUDGET_RATE_WITHIN_ORIGINAL_CANDIDATE_CEILING")
        selected_rate = acquisition_rate
    native_seconds = acquisitions / selected_rate
    byte_seconds = 2 * binary / 1048576 + 2 * other / 2097152
    # 각 serial borrower도 원 Native pacer의 예약을 사용한다. byte pacing과
    # 겹칠 거라고 가정하지 않는다. 과거 v1 receipt의 산식은 역사적 검토용만 유지.
    byte_reservations = 2 * len(required)
    byte_native_seconds = byte_reservations / ORIGINAL_OPEN_CEILING if archived else 0
    early_yield_seconds = 8 * 0.5
    margin_seconds = 60
    nominal = native_seconds + byte_seconds + byte_native_seconds + early_yield_seconds + margin_seconds
    require(nominal < 600, "LOW_RATE_MUST_FIT_UNCHANGED_600_SECOND_LOCK")
    return dict(inputs=len(required), directories=directories,
        acquisition_reservations=acquisitions,
        selected_acquisition_rate_per_second=selected_rate,
        binary_bytes=binary, other_bytes=other,
        native_acquisition_seconds=native_seconds,
        two_actual_byte_pass_nominal_seconds=byte_seconds,
        nominal_early_yield_allowance_seconds=early_yield_seconds,
        unallocated_margin_seconds=margin_seconds,
        predicted_combined_seconds=nominal, unchanged_lock_deadline_seconds=600,
        unknown_pressure_waits_included=False,
        estimate_not_completion_guarantee=True, CPU_or_PC_freeze_improvement_claimed=False,
        **(dict(two_actual_byte_pass_native_reservations=byte_reservations,
            unchanged_byte_reservation_ceiling_per_second=ORIGINAL_OPEN_CEILING,
            two_actual_byte_pass_native_pacing_seconds=byte_native_seconds,
            combined_serial_byte_pacing_seconds=byte_seconds + byte_native_seconds,
            byte_and_native_pacing_costs_assumed_overlapped=False,
            idle_pacer_credit_assumed=False) if archived else {}))


def acquisition_pacing(original_rate, *, archived=False):
    require(type(original_rate) is int and original_rate == ORIGINAL_ACQUISITION_RATE,
            "ORIGINAL_ACQUISITION_RATE")
    selected_rate = ACQUISITION_RATE if archived else LEGACY_ACQUISITION_RATE
    return dict(
        original_candidate_reservations_per_second=original_rate,
        selected_reservations_per_second=selected_rate,
        unchanged_global_and_byte_ceiling_per_second=ORIGINAL_OPEN_CEILING,
        nominal_density_reduction_percent=100.0 * (1.0 - selected_rate / original_rate),
        measured_CPU_or_freeze_improvement_claimed=False)


def validate_acquisition_pacing(doc):
    archived = doc.get("schema_version") == ARCHIVED_SCHEMA
    require(doc.get("source_acquisition_pacing") == acquisition_pacing(ORIGINAL_ACQUISITION_RATE, archived=archived),
            "SOURCE_ACQUISITION_PACING_BASELINE")
    return True


def validate_document(doc, root, body, root_pin, body_pin, required, review_result):
    archived = doc["schema_version"] == ARCHIVED_SCHEMA
    extras = pins(doc["extra_controller_pins"])
    observations = pins(doc["current_observed_source_pins"]) if archived else None
    require(required == required_from_document(doc, body, extras, observations), "EXACT_REBUILT_SOURCE_SCOPE")
    require(doc["schema_version"] in (SCHEMA, ARCHIVED_SCHEMA) and doc["state"] == PASS
            and doc["original_root_pin"] == root_pin == ROOT_PIN
            and doc["original_parent_pin"] == body_pin == BODY_PIN
            and doc["review"] == review_result
            and doc["original_executed_source_pins"] == body["source_freeze"]
            and pins(doc["extra_controller_pins"]) == {p["path"]: p for p in doc["extra_controller_pins"]}
            and set(pins(doc["extra_controller_pins"])) == set(EXTRAS)
            and doc["source_kind"] == (ARCHIVED_KIND if archived else
                "INDEPENDENT_CURRENT_SOURCE_AFTER_COMPLETED_PRODUCT_CHILD_NOT_ORIGINAL_PARTIAL_AFTER"),
            "EXACT_IMMUTABLE_CANDIDATE_AND_CONTROLLER_SCOPE")
    validate_frame(doc["source_frame"], required, archived=archived)
    if archived:
        validate_path_guard(doc["source_path_guard_diagnostics"], len(required))
        validate_acquisition(doc["source_frame"]["handles"], len(required), directory_count(required))
    require(doc["preparation_IO"]["finished"] is True
            and doc["preparation_IO"]["bound_inputs"] == doc["preparation_IO"]["final_fresh_hashes"]
            and doc["source_closing_contract_tests_passed"] == (ARCHIVED_CONTRACT_COUNT if archived else CONTRACT_COUNT)
            and doc["source_budget"] == source_budget(required, archived=archived)
            and validate_acquisition_pacing(doc)
            and doc["resource_stop_reason"] is None
            and doc["resource_watcher_cleanup_confirmed"] is True
            and doc["independent_source_frame_attempted"] is True
            and doc["independent_source_frame_qualified"] is True
            and doc["actual_product_child_executed"] is False
            and doc["runtime_acceptance_changed"] is False
            and doc["accepted_count_delta"] == 0
            and doc["P09_gate"] == doc["A12_gate"] == doc["A13_gate"] == "OPEN"
            and doc["product_complete"] is False and doc["PC_freeze_resolved"] is False,
            "NO_PRODUCT_REPLAY_OR_QUEUE_OR_GATE_PROMOTION")


def contracts(root_path, checkpoint):
    tests_path = root_path / "tools/p09/tests"
    sys.path.insert(0, str(root_path / "tools/p09"))
    sys.path.insert(0, str(tests_path))
    import resource_guarded_contract_suite as guarded
    import test_close_p340_post_product_source_frame as source_tests
    import test_review_p340_post_product_stop as review_tests
    suite = unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromModule(source_tests),
        unittest.defaultTestLoader.loadTestsFromModule(review_tests),
    ))
    with patch("subprocess.Popen", side_effect=AssertionError("P340_SOURCE_NO_CHILD")), \
            patch("subprocess.run", side_effect=AssertionError("P340_SOURCE_NO_CHILD")), \
            patch("threading.Thread.start", side_effect=AssertionError("P340_SOURCE_NO_THREAD")):
        with guarded.bind(checkpoint):
            result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun == ARCHIVED_CONTRACT_COUNT and not result.skipped,
            "SYNTHETIC_FAIL_CLOSED_SOURCE_CONTRACTS")
    return result.testsRun


def _run(args):
    # Defer the large historical runtime import until explicit source execution.
    import resume_preserved106_queue_runtime as p340

    root_path = p340.p.c.ROOT
    require(Path.cwd().resolve() == root_path, "CWD_REPOSITORY_ROOT")
    destination = root_path / SOURCE_DIR / f"p340-post-stop-source-run{args.run:03}.v1.json"
    require(not destination.exists(), "FRESH_RECEIPT_ONLY")
    context = p340.g.observation.Context()
    owner = p340.g.observation.Resources(context)
    q = frame = early = proposed = None
    progress = SourceProgress(owner)
    profile = None
    original_profile_rate = None
    body = root = required = review_result = None
    out = p340.p.r.flags()
    out.update(schema_version=ARCHIVED_SCHEMA, state="FAILED_NOT_ACCEPTED",
               original_root_pin=ROOT_PIN, original_parent_pin=BODY_PIN,
               actual_product_child_executed=False, runtime_acceptance_changed=False,
               accepted_count_delta=0, source_kind=
               ARCHIVED_KIND, current_product_source_qualified=False,
               original_runtime_file_identities_reused=False,
               independent_source_frame_attempted=False, independent_source_frame_qualified=False)
    stage = "admission"
    try:
        owner.admit()
        out["source_closing_contract_tests_passed"] = contracts(root_path, owner.checkpoint_io)
        profile = p340.m.profile
        original_profile_rate = profile.RATE
        require(original_profile_rate == ORIGINAL_ACQUISITION_RATE, "ORIGINAL_RATE_PREIMAGE")
        profile.RATE = ACQUISITION_RATE
        out["source_acquisition_pacing"] = acquisition_pacing(original_profile_rate, archived=True)
        q = p340.MetadataReader(owner, context)
        require(q.pin(ROOT_PIN["path"]) == ROOT_PIN and q.pin(BODY_PIN["path"]) == BODY_PIN,
                "IMMUTABLE_ORIGINAL_RECEIPTS")
        root = q.json(ROOT_PIN["path"])
        body = q.json(BODY_PIN["path"])
        actual_body_pin = dict(path=BODY_PIN["path"], bytes=BODY_PIN["bytes"], sha256=BODY_PIN["sha256"])
        review_result = review.validate(root, body, actual_body_pin)
        original = pins(body["source_freeze"])
        extras = {name: q.pin(name) for name in EXTRAS}
        stage = "archived_source_preflight"
        required, observations = archived_preflight(q, original, extras)
        out.update(source_archive_bindings=list(ARCHIVE_BINDINGS),
                   current_observed_source_pins=list(observations.values()))
        out["source_budget"] = source_budget(required, archived=True)
        q.finish()

        early = p340.m.early_review.EarlySourceCheckpoint(owner.checkpoint_io, owner)
        class LowerAcquisitionInputLocks(p340.AcquisitionInputLocks):
            def summary(self):
                result = super().summary()
                phase = result["acquisition_phase_pressure"]
                phase["nominal_acquisition_density_reduction_percent"] = 100.0 * (
                    1.0 - phase["acquisition_maximum_reservations_per_second"] /
                    phase["original_global_and_byte_reservation_ceiling_per_second"])
                return result

            def take(self, *args, **kwargs):
                result = super().take(*args, **kwargs)
                progress.emit("source_frame_acquire",len(self.owned))
                return result

        held = LowerAcquisitionInputLocks(root_path, early, owner, context)
        require(held.checkpoint is early and held.api.pacer.rate == 20
                and held.open_pressure.resources is owner, "ORIGINAL_P340_NATIVE_OWNER_AND_PACING")
        frame = p340.p.frames.Frame(p340.p.frames.Registry(), required, early, held=held)
        context.reader = p340.p.frames.Counters(q.reader, frame.readers)
        out["independent_source_frame_attempted"] = True
        out["early_source_native_and_byte_guard_connected"] = True
        held.mark("before_acquire")
        stage = "source_frame_acquire"
        progress.emit(stage,0,force=True)
        with context.scope("source_frame_acquire"):
            frame.acquire()
        held.mark("after_acquire")

        def factory(checkpoint):
            return p340.p.core.run.owned.OwnedReader(
                root_path, checkpoint, samples=owner, protected={p340.p.m.EXE["path"]})

        diagnostics = []
        for phase in ("metadata_hash", "final_fresh_hash"):
            stage = phase
            progress.emit(stage,len(held.owned),force=True)
            with context.scope(phase):
                p340.read_with_held_path_guards(frame, factory, owner.checkpoint_io, diagnostics)
        stage = "source_commit"
        held.mark("before_release")
        source_frame = frame.commit(body)
        out.update(source_frame=source_frame, source_path_guard_diagnostics=diagnostics,
                   independent_source_frame_qualified=True,
                   original_executed_source_pins=list(original.values()),
                   extra_controller_pins=list(extras.values()), review=review_result)
        validate_path_guard(diagnostics, len(required))
        validate_acquisition(source_frame["handles"], len(required), directory_count(required))
        validate_frame(source_frame, required, archived=True)
        proposed = dict(state=PASS)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError, KeyboardInterrupt) as error:
        out["error_code"] = p340.p.b.run.original.closed_error(error)
        out["failure_diagnostic"] = p340.m.m.diagnostic(error, stage)
    finally:
        if frame is not None:
            try:
                if not frame.close():
                    out["error_code"] = "SOURCE_FRAME_CLEANUP_FAILED"
                    proposed = None
            except (ValueError, OSError):
                out["error_code"] = "SOURCE_FRAME_CLEANUP_FAILED"
                proposed = None
            out["source_frame"] = frame.summary()
        if profile is not None and original_profile_rate is not None:
            profile.RATE = original_profile_rate
        if early is not None:
            out["early_source_checkpoint"] = early.summary()
        if q is not None:
            q.close_entry()
            out["preparation_IO"] = q.summary()
            out["bound_preparation_input_pins"] = list(q.reader.snapshots.values())
        if required is not None and root is not None and body is not None and review_result is not None:
            try:
                if out.get("state") == PASS:
                    validate_document(out, root, body, ROOT_PIN, BODY_PIN, required, review_result)
            except (ValueError, OSError, KeyError, TypeError, AttributeError):
                proposed = None
                out["state"] = "FAILED_NOT_ACCEPTED"
                out["error_code"] = "SOURCE_DOCUMENT_VALIDATION_FAILED"
        p340.m.complete_runtime(out, owner, proposed, lambda doc: validate_document(
            doc, root, body, ROOT_PIN, BODY_PIN, required, review_result) if proposed else None)
        out["metadata_observation"] = p340.g.observation.summary(owner)
        out["source_progress_diagnostics"] = progress.summary()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as stream:
            writer = p340.r.packed.dump if out["state"] == PASS else p340.r.compact.dump
            output = p340.m.PinningOutput(stream)
            writer(out, output, checkpoint=lambda: require(owner.done.is_set(), "TERMINAL_ONLY"), indent=2)
            pin = dict(path=destination.relative_to(root_path).as_posix(),
                       bytes=output.written, sha256=output.digest.hexdigest())
        print(json.dumps({"state": out["state"], "receipt_pin": pin,
                          "error_code": out.get("error_code"),
                          "resource_stop_reason": out.get("resource_stop_reason")}, ensure_ascii=False))
    return 0 if out["state"] == PASS else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, required=True)
    args = parser.parse_args()
    require(type(args.run) is int and 1 <= args.run <= 999, "RUN_RANGE")
    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
