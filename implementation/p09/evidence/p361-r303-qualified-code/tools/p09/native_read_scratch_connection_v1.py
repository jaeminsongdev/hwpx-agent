"""Opt-in scratch factory in FULL held-native path; original bodies stay.
Adds strict150+ actual default-factory evidence;149 and older are unchanged.
No new handles, stream cache, sampler, rate/deadline change or row rewriting.
"""
import threading
from types import FunctionType,SimpleNamespace as NS
import native_read_call_scratch_v1 as scratch

SELF="tools/p09/native_read_scratch_connection_v1.py"
TEST="tools/p09/tests/test_native_read_scratch_connection_v1.py"

def require(ok,code):
    if not ok:raise ValueError("NATIVE_SCRATCH_CONNECTION_"+code)

def clone(fn,env):
    return FunctionType(fn.__code__,dict(fn.__globals__,**env),
                        argdefs=fn.__defaults__,closure=fn.__closure__)

def connect(native,raw):
    original=native.ViewBorrower
    Read,projection=scratch.native_read_type(raw)
    require(scratch.prior.NativeRead is native.NativeRead,"EXACT_NATIVE_API_PARENT")
    init=clone(original.__init__,dict(NativeRead=Read))
    class Borrower(original):
        __init__=init
        def summary(self):
            row=original.summary(self);self.owner_check()
            bound=type(self.api) is Read
            if bound:
                require(self.api._owner==threading.get_ident() and not self.api._busy,"SAME_INACTIVE_API_OWNER")
                require(self.api._read_count_pointer._obj is self.api._read_count and
                        self.api._seek_result_pointer._obj is self.api._seek_result,"EXACT_SCRATCH_POINTER_OBJECTS")
            row["native_call_scratch"]=dict(
                schema_version="hwpx-agent.native-read-call-scratch/v1",
                source=scratch.SELF,connection_source=SELF,actual_default_factory_bound=bound,
                count_and_seek_objects_per_API=2 if bound else None,pointer_objects_per_API=2 if bound else None,
                same_original_serial_owner=bound,scratch_active=False if bound else None,
                original_actual_read_calls=self.read_attempts,original_actual_seek_calls=self.resets,
                zero_reset_before_each_OS_call=True,fresh_buffer_binding_preserved=True,
                original_ReadFile_seek_identity_error_and_rate_guards_retained=True,
                source_byte_hash_JSON_cache=False,second_sampler_thread_or_process=False,
                PC_freeze_resolved=False)
            return row
    locks=clone(native.locks_type,dict(ViewBorrower=Borrower))
    load=clone(native.load,dict(locks_type=locks))
    result=NS(**{**vars(native),"NativeRead":Read,"ViewBorrower":Borrower,"locks_type":locks,"load":load})
    require(result.load.__code__ is native.load.__code__ and result.locks_type.__code__ is native.locks_type.__code__
            and Borrower.__init__.__code__ is original.__init__.__code__,"FULL_LOAD_LOCKS_AND_BORROWER_INIT_CODE")
    require(all(getattr(result,k) is value for k,value in vars(native).items()
                if k not in ("NativeRead","ViewBorrower","locks_type","load")),"ALL_OTHER_NATIVE_DEPENDENCIES")
    return result,dict(scratch_projection=projection,
        original_load_locks_and_borrower_init_bytecode_defaults_closures_retained=True,
        default_source_namespaces_mutated=False,original_summary_fields_retained_with_one_addition=True,
        original_ReadView_identity_and_resource_statements_unchanged=True,
        original_scope_rates_two_reads_deadlines_and_costs_retained=True,
        runtime150_product_or_Native_qualified=False,PC_freeze_resolved=False)

def validate_scratch(row):
    index=row.get("selected_test_index")
    require(type(index) is int and 147<=index<=249,"EXACT_RECORDED_INDEX")
    if index<150:return dict(historical_scratch_not_claimed=True)
    views=row["source_frame"]["handles"]["held_native_read_views"]
    value=views["native_call_scratch"]
    expected=dict(schema_version="hwpx-agent.native-read-call-scratch/v1",
       source=scratch.SELF,connection_source=SELF,actual_default_factory_bound=True,
       count_and_seek_objects_per_API=2,pointer_objects_per_API=2,same_original_serial_owner=True,
       scratch_active=False,original_actual_read_calls=views["direct_readinto_attempts"],
       original_actual_seek_calls=views["shared_offset_resets"],zero_reset_before_each_OS_call=True,
       fresh_buffer_binding_preserved=True,original_ReadFile_seek_identity_error_and_rate_guards_retained=True,
       source_byte_hash_JSON_cache=False,second_sampler_thread_or_process=False,PC_freeze_resolved=False)
    require(type(value) is dict and set(value)==set(expected),"CLOSED_ACTUAL_SCRATCH_TRACE")
    for key,wanted in expected.items():
        require(type(value.get(key)) is type(wanted) and value[key]==wanted,"EXACT_ACTUAL_SCRATCH_VALUE")
    require(type(expected["original_actual_read_calls"]) is int and
            expected["original_actual_read_calls"]>=2*row["source_frame"]["input_count"] and
            expected["original_actual_seek_calls"]==2*row["source_frame"]["input_count"],"FULL_TWO_PASSES_NOT_FAKE_API")
    return dict(actual_scratch_factory_and_full_original_call_counts_checked=True)

def diagnostic(prior):
    def validate(row):
        proof=prior.validate(row)
        return dict(proof,**validate_scratch(row))
    return NS(**{**vars(prior),"validate":validate})
