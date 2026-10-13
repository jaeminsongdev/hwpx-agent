"""Distinct run003 after both preserved shared720 failures; no auto retry."""
from types import FunctionType,SimpleNamespace as NS
import reviewed_case160_attempt_v1 as original

SELF="tools/p09/reviewed_case160_attempt_v2.py"
TEST="tools/p09/tests/test_reviewed_case160_attempt_v2.py"
INDEX=160
PHYSICAL_RUN=3
TASK="case160-current-r003-tests"
ROOT="implementation/p09/evidence/p09-361-case160-current-runtime-run003.v1.json"
STOPPED={"path":"implementation/p09/evidence/p09-361-case160-current-runtime-run002.v1.json",
    "bytes":4217213,"sha256":"cec8b6269f552bf9c50fc528d85a1a87bd0a188925d82a0cccbcbf43ab7778c5"}
REVIEW="implementation/p09/evidence/p09-361-case160-run002-shared-metadata-stop-review-r810.v1.json"
clone=original.clone

def projected(fn,mapping,**deps):
    code=fn.__code__
    revised=code.replace(co_consts=tuple(mapping.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))
    inverse={v:k for k,v in mapping.items()}
    if revised.replace(co_consts=tuple(inverse.get(x,x) if type(x) in (int,str) else x
            for x in revised.co_consts))!=code:raise ValueError("WHOLE_RUN003_IDENTITY_METADATA_INVERSE")
    result=FunctionType(revised,dict(fn.__globals__,**deps),argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    return result

def identity(base):
    return projected(original.original.identity,{2:3},INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)(base)

def connect_template(window):
    first=original.original.prior
    template=projected(first.connect_template,{158:160,2:3},INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)
    level=NS(**{**vars(original.original),"prior":NS(**{**vars(first),"connect_template":template}),
        "identity":lambda base:identity(base)})
    execute=clone(level.connect_template,prior=level.prior,identity=identity,INDEX=INDEX,
        PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)
    connected,names,proof=execute(window)
    return connected,names,dict(proof,explicit_current160_run003_identity=True,
        original_template_metadata_inverse_code_equal=True,original_single_argument_adapter_not_stacked=True,
        actual_current160_template_or_product_qualified=False,GO_authorized=False)

def connect_worker(connector,worker,policy):
    return clone(original.original.prior.connect_worker,TASK=TASK)(connector,worker,policy)

def reviewed_failure(q,a):
    first=original.reviewed_failure(q,a)
    row=a.read_exact(q,STOPPED);review=q.json(REVIEW)
    a.fields(row,dict(state="STOPPED_NOT_ACCEPTED",selected_test_index=160,task="case160-current-r002-tests",
        stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",operation_phase="final_source_freeze",
        cleanup_confirmed=True,owned_tree_empty=True,actual_product_child_executed=True,
        product_body_observed=True,accepted_count_delta=0),"EXACT_SECOND_PRESERVED160_FAILURE")
    a.fields(row["source_frame"],dict(frame_state="CLOSED",registered_live_frame=False),"SECOND160_NOT_COMMITTED")
    a.exact(len(row["source_frame"]["actual_byte_boundaries"]),1,"SECOND160_ONLY_ONE_COMPLETE_BOUNDARY")
    a.fields(row["source_frame"]["handles"],dict(input_lock_handles_opened=3154,input_lock_handles_closed=3154,
        input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True),"SECOND160_HANDLES_RELEASED")
    a.fields(review,dict(state="REVIEW_ACTUAL160_RUN002_SHARED_METADATA_DEADLINE_NOT_RUNTIME_OR_ACCEPTANCE_PASS",
        runtime_pin=STOPPED,cleanup_confirmed=True,owned_tree_empty=True,accepted_count_after=153,
        accepted_count_delta=0,whole_Runtime_or_two_byte_boundary_qualified=False),"EXACT_SECOND_FAILURE_REVIEW")
    return dict(first_failure=first,second_failed_runtime_pin=dict(STOPPED),second_review_pin=q.snapshots[REVIEW],
        failures_promoted=False,queue_acceptance_called=False,physical_run003_or_GO_authorized=False)
