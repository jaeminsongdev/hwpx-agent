"""Retain whole25 admission; add one exact cost-selected131 source pair."""
import runtime_successor_manifest_v4 as original

SELF="tools/p09/runtime_successor_manifest_v5.py"
SCHEMA="hwpx-agent.p09-successor160-cost-selected-source-manifest/v5"
PATH="implementation/p09/evidence/p09-361-case160-source-manifest027.v5.json"
PRODUCER="implementation/p09/evidence/p09-361-case160-cost-selected131-producer-r800.v1.json"


def load(q,pin,a,*,controller,new_module,successor):
    row=a.read_exact(q,pin)
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","physical_product_run",
        "base_manifest_pin","extra_producer_pin"},"CLOSED_ACTUAL26_COST_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,physical_product_run=2),
        "EXACT_CURRENT_RUN002_MANIFEST027")
    a.exact(pin["path"],PATH,"EXACT_ACTUAL_MANIFEST027")
    a.exact(row["base_manifest_pin"]["path"],original.PATH,"UNCHANGED_ACTUAL25_MANIFEST")
    a.exact(row["extra_producer_pin"]["path"],PRODUCER,"EXACT_SELECTED131_PRODUCER")
    produced=a.read_exact(q,row["extra_producer_pin"])
    a.fields(produced,dict(state="PASS_COST_SELECTED131_EXCLUSIVE_LOSSLESS_DERIVATIVE_NOT_ADOPTED_CURRENT_RUNTIME_OR_GO",
        original_receipts_rewritten=False,decode_passes=2,write_rate_bytes_per_second=2097152,
        authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT,cleanup_confirmed=True),
        "EXACT_REAL131_PRODUCER_NOT_RUNTIME")
    a.exact(produced["original_pin"]["path"],"implementation/p09/evidence/p09-361-case131-current-runtime-run001.v1.json",
        "ONLY_MEASURED_SELECTED131")
    for p in produced["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_PRODUCER_AND_DIAGNOSTIC_SOURCES")
    base,scope,proof=original.load(q,row["base_manifest_pin"],a,controller=controller,
        new_module=new_module,successor=successor)
    a.exact(len(base.descriptors()),25,"ALL_PREVIOUS25_PRESERVED")
    source=new_module.source
    old,new=produced["original_pin"],produced["physical_pin"]
    a.exact(scope.get(old["path"]),old,"ORIGINAL131_IN_INDEPENDENT_WHOLE_SCOPE")
    descriptor=source.descriptor(old,new,next_case=160)
    a.exact(produced["descriptor"],descriptor,"EXACT_ADOPTED131_DESCRIPTOR")
    a.require(all(d["semantic_original_pin"]["path"]!=old["path"] for d in base.descriptors()),"NOT_ALREADY_ALIASED131")
    a.exact(q.fresh_pin(old["path"]),old,"FRESH_UNMODIFIED_ORIGINAL131")
    a.exact(q.fresh_pin(new["path"]),new,"FRESH_REAL_PHYSICAL131")
    scope=source.scope.extend(scope,source.scope.pins([pin,row["extra_producer_pin"],produced["diagnostic_pin"]]))
    bound=new_module.Binding(base.descriptors()+[descriptor],pin,next_case=160)
    a.exact(len(bound.descriptors()),26,"ACTUAL_TWENTY_SIX_PAIRS")
    q.pin(SELF)
    return bound,scope,dict(proof,actual_manifest027_pin=pin,source_pair_count=26,
        original_twenty_five_pairs_retained=True,selected131_exact_bytes_adopted=True,
        new_controller_complete_cost_or_GO_qualified=False)
