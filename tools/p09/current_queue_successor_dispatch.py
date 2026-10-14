"""Explicit successor execution admission; frozen CODE/preflight stay immutable.

Qualification is construction only. Actual dispatch retains the qualified outer
entry, original owned GO/Job engine and both whole Native byte boundaries.
"""
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/current_queue_successor_dispatch.py"
TEST="tools/p09/tests/test_current_queue_successor_dispatch.py"
ORIGINAL_CONTROLLER_PIN=dict(path="tools/p09/case160_run007_controller.py",bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")


def context(index,run,code_attempt,preflight_attempt,attempt):
    if any(type(v) is not int for v in (index,run,code_attempt,preflight_attempt,attempt)):
        raise ValueError("TYPED_DISPATCH_CONTEXT")
    if not (161<=index<=249 and 2<=run<=8 and all(1<=v<=8 for v in (code_attempt,preflight_attempt,attempt))):
        raise ValueError("CLOSED_DISPATCH_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{index}-successor-"
    return NS(index=index,run=run,code=prefix+f"code-run{run:03}-attempt{code_attempt:03}.v1.json",
        preflight=prefix+f"preflight-run{run:03}-attempt{preflight_attempt:03}.v1.json",
        qualification=prefix+f"dispatch-qualification-run{run:03}-attempt{attempt:03}.v1.json",
        root=f"implementation/p09/evidence/p09-361-case{index}-current-runtime-run{run:03}.v1.json")


def admit(q,ctx,a,qualification=None):
    """Read every declared source, never a candidate-derived expected scope."""
    code=q.json(ctx.code);pref=q.json(ctx.preflight)
    a.fields(code,dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",
        index=ctx.index,physical_run=ctx.run,contracts=dict(run=74,errors=0,failures=0,skipped=0),
        cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),
        "DISPATCH_EXACT_FROZEN_CODE")
    a.fields(pref,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
        index=ctx.index,physical_run=ctx.run,original_preflight_contracts=10,Rust_inputs=787,
        cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,
        product_worker_or_Native_frame_executed=False,independent_oracle_connected=True),"DISPATCH_EXACT_WHOLE_PREFLIGHT")
    a.require(code["fresh_inputs"]==code["final_fresh_hashes"] and pref["fresh_inputs"]==pref["final_fresh_hashes"],
        "DISPATCH_ALL_CLOSING_HASHES")
    a.require(code["runtime_default_import_count"]<=64 and pref["runtime_default_imports"]<=64,
        "DISPATCH_ORIGINAL_HELPER_CEILING")
    a.exact(pref["code_pin"],q.snapshots[ctx.code],"DISPATCH_PREFLIGHT_EXACT_CODE_BYTES")
    for pin in code["source_pins"]+pref["current_source_pins"]:
        a.exact(q.pin(pin["path"]),pin,"DISPATCH_UNCHANGED_ALL_QUALIFIED_SOURCES")
    if qualification is not None:
        a.fields(qualification,dict(state="PASS_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            index=ctx.index,physical_run=ctx.run,contracts=dict(run=6,errors=0,failures=0,skipped=0),
            cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),"DISPATCH_QUALIFIED_ENTRY")
        a.require(qualification["fresh_inputs"]==qualification["final_fresh_hashes"]
            and qualification["runtime_default_imports"]<=64,"DISPATCH_QUALIFICATION_FULL_CLOSURE")
        a.exact(qualification["code_pin"],q.snapshots[ctx.code],"DISPATCH_QUALIFIED_CODE")
        a.exact(qualification["preflight_pin"],q.snapshots[ctx.preflight],"DISPATCH_QUALIFIED_PREFLIGHT")
        for pin in qualification["source_pins"]:
            a.exact(q.pin(pin["path"]),pin,"DISPATCH_CURRENT_ENTRY_AND_DECLARATIONS")
        names={p["path"] for p in qualification["source_pins"]}
        a.require({SELF,TEST}<=names,"DISPATCH_ENTRY_AND_TEST_DECLARED")
    return code,pref


def previous_stops(q,ctx,a):
    """No automatic replay of any passed, incomplete or unresolved product."""
    for run in range(2,ctx.run):
        path=f"implementation/p09/evidence/p09-361-case{ctx.index}-current-runtime-run{run:03}.v1.json"
        row=q.json(path)
        a.fields(row,dict(state="DEFERRED_NOT_STARTED",task=f"case{ctx.index}-current-r{run:03}-tests",
            worker_created=False,product_body_observed=False,actual_product_child_executed=False,
            cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0,
            current_generation_runtime_candidate_qualified=False,Native_source_frame_qualified=False),
            "DISPATCH_PREVIOUS_PREBODY_STOP_ONLY")
        a.require(row["stop_reason"] in ("STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME",
            "STOP_NATIVE_OPEN_AFTER_HOST_SATURATION","STOP_SYSTEM_COMMIT_PRESSURE",
            "FLAT_QUEUE_LEAN_IMPORTED_HELPER_BOUND"),"DISPATCH_REVIEWED_PREBODY_REASON")
        a.require(row["passed_test_names"]==[] and row["source_frame"] is None,
            "DISPATCH_NO_PRIOR_PRODUCT_OR_UNRESOLVED_FRAME")


def current_namespaces(q,ctx,a,old,scope,bytes_policy,qualification=None):
    """Exact full source namespaces, not removed or hidden default imports."""
    import builtins
    sealed=scope.pins((q.json(ctx.code)["source_pins"] if qualification is None else qualification["source_pins"]))
    names=("current_queue_successor_binding","current_queue_successor_connections",
        "current_queue_successor_runtime","current_queue_successor_controller")
    pins=[]
    for name in names:
        pin=sealed[f"tools/p09/{name}.py"]
        a.exact(q.pin(pin["path"]),pin,"DISPATCH_ALL_EXACT_CURRENT_NAMESPACE_SOURCES")
        pins.append(pin)
    namespaces,proof=old.old.namespace_bundle.load(q.root,pins,{
        "current_stored_runtime_scope":scope,"owned_source_read_pressure":bytes_policy})
    # Inner imports resolve the same explicit, pinned graph as top-level aliases.
    # sys.modules is not edited. Every non-import node is retained by the loader.
    private=vars(namespaces)
    ordinary=builtins.__import__
    def declared_import(name,globals=None,locals=None,fromlist=(),level=0):
        if level==0 and name in private:return private[name]
        return ordinary(name,globals,locals,fromlist,level)
    for namespace in private.values():
        for name,value in tuple(vars(namespace).items()):
            env=getattr(value,"__globals__",None)
            if type(env) is dict and env.get("__name__","").startswith("p09_exact_current_queue_successor_"):
                env["__builtins__"]={**vars(builtins),"__import__":declared_import}
                # Function objects capture their builtins at creation. Recreate
                # the same code/defaults/closure after the private import map is
                # installed; never mutate Python's shared builtins dictionary.
                projected=FunctionType(value.__code__,env,argdefs=value.__defaults__,closure=value.__closure__)
                projected.__kwdefaults__=value.__kwdefaults__
                a.require(projected.__code__ is value.__code__ and projected.__defaults__ is value.__defaults__
                    and projected.__closure__ is value.__closure__,"DISPATCH_ENTIRE_PRIVATE_FUNCTION_RETAINED")
                env[name]=projected;setattr(namespace,name,projected)
    return namespaces.current_queue_successor_runtime,namespaces.current_queue_successor_controller,proof


def compose_outer(window,template,callback,metadata):
    """Preserve the entire qualified run chain and local diagnostic connector."""
    original=window.API.original_run_owned
    def binding_attempt(reader,run):
        metadata.require(type(run) is int and run==1,"DISPATCH_ONE_LOGICAL_ATTEMPT")
        return callback(reader)
    env=dict(original.__globals__,template=template,binding=callback,binding_attempt=binding_attempt)
    connected=metadata.clone(original,env)
    execute,state=window.CONNECTION.connect_run(connected,window.BACKEND)
    metadata.require(state["actual_local_bindings"]==0 and state["static_leaf_connections"]==1,
        "DISPATCH_ORIGINAL_NATIVE_DIAGNOSTIC_CONSTRUCTION_ONLY")
    return execute,state


def construct(q,ctx,a,old,runtime,scope,bytes_policy,controller,qualification=None,*,full_admission=True):
    a.require(type(full_admission) is bool,"DISPATCH_EXPLICIT_ADMISSION_MODE")
    if full_admission:
        admit(q,ctx,a,qualification)
    else:
        # The original Native metadata callback below performs the complete
        # admission again before Frame/GO. Do not pre-read the same 110 MB in
        # a separate preparation epoch or treat this small startup as admission.
        a.fields(qualification,dict(state="PASS_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            index=ctx.index,physical_run=ctx.run,contracts=dict(run=6,errors=0,failures=0,skipped=0),
            cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False),
            "DISPATCH_SEALED_STARTUP_NOT_FULL_ADMISSION")
        pins=scope.pins(qualification["source_pins"])
        for name in (SELF,TEST):a.exact(q.pin(name),pins[name],"DISPATCH_EXACT_QUALIFIED_STARTUP_CODE")
    q.pin(SELF);q.pin(TEST)
    loader=old.old.namespace_bundle;window=old.old.prior
    name=f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-connections{ctx.run:03}.v1.json"
    report=q.json(name)
    hint=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-worker-bootstrap{ctx.run:03}.v1.json")
    pin,wire=q._read(report["capsule_pin"]["path"],parse=True);q._bind(pin["path"],pin)
    a.exact(pin,report["capsule_pin"],"DISPATCH_EXACT_WIRE")
    graph,decoder=runtime.reconstruct_worker_graph(q.root,loader,scope,bytes_policy,hint,bytes(wire),q.checkpoint)
    a.exact(hint["step"],report["step"],"DISPATCH_SAME_STEP")
    step=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-step-config001.v1.json")
    a.exact(step,report["step"],"DISPATCH_ACTUAL_STEP_BYTES")
    old.old.base.configure(ctx.index)
    template,identity,proof=runtime.connect_factory(q.root,loader,window,ctx.index,ctx.run,q.checkpoint)
    # Complete runtime imports are declared before constructing the entry.
    names=controller.imported_sources(q.root)
    a.require(len(names)<=64,"DISPATCH_ORIGINAL_PRODUCTION_HELPER_BOUND")
    for name in sorted(names):q.pin(name)
    declared=dict(q.snapshots)
    report_pin=q.snapshots[f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-connections{ctx.run:03}.v1.json"]
    def callback(reader):
        admit(reader,ctx,a,qualification)
        previous_stops(reader,ctx,a)
        required,rust=runtime.current_input_scope(reader,graph,step,report_pin,report["manifest_pin"],declared)
        return scope.extend(required,reader.snapshots),rust
    engine,state,parent_proof=runtime.compose_parent(template,graph,callback,q.checkpoint)
    parent_states=[state]
    env=state.original.__globals__
    native_names=names|{env["SELF"],env["TEST"],env["native"].SELF,env["native"].TEST,env["scope"].SELF,env["scope"].TEST}
    a.require(len(native_names)<=64,"DISPATCH_ACTUAL_NATIVE_IMPORTED_HELPER_BOUND")
    for name in sorted(native_names):q.pin(name)
    # The exact engine's explicit helper witnesses also belong to actual scope.
    declared.update(q.snapshots)
    def parent_template():
        return engine,parent_proof
    execute,diagnostic=compose_outer(window,parent_template,callback,runtime.metadata)
    return NS(execute=execute,diagnostic=diagnostic,parent_states=parent_states,callback=callback,
        graph=graph,identity=identity,window=window,imports=names,native_imports=native_names)


def prepare_bootstrap(q,ctx,a,runtime,scope):
    """Create only the small current worker hint from exact declared graph data."""
    import json,os
    report=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-connections{ctx.run:03}.v1.json")
    a.fields(report,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",
        index=ctx.index,task=f"case{ctx.index}-current-r{ctx.run:03}-tests",cleanup_confirmed=True,
        accepted_count_delta=0,GO_authorized=False),"DISPATCH_EXACT_BOOTSTRAP_GRAPH")
    for pin in report["source_pins"]:a.exact(q.pin(pin["path"]),pin,"DISPATCH_UNCHANGED_BOOTSTRAP_GRAPH_SOURCES")
    step=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-step-config001.v1.json")
    a.exact(step,report["step"],"DISPATCH_BOOTSTRAP_STEP")
    authority=a.read_exact(q,step["prior_queue_pin"])
    a.fields(authority,dict(accepted_count_after=ctx.index-7,next_runtime_index=ctx.index,
        runtime_candidate_pin=step["prior_candidate_pin"],resource_cleanup_confirmed=True),"DISPATCH_BOOTSTRAP_AUTHORITY")
    prior=a.read_exact(q,step["prior_candidate_pin"])
    manifest=a.read_exact(q,report["manifest_pin"])
    a.exact(q.pin(report["capsule_pin"]["path"]),report["capsule_pin"],"DISPATCH_BOOTSTRAP_CAPSULE")
    hint=runtime.worker_hint(step,ctx.run,report["capsule_pin"],report["manifest_pin"],manifest,
        prior["source_input_representation"]["descriptors"])
    raw=(json.dumps(hint,ensure_ascii=True,allow_nan=False,separators=(",",":"))+"\n").encode("ascii")
    a.require(0<len(raw)<=16384,"DISPATCH_BOUNDED_BOOTSTRAP")
    name=f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-worker-bootstrap{ctx.run:03}.v1.json"
    path=q.root/name
    for parent in (path.parent,*path.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_BOOTSTRAP_ANCESTORS")
        if parent==q.root:break
    q.checkpoint()
    with path.open("xb") as stream:a.exact(stream.write(raw),len(raw),"ALL_BOOTSTRAP_BYTES");stream.flush();os.fsync(stream.fileno())
    q.fresh_pin(name)
    return name


def main(ctx,qualify,bootstrap=False):
    import io,json,os,re,time,unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows();sys.path.insert(0,str(c.ROOT))
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    namespaces,old_source_proof=envelope.namespace_bundle.load(c.ROOT,[ORIGINAL_CONTROLLER_PIN],
        {"flat_current_queue_envelope_runtime_v25":envelope})
    old=namespaces.case160_run007_controller
    guards=old.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();code=1;prepared=None;q=None
    out=dict(state="FAILED_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_ADOPTED",index=ctx.index,physical_run=ctx.run,
        accepted_count_delta=0,GO_authorized=False,product_or_Native_executed=False)
    if not qualify:a.require(not (c.ROOT/ctx.root).exists(),"DISPATCH_NO_EXISTING_CANDIDATE_REPLAY")
    if qualify:a.require(not (c.ROOT/ctx.qualification).exists(),"EXCLUSIVE_DISPATCH_QUALIFICATION")
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        qualification=None if (qualify or bootstrap) else q.json(ctx.qualification)
        if not bootstrap and qualify:admit(q,ctx,a)
        if bootstrap:
            # Bootstrap producer has no CODE yet; graph preparation pins the
            # same current source graph explicitly.
            graph_report=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-connections{ctx.run:03}.v1.json")
            qualification=dict(source_pins=graph_report["source_pins"])
            # Controller is not needed by this producer. Its exact source is
            # still available from the unchanged prior CODE qualification.
            prior_code=q.json(f"implementation/p09/evidence/p09-361-case{ctx.index}-successor-code-run002-attempt008.v1.json")
            merged=scope.extend(scope.pins(qualification["source_pins"]),scope.pins(prior_code["source_pins"]))
            qualification["source_pins"]=list(merged.values())
        runtime,controller,namespace_proof=current_namespaces(q,ctx,a,old,scope,bytes_policy,qualification)
        if bootstrap:
            q.pin(SELF);q.pin(TEST)
            name=prepare_bootstrap(q,ctx,a,runtime,scope)
            q.finish();guard.check(force=True)
            out.update(state="PREPARED_SUCCESSOR_WORKER_BOOTSTRAP_NOT_CODE_PREFLIGHT_NATIVE_OR_PRODUCT",
                bootstrap_pin=q.snapshots[name],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            code=0
        else:
            prepared=construct(q,ctx,a,old,runtime,scope,bytes_policy,controller,qualification,full_admission=qualify)
        if qualify:
            suite=unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_current_queue_successor_dispatch")
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
            contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            out["contracts"]=contracts
            a.exact(contracts,dict(run=6,errors=0,failures=0,skipped=0),"DISPATCH_ALL_CONTRACTS")
            required,rust=prepared.callback(q)
            build=prepared.parent_states[0].original.__globals__["build"]
            pacer=build.QueryPacer(q.checkpoint)
            a.exact(build.base.inputs.rust_inputs(c.ROOT,pacer.reserve),rust,"DISPATCH_FRESH_FULL_RUST_INVENTORY")
            model=prepared.graph.binding.runtime_budget(required,pacer.requests,prepared.window.DIRECT.runtime_budget,q.checkpoint)
            a.require(len(prepared.parent_states)==1 and prepared.parent_states[0].attempts==0
                and not prepared.parent_states[0].frames and prepared.diagnostic["actual_local_bindings"]==0,
                "DISPATCH_QUALIFICATION_NO_NATIVE_PRODUCT_OR_GO")
            q.finish();guard.check(force=True)
            out.update(state="PASS_SUCCESSOR_DISPATCH_CONSTRUCTION_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
                code_pin=q.snapshots[ctx.code],preflight_pin=q.snapshots[ctx.preflight],
                source_pins=list(q.snapshots.values()),source_inputs=len(required),runtime_default_imports=len(prepared.imports),
                actual_Native_helper_count=len(prepared.native_imports),private_current_namespace_source_proofs=namespace_proof,
                original_controller_whole_source_proofs=old_source_proof,
                complete_runtime_budget=model,whole_Rust_inventory=pacer.summary(),
                Native_startup_full_admission_deferred_to_original_metadata_callback=True,
                no_preparation_epoch_copy_of_whole_Native_source_reads=True,
                fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            code=0
        elif not bootstrap:
            # Small startup closes before the original entry creates its sole
            # sampler/Job; full admission occurs inside Native metadata only.
            q.finish();guard.close();a.require(guard.cleanup,"DISPATCH_PREPARATION_CLEANUP")
            code=prepared.execute(1)
            a.require(prepared.diagnostic["actual_local_bindings"]==1,"DISPATCH_ONE_ACTUAL_NATIVE_DIAGNOSTIC")
            a.require(len(prepared.parent_states)==1 and prepared.parent_states[0].attempts==1,
                "DISPATCH_ONE_REAL_PARENT_ENGINE")
            return code
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
        frames=[];tb=error.__traceback__
        while tb is not None:
            frames.append(dict(file=Path(tb.tb_frame.f_code.co_filename).name,function=tb.tb_frame.f_code.co_name,line=tb.tb_lineno))
            tb=tb.tb_next
        out["failure_frames"]=frames[-12:]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
        if guard.samples:
            out["terminal_resource_sample"]={key:guard.samples[-1].get(key) for key in
                ("system_cpu_percent","available_ram_percent","commit_used_percent",
                 "parent_cpu_machine_percent","parent_private_mib","parent_private_percent")}
        out["metadata_progress"]=dict(fresh_inputs=len(q.snapshots) if q else 0,
            actual_read_passes=q.read_passes if q else 0,actual_bytes_read=q.bytes_read if q else 0)
    a.require(guard.cleanup,"DISPATCH_GUARD_CLEANUP")
    if qualify:
        raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
        a.require(0<len(raw)<=262144,"BOUNDED_DISPATCH_REPORT")
        output=c.ROOT/ctx.qualification
        for parent in (output.parent,*output.parent.parents):
            a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_DISPATCH_REPORT_ANCESTORS")
            if parent==c.ROOT:break
        with output.open("xb") as stream:a.exact(stream.write(raw),len(raw),"ALL_DISPATCH_REPORT_BYTES");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","contracts","source_inputs","runtime_default_imports",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","error_type","failure_frames")}))
    return code


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
    parser.add_argument("--code-attempt",type=int,required=True);parser.add_argument("--preflight-attempt",type=int,required=True)
    parser.add_argument("--qualification-attempt",type=int,required=True)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument("--qualify",action="store_true");mode.add_argument("--native",action="store_true")
    mode.add_argument("--prepare-bootstrap",action="store_true")
    args=parser.parse_args()
    raise SystemExit(main(context(args.case,args.run,args.code_attempt,args.preflight_attempt,args.qualification_attempt),args.qualify,args.prepare_bootstrap))
