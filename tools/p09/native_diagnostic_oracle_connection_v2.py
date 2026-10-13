"""Explicit149+ nativeV3 and historical147/148 V2 diagnostic dispatch.

Same FULL candidate bytecodes and original additional-observer cost/cleanup/
acquisition checks. No fake old source metadata, generic legacy fallback, row
mutation, body replay or source/resource oracle replacement.
"""
from types import FunctionType,SimpleNamespace as NS

import native_diagnostic_oracle_connection_v1 as prior
import native_diagnostic_connection_v3 as diagnostic
import native_additional_observer_connection_v1 as additional

SELF="tools/p09/native_diagnostic_oracle_connection_v2.py"
TEST="tools/p09/tests/test_native_diagnostic_oracle_connection_v2.py"


def require(ok,code):
    if not ok:raise ValueError("NATIVE_VERSIONED_ORACLE2_"+code)


def for_index(index):
    require(type(index) is int and 147<=index<=249,"EXACT_NATIVE_EPOCH_INDEX")
    if index>=149:return diagnostic
    return NS(BACKEND="NATIVE_TOOLHELP_PROCESS_TIMES_V2",validate=diagnostic.validate_historical_v2)


def dispatch(original,row):
    index=row.get("selected_test_index")
    require(type(index) is int and 115<=index<=249,"EXACT_RECORDED_RUNTIME_INDEX")
    if index>=147:
        selected=for_index(index)
        require(row["serial_CPU_attribution"].get("backend")==selected.BACKEND,"ACTUAL_RECORDED_NATIVE_VERSION")
        return selected.validate(row)
    require(row["serial_CPU_attribution"].get("backend") is None,"LEGACY_RECORD_NOT_REBASED")
    return original(row)


def connect_candidate(function):
    fn=prior.connect_candidate
    return FunctionType(fn.__code__,dict(fn.__globals__,dispatch=dispatch),
                        argdefs=fn.__defaults__,closure=fn.__closure__)(function)


def additional_dispatch(original,row):
    index=row.get("selected_test_index")
    if type(index) is int and index<=146:
        return additional.dispatch(original,row,diagnostic)
    return additional.dispatch(original,row,for_index(index))


def connect_retained(original_candidate,direct_oracle,unused):
    original=original_candidate.original
    check=original.additional_observer_evidence
    private=NS(**{**vars(original),"additional_observer_evidence":lambda row:additional_dispatch(check,row)})
    candidate=NS(**{**vars(original_candidate),"original":private})
    return lambda row:direct_oracle.retained_evidence(row,candidate)


def connect_full(function,original_candidate,direct_oracle):
    budget,proof=connect_candidate(function)
    fn=additional.connect_candidate
    projected=FunctionType(fn.__code__,dict(fn.__globals__,connect_retained=connect_retained),
                          argdefs=fn.__defaults__,closure=fn.__closure__)
    result,extra=projected(budget,original_candidate,direct_oracle,diagnostic)
    return result,dict(budget=proof,additional=extra,
      all_original_full_candidate_code_retained=True,version_dispatch_only_not_product_oracle=True)
