"""Exact incomplete run003 evidence review; never an accepted runtime."""
SELF="tools/p09/review_failed_run003_v1.py"
TEST="tools/p09/tests/test_review_failed_run003_v1.py"
ROOT=dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run003.v1.json",
    bytes=4242304,sha256="61b51f2bd10ea9a9a6f4bda94b8863eec90e73550038147c0e8652fb2790feb9")
STATE="REVIEW_ACTUAL160_RUN003_SHARED_METADATA_DEADLINE_NOT_RUNTIME_OR_ACCEPTANCE_PASS"

def review(row,a):
    a.fields(row,dict(state="STOPPED_NOT_ACCEPTED",selected_test_index=160,task="case160-current-r003-tests",
        stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",operation_phase="final_source_freeze",
        cleanup_confirmed=True,owned_tree_empty=True,actual_product_child_executed=True,
        product_body_observed=True,accepted_count_delta=0,Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False),"EXACT_THIRD_PRESERVED160_FAILURE")
    frame=row["source_frame"]
    a.fields(frame,dict(frame_state="CLOSED",registered_live_frame=False,input_count=2801,input_bytes=247714063),
        "THIRD160_CLOSED_NOT_COMMITTED")
    boundaries=frame["actual_byte_boundaries"]
    a.require(type(boundaries) is list and len(boundaries)==1,"THIRD160_ONLY_ONE_COMPLETE_BOUNDARY")
    before=boundaries[0];a.fields(before,dict(role="before"),"THIRD160_ONLY_BEFORE_BOUNDARY")
    scope=a.scope.pins(row["source_freeze"],2801)
    a.exact(a.scope.pins(before["actual_byte_pins"],2801),scope,"THIRD160_COMPLETE_FIRST_BYTE_PINS")
    a.exact(sum(p["bytes"] for p in scope.values()),247714063,"THIRD160_PHYSICAL_BYTE_ACCOUNTING")
    a.fields(before["reader_diagnostics"],dict(read_passes=2801,bytes_read=247714063),"THIRD160_FIRST_ACTUAL_BYTE_COUNTS")
    handles=frame["handles"]
    a.fields(handles,dict(input_lock_handles_opened=3173,input_lock_handles_closed=3173,input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,active_reader_bindings=0,active_byte_streams=0,
        maximum_lock_seconds=600,byte_stream_identity_checks=5589),"THIRD160_HANDLES_RELEASED_PARTIAL_SECOND_READ")
    a.fields(handles["borrowed_byte_streams"],dict(logical_views_opened=5589,logical_views_closed=5589,
        logical_views_remaining=0,logical_view_close_failed_attempts=0,active_borrow_binding=False),"THIRD160_BORROWED_VIEWS_RELEASED")
    a.fields(row["aggregate_envelope_decoder"],dict(aggregate_limit_seconds=5.0,attempted_decodes=44,completed_decodes=44,
        active_decode=False,terminal_error_seen=False,two_boundaries_share_one_budget=True),"THIRD160_PARTIAL_DECODER_NOT58_PASS")
    return dict(state=STATE,runtime_pin=dict(ROOT),cleanup_confirmed=True,owned_tree_empty=True,
        accepted_count_after=153,accepted_count_delta=0,complete_byte_boundaries=1,
        partial_second_byte_identity_checks=2788,decoder_completed=44,handles_closed=3173,
        whole_Runtime_or_two_byte_boundary_qualified=False,original_failure_promoted=False,
        retry_or_GO_authorized=False,queue_acceptance_called=False)
