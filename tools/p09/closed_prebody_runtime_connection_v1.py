"""Closed-source admission on the actual private parent/worker runtime API.

The old whole parent input callback and independent checker remain mandatory.
No GO or queue writer is provided by this connector.
"""
import copy
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/closed_prebody_runtime_connection_v1.py"
TEST="tools/p09/tests/test_closed_prebody_runtime_connection_v1.py"


def require(ok,label):
    if not ok:raise ValueError("CLOSED_PREBODY_RUNTIME_"+label)


def publish_function(namespace,name,value):
    original=getattr(namespace,name)
    require(type(original) is FunctionType and original.__globals__.get("__name__","").startswith("p09_exact_"),"PRIVATE_ORIGINAL_FUNCTION")
    original.__globals__[name]=value;setattr(namespace,name,value)


def connect(runtime,bindings,alias,transport,scope,a,bridge,codec,source_schema,*,parent_policy=None):
    """Same API for startup, full preflight, Native callback and review setup."""
    require(parent_policy is None or type(parent_policy) is alias.VerifiedPolicy,"VERIFIED_PARENT_OR_WORKER_DECLARATION_ONLY")
    originals=NS(**{name:getattr(runtime,name) for name in
        ("worker_hint","validate_worker_hint","reconstruct_worker_graph","current_input_scope")})
    require(all(fn.__globals__.get("__name__","").startswith("p09_exact_")
        for fn in vars(originals).values()),"ONE_PRIVATE_RUNTIME_FAMILY")
    # Original reconstruction receives the closed base hint. Freeze its original
    # validator dependency before the runtime family's public API is extended.
    old_reconstruct=originals.reconstruct_worker_graph
    env=dict(old_reconstruct.__globals__,validate_worker_hint=originals.validate_worker_hint)
    originals.reconstruct_worker_graph=FunctionType(old_reconstruct.__code__,env,
        argdefs=old_reconstruct.__defaults__,closure=old_reconstruct.__closure__)
    originals.reconstruct_worker_graph.__kwdefaults__=old_reconstruct.__kwdefaults__
    old_hint=originals.worker_hint
    originals.worker_hint=FunctionType(old_hint.__code__,dict(old_hint.__globals__,
        validate_worker_hint=originals.validate_worker_hint),argdefs=old_hint.__defaults__,closure=old_hint.__closure__)
    originals.worker_hint.__kwdefaults__=old_hint.__kwdefaults__
    evidence=None if parent_policy is None else parent_policy.evidence()
    def validate_worker_hint(hint,task):
        require(type(hint) is dict and transport.FIELD in hint,"EXPLICIT_CLOSED_DECLARATION")
        return originals.validate_worker_hint({k:v for k,v in hint.items() if k!=transport.FIELD},task)
    def reconstruct_worker_graph(root,loader,ss,bytes_policy,hint,wire,checkpoint):
        graph,proof=transport.reconstruct(originals,bindings,root,loader,ss,bytes_policy,hint,wire,checkpoint,alias)
        if evidence is not None:a.exact(hint[transport.FIELD],evidence,"EXACT_PARENT_ADMITTED_TRANSPORT_DECLARATION")
        return NS(**{**vars(graph),"closed_source_declaration":copy.deepcopy(hint[transport.FIELD])}),proof
    def worker_hint(step,run,capsule_pin,manifest_pin,manifest,historical_pairs):
        require(parent_policy is not None,"PARENT_POLICY_REQUIRED_FOR_BOOTSTRAP_WRITER")
        return transport.parent_hint(originals,step,run,capsule_pin,manifest_pin,manifest,historical_pairs,
            parent_policy,alias,scope,NS(SCHEMA=source_schema,codec=codec))
    def current_input_scope(q,graph,step,report_pin,manifest_pin,source_pins):
        require(parent_policy is not None,"DECLARATION_CANNOT_AUTHORIZE_PARENT_OR_REVIEW")
        fresh=alias.verify(q,dict(parent_policy.producer_pin),step["index"],
            # Actual physical run is bound by the already validated transport.
            int(graph.worker.TASK.split("-r")[1][:3]),a,scope,bridge,codec,source_schema)
        a.exact(fresh.evidence(),evidence,"FRESH_ORIGINAL_ADMISSION_MATCHES_INDEPENDENT_EXPECTATION")
        declared=getattr(graph,"closed_source_declaration",None)
        if declared is None:
            # Factory construction makes the binding directly, before wire IO.
            required=scope.pins([p["semantic_original_pin"] for p in graph.binding.descriptors()]+[dict(graph.binding.manifest_pin)])
            projection,_=graph.binding.project(required,q.checkpoint)
            declared=graph.binding.representation(projection).get("closed_prebody_source_policy")
        a.exact(declared,evidence,"EXACT_GRAPH_SOURCE_DECLARATION_NOT_CANDIDATE_OBSERVATIONS")
        required,rust=originals.current_input_scope(q,graph,step,report_pin,manifest_pin,source_pins)
        return scope.extend(required,q.snapshots),rust
    for name,fn in dict(worker_hint=worker_hint,validate_worker_hint=validate_worker_hint,
        reconstruct_worker_graph=reconstruct_worker_graph,current_input_scope=current_input_scope).items():
        publish_function(runtime,name,fn)
    return dict(original_parent_input_callback=originals.current_input_scope,
        original_worker_reconstruction=originals.reconstruct_worker_graph,
        fresh_closed_original_admission_before_original_parent_callback=True,
        worker_declaration_not_promoted_to_parent_admission=True,
        original_full_parent_input_and_independent_checker_still_required=True,
        actual_entry_Native_product_or_GO_qualified=False)


def binding_api(bindings,alias,policy):
    """For original factory construction's private binding import only."""
    require(type(policy) is alias.VerifiedPolicy,"VERIFIED_PARENT_BINDING_POLICY")
    original=bindings.connect
    def connect(*args,**kwargs):
        module,proof=original(*args,**kwargs)
        alias.install(module,policy)
        return module,proof
    return NS(**{**vars(bindings),"connect":connect})


def connect_dynamic(dispatch,configure):
    """Keep entry qualification/Native dynamically created runtime connected."""
    original=dispatch.current_namespaces
    def current_namespaces(q,*args,**kwargs):
        runtime,controller,proof=original(q,*args,**kwargs)
        configure(runtime,q)
        return runtime,controller,proof
    publish_function(dispatch,"current_namespaces",current_namespaces)
    return dict(original_dynamic_namespace_function=original,
        dynamic_private_runtime_not_silently_left_unconnected=True)


def main():
    import argparse,io,json,sys,time,unittest
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    import accept_case112_current_epoch as a
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser()
    parser.add_argument("--case",type=int,required=True);parser.add_argument("--attempt",type=int,required=True)
    args=parser.parse_args()
    require(165<=args.case<=249 and 1<=args.attempt<=8,"CLOSED_CODE_CONTEXT")
    output=f"implementation/p09/evidence/p09-361-case{args.case}-closed-prebody-runtime-code{args.attempt:03}.v1.json"
    require(not (c.ROOT/output).exists(),"EXCLUSIVE_CODE_REPORT")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    row=dict(state="FAILED_CLOSED_PREBODY_RUNTIME_CODE_NOT_ADOPTED",index=args.case,
        product_or_Native_executed=False,accepted_count_delta=0)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        suite=unittest.defaultTestLoader.loadTestsFromName("tests.test_closed_prebody_runtime_connection_v1")
        sys.modules["tests.test_closed_prebody_runtime_connection_v1"].CHECKPOINT=guard.check
        def sources():
            for module in tuple(sys.modules.values()):
                path=getattr(module,"__file__",None)
                if path and Path(path).absolute().is_relative_to(c.ROOT/"tools/p09"):
                    q.pin(Path(path).absolute().relative_to(c.ROOT).as_posix())
            for name in (SELF,TEST):q.pin(name)
        sources()
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        a.exact(row["contracts"],dict(run=8,errors=0,failures=0,skipped=0),"ALL_RUNTIME_CONNECTION8")
        sources();q.finish();guard.check(force=True)
        row.update(state="PASS_CLOSED_PREBODY_RUNTIME_CONNECTION_CODE8_NOT_ENTRY_ADOPTION_NATIVE_OR_PRODUCT",
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_entry_and_independent_whole_review_NOT_RUN=True)
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
    print(json.dumps({key:row.get(key) for key in ("state","contracts","fresh_inputs","final_fresh_hashes",
        "elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
