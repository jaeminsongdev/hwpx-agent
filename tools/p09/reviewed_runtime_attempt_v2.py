"""Explicit reviewed154/run002; prior153 and qualified run1 untouched."""
from types import FunctionType
import reviewed_runtime_attempt_v1 as prior

SELF="tools/p09/reviewed_runtime_attempt_v2.py"
TEST="tools/p09/tests/test_reviewed_runtime_attempt_v2.py"
STOPPED=prior.STOPPED
REVIEW=prior.REVIEW
NEW_STOPPED={"path":"implementation/p09/evidence/p09-361-case154-current-runtime-run001.v1.json","bytes":315805,"sha256":"03cc100b7102e29baea8980fd2872adaa2fc2d0cea01b03aa7635c6bbd852a31"}
NEW_REVIEW={"path":"implementation/p09/evidence/p09-361-case154-metadata-cpu-stop-review-r528.v1.json","bytes":3492,"sha256":"4caa0e20cc2938340c4999e9b19b19ffec175d79f47d32960c4a881c5125bb9c"}
HISTORY=[STOPPED,REVIEW,NEW_STOPPED,NEW_REVIEW]

def require(ok,code):
    if not ok:raise ValueError("REVIEWED_PHYSICAL_ATTEMPT_V2_"+code)

def physical_run(index):
    prior.physical_run(index)
    return 2 if index in (153,154) else 1

def bound(fn):
    return FunctionType(fn.__code__,dict(fn.__globals__,physical_run=physical_run),
      argdefs=fn.__defaults__,closure=fn.__closure__)

root_path=bound(prior.root_path)
task=bound(prior.task)
public_run=bound(prior.public_run)
connect_engine=bound(prior.connect_engine)
validate_actual=FunctionType(prior.validate_actual.__code__,
  dict(prior.validate_actual.__globals__,physical_run=physical_run,root_path=root_path,task=task),
  argdefs=prior.validate_actual.__defaults__,closure=prior.validate_actual.__closure__)

def reviewed_failure(q,read_exact,fields):
    prior.reviewed_failure(q,read_exact,fields)
    row=read_exact(q,NEW_STOPPED)
    fields(row,dict(state="DEFERRED_NOT_STARTED",task="case154-current-r001-tests",
      selected_test_index=154,stop_reason="STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",
      product_body_observed=False,worker_created=False,Native_source_frame_qualified=False,
      source_frame=None,cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"REVIEWED154_NO_NATIVE_OR_PRODUCT")
    review=read_exact(q,NEW_REVIEW)
    fields(review,dict(state="REVIEWED154_METADATA_CPU_WARNING_BEFORE_NATIVE_OR_PRODUCT",
      original_runtime_pin=NEW_STOPPED,original_runtime_preserved=True,stopped154_retried=False,
      accepted_count_delta=0,cleanup_confirmed=True),"REVIEWED154_STOP_NOT_REBASED")
    return tuple(HISTORY)
