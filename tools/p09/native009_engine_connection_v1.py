"""Real original run009 template/worker composition, no Native dispatcher.

One exact private connect_factory run-limit slot is extended8->9. Identity,
single physical adapter, complete worker body, policy and10-second window are
the originals. Parent whole-source/Frame/GO qualification remains external.
"""
from types import FunctionType,SimpleNamespace as NS

SELF="tools/p09/native009_engine_connection_v1.py"
TEST="tools/p09/tests/test_native009_engine_connection_v1.py"
TASK="case165-current-r009-tests"
ROOT_RECEIPT="implementation/p09/evidence/p09-361-case165-current-runtime-run009.v1.json"


def require(ok,label):
    if not ok:raise ValueError("NATIVE009_ENGINE_"+label)


def factory9(original):
    require(type(original) is FunctionType and original.__name__=="connect_factory"
        and original.__code__.co_filename.replace("\\","/").endswith("tools/p09/current_queue_successor_runtime.py"),"EXACT_ORIGINAL_FACTORY")
    before=original.__code__;slots=[i for i,v in enumerate(before.co_consts) if type(v) is int and v==8]
    require(len(slots)==1,"ONE_FACTORY_RUN_BOUND_SLOT")
    values=list(before.co_consts);values[slots[0]]=9;code=before.replace(co_consts=tuple(values))
    undo=list(code.co_consts);undo[slots[0]]=8
    require(code.replace(co_consts=tuple(undo))==before,"ENTIRE_FACTORY_CODE_INVERSE")
    result=FunctionType(code,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    result.__kwdefaults__=original.__kwdefaults__
    return result,dict(constant_slot=slots[0],old=8,new=9,entire_code_inverse=True,
        original_defaults_and_closure_retained=True)


def build(root,loader,api,graph,original_window,recovery,window_tool,checkpoint):
    checkpoint()
    require(graph.worker.TASK==TASK and graph.binding.next_case==165 and len(graph.binding.descriptors())==69,"EXACT_FULL69_RUN009_GRAPH")
    require(not(root/ROOT_RECEIPT).exists(),"NO_EXISTING_NATIVE009_RECEIPT")
    window,window_proof=recovery.current_window(original_window,window_tool,(root/window_tool.WINDOW_PIN["path"]).read_bytes())
    # Normal isolated-process product configuration, not module source patching.
    window.M.base.configure(165)
    projected,factory_proof=factory9(api.runtime.connect_factory)
    template,names,identity_proof=projected(root,loader,window,165,9,checkpoint)
    require(names.physical_run(165)==9 and names.task(165)==TASK
        and names.root_path(NS(index=165))==ROOT_RECEIPT and names.public_run(165,9)==1,"ALL_REAL_IDENTITIES_AGREE")
    engine,engine_proof=template()
    original_worker=engine.worker
    # Construct exactly once; compose uses this same actual engine/worker.
    def same_engine():return engine,engine_proof
    execute,state,policy,worker_proof=api.runtime.compose_worker(same_engine,graph,root,checkpoint)
    require(state.original is original_worker and engine.worker is original_worker,"SAME_ACTUAL_ORIGINAL_WORKER")
    require(state.attempts==state.calls==0 and not state.completed,"NO_WORKER_EXECUTION_DURING_CONSTRUCTION")
    require(window.WINDOW.SECONDS==10,"UNCHANGED_PRODUCT10")
    return NS(engine=engine,execute=execute,state=state,policy=policy,names=names,graph=graph,window=window,
        factory_proof=factory_proof,identity_proof=identity_proof,worker_proof=worker_proof,window_proof=window_proof,
        original_worker=original_worker,original_template=template,
        product_Native_or_GO_authorized=False,whole_Native009_source_Frame_qualified=False)


def main():
    import argparse,importlib.util,io,json,re,sys,time,unittest
    from pathlib import Path
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
    import owned_source_read_pressure as bytes_policy
    import receipt_xz_envelope_v1 as xz
    import bounded_successor_capsule_wire_v2 as bounded
    import ast_clone_namespace_v1 as cloner
    import ast_copy_namespace_connection_v1 as optimization
    import native009_worker_transport_v1 as transport
    import flat_current_queue_product_window_runtime_v18 as original_window
    import post_product_recovery_window_v1 as window_tool
    import post_product_recovery_connection_v1 as recovery
    import prepare_native008_carrier_v1 as producer
    import successor_preparation_workspace_v1 as publisher
    parser=argparse.ArgumentParser();parser.add_argument("--attempt",type=int,required=True)
    attempt=producer.identifier(parser.parse_args().attempt);output=transport.PREFIX+f"native009-engine-code{attempt:03}.v1.json"
    require(not(c.ROOT/output).exists(),"EXCLUSIVE_ENGINE_CODE")
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))();started=time.monotonic();q=None
    row=dict(state="FAILED_NATIVE009_ENGINE_CODE_NOT_ADOPTED",actual_worker_product_or_Native_executed=False,
        accepted_count_delta=0,GO_authorized=False,whole_current_Native_source_or_dispatch_qualified=False)
    try:
        guard.acquire();guard.check(force=True);q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in (SELF,TEST,transport.SELF,transport.TEST):q.pin(path)
        prepared=q.json(transport.PREFIX+"native009-worker-transport-code002.v1.json")
        a.fields(prepared,dict(state="PASS_NATIVE009_CAPSULE69_AND_ORIGINAL_RECONSTRUCTION12_NOT_NATIVE_OR_DISPATCH",
            contracts=dict(run=12,errors=0,failures=0,skipped=0),descriptor_count=69,task=TASK,
            cleanup_confirmed=True,actual_product_Native_or_worker_process_executed=False,GO_authorized=False),"EXACT_PREPARED_TRANSPORT12")
        for pin in prepared["source_pins"]:
            if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):a.exact(q.pin(pin["path"]),pin,"CURRENT_TRANSPORT_PROGRAMS")
        hint=a.read_exact(q,prepared["bootstrap_pin"])
        pin,wire=q._read(prepared["capsule_pin"]["path"],parse=True);q._bind(pin["path"],pin);a.exact(pin,prepared["capsule_pin"],"EXACT_CURRENT_CAPSULE")
        loader,_=optimization.connect(envelope.namespace_bundle,cloner)
        api=transport.connect(c.ROOT,loader,scope,bytes_policy,xz,bounded,guard.check,a.exact)
        graph,proof=api.reconstruct(hint,bytes(wire),guard.check)
        linked=build(c.ROOT,loader,api,graph,original_window,recovery,window_tool,guard.check)
        spec=importlib.util.spec_from_file_location("native009_engine_contracts",c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
        tests.MODULE=sys.modules[__name__];tests.LINKED=linked;tests.API=api;tests.CHECKPOINT=guard.check
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row["contract_failures"]=[dict(test=t.id().rsplit(".",1)[-1],exception_type=trace.splitlines()[-1].split(":",1)[0]) for t,trace in result.errors+result.failures]
        a.exact(row["contracts"],dict(run=10,errors=0,failures=0,skipped=0),"ENGINE10")
        require(linked.state.attempts==linked.state.calls==0,"TESTS_NEVER_EXECUTED_REAL_WORKER")
        for module in tuple(sys.modules.values()):
            filename=getattr(module,"__file__",None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":q.pin(path.relative_to(c.ROOT).as_posix())
        q.finish();guard.check(force=True)
        row.update(state="PASS_NATIVE009_REAL_ENGINE_WORKER_COMPOSITION10_NOT_EXECUTION_OR_NATIVE",
            task=TASK,root_path=ROOT_RECEIPT,physical_run=9,logical_run=1,descriptor_count=69,product_window_seconds=10,
            factory_proof=linked.factory_proof,identity_proof=linked.identity_proof,worker_proof=linked.worker_proof,
            worker_code_path=linked.original_worker.__code__.co_filename,actual_worker_attempts=linked.state.attempts,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    require(guard.cleanup,"ENGINE_CODE_OWNER_CLEANUP");publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","contracts","contract_failures","task","physical_run","descriptor_count","actual_worker_attempts",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if row["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
