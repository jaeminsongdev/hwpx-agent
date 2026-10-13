"""Acceptance-only propagation of the inherited scoped validator.
Keep qualifiedV15 product/source bytes immutable. Never narrow original scope.
Original six FULL bodies and metadata identity evidence both execute.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/metadata_identity_acceptance_bridge_v1.py"
TEST="tools/p09/tests/test_metadata_identity_acceptance_bridge_v1.py"

def require(ok,code):
    if not ok:raise ValueError("METADATA_IDENTITY_ACCEPTANCE_BRIDGE_"+code)

def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    # The original inherited prepare clones this function's globals and supplies
    # its stronger scope-specific validator. Resolve it HERE, not in an older
    # namespace which would silently return to a fixed1710-member oracle.
    fn=FunctionType(original_source.validate_candidate.__code__,
      dict(original_source.validate_candidate.__globals__,validator=validator),
      argdefs=original_source.validate_candidate.__defaults__,
      closure=original_source.validate_candidate.__closure__)
    result,proof=fn(q,row,listing,oldbody,fresh,ctx,flat)
    proof.update(identity_evidence(row))
    return result,proof

def connect(current):
    candidate=FunctionType(validate_candidate.__code__,
      dict(validate_candidate.__globals__,original_source=current._original_source,
        validator=current.validator,identity_evidence=current.metadata_identity_evidence),
      argdefs=validate_candidate.__defaults__,closure=validate_candidate.__closure__)
    source=NS(**{**vars(current.CURRENT_SOURCE),"validate_candidate":candidate})
    full=FunctionType(current._full_prepare.__code__,dict(current._full_prepare.__globals__,source=source),
      argdefs=current._full_prepare.__defaults__,closure=current._full_prepare.__closure__)
    prepare=FunctionType(current.prepare.__code__,dict(current.prepare.__globals__,_full_prepare=full),
      argdefs=current.prepare.__defaults__,closure=current.prepare.__closure__)
    api=NS(**{**vars(current.API),"prepare":prepare})
    require(full.__code__ is current._full_prepare.__code__ and prepare.__code__ is current.prepare.__code__,
      "FULL_ORIGINAL_PREPARE_AND_NATIVE_SCOPE_CODE")
    runtime=NS(**{**vars(current.M),"SELF":current.SELF,"TEST":current.TEST,"source":source,"API":api,
      "own_inputs":current.own_inputs,"data_path":current.data_path,"validate_data":current.validate_data,
      "template":current.template,"context":current.context,"validator":current.validator})
    return runtime,dict(scoped_validator_explicitly_forwarded_into_all_original_candidate_bodies=True,
      all_original_candidate_defaults_closures_and_other_dependencies_retained=True,
      original_metadata_identity_evidence_after_complete_original_oracle=True,
      original_full_prepare_Native_scope_and_physical_task_checks_retained=True,
      old_source_namespaces_or_product_bytes_mutated=False,scope_guards_or_rates_weakened=False,
      Native_or_product_reexecuted=False,acceptance_witness_not_retroactive_Native_input=True)
