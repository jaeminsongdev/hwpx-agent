"""Distinct run004 identity after exact preserved run003 review; not GO."""
from types import SimpleNamespace as NS
import reviewed_case160_attempt_v2 as original
import review_failed_run003_v1 as third
SELF="tools/p09/reviewed_case160_attempt_v3.py"
TEST="tools/p09/tests/test_reviewed_case160_attempt_v3.py"
INDEX=160
PHYSICAL_RUN=4
TASK="case160-current-r004-tests"
ROOT="implementation/p09/evidence/p09-361-case160-current-runtime-run004.v1.json"
STOPPED=third.ROOT
REVIEW="implementation/p09/evidence/p09-361-case160-run003-shared-metadata-stop-review-r843.v1.json"
clone=original.clone

def identity(base):
    return original.projected(original.original.original.identity,{2:4},
        INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)(base)

def connect_template(window):
    first=original.original.original.prior
    template=original.projected(first.connect_template,{158:160,2:4},
        INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)
    level=NS(**{**vars(original.original.original),"prior":NS(**{**vars(first),"connect_template":template}),
        "identity":lambda base:identity(base)})
    execute=clone(level.connect_template,prior=level.prior,identity=identity,
        INDEX=INDEX,PHYSICAL_RUN=PHYSICAL_RUN,TASK=TASK,ROOT=ROOT)
    connected,names,proof=execute(window)
    return connected,names,dict(proof,explicit_current160_run004_identity=True,
        original_template_metadata_inverse_code_equal=True,original_single_argument_adapter_not_stacked=True,
        actual_current160_template_or_product_qualified=False,GO_authorized=False)

def connect_worker(connector,worker,policy):
    return clone(original.original.original.prior.connect_worker,TASK=TASK)(connector,worker,policy)

def reviewed_failure(q,a):
    first_two=original.reviewed_failure(q,a)
    row=a.read_exact(q,STOPPED);expected=third.review(row,a);review=q.json(REVIEW)
    a.fields(review,expected,"EXACT_THIRD_WHOLE_FAILURE_REVIEW")
    a.fields(review,dict(contracts=dict(run=10,errors=0,failures=0,skipped=0),fresh_inputs=4,
        final_fresh_hashes=4,actual_product_or_Native_reexecuted=False),"THIRD_CODE10_AND_ALL_FINAL_HASHES")
    for pin in review["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_THIRD_REVIEW_SOURCES")
    return dict(first_two_failures=first_two,third_failed_runtime_pin=dict(STOPPED),third_review_pin=q.snapshots[REVIEW],
        failures_promoted=False,queue_acceptance_called=False,physical_run004_or_GO_authorized=False)
