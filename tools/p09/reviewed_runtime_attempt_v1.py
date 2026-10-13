"""One explicitly reviewed physical retry; immutable original qualification run.
No automatic retry loop, receipt overwrite, task relabelling or original guard change.
Outer pipeline's historical run=1 qualification remains; actual engine receives2.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/reviewed_runtime_attempt_v1.py"
TEST="tools/p09/tests/test_reviewed_runtime_attempt_v1.py"
STOPPED={"path":"implementation/p09/evidence/p09-361-case153-current-runtime-run001.v1.json",
 "bytes":448239,"sha256":"7bed0574de3de8a50a8260a18cf63af6cf3c035268eff898694e739976cd65a3"}
REVIEW={"path":"implementation/p09/evidence/p09-361-case153-native-open-stop-review-r514.v1.json",
 "bytes":10843,"sha256":"15a4b5499bdc819bd71b06d8f6ff2c98c232309d90da5687f9a5bb371fdeadab"}

def require(ok,code):
    if not ok:raise ValueError("REVIEWED_PHYSICAL_ATTEMPT_"+code)

def physical_run(index):
    require(type(index) is int and 153<=index<=249,"EXACT_CURRENT_INDEX")
    return 2 if index==153 else 1

def root_path(step):
    return f"implementation/p09/evidence/p09-361-case{step.index}-current-runtime-run{physical_run(step.index):03}.v1.json"

def task(index):
    return f"case{index}-current-r{physical_run(index):03}-tests"

def public_run(index,run):
    require(type(run) is int and run==physical_run(index),"EXACT_EXPLICIT_PHYSICAL_RUN")
    return 1

def reviewed_failure(q,read_exact,fields):
    row=read_exact(q,STOPPED)
    fields(row,dict(state="DEFERRED_NOT_STARTED",stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",
      selected_test_index=153,product_body_observed=False,Native_source_frame_qualified=False,
      cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"REVIEWED153_NO_PRODUCT")
    handles=row["source_frame"]["handles"]
    fields(handles,dict(input_lock_handles_opened=1329,input_lock_handles_closed=1329,
      input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True),"REVIEWED153_HANDLES_CLOSED")
    review=read_exact(q,REVIEW)
    fields(review,dict(state="DEFERRED_NOT_STARTED",stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",
      product_body=False,cleanup=True,owned_tree_empty=True,accepted_count_delta=0,
      original_current153_receipt_unchanged=True),"REVIEWED153_CLEANUP")
    return (STOPPED,REVIEW)

def connect_engine(engine,index):
    physical=physical_run(index);original=engine.run_owned;check=require
    require(type(original) is FunctionType,"ORIGINAL_ENGINE_FUNCTION")
    env=original.__globals__
    state=NS(logical_qualification_run=1,physical_product_run=physical,actual_engine_calls=0,
      original_engine_code=original.__code__,original_worker_code=engine.worker.__code__)
    def execute(logical):
        check(type(logical) is int and logical==1,"QUALIFICATION_ONLY_RUN_ONE")
        check(state.actual_engine_calls==0,"ONE_EXPLICIT_ENGINE_CALL_NO_RETRY")
        state.actual_engine_calls+=1
        return original(physical)
    # The original sole-observer entry sets binding in run_owned.__globals__.
    # Share that SAME private environment with the preserved original engine,
    # otherwise its complete binding would silently remain stale.
    connected=FunctionType(execute.__code__,env,argdefs=execute.__defaults__,closure=execute.__closure__)
    require(connected.__globals__ is original.__globals__,"SAME_ORIGINAL_PRIVATE_BINDING_ENV")
    result=NS(**{**vars(engine),"run_owned":connected})
    require(result.worker is engine.worker and all(getattr(result,k) is v for k,v in vars(engine).items()
      if k!="run_owned"),"ALL_OTHER_ENGINE_DEPENDENCIES_RETAINED")
    return result,state,dict(original_engine_code_defaults_closure_and_worker_retained=True,
      qualification_run=1,physical_product_run=physical,original_private_binding_environment_shared=True,
      physical_destination_and_task_not_relabelled=True,automatic_retry=False,
      original_GO_Job_source_two_reads_rates_deadlines_and_cleanup_retained=True)

def validate_actual(row,step,pin):
    require(type(pin) is dict and pin.get("path")==root_path(step),"EXACT_PHYSICAL_ROOT")
    require(type(row) is dict and row.get("selected_test_index")==step.index
      and type(row.get("selected_test_index")) is int,"EXACT_RECORDED_CASE")
    require(row.get("task")==task(step.index),"ACTUAL_PHYSICAL_TASK")
    # The full source/product/cleanup oracle must run separately. This function
    # checks identity only and never promotes a stopped or synthetic row.
    return dict(logical_qualification_run=1,physical_product_run=physical_run(step.index),
      actual_root_and_task_match=True,full_product_oracle_replaced=False)
