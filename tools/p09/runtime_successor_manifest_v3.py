"""Actual25-pair manifest: preserve24 and add exact partial160 failure."""
import runtime_successor_manifest_v2 as original
import runtime_failed160_partial_projection_v1 as role

SELF="tools/p09/runtime_successor_manifest_v3.py"
SCHEMA="hwpx-agent.p09-successor160-partial-failure-source-manifest/v3"
PATH="implementation/p09/evidence/p09-361-case160-source-manifest025.v3.json"
ROLE_CODE="implementation/p09/evidence/p09-361-case160-partial-role-code6-r782.v1.json"
PRODUCER="implementation/p09/evidence/p09-361-case160-partial-failure-envelope-producer-r784.v1.json"


def load(q,pin,a,*,controller,new_module,successor):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","physical_product_run",
        "base_manifest_pin","partial_failure_role_code_pin","partial_failure_producer_pin",
        "partial_failure_admission"},"CLOSED_ACTUAL25_PARTIAL_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,physical_product_run=2),
        "EXACT_CURRENT160_PHYSICAL2_MANIFEST")
    a.exact(pin["path"],PATH,"ACTUAL_MANIFEST025_PATH")
    a.exact(row["base_manifest_pin"]["path"],original.PATH,"ORIGINAL_ACTUAL24_MANIFEST")
    admitted=role.admission(q,a)
    a.exact(row["partial_failure_admission"],admitted,"EXACT_PARTIAL_NOT_ACCEPTED_FAILURE_ROLE")
    a.require(hasattr(new_module.source,"failed160_partial_receipt_extension"),
        "PRIVATE_GRAPH_EXPLICIT_PARTIAL160_ROLE_REQUIRED")
    provenance=dict(new_module.source.failed160_partial_receipt_extension)
    provenance["failed_runtime_pin"]=dict(provenance["failed_runtime_pin"])
    provenance["independent_review_pin"]=dict(provenance["independent_review_pin"])
    a.exact(provenance,admitted,"SAME_PARTIAL_ROLE_DECLARATION")
    a.exact(row["partial_failure_role_code_pin"]["path"],ROLE_CODE,"EXACT_PARTIAL_ROLE_CODE_PATH")
    code=a.read_exact(q,row["partial_failure_role_code_pin"])
    a.fields(code,dict(state="PASS_PARTIAL160_FAILURE_ROLE_CODE6_TWO_MEMORY_DECODES_NOT_REAL_MANIFEST_NATIVE_OR_GO",
        contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
        original_failed_runtime_pin=role.ROOT),"QUALIFIED_PARTIAL_ROLE_NOT_PRODUCT")
    for p in code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_ROLE_CODE6_SOURCES")
    a.exact(row["partial_failure_producer_pin"]["path"],PRODUCER,"EXACT_PARTIAL_PRODUCER_PATH")
    produced=a.read_exact(q,row["partial_failure_producer_pin"])
    a.fields(produced,dict(state="PASS_EXCLUSIVE_PARTIAL160_FAILURE_ENVELOPE_NOT_CURRENT_RUNTIME_OR_GO",
        original_pin=role.ROOT,explicit_failure_admission=admitted,original_receipts_rewritten=False,
        decode_passes=2,write_rate_bytes_per_second=2097152,cleanup_confirmed=True),
        "REAL_EXCLUSIVE_FAILURE_DERIVATIVE_NOT_ACCEPTED_RUNTIME")
    a.exact(produced["qualified_role_pin"],row["partial_failure_role_code_pin"],"SAME_ROLE_CODE_BYTES")
    a.exact(produced["physical_pin"],code["memory_physical_pin"],"SAME_PROVEN_LOSSLESS_BYTES")
    for p in produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_PRODUCER_SOURCES")
    base,scope,proof=original.load(q,row["base_manifest_pin"],a,controller=controller,
        new_module=new_module,successor=successor)
    a.exact(len(base.descriptors()),24,"ALL_PREVIOUS24_PRESERVED")
    descriptor=new_module.source.descriptor(role.ROOT,produced["physical_pin"],next_case=160)
    a.exact(q.fresh_pin(role.ROOT["path"]),role.ROOT,"FRESH_UNMODIFIED_PARTIAL_FAILURE")
    a.exact(q.fresh_pin(produced["physical_pin"]["path"]),produced["physical_pin"],"FRESH_REAL_FAILED_ENVELOPE")
    scope=new_module.source.scope.extend(scope,new_module.source.scope.pins([
        role.ROOT,role.REVIEW,pin,row["partial_failure_role_code_pin"],row["partial_failure_producer_pin"]]))
    live=new_module.Binding(base.descriptors()+[descriptor],pin,next_case=160)
    a.exact(len(live.descriptors()),25,"ACTUAL_TWENTY_FIVE_PAIRS")
    q.pin(SELF)
    return live,scope,dict(proof,actual_manifest025_pin=pin,source_pair_count=25,
        original_twenty_four_pairs_retained=True,explicit_partial160_failure_admission=admitted,
        partial_failure_promoted=False,current160_physical2_controller_or_GO_qualified=False)
