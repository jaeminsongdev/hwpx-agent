"""Pure preserved129 compound contract, never a queue acceptor or Native runner.

실패한 source는 작은 header 검사에서 거절한다. 성공 경로의 전체 Native
oracle/입력/자원 검사는 생략하지 않는다. 원래 실패 root는 그대로 남으며
외부 호출자가 모든 receipt byte를 다시 결속하고 권위 queue를 확인해야 한다.
"""
import json
import math
import re

import close_flat_case129_preserved_source_v1 as source

a, scope = source.a, source.scope
SELF = "tools/p09/validate_flat_case129_compound_v1.py"
TEST = "tools/p09/tests/test_validate_flat_case129_compound_v1.py"
PASS = "PASS_PRESERVED129_COMPOUND_CONTRACT_NOT_FRESH_RECEIPT_BINDING_OR_QUEUE_ACCEPTANCE"
QUAL_PIN = dict(path=source.QUALIFICATION, bytes=5602,
    sha256="dd1229bfb6b438a0ec3be3a798170897f70bad75b26f7bf1ede0c6e57f00997b")


def require(ok, code):
    if not ok:
        raise ValueError("PRESERVED129_COMPOUND_" + code)


def source_header(row):
    """큰 source/root/Native/resource 순회 전에 O(1) header 거절."""
    a.fields(row, dict(schema_version=source.SCHEMA, state=source.PASS,
        accepted_count_after=122, accepted_count_delta=0, product_child_executed=False,
        Native_frame_attempted=True, independent_source_frame_qualified=True,
        original_failed_root_accepted=False, original_product_body_replayed=False,
        independent_compound_acceptance_qualified=False, P09_gate="OPEN", A12_gate="OPEN",
        A13_gate="OPEN", full249_current_qualified=False, signed16_current_qualified=False,
        P10_started=False, PC_freeze_resolved=False, source_frame_cleanup_confirmed=True,
        resource_cleanup_confirmed=True), "COMPOUND_SOURCE_HEADER")
    require(row.get("error_code") is None, "SOURCE_NO_ERROR")
    a.fields(row.get("source_frame"), dict(frame_state="COMMITTED",
        registered_live_frame=False), "COMPOUND_COMMITTED_HEADER")


def source_pin_shape(pin):
    names = scope.pins([pin], 1)
    require(len(names) == 1 and re.fullmatch(
        r"implementation/p09/evidence/p09-361-case129-independent-full-source-run[0-9]{3}\.v1\.json",
        pin["path"]) is not None, "SOURCE_RECEIPT_PATH")
    return pin


def validate(original, original_pin, source_doc, source_pin, authority, authority_pin,
             listing, qualification, qualification_pin, checkpoint):
    """Checks documents only; no files, child, sampler, Native or queue write."""
    require(callable(checkpoint), "ORIGINAL_CHECKPOINT_REQUIRED")
    source_header(source_doc)  # Failed source never reaches full traversal.
    checkpoint()
    source_pin_shape(source_pin)
    a.exact(original_pin, source.STOP_PIN, "COMPOUND_PRESERVED_ROOT")
    a.exact(authority_pin, source.AUTHORITY_PIN, "COMPOUND_PRIOR_AUTHORITY")
    a.exact(qualification_pin, QUAL_PIN, "COMPOUND_SOURCE_CODE_QUALIFICATION")
    a.fields(authority, dict(state=source.runtime.prior.accepted.original.PASS,
        accepted_count_after=122, accepted_count_delta=1, next_runtime_index=129,
        accepted_current_generation_case_count=17), "COMPOUND_CURSOR122")
    a.fields(qualification, dict(
        state="PASS_PRESERVED129_SOURCE_CODE_CONTRACTS_AND_FRESH_BINDING_NOT_NATIVE",
        accepted_count_after=122, accepted_count_delta=0, cleanup_confirmed=True),
        "COMPOUND_SOURCE_CODE_HEADER")
    a.fields(qualification, dict(source_contracts_passed=29, errors=0, failures=0, skipped=0),
        "COMPOUND_SOURCE_CODE29")
    controllers = scope.pins(qualification["source_controller_pins"], 4)
    require(set(controllers) == {source.SELF, source.TEST,
        source.completed.SELF, source.completed.TEST}, "ALL_FOUR_QUALIFIED_CONTROLLERS")
    proof = source.completed.review(original, original_pin,
        case=source.CASE, index=129, prior_count=122)
    source.runtime.actual_source_binding(original)
    a.exact(source_doc["completed_child_review"], proof, "COMPOUND_UNCHANGED_BODY_REVIEW")
    for key, expected in (("original_stopped_runtime_pin", original_pin),
            ("prior_queue_authority_pin", authority_pin), ("body_review_pin", source.REVIEW_PIN),
            ("source_qualification_pin", qualification_pin)):
        a.exact(source_doc[key], expected, "COMPOUND_RECEIPT_BINDING")
    old = scope.pins(original["source_freeze"])
    required = scope.pins(source_doc["required_source_pins"])
    require(all(required.get(name) == pin for name, pin in old.items()),
        "EVERY_ORIGINAL_INPUT_RETAINED")
    for pin in (original_pin, authority_pin, source.REVIEW_PIN, qualification_pin,
                *controllers.values()):
        a.exact(required.get(pin["path"]), pin, "COMPOUND_REQUIRED_CONTROLLER_OR_RECEIPT")
    current = scope.listing_inputs(listing)
    require(all(required.get(name) == old.get(name) == pin
        for name, pin in current.items()), "ALL_CURRENT_COMPILED_INPUTS_UNCHANGED")
    a.exact(listing["source_test_names"][128], source.CASE, "COMPOUND_EXACT129")
    imports = source_doc["imported_controller_paths"]
    require(type(imports) is list and 0 < len(imports) <= 64 and
        all(type(name) is str and name.startswith("tools/p09/") and
            name.endswith(".py") and name in required for name in imports) and
        imports == sorted(set(imports)), "COMPLETE_IMPORTED_SOURCE")
    checkpoint()
    oracle = source.validate_frame(source_doc["source_frame"], required,
        source_doc["source_path_guard_diagnostics"], checkpoint)
    a.exact(source_doc["validation"], oracle, "COMPOUND_ORIGINAL_FULL_NATIVE_ORACLE")
    a.exact(source_doc["source_budget"], source.source_budget(required),
        "COMPOUND_UNCHANGED_COMPLETE_COST")
    inventories = source_doc["Rust_inventory_observations"]
    require(type(inventories) is list and len(inventories) == 2, "TWO_RUST_INVENTORIES")
    for row in inventories:
        a.fields(row, dict(request_limit_per_second=20, requests=167,
            requests_skipped=False, cleanup_paced=False), "COMPOUND_WHOLE_RUST")
    elapsed = source_doc["elapsed_seconds"]
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and
        0 < elapsed <= 600, "ORIGINAL600_SOURCE_DEADLINE")
    # 모든 원본 표본을 원래 결정 함수로 검사한다. hot 연속성은 group 사이에도 유지.
    hot = a.resource_history(original["samples"])
    post_cleanup = original["post_Job_cleanup_resource_samples"]
    require(type(post_cleanup) is list and len(post_cleanup) <= 4096,
        "PRESERVED_POST_CLEANUP_HISTORY_SHAPE")
    # 원 STOP에는 빈 후정리 group이 있을 수 있다. 관측을 만들어 채우지 않는다.
    # 모든 존재하는 표본은 그대로 검사하며, 새 source의 final 표본으로 대체하지 않는다.
    if post_cleanup:
        a.resource_history(post_cleanup, hot)
    a.resource_history(source_doc["resource_samples"])
    a.exact(source_doc["CPU_max"], max(x["system_cpu_percent"]
        for x in source_doc["resource_samples"]), "COMPOUND_ACTUAL_CPU_MAX")
    a.exact(source_doc["RAM_min"], min(x["available_ram_percent"]
        for x in source_doc["resource_samples"]), "COMPOUND_ACTUAL_RAM_MIN")
    checkpoint()
    return dict(state=PASS, selected_test_index=129, selected_test_name=source.CASE,
        product_root_pin=original_pin, complete_source_receipt_pin=source_pin,
        prior_authority_pin=authority_pin, original_failed_receipt_preserved=True,
        original_failed_frame_promoted_to_PASS=False, two_distinct_epochs_not_same_frame=True,
        successful_product_body_replayed=False, whole_source_inputs=len(required),
        whole_source_bytes=sum(pin["bytes"] for pin in required.values()),
        original_body_postcleanup_resource_sample_count=len(post_cleanup),
        original_body_postcleanup_sample_synthesized_or_replaced=False,
        accepted_count_after=122, accepted_count_delta=0, queue_cursor_advanced=False,
        current_receipt_bytes_rebound_by_this_contract=False,
        live_authoritative_queue_scanned_by_this_contract=False,
        independent_compound_acceptance_qualified=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", P10_started=False)


def review_acquisition_stop(row, pin, checkpoint):
    """Bounded failed-source review. No copying/printing whole pins or histories."""
    require(callable(checkpoint), "ORIGINAL_CHECKPOINT_REQUIRED")
    source_pin_shape(pin)
    a.fields(row, dict(schema_version=source.SCHEMA, state="FAILED_NOT_QUALIFIED",
        error_code="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION", accepted_count_after=122,
        accepted_count_delta=0, product_child_executed=False, Native_frame_attempted=True,
        independent_source_frame_qualified=False, original_failed_root_accepted=False,
        original_product_body_replayed=False, independent_compound_acceptance_qualified=False,
        source_frame_cleanup_confirmed=True, resource_cleanup_confirmed=True,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", P10_started=False),
        "FAILED_SOURCE_REMAINS_FAILED")
    frame = row["source_frame"]
    a.fields(frame, dict(frame_state="CLOSED", registered_live_frame=False,
        actual_byte_boundaries=[]), "STOP_BEFORE_ANY_BYTE_BOUNDARY")
    handles = frame["handles"]
    a.fields(handles, dict(input_lock_cleanup_confirmed=True, input_lock_handles_remaining=0,
        handle_close_failed_attempts=0, active_reader_bindings=0, active_byte_streams=0,
        byte_stream_identity_checks=0, maximum_lock_seconds=600, borrowed_byte_streams=None),
        "STOP_ALL_NATIVE_HANDLES_CLOSED")
    opened, closed = handles["input_lock_handles_opened"], handles["input_lock_handles_closed"]
    require(type(opened) is int and type(closed) is int and opened > 0 and opened == closed,
        "ALL_OPENED_HANDLES_CLOSED")
    a.fields(handles["one_way_native_saturation_circuit_breaker"], dict(saturation_seen=True,
        opens_resume_after_cooldown=False, native_open_or_identity_checks_skipped_for_success=False,
        policy_stop_code="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION"), "ONE_WAY_STOP")
    samples = row["resource_samples"]
    require(type(samples) is list and 0 < len(samples) <= 4096, "RESOURCE_HISTORY")
    count = 0; peak = None; minimum = 100; tail = []
    for sample in samples:
        if count % 64 == 0:
            checkpoint()
        cpu, ram = sample.get("system_cpu_percent"), sample.get("available_ram_percent")
        require(all(type(value) in (int, float) and math.isfinite(value) and
            0 <= value <= 100 for value in (cpu, ram)), "ALL_RESOURCE_VALUES")
        # 닫힌 allowlist: 추가 payload, 경로, process command를 복사하지 않는다.
        safe = {key: sample[key] for key in ("system_cpu_percent", "available_ram_percent",
            "commit_used_percent", "parent_cpu_machine_percent", "parent_private_mib")
            if key in sample}
        require(all(value is None or (type(value) in (int, float) and
            math.isfinite(value) and value >= 0) for value in safe.values()),
            "CLOSED_NUMERIC_RESOURCE_FIELDS")
        count += 1; minimum = min(minimum, ram)
        if peak is None or cpu > peak["system_cpu_percent"]:
            peak = safe
        tail.append(safe)
        if len(tail) > 4:
            del tail[0]
    require(peak["system_cpu_percent"] >= 90, "ORIGINAL_WARNING_OBSERVED")
    result = dict(state="PASS_SOURCE_ACQUISITION_STOP_REVIEW_NOT_SOURCE_OR_QUEUE_ACCEPTANCE",
        source_receipt_pin=pin, original_failure_state_preserved=True,
        stopped_before_source_byte_reads=True, opened_and_closed_handles=opened,
        resource_sample_count=count, peak_resource_sample=peak, available_RAM_min_percent=minimum,
        resource_tail=tail, successful_product_body_replayed=False,
        accepted_count_after=122, accepted_count_delta=0, independent_source_frame_qualified=False,
        causal_trigger_or_CPU_freeze_fix_established=False,
        complete_source_pins_or_resources_or_logs_printed=False)
    require(len(json.dumps(result).encode("utf-8")) <= 4096, "CLOSED_OUTPUT_LIMIT")
    return result
