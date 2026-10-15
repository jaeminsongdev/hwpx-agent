"""Private real-engine metadata-reader connection; no GO/Native entry.

The full original admission callback and original BuildReader wrappers remain.
This qualification does not authorize the independent Native Frame or acceptor.
"""
import ast
import copy
import hashlib
from pathlib import Path
from types import FunctionType,SimpleNamespace as NS
import sys

SELF="tools/p09/lossless_metadata_connection_v1.py"
TEST="tools/p09/tests/test_lossless_metadata_connection_v1.py"
RETRY=dict(path="tools/p09/current_queue_successor_retry_runtime_v3.py",bytes=11451,
    sha256="c8f2c06f224890581177d8e3d8e55ab3111463ac5b11d505f6c47171d61ce348")
READER=dict(path="tools/p09/fresh_lossless_metadata_reader_v1.py",bytes=9403,
    sha256="aa312b81bb93f1eb800e281b4273abfd06894ea4f5d1f39b0b183295efc39208")
READER_TEST=dict(path="tools/p09/tests/test_fresh_lossless_metadata_reader_v1.py",bytes=3720,
    sha256="b62c3d57a6310f51949f22e971d15c64015d91cb7142102943ae866b7e4e612f")
SHARED=dict(path="tools/p09/shared_metadata_frame_decoder_budget_v1.py",bytes=7823,
    sha256="fb9440e5c89ad684fda6d076a57a940fb2f44114c26d88051d272a4a60a609f6")


def require(ok,label):
    if not ok:raise ValueError("LOSSLESS_METADATA_CONNECTION_"+label)


def connect_engine(engine,binding,fresh,budget_type,checkpoint,shared=None):
    original=engine.run_owned;require(type(original) is FunctionType,"ORIGINAL_FUNCTION")
    env=original.__globals__
    require(not any(getattr(module,"__dict__",None) is env for module in tuple(sys.modules.values()) if module),"PRIVATE_ENGINE_ONLY")
    build=env["build"];old_reader=build.BuildReader;old_summary=build.pressure_summary
    descriptors=binding.descriptors()
    required={d["semantic_original_pin"]["path"]:d["semantic_original_pin"] for d in descriptors}
    required[binding.manifest_pin["path"]]=dict(binding.manifest_pin)
    projection,proof=binding.project(required,checkpoint)
    budgets=[];readers=[]
    class Router:
        def __init__(self,budget):
            self.budget=budget;self.semantic_pins=projection.semantic_pins;self.physical_pins=projection.physical_pins
            self.next_case=projection.next_case;self.counts={}
        def decode_fresh(self,name,pin,raw,live_checkpoint):
            previous=self.budget.checkpoint
            def guarded():previous();live_checkpoint()
            self.budget.checkpoint=guarded
            try:
                value=self.budget.run(lambda check:projection.decode_fresh(name,pin,raw,check))
                self.counts[name]=self.counts.get(name,0)+1
                return value
            finally:self.budget.checkpoint=previous
    class BuildReader(old_reader):
        def __new__(cls,*args,**kwargs):
            # This subclass only selects a fresh per-reader router/budget. The
            # original constructors run in their original MRO, not manually.
            require(len(args)>=2 and callable(args[1]),"ORIGINAL_READER_CHECKPOINT")
            budget=budget_type(args[1]);router=Router(budget)
            if shared is not None:shared.attach("metadata",budget)
            Routed=fresh.reader_type(old_reader,router,descriptors)
            reader=Routed(*args,**kwargs)
            reader._lossless_metadata_router=router
            budgets.append(budget);readers.append(reader)
            return reader
    def pressure_summary(guard):
        row=old_summary(guard)
        reader=guard.reader;router=reader._lossless_metadata_router
        record=router.budget.evidence()
        return dict(row,explicit_fresh_lossless_metadata=dict(fresh.summary(reader),
            mapping_count=len(descriptors),semantic_read_counts=dict(router.counts),
            decoder=dict(scope="metadata_reader_only_not_Native_shared_budget",
                limit_seconds=record["aggregate_limit_seconds"],elapsed_work_seconds=record["elapsed_decoder_work_seconds"],
                attempted=record["attempted_decodes"],completed=record["completed_decodes"],
                active=record["active_decode"],error_seen=record["terminal_error_seen"])))
    env["build"]=NS(**{**vars(build),"BuildReader":BuildReader,"pressure_summary":pressure_summary})
    require(engine.run_owned is original and engine.run_owned.__code__ is original.__code__,"ENTIRE_ENGINE_UNCHANGED")
    require(build.BuildReader is old_reader and build.pressure_summary is old_summary,"DEFAULT_BUILD_NOT_MUTATED")
    return NS(readers=readers,budgets=budgets,original_reader=old_reader,original_run=original,
        source_projection=proof,whole_original_engine_and_worker_retained=True)


def callback(raw,pin,env):
    require(type(raw) is bytes and len(raw)==pin["bytes"] and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_FROZEN_DISPATCH")
    tree=ast.parse(raw.decode("utf-8"))
    construct=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="construct")
    nodes=[n for n in construct.body if isinstance(n,ast.FunctionDef) and n.name=="callback"]
    require(len(nodes)==1,"ONE_WHOLE_CALLBACK")
    copied=copy.deepcopy(nodes[0]);require(ast.dump(copied,include_attributes=False)==ast.dump(nodes[0],include_attributes=False),"ENTIRE_CALLBACK_AST")
    execute_env=dict(env)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copied],type_ignores=[])),pin["path"],"exec"),execute_env)
    return execute_env["callback"]


def main():
    import argparse,io,json,os,threading,time,unittest
    from unittest.mock import patch
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import owned_source_read_pressure as bytes_policy
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","attempt"):parser.add_argument("--"+name,type=int,required=True)
    args=parser.parse_args();require(164<=args.case<=249 and 2<=args.run<=8 and 1<=args.attempt<=8,"CLOSED_PROBE_CONTEXT")
    output=c.ROOT/f"implementation/p09/evidence/p09-361-case{args.case}-lossless-metadata-connection-run{args.run:03}-attempt{args.attempt:03}.v1.json"
    require(not output.exists(),"EXCLUSIVE_CONNECTION_PROBE")
    frozen,proof=envelope.namespace_bundle.load(c.ROOT,[RETRY],{})
    retry=frozen.current_queue_successor_retry_runtime_v3
    bridge_ns,proof=envelope.namespace_bundle.load(c.ROOT,[retry.BRIDGE],{})
    bridge=bridge_ns.current_queue_successor_wire_runtime_v2;retry.bind_metadata(bridge)
    old_ns,proof=envelope.namespace_bundle.load(c.ROOT,[bridge.OLD_CONTROLLER],{"flat_current_queue_envelope_runtime_v25":envelope})
    old=old_ns.case160_run007_controller;guards=old.base.FIRST
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();q=metadata=binding_state=connection=engine=shared=None
    row=dict(state="FAILED_LOSSLESS_METADATA_CONNECTION_NOT_ADOPTED",accepted_count_delta=0,
        product_or_Native_executed=False,GO_authorized=False,Native_Frame_or_shared_decoder_budget_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        own=q.pin(SELF);test=q.pin(TEST)
        for pin in (RETRY,READER,READER_TEST,SHARED,retry.BRIDGE,retry.BRIDGE_TEST,bridge.OLD_CONTROLLER):a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CONNECTION_DEPENDENCY")
        shared_code=q.json(f"implementation/p09/evidence/p09-361-case{args.case}-shared-metadata-frame-decoder-code003.v1.json")
        a.fields(shared_code,dict(state="PASS_SHARED_METADATA_FRAME_DECODER_CODE_NOT_NATIVE_OR_PRODUCT",
            contracts=dict(run=8,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"QUALIFIED_SHARED_DECODER8")
        for pin in shared_code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_SHARED_DECODER_SOURCE")
        shared_ns,proof=envelope.namespace_bundle.load(c.ROOT,[SHARED],{})
        shared_module=shared_ns.shared_metadata_frame_decoder_budget_v1
        shared=shared_module.SharedBudget()
        fresh_ns,proof=envelope.namespace_bundle.load(c.ROOT,[READER],{})
        fresh=fresh_ns.fresh_lossless_metadata_reader_v1
        test_ns,proof=envelope.namespace_bundle.load(c.ROOT,[test],{"lossless_metadata_connection_v1":sys.modules[__name__]})
        tests=test_ns.test_lossless_metadata_connection_v1;tests.Tests.setUp.__globals__["CHECKPOINT"]=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contracts"]=contracts;require(contracts==dict(run=4,errors=0,failures=0,skipped=0),"ALL_CONNECTION4_CONTRACTS")
        modules,proof=retry.load(c.ROOT,a,scope,bytes_policy,envelope,bridge,
            f"implementation/p09/evidence/p09-361-case{args.case}-retry-code002.v1.json")
        dispatch=modules.current_queue_successor_dispatch;runtime=modules.current_queue_successor_runtime
        ctx=dispatch.context(args.case,args.run,1,1,1)
        qualification=q.json(ctx.qualification)
        runtime,controller,proof=dispatch.current_namespaces(q,ctx,a,old,scope,bytes_policy,qualification)
        report_name=f"implementation/p09/evidence/p09-361-case{args.case}-successor-connections{args.run:03}.v2.json"
        report=q.json(report_name);hint=q.json(f"implementation/p09/evidence/p09-361-case{args.case}-successor-worker-bootstrap{args.run:03}.v2.json")
        step=q.json(f"implementation/p09/evidence/p09-361-case{args.case}-step-config001.v1.json")
        a.exact(step,report["step"],"EXACT_CURRENT_STEP_BEFORE_DECLARATION")
        actual,wire=q._read(report["capsule_pin"]["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,report["capsule_pin"],"EXACT_REAL_WORKER_WIRE")
        graph,proof=runtime.reconstruct_worker_graph(c.ROOT,envelope.namespace_bundle,scope,bytes_policy,hint,bytes(wire),guard.check)
        old.old.base.configure(args.case)
        template,identity,proof=runtime.connect_factory(c.ROOT,envelope.namespace_bundle,old.old.prior,args.case,args.run,guard.check)
        engine,proof=template()
        Budget=graph.frames.connection.original.DecoderBudget
        connection=connect_engine(engine,graph.binding,fresh,Budget,guard.check,shared)
        original_frame_factory=graph.frames.frame_type
        graph.frames.frame_type=lambda base,binding:shared_module.frame_type(base,binding,original_frame_factory,shared)
        require(graph.parent.connect_engine.__globals__["original"].connect_engine.__globals__["frames"] is graph.frames,
            "SAME_REAL_PRIVATE_PARENT_FRAME_FACTORY")
        metadata=engine.run_owned.__globals__["build"].BuildReader(c.ROOT,guard.check)
        metadata.pacer=bytes_policy.OwnedPacer()
        build=engine.run_owned.__globals__["build"]
        owner=NS(lock=threading.Lock(),samples=guard.samples,checkpoint_io=guard.check)
        binding_state=build.pressure.PreSaturationReadCheckpoint(metadata,owner)
        dispatch_pin=bridge.PINS[0]
        pin,raw=q._read(dispatch_pin["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,dispatch_pin,"EXACT_WHOLE_CALLBACK_SOURCE")
        execute=callback(bytes(raw),pin,dict(ctx=ctx,a=a,qualification=qualification,admit=dispatch.admit,
            previous_stops=dispatch.previous_stops,runtime=runtime,graph=graph,step=report["step"],
            report_pin=q.snapshots[report_name],report=report,declared=dict(q.snapshots),scope=scope))
        with patch("subprocess.Popen",side_effect=AssertionError("PROBE_NO_CHILD")),patch("subprocess.run",side_effect=AssertionError("PROBE_NO_CHILD")):
            required,rust=execute(metadata)
            pref=metadata.json(ctx.preflight)
            for pin in pref["complete_semantic_source_scope"]:a.exact(required[pin["path"]],pin,"ALL_DECLARED_PREFLIGHT_SCOPE_RETAINED")
            for descriptor in graph.binding.descriptors():
                pin=descriptor["semantic_original_pin"];a.exact(metadata.pin(pin["path"]),pin,"ALL56_REAL_SEMANTIC_PINS")
            metadata.finish();q.finish();guard.check(force=True)
        require(len(connection.readers)==1 and len(connection.budgets)==1,"ONE_REAL_METADATA_READER_AND_BUDGET")
        summary=build.pressure_summary(binding_state)
        routed=metadata._lossless_metadata_router
        require(set(routed.counts)==set(graph.binding.originals) and all(n>=2 for n in routed.counts.values()),"ALL56_FRESH_READ_AND_FINAL_DECODE")
        row.update(state="PASS_FULL_METADATA_LOSSLESS_CONNECTION_NOT_NATIVE_PRODUCT_OR_GATE",descriptor_count=len(graph.binding.rows),
            original_whole_admission_callback_AST_retained=True,current_scope_count=len(required),Rust_inputs=len(rust),
            metadata_fresh_inputs=len(metadata.snapshots),metadata_final_fresh_hashes=metadata.final_fresh_hashes,
            actual_metadata_read_passes=metadata.read_passes,actual_metadata_physical_bytes=metadata.bytes_read,
            metadata_pressure=summary,source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_engine_function_identity_retained=engine.run_owned is connection.original_run,
            original_metadata_reader_MRO_wrappers_retained=issubclass(type(metadata),connection.original_reader),
            current_Native_root_reexecuted=False,actual_Native_Frame_created=False,
            shared_decoder=shared.evidence(),real_parent_Frame_factory_hook_installed=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
        row["error_type"]=type(error).__name__
        frames=[];tb=error.__traceback__
        while tb is not None:
            frames.append(dict(file=Path(tb.tb_frame.f_code.co_filename).name,function=tb.tb_frame.f_code.co_name,line=tb.tb_lineno));tb=tb.tb_next
        row["failure_frames"]=frames[-6:]
    finally:
        if binding_state is not None:binding_state.restore()
        if shared is not None:shared.restore()
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
        if metadata is not None:row["metadata_progress"]=dict(fresh_inputs=len(metadata.snapshots),reads=metadata.read_passes,physical_bytes=metadata.bytes_read)
    require(guard.cleanup,"CONNECTION_PROBE_CLEANUP")
    raw=(json.dumps(row,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8");require(0<len(raw)<=262144,"BOUNDED_CONNECTION_REPORT")
    for parent in (output.parent,*output.parent.parents):
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CONNECTION_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:require(stream.write(raw)==len(raw),"COMPLETE_CONNECTION_REPORT");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:row.get(k) for k in ("state","contracts","descriptor_count","current_scope_count","Rust_inputs",
        "metadata_fresh_inputs","metadata_final_fresh_hashes","actual_metadata_physical_bytes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code","error_type","failure_frames")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
