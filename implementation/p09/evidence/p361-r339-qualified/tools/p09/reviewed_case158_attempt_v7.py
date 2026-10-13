"""Exact reviewed158/run005; preserve all original single-adapter code."""
from types import FunctionType
import reviewed_case158_attempt_v6 as original

SELF="tools/p09/reviewed_case158_attempt_v7.py"
TEST="tools/p09/tests/test_reviewed_case158_attempt_v7.py"
INDEX=158
PHYSICAL_RUN=5
TASK="case158-current-r005-tests"
ROOT="implementation/p09/evidence/p09-361-case158-current-runtime-run005.v1.json"
FAILED=original.FAILED
STOPPED=original.STOPPED
REVIEW_PATH=original.REVIEW_PATH
STOPPED004=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run004.v1.json",
    bytes=2287363,sha256="7adefac75a0c1755ea4761144dfed48df3ffae90622de601b2ccfc9cc3e48329")
REVIEW004=dict(path="implementation/p09/evidence/p09-361-case158-run004-native-stop-review-code8-r703.v1.json",
    bytes=1263,sha256="82e0f6108f14e76096b4a52669c0340d29f1fa1075e1ff5a728db5db3d5df5f8")
clone=original.clone
identity=clone(original.identity,PHYSICAL_RUN=5,TASK=TASK,ROOT=ROOT)
connect_worker=clone(original.connect_worker,TASK=TASK)


def connect_template(window18):
    old=original.connect_template;code=old.__code__
    original.original.require(sum(type(x) is int and x==4 for x in code.co_consts)==1,"ONE_RUN004_PROOF_LITERAL")
    revised=code.replace(co_consts=tuple(5 if type(x) is int and x==4 else x for x in code.co_consts))
    original.original.require(revised.replace(co_consts=code.co_consts)==code,"ALL_TEMPLATE_CHAIN_CODE_RETAINED")
    fn=FunctionType(revised,dict(old.__globals__,identity=identity,PHYSICAL_RUN=5,TASK=TASK,ROOT=ROOT),
        argdefs=old.__defaults__,closure=old.__closure__)
    return fn(window18)


def reviewed_failure(q,a,review002):
    first=original.reviewed_failure(q,a,review002)
    row=a.read_exact(q,STOPPED004);review=a.read_exact(q,REVIEW004)
    a.fields(row,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r004-tests",selected_test_index=158,
        product_body_observed=False,actual_product_child_executed=False,worker_created=False,job_assigned=False,
        source_freeze=[],cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"REVIEWED004_NO_PRODUCT")
    a.fields(row["source_frame"],dict(frame_state="CLOSED",registered_live_frame=False,actual_byte_boundaries=[]),
        "REVIEWED004_PARTIAL_NATIVE")
    a.fields(review,dict(state="PASS_EXACT158_RUN004_CLOSED_NATIVE_ACQUISITION_STOP_REVIEW_NOT_GO_OR_PRODUCT",
        contracts=dict(run=8,errors=0,failures=0,skipped=0),original_runtime_pin=STOPPED004,
        cleanup_confirmed=True,accepted_count_delta=0),"INDEPENDENT004_STOP_REVIEW")
    a.fields(review["actual_stop_review"],dict(opened=1281,closed=1281,remaining=0,
        actual_byte_boundaries=0,source_frame_committed=False,automatic_retry_or_GO_authorized=False),
        "EXACT004_HANDLE_RELEASE_NOT_COMMITTED")
    for p in review["new_code_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT004_REVIEW_SOURCE")
    return first
