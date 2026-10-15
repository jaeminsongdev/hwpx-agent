"""Expanded ordinary aliases on original closed-source preparation bodies.

No Native/review/accept entry. Parent/worker source and both complete boundary
obligations remain. Existing v4/v6/v7/v8 files are immutable; graph namespace v9.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/expanded_closed_preparation_v1.py"
NAMESPACE=dict(path="tools/p09/expanded_preparation_namespace_v1.py",bytes=4549,
    sha256="96a9ebbca1197d877238de195bab3465ab3f8916675dd5b3e1a34f93f6071f89")
PRIVATE=dict(path="tools/p09/closed_preparation_private_entry_v1.py",bytes=5180,
    sha256="a8105186083906e5d64c86dd3631d04026e2cd8f50dec83923fe66114674650f")
FIX=dict(path="tools/p09/closed_prebody_factory_admission_fix_v1.py",bytes=2542,
    sha256="552e01e5f6b6945ef46921e90b1f4e55493c23d3ae38479ccbb0387bf38235ae")
PRODUCER=dict(path="tools/p09/expand_closed_preparation_receipts_v1.py",bytes=8659,
    sha256="61bf578ad64d31de7a3107285e25d1bcdbad5d08d6b4b2042108af5a690158ac")
IO_PINS=[
    dict(path="tools/p09/reusable_audit_chunk_v1.py",bytes=8088,sha256="1aa1db74585cbdf50df32ac0c9dc07dfd31557fc37647ca6e6ea3969fbb60e75"),
    dict(path="tools/p09/single_snapshot_source_guard_v1.py",bytes=4560,sha256="f3555f4395154be7c929e76eeb451226402b49cc54b0ab6da335ba94555eae43")]


def require(ok,label):
    if not ok:raise ValueError("EXPANDED_CLOSED_PREPARATION_"+label)


def profile_loader(root,loader,namespace,private):
    def load(*items,**options):
        modules,proof=loader.load(*items,**options)
        orchestration=getattr(modules,"closed_prebody_preparation_io_v1",None)
        if orchestration is not None:
            orchestration.main,_=namespace.literal_function(orchestration.main,{"v6":"v9",".v6.json":".v9.json"})
        entry=getattr(modules,"closed_prebody_factory_admission_fix_v1",None)
        if entry is not None:
            original=entry.load
            def expanded(*args,**kwargs):
                values=list(args);a=values[1]
                class Reader(a.AcceptanceReader):
                    def __init__(self,*args,**kwargs):
                        super().__init__(*args,**kwargs)
                        for name in (SELF,namespace.SELF,namespace.TEST):self.pin(name)
                        import re
                        ctx=kwargs_outer["ctx"]
                        match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-successor-preflight-run([0-9]{3})-attempt[0-9]{3}\.v1\.json",ctx.preflight)
                        require(match is not None,"EXACT_PARENT_CODE_CONTEXT")
                        row=self.json(f"implementation/p09/evidence/p09-361-case{match[1]}-expanded-namespace-code003.v1.json")
                        a.fields(row,dict(state="PASS_EXPANDED_NAMESPACE_CODE6_NOT_NATIVE_OR_PRODUCT",
                            contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CURRENT_EXPANDED_CODE6")
                        require(row["fresh_inputs"]==row["final_fresh_hashes"]>0,"CODE6_FINAL_HASHES")
                        for pin in row["source_pins"]:a.exact(self.pin(pin["path"]),pin,"EXPANDED_CURRENT_CODE_SOURCES")
                kwargs_outer=kwargs
                values[1]=NS(**{**vars(a),"AcceptanceReader":Reader})
                linked=original(*values,**kwargs)
                configured=set()
                def configure(runtime,q=None):
                    namespace.install(runtime)
                    if id(runtime) in configured:return
                    whole=runtime.connect_factory
                    def factory(*args,**kwargs):
                        result=whole(*args,**kwargs)
                        # V6 reader admission sets its frozen SELF. Retarget only
                        # after that real admission, before worker CLI creation.
                        namespace.retarget_worker(runtime,SELF)
                        return result
                    whole.__globals__["connect_factory"]=factory;runtime.connect_factory=factory
                    configured.add(id(runtime))
                configure(linked.modules.current_queue_successor_runtime)
                linked.connection.connect_dynamic(linked.modules.current_queue_successor_dispatch,configure)
                private.publish_dynamic_family(linked.modules.current_queue_successor_dispatch)
                return linked
            entry.load=expanded
        return modules,proof
    return NS(**{**vars(loader),"load":load})


def components(root,envelope):
    modules,_=envelope.namespace_bundle.load(root,[NAMESPACE,PRIVATE],{})
    namespace=modules.expanded_preparation_namespace_v1
    private=modules.closed_preparation_private_entry_v1
    original=envelope.namespace_bundle
    routed=profile_loader(root,original,namespace,private)
    parent=private.entry_loader(routed)
    return namespace,private,NS(**{**vars(envelope),"namespace_bundle":parent}),routed


def prepare(root,a,scope,bytes_policy,envelope,index,run,attempt):
    import hashlib,json,os,re,time
    namespace,private,proxy,routed=components(root,envelope)
    utilities,_=envelope.namespace_bundle.load(root,private.PINS,{})
    publisher=utilities.successor_preparation_workspace_v1
    guard=utilities.terminal_metadata_pressure_v1.guard_type(utilities.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    prefix=f"implementation/p09/evidence/p09-361-case{index}-"
    output=prefix+f"successor-connections{run:03}.v9.json"
    diagnostic=prefix+f"expanded-graph-run{run:03}-attempt{attempt:03}.v1.json"
    manifest_name=prefix+f"successor-expanded68-manifest{run:03}.v1.json"
    capsule_name=prefix+f"successor-worker-capsule{run:03}.compact.v9.json"
    bootstrap_name=prefix+f"successor-worker-bootstrap{run:03}.v9.json"
    require(1<=attempt<=8 and all(not (root/name).exists() for name in (output,diagnostic)),"EXCLUSIVE_EXPANDED_GRAPH")
    ctx=NS(preflight=prefix+f"successor-preflight-run{run:03}-attempt007.v1.json",
        qualification=prefix+f"successor-dispatch-qualification-run{run:03}-attempt006.v1.json")
    io_modules,_=envelope.namespace_bundle.load(root,IO_PINS,{"audit_evidence_io":sys.modules["audit_evidence_io"]})
    leaf=(root/io_modules.reusable_audit_chunk_v1.ORIGINAL_PIN["path"]).read_bytes()
    buffered,_=io_modules.reusable_audit_chunk_v1.reader_type(a.AcceptanceReader,leaf)
    guarded,_=io_modules.single_snapshot_source_guard_v1.reader_type(buffered,leaf)
    api=NS(**{**vars(a),"AcceptanceReader":guarded})
    entry_ns,_=proxy.namespace_bundle.load(root,[FIX],{})
    linked=entry_ns.closed_prebody_factory_admission_fix_v1.load(root,api,scope,bytes_policy,proxy,
        prefix+"sealed-metadata-code001.v1.json",ctx=ctx)
    started=time.monotonic()
    row=dict(state="FAILED_SUCCESSOR_GRAPH_PREPARATION_NOT_ADOPTED",index=index,accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        guard.acquire();q=linked.api.AcceptanceReader(root,guard.check)
        for pin in IO_PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_GRAPH_IO_HELPERS")
        for suffix,state,count in (("preparation-workspace-code001","PASS_PREPARATION_WORKSPACE_CODE_NOT_NATIVE_OR_PRODUCT",17),
            ("preparation-single-snapshot-code001","PASS_PREPARATION_SINGLE_SNAPSHOT_CODE10_NOT_NATIVE_OR_PRODUCT",10)):
            qualified=q.json(prefix+suffix+".v1.json")
            a.fields(qualified,dict(state=state,contracts=dict(run=count,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"GRAPH_IO_CURRENT_QUALIFICATION")
            require(qualified["fresh_inputs"]==qualified["final_fresh_hashes"]>0,"GRAPH_IO_FINAL_HASHES")
            for pin in qualified["source_pins"]:a.exact(q.pin(pin["path"]),pin,"GRAPH_IO_CURRENT_SOURCE")
        for pin in (NAMESPACE,PRIVATE,FIX,PRODUCER):a.exact(q.pin(pin["path"]),pin,"EXPANDED_EXACT_COMPONENTS")
        bindings=linked.modules.current_queue_successor_binding;runtime=linked.modules.current_queue_successor_runtime
        metadata=runtime.metadata
        for pin in bindings.PINS+metadata.PINS:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_BINDING_GRAPH_SOURCES")
        base_name=prefix+f"successor-connections{run:03}.v6.json"
        base=q.json(base_name)
        a.fields(base,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
            index=index,cleanup_confirmed=True,accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False),"BASE_REAL_GRAPH")
        require(base["fresh_inputs"]==base["final_fresh_hashes"]>0,"BASE_GRAPH_FINAL_HASHES")
        for pin in base["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_OLD_GRAPH_SOURCES_RETAINED")
        manifest=a.read_exact(q,base["manifest_pin"]);step=base["step"]
        authority=a.read_exact(q,step["prior_queue_pin"]);prior=a.read_exact(q,step["prior_candidate_pin"])
        a.fields(authority,dict(accepted_count_after=index-7,next_runtime_index=index,
            runtime_candidate_pin=step["prior_candidate_pin"],resource_cleanup_confirmed=True),"ACTUAL_PREDECESSOR_AUTHORITY")
        listing=a.read_exact(q,scope.LIST_PIN)
        steps=a.native.definitions(q.text("tools/p09/prepare_current_queue_step.py"),("derive_step",),dict(re=re))
        a.exact(steps.derive_step(index,step["prior_queue_pin"],authority,prior,listing["source_test_names"]),step,"FULL_STEP_REDERIVATION")
        name=prefix+"extra-ordinary-receipts001.v1.json";produced=q.json(name)
        a.fields(produced,dict(state="PREPARED_EXTRA_ORDINARY_RECEIPTS_NOT_RUNTIME_OR_PRODUCT",index=index,
            physical_run=run,cleanup_confirmed=True,original_receipts_rewritten=False,
            product_or_Native_executed=False,accepted_count_delta=0),"ACTUAL_EXTRA_PRODUCTION")
        require(produced["fresh_inputs"]==produced["final_fresh_hashes"]>0,"EXTRA_PRODUCER_FINAL_HASHES")
        pairs=produced["explicit_descriptors"]
        require(type(pairs) is list and 1<=len(pairs)<=6,"BOUNDED_EXTRA_PAIRS")
        expected=metadata.select_extra_receipts(scope,prior["source_input_representation"]["semantic_source_freeze"],manifest["descriptors"],index,len(pairs))
        a.exact(expected,produced["expected_original_pins"],"EXTRA_EXPECTATIONS_FROM_APPROVED_PREDECESSOR")
        for pin in (PRODUCER,):a.exact(scope.pins(produced["source_pins"])[pin["path"]],pin,"CURRENT_PRODUCER_CODE")
        code=q.json("implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json")
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CODEC_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_QUALIFIED_CODEC_SOURCES")
        history=manifest["historical_predecessor_provenance"]
        module,proof=linked.connection.binding_api(bindings,linked.alias,q.closed_source_policy).connect(root,proxy.namespace_bundle,scope,index,
            history,prior["source_input_representation"]["descriptors"])
        for old,pair in zip(expected,pairs):
            a.exact(pair["semantic_original_pin"],old,"INDEPENDENT_EXTRA_ORIGINAL_PIN")
            new=pair["physical_envelope_pin"]
            a.exact(module.source.descriptor(old,new,next_case=index),pair,"UNCHANGED_ORDINARY_DESCRIPTOR")
            original_pin,raw=q._read(old["path"],parse=True);q._bind(old["path"],original_pin);a.exact(original_pin,old,"REAL_EXTRA_ORIGINAL")
            encoded_pin,encoded=q._read(new["path"],parse=True);q._bind(new["path"],encoded_pin);a.exact(encoded_pin,new,"REAL_EXTRA_PHYSICAL")
            a.exact(module.source.codec.decode(bytes(encoded),guard.check),bytes(raw),"FULL_EXTRA_ORIGINAL_RESTORED")
        expanded=dict(manifest,descriptors=manifest["descriptors"]+pairs,extra_ordinary_producer_pin=q.snapshots[name],
            extra_expectations_from_approved_predecessor=True,old_manifest_pin=base["manifest_pin"])
        def metadata_file(name,value):
            raw=(json.dumps(value,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
            expected=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            if (root/name).exists():a.exact(q.fresh_pin(name),expected,"EXISTING_DERIVATIVE_EXACT_ONLY")
            else:a.exact(publisher.publish(root,name,value,a),expected,"COMPLETE_DERIVATIVE_PUBLICATION")
            a.exact(q.pin(name),expected,"ACTUAL_METADATA_DERIVATIVE")
            return expected
        manifest_pin=metadata_file(manifest_name,expanded)
        bound=module.Binding(expanded["descriptors"],manifest_pin,next_case=index)
        graph,connected=metadata.connect(root,proxy.namespace_bundle,bytes_policy,module,bound,step,run,guard.check)
        wire,wire_info=graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
        require(0<len(wire)<=16384,"ORIGINAL_TRANSPORT16K")
        path=root/capsule_name
        for parent in (path.parent,*path.parent.parents):
            require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CAPSULE_PARENTS")
            if parent==root:break
        capsule_pin=dict(path=capsule_name,bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
        if path.exists():a.exact(q.fresh_pin(capsule_name),capsule_pin,"EXISTING_CAPSULE_EXACT_ONLY")
        else:
            with path.open("xb") as stream:require(stream.write(wire)==len(wire),"ALL_EXPANDED_WIRE_BYTES");stream.flush();os.fsync(stream.fileno())
        a.exact(q.pin(capsule_name),capsule_pin,"ACTUAL_EXPANDED_CAPSULE")
        hint=runtime.worker_hint(step,run,capsule_pin,manifest_pin,expanded,prior["source_input_representation"]["descriptors"])
        require(len((json.dumps(hint,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("ascii"))<=16384,"ORIGINAL_BOOTSTRAP16K")
        bootstrap_pin=metadata_file(bootstrap_name,hint)
        restored,decoder=runtime.reconstruct_worker_graph(root,proxy.namespace_bundle,scope,bytes_policy,hint,wire,guard.check)
        a.exact(restored.binding.descriptors(),bound.descriptors(),"ALL_EXPANDED_WORKER_ROWS")
        q.finish();guard.check(force=True)
        row.update(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",step=step,manifest_pin=manifest_pin,
            base_manifest_pin=base["manifest_pin"],base_graph_pin=q.snapshots[base_name],capsule_pin=capsule_pin,bootstrap_pin=bootstrap_pin,
            task=graph.worker.TASK,pair_count=len(bound.descriptors()),all_worker_rows_restored=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_binding_source_AST_proofs=proof["source_proofs"],original_graph_source_AST_proofs=connected["source_proofs"],decoder=decoder,
            extra_expectations_from_approved_predecessor=True,actual_parent_engine_worker_dispatch_and_full_oracle_NOT_RUN=True,
            graph_io_workspace=io_modules.reusable_audit_chunk_v1.summary(q),graph_io_source_snapshot=q.source_snapshot_diagnostics())
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            resource_tail=[{k:s.get(k) for k in ("system_cpu_percent","parent_cpu_machine_percent","parent_private_mib","available_ram_percent")} for s in guard.samples[-3:]],
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"GRAPH_CLEANUP");publisher.publish(root,diagnostic,row,a)
    if row["state"].startswith("PREPARED_"):publisher.publish(root,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","pair_count","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","error_type")}))
    return 0 if row["state"].startswith("PREPARED_") else 1


def main():
    import argparse,io,json,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    namespace,private,proxy,routed=components(c.ROOT,envelope)
    utilities,_=envelope.namespace_bundle.load(c.ROOT,private.PINS,{})
    if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
        raw,_=envelope.namespace_bundle.load(c.ROOT,[FIX],{})
        linked=raw.closed_prebody_factory_admission_fix_v1.load(c.ROOT,a,scope,bytes_policy,envelope,None,worker=True)
        runtime=linked.modules.current_queue_successor_runtime;namespace.install(runtime);namespace.retarget_worker(runtime,SELF)
        return runtime.owned_worker_entry(sys.argv[3])
    if any(flag in sys.argv for flag in ("--namespace-code","--graph","--bootstrap")):
        parser=argparse.ArgumentParser()
        for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
        mode=parser.add_mutually_exclusive_group(required=True)
        for name in ("namespace-code","graph","bootstrap"):mode.add_argument("--"+name,action="store_true")
        args=parser.parse_args();require(165<=args.case<=249 and 4<=args.run<=8 and 1<=args.attempt<=8,"CLOSED_CONTEXT")
        if args.graph:return prepare(c.ROOT,a,scope,bytes_policy,envelope,args.case,args.run,args.attempt)
        prefix=f"implementation/p09/evidence/p09-361-case{args.case}-"
        if args.bootstrap:
            ctx=NS(preflight=prefix+f"successor-preflight-run{args.run:03}-attempt007.v1.json",
                qualification=prefix+f"successor-dispatch-qualification-run{args.run:03}-attempt006.v1.json")
            sources,_=proxy.namespace_bundle.load(c.ROOT,[FIX],{})
            linked=sources.closed_prebody_factory_admission_fix_v1.load(c.ROOT,a,scope,bytes_policy,proxy,prefix+"sealed-metadata-code001.v1.json",ctx=ctx)
            return linked.modules.current_queue_successor_runtime.qualify_factory(args.case,args.run,args.run,args.attempt,True)
        output=prefix+f"expanded-namespace-code{args.attempt:03}.v1.json"
        require(not (c.ROOT/output).exists(),"EXCLUSIVE_CODE_REPORT")
        guard=utilities.terminal_metadata_pressure_v1.guard_type(utilities.distinct_final_sample_guard_v1.guard_type(a.Guard))()
        started=time.monotonic();row=dict(state="FAILED_EXPANDED_NAMESPACE_CODE_NOT_ADOPTED",product_or_Native_executed=False,accepted_count_delta=0)
        try:
            guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
            for pin in (NAMESPACE,PRIVATE,FIX,PRODUCER):a.exact(q.pin(pin["path"]),pin,"EXACT_PROFILE_COMPONENTS")
            for name in (SELF,namespace.TEST):q.pin(name)
            suite=unittest.defaultTestLoader.loadTestsFromName("tests.test_expanded_preparation_namespace_v1")
            sys.modules["tests.test_expanded_preparation_namespace_v1"].CHECKPOINT=guard.check
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=6,errors=0,failures=0,skipped=0),"ALL_NAMESPACE6")
            q.finish();guard.check(force=True)
            row.update(state="PASS_EXPANDED_NAMESPACE_CODE6_NOT_NATIVE_OR_PRODUCT",source_pins=list(q.snapshots.values()),
                fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
            row["error_type"]=type(error).__name__
        finally:
            guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
                CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
        require(guard.cleanup,"CODE_CLEANUP");utilities.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
        print(json.dumps({k:row.get(k) for k in ("state","contracts","fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed")}))
        return 0 if row["state"].startswith("PASS_") else 1
    require(any(flag in sys.argv for flag in ("--preflight","--qualify")) and
        not any(flag in sys.argv for flag in ("--native","--accept","--review","--repair-graph")),"PREPARATION_ONLY")
    original=private.main;builtins=dict(original.__builtins__);previous=builtins["__import__"]
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="flat_current_queue_envelope_runtime_v25" and level==0:return NS(**{**vars(envelope),"namespace_bundle":routed})
        return previous(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared
    execute=FunctionType(original.__code__,dict(original.__globals__,__builtins__=builtins),argdefs=original.__defaults__,closure=original.__closure__)
    execute.__kwdefaults__=original.__kwdefaults__
    return execute()


if __name__=="__main__":raise SystemExit(main())
