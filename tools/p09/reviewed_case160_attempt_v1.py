"""Reviewed160/run002 identity with the original single physical adapter.

Keep original engine/worker/template code. First run failure stays unaccepted.
"""
from types import FunctionType,SimpleNamespace as NS
import reviewed_case158_attempt_v4 as original

SELF="tools/p09/reviewed_case160_attempt_v1.py"
TEST="tools/p09/tests/test_reviewed_case160_attempt_v1.py"
INDEX=160
PHYSICAL_RUN=2
TASK="case160-current-r002-tests"
ROOT="implementation/p09/evidence/p09-361-case160-current-runtime-run002.v1.json"
STOPPED=dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run001.v1.json",
    bytes=4128024,sha256="5e2af60e8961c16661a25301d462ead53445141ef67bb58ef52f33253a001df0")
REVIEW="implementation/p09/evidence/p09-361-case160-run001-shared-metadata-stop-review-r770.v1.json"
clone=original.clone


def identity(base):
    return clone(original.identity,INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)(base)


def connect_template(window):
    fn=original.prior.connect_template;code=fn.__code__
    original.require(sum(type(x) is int and x==158 for x in code.co_consts)==1,
        "ONE_ORIGINAL_TEMPLATE_CASE_METADATA")
    changed=code.replace(co_consts=tuple(160 if type(x) is int and x==158 else x for x in code.co_consts))
    original.require(changed.replace(co_consts=code.co_consts)==code,"ENTIRE_ORIGINAL_TEMPLATE_METADATA_INVERSE")
    next_fn=FunctionType(changed,dict(fn.__globals__,INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT),
        argdefs=fn.__defaults__,closure=fn.__closure__)
    next_fn.__kwdefaults__=fn.__kwdefaults__
    prior=NS(**{**vars(original.prior),"connect_template":next_fn})
    execute=clone(original.connect_template,prior=prior,identity=identity,INDEX=INDEX,
        PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)
    template,names,proof=execute(window)
    return template,names,dict(proof,explicit_current160_run002_identity=True,
        original_template_metadata_inverse_code_equal=True,
        actual_current160_template_or_product_qualified=False,GO_authorized=False)


def connect_worker(connector,worker,policy):
    return clone(original.prior.connect_worker,TASK=TASK)(connector,worker,policy)


def reviewed_failure(q,a):
    row=a.read_exact(q,STOPPED);review=q.json(REVIEW)
    a.fields(row,dict(state="STOPPED_NOT_ACCEPTED",selected_test_index=160,
        task="case160-current-r001-tests",stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",
        operation_phase="final_source_freeze",cleanup_confirmed=True,owned_tree_empty=True,
        actual_product_child_executed=True,product_body_observed=True,accepted_count_delta=0),
        "EXACT160_FIRST_PRODUCT_CAPTURE_BUT_INCOMPLETE_SOURCE_STOP")
    a.fields(row["source_frame"],dict(frame_state="CLOSED",registered_live_frame=False),
        "FIRST160_CLOSED_NOT_COMMITTED")
    a.exact(len(row["source_frame"]["actual_byte_boundaries"]),1,"FIRST160_ONLY_ONE_WHOLE_BYTE_BOUNDARY")
    a.fields(row["source_frame"]["handles"],dict(input_lock_handles_opened=3114,
        input_lock_handles_closed=3114,input_lock_handles_remaining=0),"FIRST160_ALL_HANDLES_RELEASED")
    a.fields(review,dict(state="REVIEW_ACTUAL160_SHARED_METADATA_DEADLINE_NOT_RUNTIME_OR_ACCEPTANCE_PASS",
        runtime_pin=STOPPED,whole_Runtime_or_two_byte_boundary_qualified=False,
        cleanup_confirmed=True,accepted_count_delta=0,original_metadata_deadline_retained=720,
        original_Native_deadline_retained=600),"EXACT160_PRESERVED_FAILURE_REVIEW")
    return dict(failed_runtime_pin=STOPPED,review_pin=q.snapshots[REVIEW],
        original_failure_promoted=False,queue_acceptance_called=False,
        physical_run002_or_GO_authorized=False)
