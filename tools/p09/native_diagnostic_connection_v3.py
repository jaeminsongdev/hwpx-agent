"""NativeV3 local dependency/schema successor; old V2 history unchanged.

ALL original run/entry/checker bytecodes remain. The diagnostic expected backend
and ONE actual source literal are explicitly versioned; no row relabel/copy.
"""
import math
from types import FunctionType

import native_diagnostic_connection_v2 as prior

SELF="tools/p09/native_diagnostic_connection_v3.py"
TEST="tools/p09/tests/test_native_diagnostic_connection_v3.py"
BACKEND="NATIVE_TOOLHELP_PROCESS_TIMES_V3"


def require(ok,code):
    if not ok:raise ValueError("NATIVE_DIAGNOSTIC_V3_"+code)


def versioned(function):
    code=function.__code__
    old="tools/p09/native_process_cpu_attribution_v2.py"
    new="tools/p09/native_process_cpu_attribution_v3.py"
    require(sum(type(c) is str and c==old for c in code.co_consts)==1,"ONE_SOURCE_LITERAL")
    constants=tuple(new if type(c) is str and c==old else c for c in code.co_consts)
    revised=code.replace(co_consts=constants)
    require(revised.replace(co_consts=code.co_consts)==code,"ALL_OTHER_ORIGINAL_CODE_FIELDS")
    return FunctionType(revised,dict(function.__globals__,BACKEND=BACKEND),
                        argdefs=function.__defaults__,closure=function.__closure__)


_connect_entry=versioned(prior.connect_entry)
_validate=versioned(prior.validate)


def connect_entry(api,raw,old,backend,state):
    return _connect_entry(api,raw,old,backend,state)


def connect_run(function,backend):
    fn=prior.connect_run
    return FunctionType(fn.__code__,dict(fn.__globals__,connect_entry=connect_entry),
                        argdefs=fn.__defaults__,closure=fn.__closure__)(function,backend)


def validate(row):
    proof=_validate(row)
    p=row["serial_CPU_attribution"]["probes"][0]
    for key,value in dict(capture_api_source="tools/p09/bounded_cpu_attribution_probe_v2.py",
     constructor_and_first_capture_share_setup_budget=True,cooperative_capture_deadline_seconds=.05,
     partial_capture_never_baseline_or_valid_sample=True,time_scratch_allocations_per_capture=1,
     create_and_close_in_capture_clock=True,OS_call_hard_preemption_guaranteed=False).items():
        require(type(p.get(key)) is type(value) and p[key]==value,"EXACT_NEW_CAPTURE_POLICY")
    constructor=p["capture_api_constructor_seconds"]
    require(type(constructor) in (int,float) and math.isfinite(constructor) and 0<=constructor<=p["total_added_sample_seconds"],
            "REAL_CONSTRUCTOR_IN_TOTAL_BUDGET")
    for key in ("cooperative_budget_stops","partial_captures_discarded"):
        require(type(p.get(key)) is int and 0<=p[key]<=p["query_calls"],"BOUNDED_PARTIAL_STOP_COUNTS")
    require(p["cooperative_budget_stops"]==p["partial_captures_discarded"],"NO_PARTIAL_CAPTURE_PROMOTED")
    if p["partial_captures_discarded"]:
        require(p["disabled_reason"]=="MEASUREMENT_COST_BUDGET_EXCEEDED","EXPLICIT_PARTIAL_STOP_REASON")
    return dict(proof,capture_v2_provenance_and_partial_setup_policy_checked=True)


def validate_historical_v2(row):
    return prior.validate(row)
