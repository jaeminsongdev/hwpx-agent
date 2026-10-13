"""Fresh exact source-manifest admission. Not a Native/product controller.

All old authority/runtime and CODE/producer/focused receipts are read at exact
pins. Current codec/source bytes and original/physical receipt pairs are freshly
checked; no fixture qualification or CLOSED frame becomes product acceptance.
"""
import runtime_envelope_scope_binding_v1 as scope_binding

SELF="tools/p09/runtime_envelope_source_manifest_v1.py"
TEST="tools/p09/tests/test_runtime_envelope_source_manifest_v1.py"
SCHEMA="hwpx-agent.p09-envelope-full-source-manifest/v1"
PATH="implementation/p09/evidence/p09-361-case158-envelope-full-source-manifest019.v1.json"


def load(q, pin, authority):
    a=authority
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","prior_queue_pin",
        "prior_product_pin","descriptors","projection_qualification_pin","physical_qualification_pin",
        "held_guard_qualification_pin","binding_qualification_pin","actual_producer_pin","actual_focus_pin"},"CLOSED_ENVELOPE_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=158,before=151),"MANIFEST_ONLY158")
    a.exact(pin["path"],PATH,"MANIFEST_PATH")
    a.exact(row["prior_queue_pin"]["path"],"implementation/p09/evidence/p09-361-case157-current-epoch-accept001.v1.json","PRIOR_AUTHORITY151_PATH")
    a.exact(row["prior_product_pin"]["path"],"implementation/p09/evidence/p09-361-case157-current-runtime-run001.v1.json","PRIOR_PRODUCT157_PATH")
    prior=a.read_exact(q,row["prior_queue_pin"])
    a.fields(prior,dict(accepted_count_after=151,next_runtime_index=158,resource_cleanup_confirmed=True,P09_gate="OPEN"),"AUTHORITATIVE151")
    a.exact(prior["runtime_candidate_pin"],row["prior_product_pin"],"SAME_ACCEPTED_PRODUCT157")
    root=a.read_exact(q,row["prior_product_pin"])
    a.fields(root,dict(cleanup_confirmed=True,owned_tree_empty=True,Native_source_frame_qualified=True),"ACTUAL_PRIOR_PRODUCT")
    qualifications=[
        ("projection_qualification_pin","p09-361-case158-envelope-source-code11-actual157-candidate-r618.v1.json",11,"PASS_ENVELOPE_SOURCE_PROJECTION_CODE11_REAL157_CANDIDATE_NOT_NATIVE_PRODUCT_OR_ADOPTED"),
        ("physical_qualification_pin","p09-361-case158-envelope-physical-code13-r625.v1.json",13,"PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT"),
        ("held_guard_qualification_pin","p09-361-case158-held-envelope-guard-code7-r627.v1.json",7,"PASS_HELD_ENVELOPE_ORIGINAL_FRAME_DECODER_GUARD_CODE7_NOT_ACTUAL_NATIVE_OR_PRODUCT"),
        ("binding_qualification_pin","p09-361-case158-full-scope-frame-code15-r630.v1.json",15,"PASS_EXPLICIT_FULL_SCOPE_BINDING_AND_ORIGINAL_FRAME_CONNECTION_CODE15_NOT_ACTUAL_WHOLE_OR_PRODUCT")]
    for key,filename,count,state in qualifications:
        p=row[key];a.exact(p["path"],"implementation/p09/evidence/"+filename,"EXACT_QUALIFICATION_PATH")
        code=a.read_exact(q,p)
        a.fields(code,dict(state=state,contracts=dict(run=count,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"QUALIFIED_CODE_NOT_PRODUCT")
        for frozen in code.get("source_pins",[])+code["new_code_pins"]:
            a.exact(q.pin(frozen["path"]),frozen,"FRESH_QUALIFIED_SOURCE")
    a.exact(row["actual_producer_pin"]["path"],"implementation/p09/evidence/p09-361-case158-eight-envelope-producer-r624.v1.json","PRODUCER_PATH")
    produced=a.read_exact(q,row["actual_producer_pin"])
    a.fields(produced,dict(state="PASS_EIGHT_EXPLICIT_LOSSLESS_DERIVATIVES_FRESH_ORIGINALS_AND_OUTPUTS_NOT_CURRENT_NATIVE_OR_PRODUCT",
        exclusive_no_original_overwrite=True,total_derivative_bytes=4831334,cleanup_confirmed=True,current_physical_scope_adopted=False),"ACTUAL_GENERATED_INPUTS_ONLY")
    a.exact(produced["explicit_descriptors"],row["descriptors"],"SAME_ACTUAL_DERIVATIVES")
    a.exact(row["actual_focus_pin"]["path"],"implementation/p09/evidence/p09-361-case158-held-envelope-eight-focused-r628.v1.json","FOCUSED_PATH")
    focused=a.read_exact(q,row["actual_focus_pin"])
    a.fields(focused,dict(state="PASS_ACTUAL_EIGHT_ENVELOPES_TWO_HELD_PHYSICAL_BYTE_AND_SEMANTIC_BOUNDARIES_NOT_WHOLE_CURRENT158_OR_PRODUCT",
        focused_semantic_input_count=8,whole_current_Native_scope_qualified=False,actual_product_or_acceptance_executed=False,
        independent_full_oracle_connection_qualified=False,cleanup_confirmed=True),"FOCUSED_NOT_CURRENT_WHOLE_PRODUCT")
    a.exact(focused["explicit_descriptors"],row["descriptors"],"FOCUSED_SAME_INPUTS")
    a.fields(focused["focused_frame"],dict(frame_state="CLOSED",input_count=8,input_bytes=4831334),"CLOSED_NOT_COMMITTED")
    b=scope_binding.Binding(row["descriptors"],pin,next_case=158)
    inherited=scope_binding.source.scope.extend(scope_binding.source.scope.pins(root["source_freeze"]),
        scope_binding.source.scope.pins([row["prior_product_pin"],pin]))
    for desc in row["descriptors"]:
        original,physical=desc["semantic_original_pin"],desc["physical_envelope_pin"]
        a.exact(inherited.get(original["path"]),original,"ORIGINAL_INSIDE_INHERITED_WHOLE_SCOPE")
        a.exact(q.fresh_pin(original["path"]),original,"FRESH_ORIGINAL_ARCHIVE")
        a.exact(q.fresh_pin(physical["path"]),physical,"FRESH_PHYSICAL_INPUT")
    q.pin(SELF);q.pin(TEST)
    return b,inherited,dict(manifest_fresh_pin=pin,previous_authority=151,
        current_source_namespace_and_receipt_pairs_freshly_checked=True,
        old_CODE_and_actual_focus_not_promoted=True,full_current158_oracle_or_runtime_connected=False,
        metadata_and_worker_raw_live_policy_connected=False,GO_authorized=False)
