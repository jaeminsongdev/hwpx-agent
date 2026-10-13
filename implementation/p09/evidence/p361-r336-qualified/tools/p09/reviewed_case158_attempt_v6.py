"""Exact reviewed158/run004; preserve the original single argument adapter."""
from types import FunctionType
import reviewed_case158_attempt_v5 as original

SELF="tools/p09/reviewed_case158_attempt_v6.py"
TEST="tools/p09/tests/test_reviewed_case158_attempt_v6.py"
INDEX=158
PHYSICAL_RUN=4
TASK="case158-current-r004-tests"
ROOT="implementation/p09/evidence/p09-361-case158-current-runtime-run004.v1.json"
FAILED=original.FAILED
STOPPED=original.STOPPED
REVIEW_PATH=original.REVIEW_PATH
STOPPED003=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run003.v1.json",
    bytes=2209026,sha256="e93a86080ad9fce059fe8eba26aa4d0c0f343d0c2530677dd86340d52334e609")
REVIEW003=dict(path="implementation/p09/evidence/p09-361-case158-run003-native-stop-review-code8-r688.v1.json",
    bytes=1260,sha256="ddab10e467cbf260364ac2d4f73517861538f10557bd7b94df27b090d7ed0838")
clone=original.clone
identity=clone(original.identity,PHYSICAL_RUN=4,TASK=TASK,ROOT=ROOT)
connect_worker=clone(original.connect_worker,TASK=TASK)


def connect_template(window18):
    old=original.connect_template;code=old.__code__
    original.require(sum(type(x) is int and x==3 for x in code.co_consts)==1,"ONE_RUN003_PROOF_LITERAL")
    revised=code.replace(co_consts=tuple(4 if type(x) is int and x==3 else x for x in code.co_consts))
    original.require(revised.replace(co_consts=code.co_consts)==code,"ALL_TEMPLATE_CHAIN_CODE_RETAINED")
    fn=FunctionType(revised,dict(old.__globals__,identity=identity,PHYSICAL_RUN=4,TASK=TASK,ROOT=ROOT),
        argdefs=old.__defaults__,closure=old.__closure__)
    return fn(window18)


def reviewed_failure(q,a,review002):
    first=original.reviewed_failure(q,a,review002)
    row=a.read_exact(q,STOPPED003);review=a.read_exact(q,REVIEW003)
    a.fields(row,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r003-tests",selected_test_index=158,
        product_body_observed=False,worker_created=False,source_freeze=[],cleanup_confirmed=True,
        owned_tree_empty=True,accepted_count_delta=0),"REVIEWED003_NO_PRODUCT")
    a.fields(row["source_frame"],dict(frame_state="CLOSED",registered_live_frame=False,actual_byte_boundaries=[]),
        "REVIEWED003_PARTIAL_NATIVE")
    a.fields(review,dict(state="PASS_EXACT158_RUN003_CLOSED_NATIVE_ACQUISITION_STOP_REVIEW_NOT_GO_OR_PRODUCT",
        contracts=dict(run=8,errors=0,failures=0,skipped=0),original_runtime_pin=STOPPED003,
        cleanup_confirmed=True,accepted_count_delta=0),"INDEPENDENT003_STOP_REVIEW")
    for p in review["new_code_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT003_REVIEW_SOURCE")
    return first
