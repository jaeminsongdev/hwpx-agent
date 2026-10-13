"""Exact160 Binding with explicit historical159 failure lineage.

Original methods and byte/resource oracles survive. Project only exact case
literals and the historical provenance key, proving inverse code equality.
The old152/158/159 lineage remains unchanged inside historical metadata.
"""
import copy
from types import FunctionType,MappingProxyType
import runtime_successor_binding_v1 as original

SELF="tools/p09/runtime_successor_binding_v2.py"
TEST="tools/p09/tests/test_runtime_successor_binding_v2.py"
SCHEMA="hwpx-agent.p09-successor160-historical-failure-context/v2"
AUTHORITY=dict(path="implementation/p09/evidence/p09-361-case159-current-epoch-accept001.v1.json",
    bytes=436264,sha256="be740fc83c883f3e07e010299a9f05955da728911ad3e1c36a02ce1688f7947e")
ROOT=dict(path="implementation/p09/evidence/p09-361-case159-current-runtime-run001.v1.json",
    bytes=4580676,sha256="090e2e069852a45d2db306f9968c2ca997962222e3bc622c7c10c7dee2d830d2")


def declaration(history):
    return dict(schema_version=SCHEMA,next_case=160,accepted_count_before=153,
        authority_pin=dict(AUTHORITY),prior_runtime_pin=dict(ROOT),
        historical_case159_failure_lineage=copy.deepcopy(history),
        historical_failures_promoted=False,current160_product_or_GO_qualified=False)


def admission(q,a,failed003,failed004):
    authority=a.read_exact(q,AUTHORITY)
    a.fields(authority,dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",
        accepted_count_after=153,next_runtime_index=160,runtime_candidate_pin=ROOT,
        resource_cleanup_confirmed=True,P09_gate="OPEN"),"EXACT153_NEXT160_AUTHORITY")
    prior=a.read_exact(q,ROOT)
    a.fields(prior,dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
        selected_test_index=159,Native_source_frame_qualified=True,current_generation_runtime_candidate_qualified=True,
        cleanup_confirmed=True,owned_tree_empty=True),"EXACT_COMMITTED_PRIOR159")
    a.fields(prior["source_frame"],dict(frame_state="COMMITTED"),"REAL_PRIOR159_FRAME")
    a.require(len(prior["source_frame"]["actual_byte_boundaries"])==2,"WHOLE_PRIOR159_BYTES_TWO")
    history=original.admission(q,a,failed003,failed004)
    a.exact(prior["source_input_representation"]["prior_failure_lineage"],history,
        "UNCHANGED_HISTORICAL159_FAILED158_LINEAGE")
    return declaration(history)


def project(fn,before,after):
    code=fn.__code__
    original.require(sum(type(x) is type(before) and x==before for x in code.co_consts)==1,"ONE_EXACT160_METADATA_LITERAL")
    original.require(not any(type(x) is type(after) and x==after for x in code.co_consts),"UNAMBIGUOUS160_INVERSE")
    revised=code.replace(co_consts=tuple(after if type(x) is type(before) and x==before else x for x in code.co_consts))
    inverse=revised.replace(co_consts=tuple(before if type(x) is type(after) and x==after else x for x in revised.co_consts))
    original.require(inverse==code,"ENTIRE160_ORIGINAL_CODE_RESTORED")
    out=FunctionType(revised,fn.__globals__,argdefs=fn.__defaults__,closure=fn.__closure__)
    out.__kwdefaults__=fn.__kwdefaults__
    return out


def connect(module,context,failed003,failed004):
    expected_history=original.declaration([dict(schema_version=f.ADMISSION_SCHEMA,source_role=f.ROLE,
        failed_runtime_pin=f.ROOT,independent_review_pin=f.REVIEW,current_case=158,
        original_failure_promoted=False,current_product_or_GO_qualified=False) for f in (failed003,failed004)])
    module.exact(context,declaration(expected_history),"EXACT160_CONTEXT_AND_HISTORICAL159_PROVENANCE")
    proof=original.connect(module,expected_history,failed003,failed004)
    ctor=module.Binding.__init__;descriptor=module.source.descriptor;representation=module.Binding.representation
    module.Binding.__init__=project(ctor,159,160)
    current_descriptor=project(descriptor,159,160)
    historical_representation=project(representation,"prior_failure_lineage","historical_case159_failure_lineage")
    module.source.descriptor=current_descriptor
    module.source.Projection.__init__.__globals__["descriptor"]=current_descriptor
    frozen=copy.deepcopy(context)
    def represented(self,projection):
        row=historical_representation(self,projection)
        row["successor_context"]=copy.deepcopy(frozen)
        return row
    module.Binding.representation=represented
    module.successor_failure_lineage=MappingProxyType(dict(schema_version=SCHEMA,next_case=160,
        historical_failures_promoted=False,original_metadata_inverse_code_equal=True))
    return dict(proof,constructor159_to160_inverse_code_equal=True,descriptor159_to160_inverse_code_equal=True,
        historical_provenance_key_inverse_code_equal=True,original_nonconstructor_oracle_methods_retained=True,
        historical159_lineage_fields_not_relabelled=True,original_context_159_not_claimed_as160=True,
        current160_controller_scope_Native_or_GO_qualified=False)
