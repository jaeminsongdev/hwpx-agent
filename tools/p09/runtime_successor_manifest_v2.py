"""Actual160 manifest admission through unchanged complete159 admission."""
SELF="tools/p09/runtime_successor_manifest_v2.py"
SCHEMA="hwpx-agent.p09-successor160-source-manifest/v2"
PATH="implementation/p09/evidence/p09-361-case160-source-manifest024.v2.json"
SELECTION="implementation/p09/evidence/p09-361-case160-step-and-lossless-selection-r753.v1.json"
PRODUCER="implementation/p09/evidence/p09-361-case160-four-envelope-producer-r754.v1.json"


def load(q,pin,a,*,controller,new_module,successor):
    m=controller;old=m.old
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","authority_pin","prior_runtime_pin",
        "prior_manifest_pin","selection_pin","extra_producer_pin","successor_context"},"CLOSED_ACTUAL160_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,authority_pin=successor.AUTHORITY,
        prior_runtime_pin=successor.ROOT),"EXACT160_CURRENT_MANIFEST")
    a.exact(pin["path"],PATH,"EXACT160_MANIFEST_PATH")
    prior=a.read_exact(q,successor.ROOT)
    a.exact(row["prior_manifest_pin"],prior["source_input_representation"]["manifest_pin"],"UNCHANGED_ACTUAL159_MANIFEST_PIN")
    graph=m.graph_value()
    previous,inherited,old_proof=m.current_binding.manifest.load(q,row["prior_manifest_pin"],a,
        old_manifest=old.manifest,new_module=graph.binding_module,successor=m.current_binding.successor,
        failed003=old.failed_role,failed004=old.failed004_role)
    a.require(type(previous) is not new_module.Binding,"SEPARATE_ACTUAL159_AND160_CONSTRUCTORS")
    a.exact(previous.descriptors(),prior["source_input_representation"]["descriptors"],"ALL_ACTUAL159_TWENTY_PAIRS")
    current=successor.admission(q,a,old.failed_role,old.failed004_role)
    a.exact(row["successor_context"],current,"FRESH160_CURRENT_AND_HISTORICAL159_CONTEXT")
    a.exact(row["selection_pin"]["path"],SELECTION,"EXACT160_SELECTION_PATH")
    selected=a.read_exact(q,row["selection_pin"])
    a.fields(selected,dict(state="PASS_ACTUAL153_SUCCESSOR160_STEP_AND_FOUR_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
        authority153_pin=successor.AUTHORITY,actual159_pin=successor.ROOT,cleanup_confirmed=True),"EXACT160_SELECTION")
    a.exact(row["extra_producer_pin"]["path"],PRODUCER,"EXACT160_PRODUCER_PATH")
    produced=a.read_exact(q,row["extra_producer_pin"])
    a.fields(produced,dict(state="PASS_FOUR_SUCCESSOR160_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_RUNTIME_OR_GO",
        authority153_pin=successor.AUTHORITY,actual159_pin=successor.ROOT,original_receipts_rewritten=False,
        decode_passes=8,write_rate_bytes_per_second=2097152,cleanup_confirmed=True),"ORIGINAL_FOUR160_EXCLUSIVE_OUTPUTS")
    for p in selected["source_pins"]+produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT160_SELECTION_AND_PRODUCER_SOURCES")
    source=new_module.source
    scope=source.scope.extend(source.scope.extend(inherited,
        source.scope.pins(prior["source_input_representation"]["semantic_source_freeze"])),
        source.scope.pins([successor.AUTHORITY,successor.ROOT,pin]))
    descriptors=[source.descriptor(d["semantic_original_pin"],d["physical_envelope_pin"],next_case=160)
        for d in previous.descriptors()]
    a.require(len(selected["selected_originals"])==len(produced["explicit_descriptors"])==4,"FOUR160_EXPLICIT_PAIRS")
    for desc,chosen in zip(produced["explicit_descriptors"],selected["selected_originals"]):
        original,physical=desc["semantic_original_pin"],desc["physical_envelope_pin"]
        a.exact(original,chosen,"SAME_SELECTED160_ORIGINAL")
        a.exact(scope.get(original["path"]),original,"NEW_ORIGINAL_INSIDE_INDEPENDENT_PRIOR_SCOPE")
        a.exact(desc,source.descriptor(original,physical,next_case=160),"EXACT160_DESCRIPTOR")
        descriptors.append(desc)
    a.exact(len(descriptors),24,"ALL_ACTUAL160_TWENTY_FOUR_PAIRS")
    for d in descriptors:
        for p in (d["semantic_original_pin"],d["physical_envelope_pin"]):
            a.exact(q.fresh_pin(p["path"]),p,"FRESH160_ALL_ORIGINAL_AND_PHYSICAL_BYTES")
    bound=new_module.Binding(descriptors,pin,next_case=160)
    q.pin(SELF)
    return bound,scope,dict(old_proof,source_pair_count=24,actual_manifest_pin=pin,
        unchanged_complete159_admission_executed=True,original_historical159_lineage_not_relabelled=True,
        current160_whole_controller_scope_Native_or_GO_qualified=False)
