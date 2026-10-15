"""Prepare v2 lineage-complete metadata, then run original parent callback.

Metadata/declared-scope and cost planning only: never acquire a Native Source
Frame or execute parent engine/worker/product. Existing v1 artifacts remain.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import FunctionType

SELF="tools/p09/native009_parent_scope_v1.py"
TEST="tools/p09/tests/test_native009_parent_scope_v1.py"
PREFIX="implementation/p09/evidence/p09-361-case165-"
MANIFEST=PREFIX+"successor-native009-parent69-manifest001.v1.json"
CAPSULE=PREFIX+"successor-worker-capsule009.compact.v2.json"
BOOTSTRAP=PREFIX+"successor-worker-bootstrap009.v2.json"
GRAPH=PREFIX+"successor-native009-parent-graph001.v2.json"


def admit_failed_declaration(q,failed,a,producer):
    # The unchanged parent callback consumes q.snapshots. Declare/read the new
    # failed original BEFORE its full69 union, never remove that requirement.
    row=a.read_exact(q,failed.ORIGINAL)
    producer.failed_state(row)
    return row


def inherit_declaration(graph,inherited,scope):
    """Preparation only: keep the failed parent's full declaration, not PASS.

    Neither metadata pins nor this union qualify a current byte boundary.
    The complete original union still rejects conflicts and missing originals.
    """
    declared=scope.pins(list(inherited.values()))
    require(declared==inherited,"EXACT_INHERITED_MAPPING")
    cls=type(graph.binding);original=cls.semantic_union
    require(not getattr(cls,"native009_preparation_declaration",False),"ONE_PREPARATION_DECLARATION")
    proof=dict(inherited_declared_inputs=len(declared),first_union_added_original_paths=None,
        current_fresh_hashes_or_Frame_qualified=False,original_union_retained=True)
    def union(self,rows,checkpoint):
        checkpoint()
        if proof['first_union_added_original_paths'] is None:
            proof['first_union_added_original_paths']=sorted(n for n in self.originals if n not in rows and n in declared)
        return original(self,scope.extend(rows,declared),checkpoint)
    cls.semantic_union=union;cls.native009_preparation_declaration=True
    return proof


def require(ok,label):
    if not ok:raise ValueError("NATIVE009_PARENT_SCOPE_"+label)


def version2(api,transport):
    original=api.runtime.validate_worker_hint;before=original.__code__
    old=".compact.v1.json";new=".compact.v2.json"
    slots=[i for i,v in enumerate(before.co_consts) if type(v) is str and v==old]
    require(len(slots)==1,"ONE_EXACT_CAPSULE_SUFFIX_SLOT")
    values=list(before.co_consts);values[slots[0]]=new;code=before.replace(co_consts=tuple(values))
    undo=list(code.co_consts);undo[slots[0]]=old
    require(code.replace(co_consts=tuple(undo))==before,"WHOLE_VALIDATOR_SUFFIX_INVERSE")
    fn=FunctionType(code,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    fn.__kwdefaults__=original.__kwdefaults__;transport.publish_function(api.runtime,"validate_worker_hint",fn)
    return dict(old=old,new=new,constant_slot=slots[0],whole_code_inverse=True,
        run_case_schema_hash_and16KiB_checks_retained=True)


def publish_bytes(root,name,raw,q,guard,bytes_policy,a,limit):
    require(type(raw) is bytes and 0<len(raw)<=limit,"BOUNDED_NEW_METADATA")
    path=root/name
    for parent in (path.parent,*path.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_METADATA_ANCESTORS")
        if parent==root:break
    expected=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    if path.exists():a.exact(q.fresh_pin(name),expected,"ONLY_EXACT_PREPARATION_BYTES_REUSED");return expected
    pacer=bytes_policy.OwnedPacer();pacer.select(name)
    import os
    with path.open("xb") as stream:
        for offset in range(0,len(raw),65536):
            guard.check();block=raw[offset:offset+65536];pacer.reserve(guard.check)
            a.exact(stream.write(block),len(block),"COMPLETE_METADATA_CHUNK");pacer.refund(len(block))
        stream.flush();os.fsync(stream.fileno())
    a.exact(q.pin(name),expected,"ACTUAL_NEW_METADATA_PIN");return expected


def main():
    import argparse,importlib.util,io,os,re,time,traceback,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    host.configure_host_policy(c);c.Windows()
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import flat_current_queue_envelope_runtime_v25 as envelope
    import current_stored_runtime_scope as scope
    import current_queue_successor_binding as bindings
    import owned_source_read_pressure as bytes_policy
    import receipt_xz_envelope_v1 as xz
    import bounded_successor_capsule_wire_v2 as bounded
    import ast_clone_namespace_v1 as cloner
    import ast_copy_namespace_connection_v1 as optimization
    import native009_worker_transport_v1 as transport
    import native009_engine_connection_v1 as engine
    import native008_failure_binding_v1 as failed
    import flat_current_queue_product_window_runtime_v18 as original_window
    import post_product_recovery_window_v1 as window_tool
    import post_product_recovery_connection_v1 as recovery
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--phase",choices=("graph","plan"),required=True)
    parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--generation",type=int,default=1)
    args=parser.parse_args();attempt=producer.identifier(args.attempt)
    generation=producer.identifier(args.generation)
    graph_name=PREFIX+f"successor-native009-parent-graph{generation:03}.v2.json"
    output=PREFIX+f"native009-parent-{args.phase}{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_PARENT_PREPARATION_REPORT")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None;stage="ADMISSION"
    row=dict(state="FAILED_NATIVE009_PARENT_"+args.phase.upper()+"_NOT_NATIVE",accepted_count_delta=0,
        product_worker_or_Native_executed=False,GO_authorized=False,current_live_input_hash_or_Native_Frame_qualified=False,
        whole_Native_helper_bound_qualified=False)
    encoded=lambda data:(json.dumps(data,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("ascii")
    graph_result=None
    try:
        guard.acquire();guard.check(force=True);q=a.AcceptanceReader(c.ROOT,guard.check)
        q.pin(SELF);q.pin(TEST)
        for name,state in ((PREFIX+"native009-engine-code001.v1.json","PASS_NATIVE009_REAL_ENGINE_WORKER_COMPOSITION10_NOT_EXECUTION_OR_NATIVE"),
            (PREFIX+"native009-actual-worker-probe002.v1.json","PASS_ACTUAL_WORKER009_FULL69_EOF_AND_EXACT_COMMAND_DENIED_NOT_NATIVE")):
            proof=q.json(name);a.fields(proof,dict(state=state,cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False),"CURRENT_ENGINE_AND_WORKER_EVIDENCE")
            for pin in proof["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_QUALIFIED_PREPARATION_INPUTS")
        q.pin("tools/p09/prepare_current_queue_step.py");q.pin("tools/p09/current_issuer_build_inputs.py")
        q.pin(PREFIX+"step-config001.v1.json")
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact)
        suffix=version2(api,transport)
        if args.phase=="graph":
            stage="DERIVE_LINEAGE"
            old_hint=q.json(PREFIX+"successor-worker-bootstrap009.v1.json")
            manifest=a.read_exact(q,old_hint["manifest_pin"]);step=old_hint["step"]
            prior=a.read_exact(q,step["prior_candidate_pin"])
            history={k:copy.deepcopy(prior["source_input_representation"][k]) for k in bindings.PROVENANCE_KEYS
                if k in prior["source_input_representation"]}
            a.exact(history,old_hint["historical_provenance"],"LINEAGE_FROM_ACTUAL_PREDECESSOR_NOT_CURRENT_CANDIDATE")
            fresh=dict(manifest,schema_version="hwpx-agent.p09-native009-parent-scope-manifest/v1",
                historical_predecessor_provenance=history,prior_metadata_manifest_pin=old_hint["manifest_pin"],
                current_whole_Native_source_scope_qualified=False)
            manifest_pin=publish_bytes(c.ROOT,MANIFEST,encoded(fresh),q,guard,bytes_policy,a,262144)
            hint=copy.deepcopy(old_hint);hint["manifest_pin"]=manifest_pin
            module=api.factory(hint,fresh["descriptors"][:68])
            bound=module.Binding(fresh["descriptors"],manifest_pin,next_case=165)
            graph,_=api.metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,9,guard.check)
            wire,_=graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
            hint["capsule_pin"]=publish_bytes(c.ROOT,CAPSULE,wire,q,guard,bytes_policy,a,16384)
            hint_pin=publish_bytes(c.ROOT,BOOTSTRAP,encoded(hint),q,guard,bytes_policy,a,16384)
            stage="V2_RECONSTRUCTION"
            rebuilt,reconstruction=api.reconstruct(hint,wire,guard.check)
            a.exact(rebuilt.binding.descriptors(),fresh["descriptors"],"SAME69_WITH_LINEAGE_COMPLETE_MANIFEST")
            spec=importlib.util.spec_from_file_location("native009_parent_scope_contracts",c.ROOT/TEST)
            tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
            tests.MODULE=sys.modules[__name__];tests.API=api;tests.HINT=hint;tests.WIRE=wire;tests.CHECKPOINT=guard.check
            result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row["contract_failures"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
            a.exact(row["contracts"],dict(run=11,errors=0,failures=0,skipped=0),"V2_METADATA11")
            graph_result=dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",index=165,
                physical_run=9,step=step,manifest_pin=manifest_pin,capsule_pin=hint["capsule_pin"],bootstrap_pin=hint_pin,
                descriptors=69,product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False,
                actual_current_Native_source_hashes_or_Frame_qualified=False)
            row.update(state="PASS_NATIVE009_LINEAGE_COMPLETE_GRAPH_V2_NOT_PARENT_ADMISSION",suffix_proof=suffix,
                manifest_pin=manifest_pin,capsule_pin=hint["capsule_pin"],bootstrap_pin=hint_pin,reconstruction_proof=reconstruction)
        else:
            stage="ORIGINAL_PARENT_CALLBACK"
            prepared=q.json(graph_name);a.fields(prepared,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
                index=165,physical_run=9,cleanup_confirmed=True,product_or_Native_executed=False,GO_authorized=False),"REAL_NEW_GRAPH_ONLY_NOT_NATIVE")
            hint=a.read_exact(q,prepared["bootstrap_pin"])
            pin,data=q._read(prepared["capsule_pin"]["path"],parse=True);q._bind(pin["path"],pin)
            a.exact(pin,prepared["capsule_pin"],"CURRENT_V2_CAPSULE")
            graph,_=api.reconstruct(hint,bytes(data),guard.check)
            graph_pin=q.snapshots[graph_name]
            explicit=scope.pins(prepared["source_pins"])
            explicit=scope.extend(explicit,{graph_name:graph_pin})
            failed_native=admit_failed_declaration(q,failed,a,producer)
            inherited=scope.pins(failed_native["source_input_representation"]["semantic_source_freeze"])
            declaration=scope.extend(inherited,{failed.ORIGINAL['path']:failed.ORIGINAL})
            row['preparation_declaration_union']=inherit_declaration(graph,declaration,scope)
            required,rust=api.runtime.current_input_scope(q,graph,hint["step"],graph_pin,prepared["manifest_pin"],explicit)
            stage="PRESERVE_NATIVE008_COMPLETE_DECLARATION"
            # Declaration inheritance, NOT failed Native/PASS reuse or freshness.
            required=scope.extend(required,inherited)
            required=scope.extend(required,q.snapshots)
            required,_=graph.binding.semantic_union(required,guard.check)
            require(set(inherited)<=set(required),"NO_NATIVE008_DECLARED_INPUT_REMOVED")
            declaration_name=PREFIX+f"native009-parent-declared-scope{attempt:03}.v1.json"
            declaration=dict(schema_version="hwpx-agent.p09-native009-declared-inputs/v1",index=165,physical_run=9,
                current_live_input_hashes_or_Frame_qualified=False,
                inherited_Native008_source_declaration_not_product_reuse=True,
                input_pins=sorted(required.values(),key=lambda p:p["path"]),
                self_pin_added_separately_after_publication=True)
            declaration_pin=publish_bytes(c.ROOT,declaration_name,encoded(declaration),q,guard,bytes_policy,a,2*1024*1024)
            required=scope.extend(required,{declaration_pin["path"]:declaration_pin})
            projection,_=graph.binding.project(required,guard.check)
            stage="CURRENT_RUST_INVENTORY"
            inventory=a.native.definitions(q.text("tools/p09/current_issuer_build_inputs.py"),("rust_inputs",),dict(os=os,Path=Path,require=require))
            requests=[]
            def paced_inventory():requests.append(1);q.open_pacer.reserve()
            actual=inventory.rust_inputs(c.ROOT,paced_inventory);a.exact(actual,rust,"CURRENT_RUST787_PATH_SET")
            linked=engine.build(c.ROOT,loader,api,graph,original_window,recovery,window_tool,guard.check)
            stage="ORIGINAL_COMPLETE_COST"
            row.update(scope_declaration_pin=declaration_pin,semantic_inputs=len(required),physical_inputs=len(projection.physical_pins),
                physical_bytes=sum(p["bytes"] for p in projection.physical_pins.values()),
                inherited_Native008_declared_inputs=len(inherited),current_Rust_path_count=len(rust),inventory_requests=len(requests),
                scope_manifest_itself_included_in_final_modeled_scope=True,
                additional_qualification_and_actual_run_sources_must_be_recosted=True)
            budget=graph.binding.runtime_budget(required,len(requests),linked.window.DIRECT.runtime_budget,guard.check)
            nominal=budget["predicted_runtime_combined_seconds"]+15
            row.update(original_complete_runtime_budget=budget,additional_readiness_seconds_without_old_allowance_credit=15,
                predicted_complete_seconds_with_readiness=nominal,nominal_fits600=nominal<600,
                original_parent_callback_code_unchanged=True,all_declared_source_hashes_not_freshly_read=True,
                actual_parent_Source_Frame_or_product_not_executed=True)
            require(nominal<600,"COMPLETE_SCOPE_PLUS_READINESS_OUTSIDE600")
            stage="FINAL_RUST_INVENTORY"
            final=[]
            def final_inventory():final.append(1);q.open_pacer.reserve()
            a.exact(inventory.rust_inputs(c.ROOT,final_inventory),rust,"FINAL_RUST787_PATH_SET")
            a.exact(len(final),len(requests),"SAME_CURRENT_INVENTORY_PACING")
            row["state"]="PASS_NATIVE009_DECLARED_SCOPE_AND_COST_NOT_LIVE_HASH_OR_NATIVE"
        stage="FINAL_METADATA_HASHES"
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        if graph_result is not None:graph_result.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__;row["error_frames"]=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno) for f in traceback.extract_tb(error.__traceback__)[-6:]]
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,operation_phase=stage,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"PARENT_PREPARATION_OWNER_CLEANUP")
    if graph_result is not None and row["state"].startswith("PASS_"):
        graph_result["cleanup_confirmed"]=True;row["graph_report_pin"]=publisher.publish(c.ROOT,graph_name,graph_result,a)
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_failures","semantic_inputs","physical_inputs","physical_bytes","current_Rust_path_count",
        "inventory_requests","predicted_complete_seconds_with_readiness","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","operation_phase","error_code","error_frames")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
