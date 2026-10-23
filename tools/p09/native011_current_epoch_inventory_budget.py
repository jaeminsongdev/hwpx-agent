"""Bind fresh source-inventory identity data, retaining original budget code."""
from types import FunctionType

SELF='tools/p09/native011_current_epoch_inventory_budget.py'
TEST='tools/p09/tests/test_native011_current_epoch_inventory_budget.py'
ORIGINAL_REQUESTS=167
SOURCE=dict(path='tools/p09/held_native_view_oracle_v1.py',bytes=9527,
    sha256='831152fa350e2f743a6c9788bf7b6f8f5d8e2e212544874bc8361a865589a979')


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_INVENTORY_BUDGET_'+code)


def bind(original,actual_requests):
    require(type(original) is FunctionType and original.__name__=='runtime_budget'
        and original.__code__.co_filename.replace('\\','/').endswith(SOURCE['path']),
        'ORIGINAL_EXACT_BUDGET_FUNCTION_FAMILY')
    require(type(actual_requests) is int and 1<=actual_requests<=8192,'ACTUAL_BOUNDED_INVENTORY_COUNT')
    before=original.__globals__
    require(type(before.get('INVENTORY_REQUESTS')) is int and before['INVENTORY_REQUESTS']==ORIGINAL_REQUESTS,
        'ORIGINAL167_IDENTITY_NOT_ALREADY_PROJECTED')
    require('INVENTORY_REQUESTS' in original.__code__.co_names,'ORIGINAL_EXACT_COUNT_CHECK_RETAINED')
    env=dict(before,INVENTORY_REQUESTS=actual_requests)
    current=FunctionType(original.__code__,env,argdefs=original.__defaults__,closure=original.__closure__)
    current.__kwdefaults__=original.__kwdefaults__
    require(current.__code__ is original.__code__ and current.__defaults__ is original.__defaults__
        and current.__closure__ is original.__closure__ and current.__kwdefaults__ is original.__kwdefaults__
        and before['INVENTORY_REQUESTS']==ORIGINAL_REQUESTS,'ORIGINAL_CODE_DEFAULTS_CLOSURE_AND_GLOBALS_RETAINED')
    require(set(env)==set(before) and all(env[n] is value for n,value in before.items() if n!='INVENTORY_REQUESTS'),
        'ONLY_EXPLICIT_INVENTORY_IDENTITY_DATA_CHANGED')
    return current,dict(original_budget_source_pin=SOURCE,original_inventory_requests=ORIGINAL_REQUESTS,
        actual_inventory_requests=actual_requests,entire_original_budget_code_retained=True,
        original_exact_request_equality_guard_retained=True,original_model_and_views_retained=True,
        deadline600_or_margin60_or_decoder5_or_readiness15_changed=False,
        original_default_namespace_mutated=False,actual_Native_or_runtime_qualified=False)
