"""Worker transport for independently admitted closed-source declarations.

No source producer, Native launcher, GO, or queue writer. Worker reconstruction
checks transport only; parent source admission and independent review stay required.
"""
import copy
import sys
from types import FunctionType, SimpleNamespace as NS

SELF="tools/p09/closed_prebody_worker_connection_v1.py"
TEST="tools/p09/tests/test_closed_prebody_worker_connection_v1.py"
FIELD="closed_prebody_source_declaration"
KEYS={"schema_version","index","before_run","producer_pin","closed_descriptors",
      "earlier_closed_prebody_only","current_or_passed_product_not_permitted",
      "original_raw_receipts_not_claimed_physically_locked"}


def private_transport(root,loader,bridge,wire,checkpoint):
    pins=[p for p in bridge.PINS if p["path"].endswith(("/current_queue_successor_runtime.py","/current_queue_successor_connections.py"))]
    require(len(pins)==2,"EXACT_RUNTIME_CONNECTION_SOURCE_SET")
    modules,_=loader.load(root,pins,{})
    runtime=modules.current_queue_successor_runtime
    wire.install(runtime.metadata,checkpoint)
    return runtime,runtime.metadata


def require(ok,label):
    if not ok:raise ValueError("CLOSED_PREBODY_WORKER_"+label)


def declaration(value,index,run,alias,scope,source):
    """Validate sealed declaration shape, NOT original source contents."""
    require(type(value) is dict and set(value)==KEYS,"EXACT_DECLARATION_FIELDS")
    require(type(index) is int and 165<=index<=249 and type(run) is int and 3<=run<=8,"CLOSED_CONTEXT")
    require(value["schema_version"]==alias.POLICY and type(value["index"]) is int
        and value["index"]==index and type(value["before_run"]) is int
        and 3<=value["before_run"]<=run,"EXACT_DECLARATION_CONTEXT")
    for flag in ("earlier_closed_prebody_only","current_or_passed_product_not_permitted",
                 "original_raw_receipts_not_claimed_physically_locked"):
        require(value[flag] is True,"EXACT_DECLARATION_FLAGS")
    import re
    pin=value["producer_pin"];scope.pins([pin])
    require(re.fullmatch(alias.PREFIX+rf"p09-361-case{index}-closed-prebody-sources00[1-8]\.v1\.json",pin["path"])
        is not None,"EXPLICIT_SOURCE_PRODUCER")
    rows=value["closed_descriptors"]
    require(type(rows) is list and 1<=len(rows)<=6,"BOUNDED_DECLARED_PAIRS")
    attempts=[];physical=set()
    for row in rows:
        require(type(row) is dict and set(row)=={"schema_version","next_case","semantic_original_pin","physical_envelope_pin"},"EXACT_PAIR_FIELDS")
        require(row["schema_version"]==source.SCHEMA and type(row["next_case"]) is int
            and row["next_case"]==index,"EXACT_PAIR_CONTEXT")
        old,new=row["semantic_original_pin"],row["physical_envelope_pin"]
        scope.pins([old,new]);attempts.append(alias.root_attempt(old,index,value["before_run"],scope))
        require(new["path"]==alias.encoded_path(old,index,value["before_run"],scope)
            and new["path"] not in physical,"UNIQUE_EXPLICIT_PHYSICAL_PATH")
        require(0<old["bytes"]<=source.codec.MAX_BYTES and 0<new["bytes"]<=source.codec.MAX_BYTES,"CODEC_BOUNDS")
        physical.add(new["path"])
    require(attempts==sorted(set(attempts)),"ORDERED_UNIQUE_ATTEMPTS")
    return copy.deepcopy(value)


def install_declaration(module,value,index,run,alias,scope):
    """Private worker descriptor predicate; never creates a VerifiedPolicy."""
    sealed=declaration(value,index,run,alias,scope,module.source)
    source=module.source;env=source.Projection.__init__.__globals__
    require(env.get("__name__","").startswith("p09_exact_") and
        not any(getattr(m,"__dict__",None) is env for m in tuple(sys.modules.values()) if m),"PRIVATE_NAMESPACE")
    original=source.descriptor;represented=module.Binding.representation
    methods={name:fn for name,fn in vars(module.Binding).items() if name!="representation"}
    pairs={row["semantic_original_pin"]["path"]:row for row in sealed["closed_descriptors"]}
    def descriptor(old,new,*,next_case):
        if type(old) is dict and old.get("path") in pairs:
            require(type(next_case) is int and next_case==index,"EXACT_WORKER_CASE")
            expected=pairs[old["path"]]
            module.exact(source.copy_pin(old),expected["semantic_original_pin"],"DECLARED_ORIGINAL_PIN")
            module.exact(source.copy_pin(new),expected["physical_envelope_pin"],"DECLARED_PHYSICAL_PIN")
            return copy.deepcopy(expected)
        return original(old,new,next_case=next_case)
    def representation(self,projection):
        result=represented(self,projection)
        result["closed_prebody_source_policy"]=copy.deepcopy(sealed)
        return result
    source.descriptor=descriptor;env["descriptor"]=descriptor
    module.Binding.representation=representation
    require(all(vars(module.Binding).get(name) is fn for name,fn in methods.items()),"ORIGINAL_ORACLES_RETAINED")
    return dict(worker_declaration_only=True,original_closed_source_bytes_verified_here=False,
        original_receipt_manifest_or_authority_files_read=False,parent_fresh_admission_required=True,
        independent_whole_review_required=True,actual_Native_product_or_GO_qualified=False)


def parent_hint(runtime,step,run,capsule_pin,manifest_pin,manifest,historical_pairs,policy,alias,scope,source):
    require(type(policy) is alias.VerifiedPolicy,"PARENT_VERIFIED_POLICY_REQUIRED")
    value=declaration(policy.evidence(),step["index"],run,alias,scope,source)
    rows={row["semantic_original_pin"]["path"]:row for row in manifest["descriptors"]}
    for row in value["closed_descriptors"]:
        require(rows.get(row["semantic_original_pin"]["path"])==row,"ALL_ADMITTED_PAIRS_IN_MANIFEST")
    hint=runtime.worker_hint(step,run,capsule_pin,manifest_pin,manifest,historical_pairs)
    hint[FIELD]=value
    return hint


def reconstruct(runtime,bindings,root,loader,scope,bytes_policy,hint,wire,checkpoint,alias):
    """Retain original worker reconstruction code, defaults and closure."""
    require(type(hint) is dict and FIELD in hint,"EXPLICIT_WORKER_DECLARATION")
    base={key:value for key,value in hint.items() if key!=FIELD}
    index,run=runtime.validate_worker_hint(base,f"case{base['index']}-current-r{base['run']:03}-tests")
    def connect(*args,**kwargs):
        module,proof=bindings.connect(*args,**kwargs)
        install_declaration(module,hint[FIELD],index,run,alias,scope)
        return module,proof
    fn=runtime.reconstruct_worker_graph;env=dict(fn.__globals__)
    builtins=dict(fn.__builtins__);previous=builtins["__import__"]
    def declared(name,globals=None,locals=None,fromlist=(),level=0):
        if name=="current_queue_successor_binding" and level==0:
            return NS(**{**vars(bindings),"connect":connect})
        return previous(name,globals,locals,fromlist,level)
    builtins["__import__"]=declared;env["__builtins__"]=builtins
    whole=FunctionType(fn.__code__,env,argdefs=fn.__defaults__,closure=fn.__closure__)
    whole.__kwdefaults__=fn.__kwdefaults__
    graph,proof=whole(root,loader,scope,bytes_policy,base,wire,checkpoint)
    rows={row["semantic_original_pin"]["path"]:row for row in graph.binding.descriptors()}
    for row in hint[FIELD]["closed_descriptors"]:
        require(rows.get(row["semantic_original_pin"]["path"])==row,"ALL_DECLARED_PAIRS_IN_REAL_WIRE")
    return graph,dict(proof,worker_declaration_only=True,original_closed_source_bytes_verified_here=False,
        original_worker_reconstruction_code_defaults_closure_retained=True,
        parent_fresh_admission_and_independent_whole_review_required=True)


def main():
    import argparse,io,json,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",type=int,required=True)
    parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--probe",action="store_true")
    parser.add_argument("--run",type=int,default=4)
    parser.add_argument("--source-attempt",type=int,default=2)
    parser.add_argument("--code-attempt",type=int,default=3)
    args=parser.parse_args()
    require(type(args.case) is int and 165<=args.case<=249 and all(1<=n<=8 for n in
        (args.attempt,args.source_attempt,args.code_attempt)) and 3<=args.run<=8,"CLOSED_CODE_CONTEXT")
    kind="transport" if args.probe else "code"
    output=f"implementation/p09/evidence/p09-361-case{args.case}-closed-prebody-worker-{kind}{args.attempt:03}.v1.json"
    require(not (c.ROOT/output).exists(),"EXCLUSIVE_CODE_REPORT")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_CLOSED_PREBODY_WORKER_CODE_NOT_ADOPTED",index=args.case,
        product_or_Native_executed=False,accepted_count_delta=0)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        def sources():
            for module in tuple(sys.modules.values()):
                path=getattr(module,"__file__",None)
                if path and Path(path).absolute().is_relative_to(c.ROOT/"tools/p09"):
                    q.pin(Path(path).absolute().relative_to(c.ROOT).as_posix())
            for name in (SELF,TEST):q.pin(name)
        if args.probe:
            import closed_prebody_source_alias_v1 as alias
            import current_queue_successor_runtime as runtime
            import current_queue_successor_connections as metadata
            import current_queue_successor_binding as bindings
            import current_stored_runtime_scope as scope
            import runtime_envelope_namespace_bundle_v1 as loader
            import owned_source_read_pressure as bytes_policy
            import bounded_successor_capsule_wire_v2 as bounded_wire
            sources()
            code=q.json(alias.PREFIX+f"p09-361-case{args.case}-closed-prebody-worker-code{args.code_attempt:03}.v1.json")
            a.fields(code,dict(state="PASS_CLOSED_PREBODY_WORKER_TRANSPORT_CODE10_NOT_NATIVE_PRODUCT_OR_PARENT_ADOPTION",
                contracts=dict(run=10,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"MANDATORY_CURRENT_WORKER_CODE10")
            require(code["fresh_inputs"]==code["final_fresh_hashes"]>0,"COMPLETE_CODE_HASHES")
            require({SELF,TEST}<={p["path"] for p in code["source_pins"]},"OWN_CODE_WITNESSES")
            for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CODE_SOURCE")
            producer_pin=q.pin(alias.PREFIX+f"p09-361-case{args.case}-closed-prebody-sources{args.source_attempt:03}.v1.json")
            frozen,_=loader.load(c.ROOT,[alias.BRIDGE_PIN],{})
            runtime,metadata=private_transport(c.ROOT,loader,frozen.current_queue_successor_wire_runtime_v2,bounded_wire,guard.check)
            for pin in frozen.current_queue_successor_wire_runtime_v2.PINS:a.exact(q.pin(pin["path"]),pin,"FROZEN_FULL_RUNTIME_SOURCE")
            for pin in [alias.BRIDGE_PIN]+bindings.PINS+metadata.PINS:a.exact(q.pin(pin["path"]),pin,"FROZEN_TRANSPORT_SOURCES")
            prepared=q.json(alias.PREFIX+f"p09-361-case{args.case}-successor-binding001.v1.json")
            a.fields(prepared,dict(state="PREPARED_REAL_SUCCESSOR_BINDING_ALL_PAIRS_NOT_WHOLE_RUNTIME_OR_GO",
                index=args.case,cleanup_confirmed=True),"BASE_PREPARED_BINDING")
            manifest=a.read_exact(q,prepared["manifest_pin"])
            prior=a.read_exact(q,manifest["prior_manifest_pin"])
            module,_=bindings.connect(c.ROOT,loader,scope,args.case,manifest["historical_predecessor_provenance"],prior["descriptors"])
            policy=alias.verify(q,producer_pin,args.case,args.run,a,scope,frozen.current_queue_successor_wire_runtime_v2,module.source.codec,module.source.SCHEMA)
            alias.install(module,policy)
            expanded=dict(manifest,descriptors=manifest["descriptors"]+policy.descriptors(),
                closed_prebody_source_policy=policy.evidence(),transport_probe_only=True,GO_authorized=False)
            manifest_name=alias.PREFIX+f"p09-361-case{args.case}-successor-closed-transport-manifest{args.attempt:03}.v1.json"
            manifest_pin=publisher.publish(c.ROOT,manifest_name,expanded,a)
            a.exact(q.pin(manifest_name),manifest_pin,"ACTUAL_DIAGNOSTIC_MANIFEST_BYTES")
            bound=module.Binding(expanded["descriptors"],manifest_pin,next_case=args.case)
            step=q.json(alias.PREFIX+f"p09-361-case{args.case}-step-config001.v1.json")
            graph,_=metadata.connect(c.ROOT,loader,bytes_policy,module,bound,step,args.run,guard.check)
            wire,wire_pin=graph.worker.encode(bound,step["prior_queue_pin"],step["prior_candidate_pin"],guard.check)
            capsule_pin=dict(wire_pin,path=alias.PREFIX+f"p09-361-case{args.case}-successor-worker-capsule{args.run:03}.compact.v1.json")
            hint=parent_hint(runtime,step,args.run,capsule_pin,manifest_pin,expanded,prior["descriptors"],policy,alias,scope,module.source)
            restored,proof=reconstruct(runtime,bindings,c.ROOT,loader,scope,bytes_policy,hint,wire,guard.check,alias)
            a.exact(restored.binding.descriptors(),bound.descriptors(),"ALL_REAL_DECLARED_TRANSPORT_ROWS")
            semantic=scope.pins([p["semantic_original_pin"] for p in bound.descriptors()]+[manifest_pin])
            parent_projection,_=bound.project(semantic,guard.check)
            worker_projection,_=restored.binding.project(semantic,guard.check)
            a.exact(bound.representation(parent_projection),restored.binding.representation(worker_projection),"ALL_REAL_PARENT_WORKER_REPRESENTATION_IDENTICAL")
            row.update(state="PASS_CLOSED_PREBODY_REAL_DECLARED_TRANSPORT_NOT_RUNTIME_ADOPTION",
                pair_count=len(bound.descriptors()),wire_bytes=len(wire),bootstrap_hint_bytes=len(json.dumps(hint,ensure_ascii=True).encode("ascii")),
                producer_pin=producer_pin,transport_proof=proof,execution_manifest_bootstrap_or_capsule_published=False,
                diagnostic_manifest_pin=manifest_pin,capsule_declared_pin_not_published=True,
                full_current_source_byte_inventory_rechecked=False)
        else:
            suite=unittest.defaultTestLoader.loadTestsFromName("tests.test_closed_prebody_worker_connection_v1")
            test=sys.modules["tests.test_closed_prebody_worker_connection_v1"];test.CHECKPOINT=guard.check
            sources()
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            a.exact(row["contracts"],dict(run=10,errors=0,failures=0,skipped=0),"ALL_CLOSED_WORKER10")
            row["state"]="PASS_CLOSED_PREBODY_WORKER_TRANSPORT_CODE10_NOT_NATIVE_PRODUCT_OR_PARENT_ADOPTION"
        sources();q.finish();guard.check(force=True)
        row.update(source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_runtime_entry_not_changed=True,real_parent_worker_entry_and_independent_oracle_connection_NOT_RUN=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((sample["system_cpu_percent"] for sample in guard.samples),default=None),
            RAM_min=min((sample["available_ram_percent"] for sample in guard.samples),default=None))
    require(guard.cleanup,"CODE_CLEANUP")
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({key:row.get(key) for key in ("state","contracts","pair_count","wire_bytes","bootstrap_hint_bytes","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
