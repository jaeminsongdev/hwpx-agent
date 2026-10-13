"""Preflight-only stable original bound callback plus qualified guard dedup.
Original guard method/code/self/arguments and all preflight statements retained.
Only a fresh diagnostic destination differs; product controller not rewritten.
"""
from types import MethodType,FunctionType,SimpleNamespace as NS

SELF="tools/p09/preflight_guard_identity_v1.py"
TEST="tools/p09/tests/test_preflight_guard_identity_v1.py"

def require(ok,code):
    if not ok:raise ValueError("PREFLIGHT_GUARD_IDENTITY_"+code)

def guard_type(original):
    class Guard(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            callback=self.check
            require(type(callback) is MethodType and callback.__self__ is self
              and callback.__func__ is original.check,"EXACT_ORIGINAL_BOUND_METHOD")
            # Ordinary attribute reads otherwise allocate a new bound method.
            # Preserve this EXACT original method once on this private instance.
            self.check=callback
            require(self.check is callback,"STABLE_PRIVATE_CALLBACK_REFERENCE")
    return Guard

def projection(function,raw,optimization):
    env=dict(function.__globals__)
    old="-native-diagnostic-preflight016.v1.json";new="-native-diagnostic-preflight017.v1.json"
    code=function.__code__
    require(sum(type(x) is str and x==old for x in code.co_consts)==1,"ONE_FRESH_PREFLIGHT_DESTINATION")
    revised=code.replace(co_consts=tuple(new if type(x) is str and x==old else x for x in code.co_consts))
    require(revised.replace(co_consts=code.co_consts)==code,"ALL_ORIGINAL_PREFLIGHT_CODE_TEST10")
    Original=env["a"].Guard
    New,proof=optimization.checkpoint_type(env["MetadataCheckpoint"],raw)
    env["a"]=NS(**{**vars(env["a"]),"Guard":guard_type(Original)})
    env["MetadataCheckpoint"]=New
    fn=FunctionType(revised,env,argdefs=function.__defaults__,closure=function.__closure__)
    return fn,dict(original_preflight_code_defaults_closure_and_test10_retained=True,
      original_guard_method_code_self_arguments_and_criteria_retained=True,
      no_second_system_observer_or_native_query=True,original_bound_callback_stable_on_private_instance=True,
      only_fresh_diagnostic_destination_changed=True,metadata_checkpoint_projection=proof,
      actual_product_or_full_preflight_executed=False,PC_freeze_resolved=False)
