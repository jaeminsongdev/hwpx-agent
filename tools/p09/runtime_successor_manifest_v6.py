"""Run003 actual29 declaration; retain whole26 and add three exact receipts."""
import runtime_successor_manifest_v5 as original
SELF="tools/p09/runtime_successor_manifest_v6.py"
SCHEMA="hwpx-agent.p09-successor160-run003-source-manifest/v6"
PATH="implementation/p09/evidence/p09-361-case160-source-manifest028.v6.json"
PRODUCER="implementation/p09/evidence/p09-361-case160-cost-selected-three-producer-r819.v1.json"

def load(q,pin,a,*,controller,new_module,successor):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","physical_product_run",
        "base_manifest_pin","extra_producer_pin"},"CLOSED_ACTUAL29_RUN003_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,physical_product_run=3),"EXACT_RUN003_MANIFEST028")
    a.exact(pin["path"],PATH,"ACTUAL_MANIFEST028_PATH")
    a.exact(row["base_manifest_pin"]["path"],original.PATH,"UNCHANGED_HISTORICAL_RUN002_MANIFEST027")
    a.exact(row["extra_producer_pin"]["path"],PRODUCER,"EXACT_THREE_PRODUCER")
    produced=a.read_exact(q,row["extra_producer_pin"])
    a.fields(produced,dict(state="PASS_COST_SELECTED_THREE_EXCLUSIVE_LOSSLESS_DERIVATIVES_NOT_ADOPTED_CURRENT_RUNTIME_OR_GO",
        source_pair_count=3,decode_passes=6,original_receipts_rewritten=False,write_rate_bytes_per_second=2097152,
        authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT,cleanup_confirmed=True),"ORIGINAL_THREE_EXACT_OUTPUTS")
    a.exact([p["original_pin"]["path"] for p in produced["selected_outputs"]],
        ["implementation/p09/evidence/p09-361-case%03d-current-runtime-run001.v1.json"%i for i in (133,138,137)],
        "ONLY_MEASURED_SELECTED_THREE")
    a.require(produced["fresh_inputs"]==produced["final_fresh_hashes"]>0,"COMPLETE_PRODUCER_FINAL_FRESHNESS")
    for p in produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_THREE_PRODUCER_SOURCES")
    base,scope,proof=original.load(q,row["base_manifest_pin"],a,controller=controller,
        new_module=new_module,successor=successor)
    a.exact(len(base.descriptors()),26,"ALL_PREVIOUS26_PRESERVED")
    source=new_module.source;descriptors=base.descriptors()
    for item in produced["selected_outputs"]:
        old,new=item["original_pin"],item["physical_pin"]
        a.exact(scope.get(old["path"]),old,"SELECTED_SOURCE_IN_INDEPENDENT_WHOLE_SCOPE")
        a.require(all(d["semantic_original_pin"]["path"]!=old["path"] for d in descriptors),"NO_REPEATED_SOURCE_ALIAS")
        desc=source.descriptor(old,new,next_case=160)
        a.exact(desc,item["descriptor"],"EXACT_NEW_SOURCE_DESCRIPTOR")
        a.exact(q.fresh_pin(old["path"]),old,"FRESH_UNMODIFIED_ORIGINAL")
        a.exact(q.fresh_pin(new["path"]),new,"FRESH_REAL_PHYSICAL_DERIVATIVE")
        descriptors.append(desc)
    scope=source.scope.extend(scope,source.scope.pins([pin,row["extra_producer_pin"],produced["diagnostic_pin"]]))
    bound=new_module.Binding(descriptors,pin,next_case=160)
    a.exact(len(bound.descriptors()),29,"ACTUAL_TWENTY_NINE_PAIRS")
    q.pin(SELF)
    return bound,scope,dict(proof,actual_manifest028_pin=pin,source_pair_count=29,
        original26_pairs_retained=True,physical_run003_declared_without_relabeling_prior_run002=True,
        current_run003_controller_or_Native_or_GO_qualified=False)
