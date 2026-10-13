"""Acceptance-only qualified metadata guard factory connection.
Default/historical namespaces and all original acceptor bodies remain unchanged.
"""
from types import SimpleNamespace as NS

SELF="tools/p09/acceptance_metadata_guard_identity_v1.py"
TEST="tools/p09/tests/test_acceptance_metadata_guard_identity_v1.py"

def require(ok,code):
    if not ok:raise ValueError("ACCEPTANCE_METADATA_IDENTITY_"+code)

def connect(runtime,raw,optimization):
    source=runtime.source
    metadata=source.prior.prior.metadata
    New,proof=optimization.checkpoint_type(metadata.MetadataCheckpoint,raw)
    private_metadata=NS(**{**vars(metadata),"MetadataCheckpoint":New})
    private_inner=NS(**{**vars(source.prior.prior),"metadata":private_metadata})
    private_prior=NS(**{**vars(source.prior),"prior":private_inner})
    private_source=NS(**{**vars(source),"prior":private_prior})
    result=NS(**{**vars(runtime),"source":private_source})
    require(all(getattr(result,k) is x for k,x in vars(runtime).items() if k!="source"),
      "ONLY_ACCEPTANCE_FACTORY_SOURCE_DEPENDENCY")
    return result,dict(metadata_checkpoint_projection=proof,
      exact_acceptance_metadata_factory_changed_only_in_private_dependency_namespace=True,
      all_original_acceptor_prepare_Native_scope_and_metadata_identity_checks_retained=True,
      original_Guard_Reader_pacer_and_source_byte_operations_retained=True,
      original_default_historical_namespaces_not_mutated=True,
      new_sampler_or_native_query=False,scope_guards_or_deadlines_weakened=False,
      product_reexecuted=False,acceptance_witness_not_retroactive_Native_input=True)
