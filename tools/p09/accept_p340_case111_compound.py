"""Link the already-passed P340 case111 child to a future full source frame.

This is a pure candidate contract only: it never reads/writes receipts, runs a
child, or advances the queue. A caller must supply receipt documents and pin
snapshots from the same MetadataReader, plus a freshly scanned P340 plan. This
helper does not itself prove those byte reads or the live queue scan.
"""
from __future__ import annotations

import re
import review_p340_post_product_stop as review
import close_p340_post_product_source_frame as source


SCHEMA = "hwpx-agent.p09-case111-product-source-compound-candidate/v1"
PASS = "PASS_CASE111_COMPOUND_EVIDENCE_NOT_QUEUE_ACCEPTANCE"
PRODUCT_REVIEW_PASS = "PASS_CASE111_SEMANTIC_BODY_REVIEW_NOT_SOURCE_OR_QUEUE"
CIRCUIT_BREAKER_STOP = "STOP_NATIVE_OPEN_AFTER_HOST_SATURATION"
CLOSED_PHASE092_PIN = dict(path=source.SOURCE_DIR + "/p340-post-stop-source-run092.v1.json",
    bytes=28481,sha256="a7166c49ee2aa23957fce0e0662d45e2673bbf36d214b85f19aafb66c2220ee8")
CLOSED_PHASE092_CODE = (
    dict(path=source.SELF,bytes=33615,sha256="059420df91b78d2c36a52f1bef920437c8ba08d9d825e0d6f408cc692185292d"),
    dict(path=source.TEST,bytes=24008,sha256="13db00e55464c13a667ee9d7d713055c408df605d8952a923b3b4bef15132060"))
PRODUCT_ROOT_PATH = review.ROOT_RECEIPT
PRODUCT_BODY_PATH = review.SIDECAR_RECEIPT
PRODUCT_PLACEHOLDER_PATH = review.CASE_RECEIPT
EMPTY_RECEIPT_PIN = dict(path=PRODUCT_PLACEHOLDER_PATH, bytes=0,
                         sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")


def require(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("P340_CASE111_COMPOUND_" + code)


def review_product_candidate(product_root, product_body, root_pin, body_pin,
                             placeholder_pin, supplied_current_plan):
    """Review the preserved child sidecar and its untouched zero-byte placeholder."""
    product_review = review.validate(product_root, product_body, body_pin)
    require(root_pin == source.ROOT_PIN and body_pin == source.BODY_PIN,
            "EXACT_PRESERVED_PRODUCT_RECEIPT_PINS")
    require(placeholder_pin == EMPTY_RECEIPT_PIN,
            "ORIGINAL_ZERO_PLACEHOLDER_REMAINS_UNTOUCHED")
    require(product_root["prior_runtime_plan"] == supplied_current_plan
            and supplied_current_plan["runtime_source_qualified_individual_cases"] == 104
            and supplied_current_plan["next_runtime_index"] == 111
            and product_root["selected_test_index"] == 111
            and product_root["selected_test_name"] == review.TEST_NAME
            and product_root["current95_code_pins"]
                and product_root["actual_product_child_executed"] is False
            and product_body["actual_product_child_executed"] is True
            and product_root["source_qualified"] is False
            and product_root["P09_gate"] == product_root["A12_gate"] ==
                product_root["A13_gate"] == "OPEN",
            "LIVE_104_TO_111_PRODUCT_CANDIDATE_NOT_ACCEPTED_ROOT")
    return dict(schema_version=SCHEMA, state=PRODUCT_REVIEW_PASS,
        product_root_pin=root_pin, product_sidecar_pin=body_pin,
        product_placeholder_pin=placeholder_pin,
        source_review=product_review,
        semantic_body_capture_complete=True,
        current_plan_matches_preserved_product_root=True,
        runtime_acceptance_changed=False, accepted_count_delta=0,
        queue_cursor_advanced=False, P09_gate="OPEN", A12_gate="OPEN",
        A13_gate="OPEN", product_complete=False)


def validate(product_root, product_body, root_pin, body_pin, source_doc,
             source_pin, required, supplied_current_plan):
    """Verify exact child PASS + completed source frame without queue promotion."""
    placeholder = EMPTY_RECEIPT_PIN
    product_review = review_product_candidate(product_root, product_body,
        root_pin, body_pin, placeholder, supplied_current_plan)["source_review"]
    require(type(source_pin) is dict and set(source_pin) == {"path", "bytes", "sha256"}
            and type(source_pin["bytes"]) is int and source_pin["bytes"] > 0
            and re.fullmatch(r"[0-9a-f]{64}", source_pin["sha256"]) is not None
            and re.fullmatch(re.escape(source.SOURCE_DIR) +
                r"/p340-post-stop-source-run[0-9]{3}\.v1\.json", source_pin["path"]) is not None,
            "EXACT_SOURCE_RECEIPT_PIN_SHAPE")
    require(product_root["prior_runtime_plan"] == supplied_current_plan
            and supplied_current_plan["runtime_source_qualified_individual_cases"] == 104
            and supplied_current_plan["next_runtime_index"] == 111
            and product_root["selected_test_index"] == 111
            and product_root["selected_test_name"] == review.TEST_NAME,
            "FRESH_CURRENT_CURSOR_STILL_CASE111")
    source.validate_document(source_doc, product_root, product_body,
        root_pin, body_pin, required, product_review)
    require(source_doc["state"] == source.PASS
            and source_doc["independent_source_frame_qualified"] is True
            and source_doc["source_frame"]["frame_state"] == "COMMITTED"
            and source_doc["actual_product_child_executed"] is False
            and source_doc["runtime_acceptance_changed"] is False
            and source_doc["accepted_count_delta"] == 0,
            "COMPLETED_SOURCE_ONLY_NO_REPLAY_OR_ACCEPTANCE")
    return dict(schema_version=SCHEMA, state=PASS,
        product_root_pin=root_pin, product_sidecar_pin=body_pin,
        source_receipt_pin=source_pin,
        source_review=product_review,
        source_frame_pin_set_count=len(required),
        selected_test_index=111, selected_test_name=review.TEST_NAME,
        supplied_plan_matches_product_run_plan=True,
        live_current_queue_verified_by_this_contract=False,
        receipt_bytes_rebound_by_this_contract=False,
        original_product_child_replayed=False,
        completed_source_frame_reused=True,
        accepted_count_delta=0, runtime_acceptance_changed=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN",
        product_complete=False, P10_started=False,
        queue_cursor_advanced=False,
        acceptance_requires_separate_authoritative_queue_integration=True)


def validate_from_reader(reader, source_path, required, supplied_current_plan):
    """Bind all three receipts through one P340 MetadataReader before review.

    This proves only same-reader receipt binding. The caller must finish that
    reader's fresh pass and must still obtain the plan from the authoritative
    P340 scanner; this helper does neither and never advances the queue.
    """
    require(callable(getattr(reader, "json", None)), "METADATA_READER_REQUIRED")
    root = reader.json(PRODUCT_ROOT_PATH)
    body = reader.json(PRODUCT_BODY_PATH)
    source_doc = reader.json(source_path)
    snapshots = getattr(getattr(reader, "reader", None), "snapshots", None)
    require(type(snapshots) is dict, "METADATA_READER_SNAPSHOTS_REQUIRED")
    root_pin = snapshots.get(PRODUCT_ROOT_PATH)
    body_pin = snapshots.get(PRODUCT_BODY_PATH)
    source_pin = snapshots.get(source_path)
    require(type(root_pin) is dict and root_pin.get("path") == PRODUCT_ROOT_PATH
            and type(body_pin) is dict and body_pin.get("path") == PRODUCT_BODY_PATH
            and type(source_pin) is dict and source_pin.get("path") == source_path,
            "ALL_RECEIPTS_BOUND_BY_SAME_READER")
    pin_method = getattr(reader, "pin", None)
    require(callable(pin_method), "PLACEHOLDER_PIN_READER_REQUIRED")
    placeholder_pin = pin_method(PRODUCT_PLACEHOLDER_PATH)
    require(placeholder_pin == EMPTY_RECEIPT_PIN
            and snapshots.get(PRODUCT_PLACEHOLDER_PATH) == EMPTY_RECEIPT_PIN,
            "ORIGINAL_ZERO_PLACEHOLDER_REMAINS_UNTOUCHED")
    result = validate(root, body, root_pin, body_pin, source_doc,
                      source_pin, required, supplied_current_plan)
    result.update(receipt_bytes_rebound_by_this_contract=True,
                  product_placeholder_pin=placeholder_pin,
                  all_receipt_bytes_bound_to_same_reader=True,
                  final_reader_freshness_completed_by_this_contract=False)
    return result


def validate_failed_source_receipt(source_doc, source_pin):
    """Keep a stopped source attempt visible but categorically non-accepting."""
    require(type(source_pin) is dict and set(source_pin) == {"path", "bytes", "sha256"}
            and re.fullmatch(re.escape(source.SOURCE_DIR) +
                r"/p340-post-stop-source-run[0-9]{3}\.v1\.json", source_pin["path"]) is not None
            and type(source_pin["bytes"]) is int and source_pin["bytes"] > 0
            and re.fullmatch(r"[0-9a-f]{64}", source_pin["sha256"]) is not None,
            "FAILED_SOURCE_RECEIPT_PIN_SHAPE")
    reason = source_doc.get("resource_stop_reason")
    error = source_doc.get("error_code")
    failure = source_doc.get("failure_diagnostic")
    source_frame = source_doc.get("source_frame")
    handles = source_frame.get("handles") if type(source_frame) is dict else None
    breaker = handles.get("one_way_native_saturation_circuit_breaker") if type(handles) is dict else None
    breaker_summary_confirmed = (
        type(source_frame) is dict and source_frame.get("frame_state") == "CLOSED"
        and source_frame.get("registered_live_frame") is False
        and type(handles) is dict
        and type(handles.get("input_lock_handles_remaining")) is int
        and handles.get("input_lock_handles_remaining") == 0
        and handles.get("input_lock_cleanup_confirmed") is True
        and type(handles.get("active_reader_bindings")) is int
        and handles.get("active_reader_bindings") == 0
        and type(handles.get("active_byte_streams")) is int
        and handles.get("active_byte_streams") == 0
        and type(breaker) is dict
        and breaker.get("one_way_circuit_breaker") is True
        and breaker.get("saturation_seen") is True
        and breaker.get("opens_resume_after_cooldown") is False
        and breaker.get("original_checkpoint_and_resource_guards_run_before_unlatched_reservations") is True
        and breaker.get("latched_warning_preempts_next_resource_checkpoint") is True
        and breaker.get("native_open_or_identity_checks_skipped_for_success") is False
        and breaker.get("policy_stop_code") == CIRCUIT_BREAKER_STOP)
    resource_stop = (reason is not None and reason != CIRCUIT_BREAKER_STOP and error == reason)
    policy_stop = (reason is None and error == CIRCUIT_BREAKER_STOP
                   and type(failure) is dict and failure.get("stage") == "source_frame_acquire"
                   and breaker_summary_confirmed)
    # 실패한 조기 drift 검사는 보존하되 source/제품 PASS나 cursor 전진을 만들지 않는다.
    drift_stop = (reason is None and error == source.DRIFT_ERROR
                  and type(failure) is dict and failure.get("stage") == "frozen_mutable_input_preflight"
                  and source_frame is None
                  and source_doc.get("independent_source_frame_attempted") is False
                  and source.validate_drift_preflight(source_doc))
    archived_resource_stop = (source_doc.get("schema_version") == source.ARCHIVED_SCHEMA
        and resource_stop and type(failure) is dict and failure.get("stage") in (
            "admission", "archived_source_preflight", "source_frame_acquire",
            "metadata_hash", "final_fresh_hash", "source_commit")
        and (source_frame is None or (type(source_frame) is dict
            and source_frame.get("frame_state") == "CLOSED"
            and source_frame.get("registered_live_frame") is False
            and type(handles) is dict and handles.get("input_lock_handles_remaining") == 0
            and handles.get("input_lock_cleanup_confirmed") is True)))
    timing = handles.get("lock_timing_diagnostic") if type(handles) is dict else None
    first_error = timing.get("first_original_error") if type(timing) is dict else None
    deadline_stop = (source_doc.get("schema_version") == source.ARCHIVED_SCHEMA
        and reason is None and error == "P206_LOCK_DEADLINE_EXCEEDED"
        and type(failure) is dict and failure.get("stage") in (
            "source_frame_acquire", "metadata_hash", "final_fresh_hash", "source_commit")
        and type(source_frame) is dict and source_frame.get("frame_state") == "CLOSED"
        and source_frame.get("registered_live_frame") is False
        and type(handles) is dict and handles.get("maximum_lock_seconds") == 600
        and type(handles.get("input_lock_handles_remaining")) is int
        and handles["input_lock_handles_remaining"] == 0
        and handles.get("input_lock_cleanup_confirmed") is True
        and type(handles.get("active_reader_bindings")) is int and handles["active_reader_bindings"] == 0
        and type(handles.get("active_byte_streams")) is int and handles["active_byte_streams"] == 0
        and type(timing) is dict and timing.get("original_lock_limit_seconds") == 600
        and timing.get("original_check_invoked_without_replacement") is True
        and timing.get("original_resource_guard_or_deadline_extended") is False
        and type(first_error) is dict and first_error.get("original_error_code") == error
        and first_error.get("original_lock_limit_seconds") == 600
        and type(first_error.get("original_lock_elapsed_seconds")) in (int,float)
        and 600 < first_error["original_lock_elapsed_seconds"] < float("inf"))
    bound_pins = source_doc.get("bound_preparation_input_pins")
    phase_binding_stop = (source_pin == CLOSED_PHASE092_PIN
        and source_doc.get("schema_version") == source.ARCHIVED_SCHEMA
        and reason is None and error == "P193_CLOSED_PHASE"
        and type(failure) is dict and failure.get("stage") == "source_frame_acquire"
        and type(bound_pins) is list and all(pin in bound_pins for pin in CLOSED_PHASE092_CODE)
        and source_doc.get("source_closing_contract_tests_passed") == 44
        and source_doc.get("preparation_IO",{}).get("finished") is True
        and type(source_frame) is dict and source_frame.get("frame_state") == "CLOSED"
        and source_frame.get("registered_live_frame") is False
        and source_frame.get("actual_byte_boundaries") == []
        and type(handles) is dict and handles.get("input_lock_cleanup_confirmed") is True
        and all(type(handles.get(key)) is int and handles[key] == 0 for key in (
            "input_lock_handles_opened", "input_lock_handles_closed", "input_lock_handles_remaining",
            "active_reader_bindings", "active_byte_streams", "byte_stream_identity_checks"))
        and handles.get("native_open_pacing",{}).get("open_reservations") == 0)
    require(source_doc.get("schema_version") in (source.SCHEMA, source.ARCHIVED_SCHEMA)
            and source_doc.get("state") == "FAILED_NOT_ACCEPTED"
            and (resource_stop or policy_stop or drift_stop or deadline_stop or phase_binding_stop)
            and source_doc.get("resource_watcher_cleanup_confirmed") is True
            and type(failure) is dict and (archived_resource_stop or deadline_stop or failure.get("stage") in (
                ("frozen_mutable_input_preflight",) if drift_stop else ("source_frame_acquire",)))
            and source_doc.get("actual_product_child_executed") is False
            and source_doc.get("runtime_acceptance_changed") is False
            and source_doc.get("accepted_count_delta") == 0
            and source_doc.get("independent_source_frame_qualified") is False
            and source_doc.get("P09_gate") == source_doc.get("A12_gate") ==
                source_doc.get("A13_gate") == "OPEN",
            "FAILED_SOURCE_MUST_REMAIN_UNACCEPTED")
    return dict(state="FAILED_SOURCE_RETAINED_NOT_ACCEPTED",
        source_receipt_pin=source_pin,
        resource_stop_reason=reason,error_code=error,
        stop_classification=("FROZEN_INPUT_DRIFT_BEFORE_NATIVE" if drift_stop else
            "POLICY_CIRCUIT_BREAKER" if policy_stop else
            "ORIGINAL_LOCK_DEADLINE" if deadline_stop else
            "EXACT_LOCAL_PHASE_BINDING_FAILURE" if phase_binding_stop else "RESOURCE_GUARD"),
        accepted_count_delta=0, queue_cursor_advanced=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN")
