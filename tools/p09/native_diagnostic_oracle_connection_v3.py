"""Explicit native versions for FULL candidate path; no history rebase.
147/148 V2;149..152 V3;153+ V4. Stopped153V3 is NOT an accepted predecessor.
All original six candidate bodies retained;only diagnostic dependencies switch.
"""
from types import FunctionType,SimpleNamespace as NS
import native_diagnostic_oracle_connection_v2 as prior
import native_diagnostic_connection_v4 as diagnostic

SELF="tools/p09/native_diagnostic_oracle_connection_v3.py"
TEST="tools/p09/tests/test_native_diagnostic_oracle_connection_v3.py"

def require(ok,code):
    if not ok:raise ValueError("NATIVE_VERSIONED_ORACLE3_"+code)

def for_index(index):
    require(type(index) is int and 147<=index<=249,"EXACT_NATIVE_EPOCH")
    if index>=153:return diagnostic
    if index>=149:return NS(BACKEND="NATIVE_TOOLHELP_PROCESS_TIMES_V3",validate=diagnostic.validate_historical_v3)
    return NS(BACKEND="NATIVE_TOOLHELP_PROCESS_TIMES_V2",validate=diagnostic.validate_historical_v2)

def dispatch(original,row):
    index=row.get("selected_test_index")
    require(type(index) is int and 115<=index<=249,"EXACT_RECORDED_RUNTIME_INDEX")
    if index>=147:
        chosen=for_index(index)
        require(row["serial_CPU_attribution"].get("backend")==chosen.BACKEND,"ACTUAL_RECORDED_VERSION")
        return chosen.validate(row)
    require(row["serial_CPU_attribution"].get("backend") is None,"LEGACY_NOT_REBASED")
    return original(row)

def connect_candidate(function):
    fn=prior.prior.connect_candidate
    return FunctionType(fn.__code__,dict(fn.__globals__,dispatch=dispatch),
       argdefs=fn.__defaults__,closure=fn.__closure__)(function)

def additional_dispatch(original,row):
    index=row.get("selected_test_index")
    if type(index) is int and index<=146:return prior.additional.dispatch(original,row,diagnostic)
    return prior.additional.dispatch(original,row,for_index(index))

def connect_retained(original_candidate,direct_oracle,unused):
    fn=prior.connect_retained
    return FunctionType(fn.__code__,dict(fn.__globals__,additional_dispatch=additional_dispatch),
       argdefs=fn.__defaults__,closure=fn.__closure__)(original_candidate,direct_oracle,unused)

def connect_full(function,original_candidate,direct_oracle):
    fn=prior.connect_full
    return FunctionType(fn.__code__,dict(fn.__globals__,connect_candidate=connect_candidate,
       connect_retained=connect_retained,diagnostic=diagnostic),argdefs=fn.__defaults__,
       closure=fn.__closure__)(function,original_candidate,direct_oracle)
