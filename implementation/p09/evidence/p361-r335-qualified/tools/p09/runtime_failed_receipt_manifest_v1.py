"""V2's eleven pairs plus one explicitly reviewed same-case failed receipt.

Requires the separately qualified private failed-role source graph. Keeps every
V2 source/producer/qualifier and both original and encoded fresh byte pins.
No current controller/worker/full-oracle or Gate qualification is inferred.
"""
import runtime_envelope_source_manifest_v2 as original
import runtime_failed_receipt_projection_v1 as failed

SELF="tools/p09/runtime_failed_receipt_manifest_v1.py"
TEST="tools/p09/tests/test_runtime_failed_receipt_manifest_v1.py"
SCHEMA="hwpx-agent.p09-envelope-failed-receipt-manifest/v1"
PATH="implementation/p09/evidence/p09-361-case158-envelope-failed-source-manifest021.v1.json"
CODE="implementation/p09/evidence/p09-361-case158-failed003-role-projection-code9-r691.v1.json"
PRODUCER="implementation/p09/evidence/p09-361-case158-failed003-exclusive-producer-r692.v1.json"


def load(q,pin,a):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","base_manifest_pin",
        "failed_role_code_pin","failed_producer_pin","failed_descriptor","failure_admission"},"CLOSED_FAILED_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=158,before=151),"ONLY_CURRENT158_MANIFEST")
    a.exact(pin["path"],PATH,"EXACT_FAILED_MANIFEST_PATH")
    a.exact(row["base_manifest_pin"]["path"],original.PATH,"ORIGINAL_ELEVEN_MANIFEST")
    a.exact(row["failed_role_code_pin"]["path"],CODE,"EXACT_FAILED_ROLE_CODE_PATH")
    code=a.read_exact(q,row["failed_role_code_pin"])
    a.fields(code,dict(state="PASS_EXACT_FAILED003_ROLE_CODE9_AND_TWO_MEMORY_PROJECTION_DECODES_NOT_CURRENT_RUNTIME_OR_GO",
        contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"FAILED_ROLE_CODE9_NOT_RUNTIME")
    for p in code["new_code_pins"]+code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_ROLE_SOURCE_BYTES")
    admitted=failed.admission(q,a)
    a.exact(admitted,row["failure_admission"],"FRESH_ROLE_EQUALS_DECLARATION")
    module=original.original.scope_binding
    a.require(hasattr(module.source,"failed_receipt_extension"),"QUALIFIED_PRIVATE_GRAPH_REQUIRED")
    base,inherited,proof=original.load(q,row["base_manifest_pin"],a)
    a.exact(row["failed_producer_pin"]["path"],PRODUCER,"EXACT_FAILED_PRODUCER_PATH")
    produced=a.read_exact(q,row["failed_producer_pin"])
    a.fields(produced,dict(state="PASS_EXCLUSIVE_FAILED003_LOSSLESS_DERIVATIVE_NOT_CURRENT_RUNTIME_OR_GO",
        original_pin=failed.ROOT,explicit_failure_admission=admitted,exact_original_failure_retained=True,
        original_receipts_rewritten=False,current_physical_source_scope_adopted=False,
        decode_passes=2,write_rate_bytes_per_second=2097152,cleanup_confirmed=True),"ACTUAL_PRODUCER_NOT_PRODUCT")
    a.exact(row["failed_descriptor"],produced["descriptor"],"SAME_FAILED_SOURCE_PAIR")
    desc=row["failed_descriptor"]
    a.exact(desc,module.source.descriptor(failed.ROOT,produced["physical_pin"],next_case=158),"EXACT_TYPED_FAILED_PAIR")
    for p in produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_PRODUCER_SOURCES")
    a.exact(q.fresh_pin(failed.ROOT["path"]),failed.ROOT,"FRESH_UNREWRITTEN_FAILURE_ROOT")
    a.exact(q.fresh_pin(produced["physical_pin"]["path"]),produced["physical_pin"],"FRESH_FAILED_PHYSICAL_BYTES")
    descriptors=base.descriptors()+[desc]
    a.require(len(descriptors)==12,"EXACT_TWELVE_PAIRS")
    binding=module.Binding(descriptors,pin,next_case=158)
    inherited=module.source.scope.extend(inherited,module.source.scope.pins([failed.ROOT,pin]))
    q.pin(SELF);q.pin(TEST)
    return binding,inherited,dict(proof,failed_role_admission=admitted,source_pair_count=12,
        original_eleven_pairs_preserved=True,whole_current_Runtime_or_Native_or_product_qualified=False,
        current_controller_worker_and_full_oracle_connected=False,GO_authorized=False)
