"""Closed-prebody sources on frozen V5 parent and worker preparation paths.

Native/review/accept dispatch is intentionally unavailable until complete entry
qualification and independent review wiring are verified. No prior file changes.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/current_queue_closed_metadata_runtime_v6.py"
PINS=[
    dict(path="tools/p09/current_queue_sealed_metadata_runtime_v5.py",bytes=12552,sha256="c38b9bb62014d626565159353b0e4bf0431e4336e3fafefd9e57d7401657eff0"),
    dict(path="tools/p09/closed_prebody_source_alias_v1.py",bytes=20052,sha256="153f31453a9a87433d3f0b2bdabc6ceb1151e8c14e29fc7e7faea1fe9f5ae0c9"),
    dict(path="tools/p09/closed_prebody_worker_connection_v1.py",bytes=16441,sha256="d9c69c7373fc2f475048b1d8a8466f2b8c013e086856da0bed73a9e8c80b265b"),
    dict(path="tools/p09/closed_prebody_runtime_connection_v1.py",bytes=9638,sha256="9c57bda67b8b93c4cd1c228d97069ba5bc9ca8f7bec1fe904d08d8565b73faf5")]


def require(ok,label):
    if not ok:raise ValueError("CLOSED_METADATA_V6_"+label)


def load(root,a,scope,bytes_policy,envelope,qualification_path,*,worker=False,ctx=None):
    sources,_=envelope.namespace_bundle.load(root,PINS,{})
    v5=sources.current_queue_sealed_metadata_runtime_v5
    alias=sources.closed_prebody_source_alias_v1
    transport=sources.closed_prebody_worker_connection_v1
    connection=sources.closed_prebody_runtime_connection_v1
    state={};configured={}
    def configure(runtime,q=None):
        policy=None if worker else q.closed_source_policy
        if id(runtime) in configured:
            a.exact(configured[id(runtime)],None if policy is None else policy.evidence(),"V6_SAME_EPOCH_POLICY")
            return
        bindings=linked.modules.current_queue_successor_binding
        codec_names,_=envelope.namespace_bundle.load(root,bindings.PINS,{"current_stored_runtime_scope":scope})
        source=codec_names.runtime_envelope_source_projection_v1
        connection.connect(runtime,bindings,alias,transport,scope,a,linked.bridge,source.codec,source.SCHEMA,parent_policy=policy)
        if policy is not None:
            linked.v4.override_import(runtime,"current_queue_successor_binding",connection.binding_api(bindings,alias,policy))
        for fn in vars(runtime).values():
            if type(fn) is FunctionType and fn.__globals__.get("__name__","").startswith("p09_exact_current_queue_successor_runtime"):
                fn.__globals__.update(SELF=SELF,TEST=connection.TEST)
        runtime.SELF,runtime.TEST=SELF,connection.TEST
        configured[id(runtime)]=None if policy is None else policy.evidence()
    class Reader(a.AcceptanceReader):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.pin(SELF)
            for pin in PINS:a.exact(self.pin(pin["path"]),pin,"V6_EXACT_CONNECTION_COMPONENTS")
            require(qualification_path is not None,"PARENT_REQUIRES_FROZEN_V5_QUALIFICATION")
            qualified=self.json(qualification_path)
            a.fields(qualified,dict(state="PASS_SEALED_METADATA_V5_CODE_NOT_NATIVE_PRODUCT_OR_QUEUE",
                contracts=dict(run=19,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"V6_FROZEN_V5_CODE19")
            require(qualified["fresh_inputs"]==qualified["final_fresh_hashes"]>0,"V5_CLOSED_HASHES")
            for pin in qualified["source_pins"]:a.exact(self.pin(pin["path"]),pin,"V6_CURRENT_FROZEN_V5_SOURCES")
            for suffix,state_name,count in (("runtime-code002","PASS_CLOSED_PREBODY_RUNTIME_CONNECTION_CODE8_NOT_ENTRY_ADOPTION_NATIVE_OR_PRODUCT",8),
                ("worker-code004","PASS_CLOSED_PREBODY_WORKER_TRANSPORT_CODE10_NOT_NATIVE_PRODUCT_OR_PARENT_ADOPTION",10)):
                # Current source qualification remains mandatory in every parent reader.
                index=state["index"]
                row=self.json(alias.PREFIX+f"p09-361-case{index}-closed-prebody-{suffix}.v1.json")
                a.fields(row,dict(state=state_name,contracts=dict(run=count,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"V6_CURRENT_COMPONENT_CODE")
                require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"CLOSED_COMPONENT_HASHES")
                for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"V6_CURRENT_QUALIFIED_SOURCES")
            producer=self.pin(alias.PREFIX+f"p09-361-case{state['index']}-closed-prebody-sources002.v1.json")
            bindings=linked.modules.current_queue_successor_binding
            names,_=envelope.namespace_bundle.load(root,bindings.PINS,{"current_stored_runtime_scope":scope})
            source=names.runtime_envelope_source_projection_v1
            self.closed_source_policy=alias.verify(self,producer,state["index"],state["run"],a,scope,linked.bridge,source.codec,source.SCHEMA)
            configure(linked.modules.current_queue_successor_runtime,self)
    api=NS(**{**vars(a),"AcceptanceReader":Reader})
    linked=v5.load(root,api,scope,bytes_policy,envelope,qualification_path,worker=worker,ctx=ctx)
    if not worker:
        require(ctx is not None,"EXPLICIT_PARENT_CONTEXT")
        import re
        match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-preflight-run([0-9]{3})-attempt[0-9]{3}\.v1\.json",ctx.preflight)
        require(match is not None,"EXACT_PARENT_CONTEXT_PATH")
        state.update(index=int(match[1]),run=int(match[2]))
        require(165<=state["index"]<=249 and 4<=state["run"]<=8,"CLOSED_PARENT_CONTEXT")
        connection.connect_dynamic(linked.modules.current_queue_successor_dispatch,configure)
    else:configure(linked.modules.current_queue_successor_runtime)
    return NS(**{**vars(linked),"api":api,"alias":alias,"transport":transport,
        "connection":connection,"state":state,"configure":configure})


def prepare(root,a,scope,bytes_policy,envelope,index,run):
    import hashlib,json,os,time
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import successor_preparation_workspace_v1 as publisher
    require(165<=index<=249 and 4<=run<=8,"CLOSED_PREPARATION_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{index}-successor-"
    report_name=prefix+f"connections{run:03}.v4.json"
    capsule_name=prefix+f"worker-capsule{run:03}.compact.v4.json"
    manifest_name=prefix+f"closed-manifest{run:03}.v1.json"
    for name in (report_name,capsule_name,manifest_name):require(not (root/name).exists(),"EXCLUSIVE_GRAPH_NO_REPLAY")
    ctx=NS(preflight=prefix+f"preflight-run{run:03}-attempt001.v1.json",qualification=prefix+f"dispatch-qualification-run{run:03}-attempt001.v1.json")
    qualification=f"implementation/p09/evidence/p09-361-case{index}-sealed-metadata-code001.v1.json"
    linked=load(root,a,scope,bytes_policy,envelope,qualification,ctx=ctx)
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_SUCCESSOR_GRAPH_PREPARATION_NOT_ADOPTED",index=index,accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        guard.acquire();q=linked.api.AcceptanceReader(root,guard.check)
        bindings=linked.modules.current_queue_successor_binding;metadata=linked.modules.current_queue_successor_runtime.metadata
        for name in (bindings.SELF,bindings.TEST,metadata.SELF,metadata.TEST):q.pin(name)
        for pin in bindings.PINS+metadata.PINS:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_GRAPH_SOURCES")
        original=q.json(prefix+"binding001.v1.json")
        a.fields(original,dict(state="PREPARED_REAL_SUCCESSOR_BINDING_ALL_PAIRS_NOT_WHOLE_RUNTIME_OR_GO",index=index,
            cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"BASE_BINDING_QUALIFICATION")
        require(original["fresh_inputs"]==original["final_fresh_hashes"]>0,"BASE_BINDING_CLOSED_HASHES")
        manifest=a.read_exact(q,original["manifest_pin"])
        step=q.json(f"implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json")
        authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
        a.fields(authority,dict(accepted_count_after=index-7,next_runtime_index=index,runtime_candidate_pin=step["prior_candidate_pin"],
            resource_cleanup_confirmed=True),"LIVE_PREDECESSOR_AUTHORITY")
        a.exact(manifest["authority_pin"],step["prior_queue_pin"],"MANIFEST_PRIOR_AUTHORITY")
        a.exact(manifest["prior_runtime_pin"],step["prior_candidate_pin"],"MANIFEST_PRIOR_RUNTIME")
        history={k:prior["source_input_representation"][k] for k in bindings.PROVENANCE_KEYS if k in prior["source_input_representation"]}
        a.exact(manifest["historical_predecessor_provenance"],history,"UNCHANGED_PRIOR_PROVENANCE")
        module,proof=linked.connection.binding_api(bindings,linked.alias,q.closed_source_policy).connect(root,envelope.namespace_bundle,scope,index,history,
            prior["source_input_representation"]["descriptors"])
        expanded=dict(manifest,descriptors=manifest["descriptors"]+q.closed_source_policy.descriptors(),
            closed_prebody_source_policy=q.closed_source_policy.evidence())
        manifest_pin=publisher.publish(root,manifest_name,expanded,a);a.exact(q.pin(manifest_name),manifest_pin,"REAL_EXPANDED_MANIFEST")
        bound=module.Binding(expanded["descriptors"],manifest_pin,next_case=index)
        graph,connected=metadata.connect(root,envelope.namespace_bundle,bytes_policy,module,bound,step,run,guard.check)
        wire,pin=graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
        restored,_=graph.worker.decode(wire,pin,guard.check);a.exact(restored.descriptors(),bound.descriptors(),"EVERY_WORKER_ROW")
        require(0<len(wire)<=16384,"ORIGINAL_WIRE_BOUND")
        path=root/capsule_name
        for parent in (path.parent,*path.parent.parents):
            require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CAPSULE_PARENTS")
            if parent==root:break
        with path.open("xb") as stream:require(stream.write(wire)==len(wire),"ALL_CAPSULE_BYTES");stream.flush();os.fsync(stream.fileno())
        capsule_pin=dict(path=capsule_name,bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
        a.exact(q.pin(capsule_name),capsule_pin,"ACTUAL_CAPSULE_BYTES")
        q.finish();guard.check(force=True)
        row.update(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",step=step,
            binding_report_pin=q.snapshots[prefix+"binding001.v1.json"],manifest_pin=manifest_pin,base_manifest_pin=original["manifest_pin"],
            capsule_pin=capsule_pin,task=graph.worker.TASK,pair_count=len(bound.descriptors()),all_worker_rows_restored=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_binding_source_AST_proofs=proof["source_proofs"],original_graph_source_AST_proofs=connected["source_proofs"],
            closed_source_policy=q.closed_source_policy.evidence(),entire_current_runtime_imported_closure_and_cost_NOT_qualified=True,
            actual_parent_engine_worker_dispatch_and_full_oracle_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"GRAPH_CLEANUP");publisher.publish(root,report_name,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","pair_count","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PREPARED_") else 1


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    require(not any(flag in sys.argv for flag in ("--native","--review","--accept","--source-code")),"FULL_ENTRY_QUALIFICATION_AND_REVIEW_WIRING_PENDING")
    if "--graph" in sys.argv:
        import argparse
        parser=argparse.ArgumentParser()
        parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
        parser.add_argument("--attempt",type=int,required=True);parser.add_argument("--graph",action="store_true",required=True)
        args=parser.parse_args();require(args.attempt==1,"ONE_EXCLUSIVE_GRAPH_ATTEMPT_PER_RUN")
        return prepare(c.ROOT,a,scope,bytes_policy,envelope,args.case,args.run)
    # Reuse the complete frozen entry parser/dispatch, not a source copy.
    sources,_=envelope.namespace_bundle.load(c.ROOT,[PINS[0]],{})
    v5=sources.current_queue_sealed_metadata_runtime_v5
    v5.main.__globals__["load"]=load
    return v5.main()


if __name__=="__main__":raise SystemExit(main())
