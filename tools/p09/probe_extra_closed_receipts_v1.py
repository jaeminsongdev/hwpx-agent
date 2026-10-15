"""Independently verify extra prior aliases and compare declared scope costs.

No current runner/Native/worker/GO adoption. Entire prior declared scope stays;
new manifest metadata is explicit, originals and previous reports are immutable.
"""
from pathlib import Path
import sys

SELF="tools/p09/probe_extra_closed_receipts_v1.py"
PRODUCER=dict(path="tools/p09/expand_closed_preparation_receipts_v1.py",bytes=8659,
    sha256="61bf578ad64d31de7a3107285e25d1bcdbad5d08d6b4b2042108af5a690158ac")
EXTRA_PINS=[
    dict(path="tools/p09/current_queue_successor_binding.py",bytes=15040,sha256="6d48c8df7a085461bdad22f8ee4be2baa9675f8035b558f7bc3474b52ea6e915"),
    dict(path="tools/p09/closed_prebody_source_alias_v1.py",bytes=20052,sha256="153f31453a9a87433d3f0b2bdabc6ceb1151e8c14e29fc7e7faea1fe9f5ae0c9"),
    dict(path="tools/p09/current_queue_successor_wire_runtime_v2.py",bytes=11932,sha256="74c509ee713b571a8ed8d52f904513a567ff19391fb418942d1336a5ce6d6efd")]
OLD=dict(path="tools/p09/case160_run007_controller.py",bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")


def require(ok,label):
    if not ok:raise ValueError("EXTRA_CLOSED_PROBE_"+label)


def main():
    import argparse,hashlib,json,re,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    parser.add_argument("--producer-attempt",type=int,default=1)
    args=parser.parse_args()
    require(165<=args.case<=249 and 4<=args.run<=8 and all(1<=v<=8 for v in (args.attempt,args.producer_attempt)),"CLOSED_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{args.case}-"
    output=prefix+f"extra-ordinary-projection{args.attempt:03}.v1.json"
    manifest_name=prefix+f"successor-extra-probe-manifest{args.attempt:03}.v1.json"
    require(all(not (c.ROOT/name).exists() for name in (output,manifest_name)),"EXCLUSIVE_OUTPUTS")
    producer_ns,_=envelope.namespace_bundle.load(c.ROOT,[PRODUCER],{})
    producer=producer_ns.expand_closed_preparation_receipts_v1
    modules,_=envelope.namespace_bundle.load(c.ROOT,producer.PINS+EXTRA_PINS,
        {"current_stored_runtime_scope":scope,"owned_source_read_pressure":bytes_policy})
    alias=modules.closed_prebody_source_alias_v1;bindings=modules.current_queue_successor_binding
    publisher=modules.successor_preparation_workspace_v1
    guard=modules.terminal_metadata_pressure_v1.guard_type(modules.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic()
    row=dict(state="FAILED_EXTRA_ORDINARY_PROJECTION_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0,
        original_receipts_rewritten=False,whole_current_source_byte_inventory_rechecked=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        for pin in [PRODUCER]+producer.PINS+EXTRA_PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_CURRENT_PROJECTION_COMPONENTS")
        name=prefix+f"extra-ordinary-receipts{args.producer_attempt:03}.v1.json"
        produced=q.json(name)
        a.fields(produced,dict(schema_version="hwpx-agent.p09-extra-ordinary-closed-preparation-receipts/v1",
            state="PREPARED_EXTRA_ORDINARY_RECEIPTS_NOT_RUNTIME_OR_PRODUCT",index=args.case,physical_run=args.run,
            cleanup_confirmed=True,product_or_Native_executed=False,accepted_count_delta=0,original_receipts_rewritten=False),"ACTUAL_EXTRA_PRODUCER")
        require(type(produced["fresh_inputs"]) is int and produced["fresh_inputs"]==produced["final_fresh_hashes"]>0,"PRODUCER_FINAL_HASHES")
        inventory=scope.pins(produced["source_pins"])
        for pin in [PRODUCER]+producer.PINS:a.exact(inventory.get(pin["path"]),pin,"PRODUCER_SOURCE_WITNESSES")
        code=q.json(producer.CODE)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_CODEC_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"QUALIFIED_CODEC_SOURCES")
        graph=a.read_exact(q,produced["base_graph_pin"]);manifest=a.read_exact(q,graph["manifest_pin"])
        step=graph["step"]
        authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
        a.fields(authority,dict(accepted_count_after=args.case-7,next_runtime_index=args.case,
            runtime_candidate_pin=step["prior_candidate_pin"],resource_cleanup_confirmed=True),"APPROVED_PREDECESSOR_NOT_CURRENT_OBSERVATIONS")
        pairs=produced["explicit_descriptors"]
        require(type(pairs) is list and 1<=len(pairs)<=6,"BOUNDED_EXTRA_PAIRS")
        expected=modules.current_queue_successor_connections.select_extra_receipts(scope,
            prior["source_input_representation"]["semantic_source_freeze"],manifest["descriptors"],args.case,len(pairs))
        a.exact(produced["expected_original_pins"],expected,"RESELECTED_FROM_APPROVED_PREDECESSOR_SCOPE")
        module,_=bindings.connect(c.ROOT,envelope.namespace_bundle,scope,args.case,
            manifest["historical_predecessor_provenance"],prior["source_input_representation"]["descriptors"])
        policy=alias.verify(q,manifest["closed_prebody_source_policy"]["producer_pin"],args.case,args.run,a,scope,
            modules.current_queue_successor_wire_runtime_v2,module.source.codec,module.source.SCHEMA)
        alias.install(module,policy)
        for old,pair in zip(expected,pairs):
            a.exact(pair["semantic_original_pin"],old,"EXACT_EXTRA_ORIGINAL_EXPECTATION")
            new=pair["physical_envelope_pin"]
            a.exact(module.source.descriptor(old,new,next_case=args.case),pair,"ORDINARY_DESCRIPTOR_UNCHANGED")
            match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",old["path"])
            require(match is not None and new["path"]==f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{match[1]}-runtime-run{match[2]}.envelope.v1.json","CANONICAL_EXPLICIT_PHYSICAL_PATH")
            a.exact(inventory.get(old["path"]),old,"ORIGINAL_PRODUCER_INVENTORY")
            a.exact(inventory.get(new["path"]),new,"PHYSICAL_PRODUCER_INVENTORY")
            raw_pin,raw=q._read(old["path"],parse=True);q._bind(old["path"],raw_pin);a.exact(raw_pin,old,"FRESH_ORIGINAL")
            encoded_pin,encoded=q._read(new["path"],parse=True);q._bind(new["path"],encoded_pin);a.exact(encoded_pin,new,"FRESH_ENCODED")
            a.exact(module.source.codec.decode(bytes(encoded),guard.check),bytes(raw),"WHOLE_BYTES_INDEPENDENTLY_RESTORED")
        old_bytes=sum(p["bytes"] for p in expected);new_bytes=sum(p["physical_envelope_pin"]["bytes"] for p in pairs)
        a.fields(produced,dict(original_bytes=old_bytes,encoded_bytes=new_bytes,bytes_saved=old_bytes-new_bytes,decode_passes=2*len(pairs)),"EXACT_PRODUCTION_STATISTICS")
        pref=a.read_exact(q,produced["base_preflight_pin"])
        a.fields(pref,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            index=args.case,physical_run=args.run,cleanup_confirmed=True),"SEALED_DECLARED_BASELINE_ONLY")
        require(type(pref["fresh_inputs"]) is int and pref["fresh_inputs"]==pref["final_fresh_hashes"]>0,"BASELINE_FINAL_HASHES")
        baseline=module.Binding(manifest["descriptors"],graph["manifest_pin"],next_case=args.case)
        original_scope=scope.pins(pref["complete_semantic_source_scope"])
        expanded=dict(manifest,descriptors=manifest["descriptors"]+pairs,extra_ordinary_producer_pin=q.snapshots[name],
            extra_originals_independently_reselected_from_approved_predecessor=True,diagnostic_only_not_runtime_adoption=True)
        new_manifest=publisher.publish(c.ROOT,manifest_name,expanded,a);a.exact(q.pin(manifest_name),new_manifest,"ACTUAL_PROBE_MANIFEST")
        current=module.Binding(expanded["descriptors"],new_manifest,next_case=args.case)
        current_scope=scope.extend(original_scope,{new_manifest["path"]:new_manifest})
        before,_=baseline.project(original_scope,guard.check);after,_=current.project(current_scope,guard.check)
        a.exact({n:dict(after.semantic_pins[n]) for n in before.semantic_pins},
            {n:dict(p) for n,p in before.semantic_pins.items()},"EVERY_ORIGINAL_SEMANTIC_INPUT_UNCHANGED")
        require(set(after.semantic_pins)-set(before.semantic_pins)=={new_manifest["path"]},"ONLY_NEW_MANIFEST_METADATA_ADDED")
        old_names,_=envelope.namespace_bundle.load(c.ROOT,[OLD],{"flat_current_queue_envelope_runtime_v25":envelope})
        a.exact(q.pin(OLD["path"]),OLD,"ORIGINAL_COMPLETE_COST_ENGINE_SOURCE")
        complete_budget=old_names.case160_run007_controller.old.prior.DIRECT.runtime_budget
        requests=pref["whole_Rust_inventory"]["requests"]
        require(requests==167,"ORIGINAL_FULL_RUST_FINAL_INVENTORY_RESERVATIONS")
        before_model=baseline.runtime_budget(original_scope,requests,complete_budget,guard.check)
        after_model=current.runtime_budget(current_scope,requests,complete_budget,guard.check)
        q.finish();guard.check(force=True)
        row.update(state="PASS_EXTRA_ORDINARY_DECLARED_SCOPE_AND_COST_NOT_CURRENT_ENTRY_ADOPTION",pair_count=len(current.descriptors()),
            baseline_semantic_inputs=len(before.semantic_pins),expanded_semantic_inputs=len(after.semantic_pins),
            original_bytes=old_bytes,encoded_bytes=new_bytes,bytes_saved=old_bytes-new_bytes,
            before_declared_cost_seconds=before_model["predicted_runtime_combined_seconds"],
            after_declared_cost_seconds=after_model["predicted_runtime_combined_seconds"],
            expanded_manifest_pin=new_manifest,producer_pin=q.snapshots[name],source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_parent_worker_oracle_and_actual_entry_cost_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"PROBE_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","pair_count","baseline_semantic_inputs","expanded_semantic_inputs",
        "bytes_saved","before_declared_cost_seconds","after_declared_cost_seconds","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","error_type")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
