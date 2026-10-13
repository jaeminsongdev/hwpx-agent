"""Scoped actual capture/GO/model-oracle connection without source exclusions.

The preserved physical adapter and original engine/worker execute exactly once.
Only the original capture base and owned Popen are wrapped in the same process;
original global bindings are restored even on failure. No extra sampler/Job.
"""
import math
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch

SELF="tools/p09/strict_product_window_connection_v1.py"
TEST="tools/p09/tests/test_strict_product_window_connection_v1.py"

def require(ok,code):
    if not ok:raise ValueError("STRICT_WINDOW_CONNECTION_"+code)

def clone(fn,**deps):
    new=FunctionType(fn.__code__,dict(fn.__globals__,**deps),argdefs=fn.__defaults__,closure=fn.__closure__)
    new.__kwdefaults__=fn.__kwdefaults__
    require(new.__code__ is fn.__code__ and new.__closure__ is fn.__closure__,"ORIGINAL_FUNCTION_CODE_AND_CLOSURE")
    return new

def evidence(state):
    out=state.diagnostics()
    out["actual_GO_to_last_window_check_seconds"]=None if state.started is None or state.last is None else state.last-state.started
    out["capture_and_GO_actual_connection_required_before_acceptance"]=True
    return out

def connect_engine(engine,component):
    original=engine.run_owned;env=original.__globals__
    require(type(original) is FunctionType and all(k in env for k in ("subprocess","json","BoundedProcessCapture")),"ORIGINAL_ENGINE_BINDING_ENVIRONMENT")
    states=[];calls=[];check=require;patcher=patch;record=evidence
    def execute(run):
        check(not calls,"ONE_ENGINE_CALL_NOT_RETRY")
        calls.append(run)
        subprocess=env["subprocess"];json=env["json"]
        raw_dump=json.dump
        binding=component.connect(subprocess.Popen,env["BoundedProcessCapture"])
        states.append(binding.state)
        def dump(row,file,**kwargs):
            check(type(row) is dict,"ORIGINAL_FINAL_RUNTIME_ROW")
            row["strict_product_window"]=record(binding.state)
            if row.get("current_generation_runtime_candidate_qualified") is True:
                check(binding.state.completed is not None and not binding.state.stopped
                    and binding.state.go_writes==binding.state.capture_count==1,"ACTUAL_COMPLETE_WINDOW_BEFORE_RUNTIME_PASS")
            return raw_dump(row,file,**kwargs)
        # The original engine itself installs/restores its final writer. Its
        # captured raw_dump now delegates here, then to the existing formatter.
        with patcher.object(subprocess,"Popen",binding.Popen),patcher.object(json,"dump",dump), \
                patcher.dict(env,{"BoundedProcessCapture":binding.Capture}):
            return original(run)
    connected=FunctionType(execute.__code__,env,argdefs=execute.__defaults__,closure=execute.__closure__)
    require(connected.__globals__ is original.__globals__,"SAME_PHYSICAL_ADAPTER_BINDING_ENV")
    return NS(**{**vars(engine),"run_owned":connected}),NS(states=states,calls=calls,original_engine_code=original.__code__,original_worker_code=engine.worker.__code__)

def direct_oracle(original,new_native,link):
    budget=clone(original.runtime_budget,views=new_native)
    cost=clone(original.cost,runtime_budget=budget)
    retained=clone(original.retained_evidence,runtime_budget=budget)
    def mechanics(node):
        revised=original.mechanics_projection(node)
        return link.changed_expectations(revised,{"RUNTIME_COST":{"product_allowance_seconds":(20,15)}})
    return NS(**{**vars(original),"runtime_budget":budget,"cost":cost,"retained_evidence":retained,"mechanics_projection":mechanics})

def check_evidence(row,a):
    require(type(row.get("selected_test_index")) is int and row["selected_test_index"]==157,"ONLY_QUALIFIED_ORDINARY157")
    a.fields(row["source_frame"],dict(frame_state="COMMITTED",registered_live_frame=False,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True),"REAL_FULL_FRAME_NOT_PIPE_PROBE")
    a.fields(row["complete_runtime_budget"],dict(product_allowance_seconds=15,
        strict_GO_to_complete_capture_window_seconds=15,
        actual_window_binding_and_complete_capture_required_before_acceptance=True,
        unallocated_margin_seconds=60,additional_early_source_wait_allowance_seconds=11,
        unchanged_lock_deadline_seconds=600,input_scope_reduction_or_rate_change=False),"STRICT_ACTUAL_WINDOW_COST")
    w=row["strict_product_window"]
    a.fields(w,dict(maximum_GO_to_complete_capture_seconds=15,original_GO_bytes_retained=True,
        actual_GO_writes=1,actual_capture_count=1,actual_complete_capture_within_window=True,
        stopped=False,added_sampler_thread_or_process_query=False,capture_constructor_window_check_failed=False,
        original_source_scope_rates_CPU_RAM600_and_1200_retained=True,
        blocking_OS_latency_hard_preemption_guaranteed=False,
        capture_and_GO_actual_connection_required_before_acceptance=True,queue_advance_authorized=False,PC_freeze_resolved=False),"ACTUAL_GO_AND_COMPLETE_CAPTURE_WINDOW")
    elapsed=w["GO_to_complete_capture_elapsed_seconds"];last=w["actual_GO_to_last_window_check_seconds"]
    require(type(elapsed) in (int,float) and math.isfinite(elapsed) and 0<=elapsed<15
        and type(last) is type(elapsed) and last==elapsed,"ACTUAL_CAPTURE_COMPLETE_BEFORE_WINDOW_DEADLINE")
    return dict(actual_strict_GO_capture_window_qualified=True,all_original_full_source_and_product_oracles_required=True)
