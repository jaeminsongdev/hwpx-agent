"""Whole original checker/projector over explicit physical expectation scope.

Every qualified generator code/default/closure remains. Only its original scope
dependency and ORACLE_SCOPE get private extend/cost functions. The exact whole
semantic union is checked separately before physical expectations are returned.
No observed row/frame/counters are rewritten to appease a legacy predicate.
"""
from types import FunctionType,SimpleNamespace as NS
import runtime_envelope_scope_binding_v1 as binding_module

SELF="tools/p09/runtime_envelope_full_oracle_connection_v1.py"
TEST="tools/p09/tests/test_runtime_envelope_full_oracle_connection_v1.py"


def clone(fn, **values):
    result=FunctionType(fn.__code__,dict(fn.__globals__,**values),argdefs=fn.__defaults__,closure=fn.__closure__)
    result.__kwdefaults__=fn.__kwdefaults__
    binding_module.require(result.__code__ is fn.__code__ and result.__defaults__ is fn.__defaults__
        and result.__closure__ is fn.__closure__,"ENTIRE_ORIGINAL_FUNCTION_RETAINED")
    return result


def projector(original,binding,complete_budget,checkpoint,*,mechanics_projection=None):
    require=binding_module.require
    require(type(original) is FunctionType and type(binding) is binding_module.Binding
        and callable(complete_budget) and callable(checkpoint),"ORACLE_CONNECTION_ARGUMENTS")
    globals_=original.__globals__
    require(all(name in globals_ for name in ("original","ORACLE_SCOPE","mechanics_projection"))
        and hasattr(globals_["original"],"scope"),"QUALIFIED_FULL_PROJECTOR_INTERFACE")
    original_namespace=globals_["original"]
    metadata_scope=original_namespace.scope
    oracle_scope=globals_["ORACLE_SCOPE"]
    observed=dict(generator_calls=0,explicit_scope_checks=0,original_checker_calls=0)
    projected_generators=[]

    def project(raw,row,listing,body):
        checkpoint();observed["generator_calls"]+=1
        def extend(required,added):
            checkpoint()
            joined=metadata_scope.extend(required,added)
            projection,_=binding.project(joined,checkpoint)
            binding.validate_scope_evidence(row,joined,checkpoint)
            observed["explicit_scope_checks"]+=1
            return {n:dict(p) for n,p in projection.physical_pins.items()}
        def cost(required,rate):
            require(type(rate) is int and rate==14,"UNCHANGED_ORIGINAL_ACQUISITION14")
            return binding.runtime_budget(required,167,complete_budget,checkpoint)
        metadata=NS(**{**vars(metadata_scope),"extend":extend})
        oracle=NS(**{**vars(oracle_scope),"extend":extend,"cost":cost})
        dependencies=dict(original=NS(**{**vars(original_namespace),"scope":metadata}),ORACLE_SCOPE=oracle)
        if mechanics_projection is not None:
            require(callable(mechanics_projection),"QUALIFIED_MECHANICS_DEPENDENCY")
            dependencies["mechanics_projection"]=mechanics_projection
        generator=clone(original,**dependencies);projected_generators.append(generator)
        check,proof=generator(raw,row,listing,body)
        require(type(check) is FunctionType,"FULL_COMPILED_ORIGINAL_CHECKER")
        def execute(candidate,current_listing,old_body,fresh,guard):
            checkpoint()
            require(candidate is row,"SAME_UNMODIFIED_CANDIDATE_OBJECT")
            observed["original_checker_calls"]+=1
            return check(candidate,current_listing,old_body,fresh,guard)
        return execute,dict(proof,whole_original_checker_code_retained=True,
            entire_original_generator_code_defaults_and_closure_retained=True,
            physical_expectation_scope_explicitly_projected=True,
            original_observed_row_frame_or_counters_mutated=False,
            semantic_whole_scope_checked_before_physical_expectations=True,
            complete_original_cost_plus_shared_decoder5=True,
            whole_current158_runtime_or_acceptance_qualified=False)
    return project,NS(observed=observed,projected_generators=projected_generators,
        original_generator=original,original_default_globals_not_mutated=True)
