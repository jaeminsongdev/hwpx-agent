"""Explicit V4 diagnostic schema; historical V3/V2 never relabelled.
Keep original entry/run/checker code except version source and unavailable enum.
New suppression reason must match real original CPU warning and false query flags.
"""
import math
from types import FunctionType
import native_diagnostic_connection_v3 as prior
import native_process_cpu_attribution_v4 as backend

SELF="tools/p09/native_diagnostic_connection_v4.py"
TEST="tools/p09/tests/test_native_diagnostic_connection_v4.py"
BACKEND=backend.BACKEND
SUPPRESSED=backend.SUPPRESSED

def require(ok,code):
    if not ok:raise ValueError("NATIVE_DIAGNOSTIC_V4_"+code)

def versioned(function,unavailable=False):
    code=function.__code__;old="tools/p09/native_process_cpu_attribution_v3.py"
    new="tools/p09/native_process_cpu_attribution_v4.py";source_count=reason_count=0;constants=[]
    reasons=("NOT_SAMPLED_COLD_INTERVAL","MEASUREMENT_COST_BUDGET_EXCEEDED","QUERY_COUNT_BOUND","BASELINE_UNAVAILABLE")
    for value in code.co_consts:
        if type(value) is str and value==old:source_count+=1;constants.append(new)
        elif unavailable and type(value) is tuple and value==reasons:
            reason_count+=1;constants.append(reasons+(SUPPRESSED,))
        else:constants.append(value)
    require(source_count==1 and reason_count==int(unavailable),"EXACT_VERSION_AND_UNAVAILABLE_ENUM")
    revised=code.replace(co_consts=tuple(constants))
    require(revised.replace(co_consts=code.co_consts)==code,"ALL_OTHER_ORIGINAL_CODE_FIELDS")
    return FunctionType(revised,dict(function.__globals__,BACKEND=BACKEND),
                        argdefs=function.__defaults__,closure=function.__closure__)

_connect_entry=versioned(prior._connect_entry)
_validate=versioned(prior._validate,True)
_capture_policy=FunctionType(prior.validate.__code__,dict(prior.validate.__globals__,_validate=_validate),
                           argdefs=prior.validate.__defaults__,closure=prior.validate.__closure__)

def connect_entry(api,raw,old,actual_backend,state):
    return _connect_entry(api,raw,old,actual_backend,state)

def connect_run(function,actual_backend):
    fn=prior.prior.connect_run
    return FunctionType(fn.__code__,dict(fn.__globals__,connect_entry=connect_entry),
              argdefs=fn.__defaults__,closure=fn.__closure__)(function,actual_backend)

def validate(row):
    proof=_capture_policy(row)
    info=row["serial_CPU_attribution"];p=info["probes"][0]
    for obj,values in ((info,dict(warning_optional_attribution_suppressed=True,warning_suppression_percent=75)),
      (p,dict(warning_optional_attribution_suppressed=True,warning_suppression_percent=75,
       original_low_load_sample_code_retained=True,suppressed_result_is_unavailable_not_zero=True,
       suppression_does_not_change_original_guard_decisions=True,
       suppression_does_not_close_reset_or_rebaseline_probe=True))):
        for key,value in values.items():require(type(obj.get(key)) is type(value) and obj[key]==value,"EXACT_WARNING_POLICY")
    all_samples=row["samples"]+row.get("post_Job_cleanup_resource_samples",[])
    observed=0
    for sample in all_samples:
        diagnostic=sample.get("serial_cpu_attribution",{})
        if diagnostic.get("reason")==SUPPRESSED:
            observed+=1
            cpu=sample["system_cpu_percent"]
            require(type(cpu) in (int,float) and math.isfinite(cpu) and 75<=cpu<=100,"REAL_WARNING_K32")
            for key,value in dict(available=False,values=None,optional_native_query_attempted=False,
                 original_K32_CPU_RAM_decisions_replaced=False,diagnostic_measurement_fresh=False).items():
                require(type(diagnostic.get(key)) is type(value) and diagnostic[key]==value,"NO_FAKE_SUPPRESSION_VALUE_OR_QUERY")
    count=p["warning_attribution_suppressions"]
    require(type(count) is int and count==observed,"ALL_OBSERVED_WARNING_SUPPRESSIONS_COUNTED")
    return dict(proof,explicit_warning_suppression_not_a_fresh_native_measurement=True,
                warning_suppressions=count,historical_records_mutated=False)

def validate_historical_v3(row):return prior.validate(row)
def validate_historical_v2(row):return prior.validate_historical_v2(row)
