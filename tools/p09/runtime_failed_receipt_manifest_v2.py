"""Retain manifest021's twelve pairs, add explicit failed004 and prior144-146.

All old admissions, fresh original/physical pins and reviewer sources remain.
Requires a newly owned graph with both failure roles explicitly connected.
No current controller/worker/full-scope/cost/GO qualification is inferred.
"""
import runtime_failed_receipt_manifest_v1 as original
import runtime_failed_receipt_projection_v2 as failed

SELF="tools/p09/runtime_failed_receipt_manifest_v2.py"
TEST="tools/p09/tests/test_runtime_failed_receipt_manifest_v2.py"
SCHEMA="hwpx-agent.p09-envelope-two-failure-manifest/v2"
PATH="implementation/p09/evidence/p09-361-case158-envelope-failed-source-manifest022.v2.json"
CODE="implementation/p09/evidence/p09-361-case158-failed004-role-projection-code9-r715.v1.json"
PRODUCER="implementation/p09/evidence/p09-361-case158-failed004-exclusive-producer-r716.v1.json"
EXTRA="implementation/p09/evidence/p09-361-case158-prior144to146-envelope-producer-r714.v1.json"
SELECTION="implementation/p09/evidence/p09-361-case158-prior144to146-lossless-selection-r713.v1.json"


def load(q,pin,a):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","base_manifest_pin",
        "failed004_role_code_pin","failed004_producer_pin","failed004_descriptor","failure004_admission",
        "extra_three_producer_pin","extra_three_descriptors"},"CLOSED_TWO_FAILURE_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=158,before=151),"ONLY_CURRENT158_NEW_MANIFEST")
    a.exact(pin["path"],PATH,"EXACT_NEW_MANIFEST_PATH")
    a.exact(row["base_manifest_pin"]["path"],original.PATH,"ORIGINAL_MANIFEST021")
    module=original.original.original.scope_binding
    a.require(hasattr(module.source,"failed_receipt_extension") and
        hasattr(module.source,"failed004_receipt_extension"),"EXPLICIT_BOTH_PRIVATE_FAILURE_ROLES")
    base,inherited,proof=original.load(q,row["base_manifest_pin"],a)
    a.exact(row["failed004_role_code_pin"]["path"],CODE,"EXACT_FAILED004_CODE_PATH")
    code=a.read_exact(q,row["failed004_role_code_pin"])
    a.fields(code,dict(state="PASS_EXACT_FAILED004_ROLE_CODE9_AND_TWO_MEMORY_PROJECTION_DECODES_NOT_CURRENT_RUNTIME_OR_GO",
        contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"FAILED004_COMPONENT_NOT_GO")
    for p in code["new_code_pins"]+code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_FAILED004_CODE_BYTES")
    admission=failed.admission(q,a)
    a.exact(admission,row["failure004_admission"],"ACTUAL_FRESH_FAILED004_ADMISSION")
    a.exact(row["failed004_producer_pin"]["path"],PRODUCER,"EXACT_FAILED004_PRODUCER_PATH")
    produced=a.read_exact(q,row["failed004_producer_pin"])
    a.fields(produced,dict(state="PASS_EXCLUSIVE_FAILED004_LOSSLESS_DERIVATIVE_NOT_CURRENT_RUNTIME_OR_GO",
        original_pin=failed.ROOT,explicit_failure_admission=admission,exact_original_failure_retained=True,
        original_receipts_rewritten=False,current_physical_source_scope_adopted=False,decode_passes=2,
        write_rate_bytes_per_second=2097152,cleanup_confirmed=True),"FAILED004_DERIVATIVE_NOT_PRODUCT")
    a.exact(row["failed004_descriptor"],produced["descriptor"],"EXACT_FAILED004_PAIR")
    desc=row["failed004_descriptor"]
    a.exact(desc,module.source.descriptor(failed.ROOT,produced["physical_pin"],next_case=158),"TYPED_FAILED004_PAIR")
    for p in produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_FAILED004_PRODUCER")
    a.exact(q.fresh_pin(failed.ROOT["path"]),failed.ROOT,"FRESH_UNREWRITTEN_FAILED004")
    a.exact(q.fresh_pin(produced["physical_pin"]["path"]),produced["physical_pin"],"FRESH_FAILED004_DERIVATIVE")
    a.exact(row["extra_three_producer_pin"]["path"],EXTRA,"EXACT_NEW_PRIOR_THREE_PRODUCER")
    extra=a.read_exact(q,row["extra_three_producer_pin"])
    a.fields(extra,dict(state="PASS_THREE_EXTRA_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_NATIVE_OR_PRODUCT",
        original_receipts_rewritten=False,decode_passes=6,write_rate_bytes_per_second=2097152,
        cleanup_confirmed=True),"THREE_PRIOR_DERIVATIVES_NOT_PRODUCT_REPLAY")
    a.exact(extra["authority151_pin"],q.snapshots["implementation/p09/evidence/p09-361-case157-current-epoch-accept001.v1.json"],
        "SAME_FRESH_AUTHORITY151")
    a.exact(extra["actual157_pin"],q.snapshots["implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json"],
        "SAME_UNREPLAYED_RUNTIME157")
    a.exact(extra["selection_pin"]["path"],SELECTION,"EXACT_THREE_SELECTION")
    selection=a.read_exact(q,extra["selection_pin"])
    a.fields(selection,dict(state="PASS_EXACT_THREE_EXTRA_RECEIPT_SIZE_SELECTION_NOT_DERIVATIVES_OR_NATIVE",
        selected_indices=[144,145,146],cleanup_confirmed=True),"EXACT_PRIOR_SELECTION")
    a.require(type(selection["top_additional_candidates"]) is list and
        len(selection["top_additional_candidates"])==3,"ALL_THREE_SELECTION_PINS")
    a.exact(extra["explicit_descriptors"],row["extra_three_descriptors"],"EXACT_THREE_ACTUAL_PAIRS")
    a.require(type(row["extra_three_descriptors"]) is list and len(row["extra_three_descriptors"])==3,
        "EXACT_THREE_PRIOR_PAIRS")
    for p in extra["source_pins"]+selection["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_THREE_PRODUCER_AND_SELECTION")
    for item,expected in zip(row["extra_three_descriptors"],selection["top_additional_candidates"]):
        old,new=item["semantic_original_pin"],item["physical_envelope_pin"]
        a.exact(old,expected,"SAME_EXACT_SELECTED_PRIOR_PIN")
        a.exact(inherited.get(old["path"]),old,"PRIOR_ORIGINAL_IN_INHERITED_WHOLE_SCOPE")
        a.exact(item,module.source.descriptor(old,new,next_case=158),"EXACT_TYPED_PRIOR_PAIR")
        a.exact(q.fresh_pin(old["path"]),old,"FRESH_PRIOR_ORIGINAL_BYTES")
        a.exact(q.fresh_pin(new["path"]),new,"FRESH_PRIOR_DERIVATIVE_BYTES")
    descriptors=base.descriptors()+[desc]+row["extra_three_descriptors"]
    a.require(len(descriptors)==16,"EXACT_SIXTEEN_EXPLICIT_PAIRS")
    binding=module.Binding(descriptors,pin,next_case=158)
    inherited=module.source.scope.extend(inherited,module.source.scope.pins([failed.ROOT,pin]))
    q.pin(SELF);q.pin(TEST)
    return binding,inherited,dict(proof,source_pair_count=16,failed004_admission=admission,
        original_twelve_pairs_retained=True,current_controller_worker_and_full_oracle_connected=False,
        complete_current_scope_or_cost_qualified=False,GO_authorized=False)
