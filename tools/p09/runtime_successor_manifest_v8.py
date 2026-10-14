"""Actual run004 declaration retaining32 and adding two exact real priors."""
import runtime_successor_manifest_v7 as original
SELF="tools/p09/runtime_successor_manifest_v8.py"
TEST="tools/p09/tests/test_runtime_successor_manifest_v8.py"
SCHEMA="hwpx-agent.p09-successor160-run004-source-manifest/v8"
PATH="implementation/p09/evidence/p09-361-case160-source-manifest030.v8.json"
PRODUCER="implementation/p09/evidence/p09-361-case160-prior136130-producer-r854.v1.json"
PRIORS=(dict(path="implementation/p09/evidence/p09-361-case136-current-runtime-run001.v1.json",bytes=2461083,
    sha256="b1a7b13d76de8946340dca11e21dcf7480c17a8999117b08102138aaba8d4043"),
    dict(path="implementation/p09/evidence/p09-361-case130-current-runtime-run001.v1.json",bytes=2417619,
    sha256="4596a1972a5f5e0cfa1160d9672ce3d01c6feaef7e62cf83d800317eef351a26"))

def validate(row,a,base_pin):
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","physical_product_run",
        "base_manifest_pin","extra_prior_producer_pin"},"CLOSED_REAL34_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,physical_product_run=4,base_manifest_pin=base_pin),
        "EXACT34_SAME_RUN004_CONTEXT")
    a.exact(row["extra_prior_producer_pin"]["path"],PRODUCER,"ONLY_REAL136130_PRODUCER")
    return row

def selected(producer,a):
    a.fields(producer,dict(state="PASS_REAL_PRIOR136130_EXCLUSIVE_LOSSLESS_NOT_ADOPTED_MANIFEST_OR_GO",
        exact_original_restore_passes=4,write_rate_bytes_per_second=2097152,cleanup_confirmed=True,
        original_receipts_rewritten=False,product_or_Native_reexecuted=False,GO_authorized=False),"REAL_TWO_PRIOR_PRODUCER")
    a.require(producer["fresh_inputs"]==producer["final_fresh_hashes"]>0,"ALL_TWO_PRIOR_FINAL_HASHES")
    rows=producer["selected_outputs"]
    a.require(type(rows) is list and len(rows)==2,"ONLY_TWO_REAL_PRIORS")
    for root,item in zip(PRIORS,rows):a.exact(item["original_pin"],root,"EXACT136130_ORDER_AND_BYTES")
    return rows

def load(q,pin,a,*,base_graph,base29_pin,base32_pin,prepared_scope):
    row=validate(a.read_exact(q,pin),a,base32_pin);a.exact(pin["path"],PATH,"ACTUAL_MANIFEST030_PATH")
    bound,scope,proof=original.load(q,base32_pin,a,base_graph=base_graph,base_pin=base29_pin,prepared_scope=prepared_scope)
    a.exact(len(bound.descriptors()),32,"ALL_ORIGINAL32_RETAINED")
    producer=a.read_exact(q,row["extra_prior_producer_pin"]);items=selected(producer,a)
    for p in producer["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT136130_PRODUCER_SOURCES")
    source=base_graph.binding_module.source;descriptors=bound.descriptors()
    for root,item in zip(PRIORS,items):
        a.exact(scope.get(root["path"]),root,"BOTH_PRIORS_IN_REAL_INHERITED_SCOPE")
        a.require(all(d["semantic_original_pin"]["path"]!=root["path"] for d in descriptors),"NO_PRIOR_ALIAS_REPLACEMENT")
        a.exact(q.fresh_pin(root["path"]),root,"FRESH_UNMODIFIED_REAL_PRIOR")
        a.exact(q.fresh_pin(item["physical_pin"]["path"]),item["physical_pin"],"FRESH_REAL_PRIOR_PHYSICAL")
        descriptor=source.descriptor(root,item["physical_pin"],next_case=160)
        a.exact(descriptor,item["descriptor"],"ALL_REAL_PRIOR_DESCRIPTOR_FIELDS")
        descriptors.append(descriptor)
    scope=source.scope.extend(scope,q.snapshots);scope=source.scope.extend(scope,{pin["path"]:pin})
    bound=base_graph.binding_module.Binding(descriptors,pin,next_case=160)
    a.exact(len(bound.descriptors()),34,"ACTUAL_ALL34")
    q.pin(SELF)
    return bound,source.scope.extend(scope,q.snapshots),dict(proof,actual_manifest030_pin=pin,source_pairs=34,
        all_previous32_retained=True,extra_real_prior_pins=list(PRIORS),
        new_controller_Native_independent_product_oracle_or_GO_qualified=False)
