"""One successor CODE/preflight controller; no implicit Native execution.

Fresh source closure and exact case data are separate from fixture PASS.
Current source and every imported helper must remain in the declared input scope.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import sys

SELF="tools/p09/current_queue_successor_controller.py"
TEST="tools/p09/tests/test_current_queue_successor_controller.py"
ORIGINAL_PREFLIGHT_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_metadata_connection.py",bytes=4896,
    sha256="3d694c9497eb8354113a2df3969f218bd63fbc438144d64c29325d07ac324026")
SUITES=("test_current_queue_successor_controller","test_current_queue_successor_oracle",
    "test_current_queue_successor_runtime","test_current_queue_successor_connections",
    "test_current_queue_successor_binding","test_runtime_envelope_worker_connection_v1",
    "test_compact_worker_capsule_wire_v1","test_runtime_envelope_full_oracle_connection_v1")


def destination(index,run,mode,attempt):
    if type(index) is not int or not 161<=index<=249 or type(run) is not int or not 2<=run<=8:
        raise ValueError("CLOSED_CONTROLLER_CONTEXT")
    if mode not in ("code","preflight") or type(attempt) is not int or not 1<=attempt<=8:
        raise ValueError("CLOSED_CONTROLLER_MODE_OR_ATTEMPT")
    return f"implementation/p09/evidence/p09-361-case{index}-successor-{mode}-run{run:03}-attempt{attempt:03}.v1.json"


def imported_sources(root):
    """Original direct module inventory, no hiding or recursive discovery."""
    names=set()
    for module in tuple(sys.modules.values()):
        filename=getattr(module,"__file__",None)
        if filename:
            path=Path(filename).absolute()
            if path.is_relative_to(root/"tools/p09") and path.suffix==".py":names.add(path.relative_to(root).as_posix())
    return names


def run_code(index,run,attempt):
    import hashlib
    import io
    import json
    import os
    import re
    import time
    import unittest
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows();sys.path.insert(0,str(c.ROOT));sys.path.insert(0,str(c.ROOT/"tools/p09/tests"))
    import accept_case112_current_epoch as a
    import current_queue_successor_runtime as runtime
    import current_queue_successor_oracle as oracle
    import case160_run007_controller as old
    # Reuse the explicitly pinned private guards from the accepted controller.
    # Do not hide modules or raise the original production helper ceiling.
    distinct=old.base.FIRST.distinct_final_sample_guard_v1
    pressure=old.base.FIRST.terminal_metadata_pressure_v1
    output=c.ROOT/destination(index,run,"code",attempt)
    a.require(not output.exists(),"EXCLUSIVE_CURRENT_CODE_REPORT")
    guard=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_CURRENT_SUCCESSOR_CODE_NOT_ADOPTED",index=index,physical_run=run,
        accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for name in (SELF,TEST,runtime.SELF,runtime.TEST,oracle.SELF,oracle.TEST):q.pin(name)
        initial=imported_sources(c.ROOT)
        out["runtime_default_import_count"]=len(initial)
        a.require(len(initial)<=64,"ORIGINAL_RUNTIME_IMPORTED_HELPER_BOUND")
        for name in sorted(initial):q.pin(name)
        loader=unittest.defaultTestLoader
        suite=unittest.TestSuite(loader.loadTestsFromName("tools.p09.tests."+name) for name in SUITES)
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        out["contracts"]=contracts
        a.exact(contracts,dict(run=74,errors=0,failures=0,skipped=0),"ALL_CURRENT_CONTROLLER_CODE_CONTRACTS")
        # Test-only imports are part of CODE evidence, not silently promoted to
        # the <=64 production import graph. Native/preflight run in fresh processes.
        complete=imported_sources(c.ROOT)
        for name in sorted(complete):q.pin(name)
        q.finish();guard.check(force=True)
        out.update(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",runtime_default_import_count=len(initial),
            code_and_test_import_count=len(complete),source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,actual_read_passes=q.read_passes,actual_bytes_read=q.bytes_read,
            runtime_imported_helper_bound=64,new_runtime_process_required_before_preflight_or_Native=True,
            independent_checker_source_and_controller_contracts_included=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    a.require(guard.cleanup,"CONTROLLER_CODE_CLEANUP")
    raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0<len(raw)<=262144,"BOUNDED_CODE_REPORT")
    for parent in (output.parent,*output.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_CODE_REPORT_ANCESTORS")
        if parent==c.ROOT:break
    with output.open("xb") as stream:a.exact(stream.write(raw),len(raw),"ALL_CODE_REPORT_BYTES");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","contracts","runtime_default_import_count","code_and_test_import_count",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("PASS_") else 1


def run_preflight(index,run,code_attempt,attempt):
    """Original metadata-preflight obligations, no child or Native Frame."""
    import io,json,os,re,threading,time,unittest
    from unittest.mock import patch
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows();sys.path.insert(0,str(c.ROOT));sys.path.insert(0,str(c.ROOT/"tools/p09/tests"))
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import current_queue_successor_runtime as runtime
    import current_queue_successor_oracle as oracle
    import owned_source_read_pressure as bytes_policy
    import case160_run007_controller as old
    loader=old.old.namespace_bundle
    guards=old.base.FIRST
    output=c.ROOT/destination(index,run,"preflight",attempt)
    code_name=destination(index,run,"code",code_attempt)
    a.require(not output.exists(),"EXCLUSIVE_CURRENT_PREFLIGHT_REPORT")
    guard=guards.terminal_metadata_pressure_v1.guard_type(guards.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();binding=None;q=None
    out=dict(state="FAILED_CURRENT_SUCCESSOR_PREFLIGHT_NOT_ADOPTED",index=index,physical_run=run,
        product_worker_or_Native_frame_executed=False,accepted_count_delta=0,runtime_connection_qualified=False,
        GO_authorized=False,P09_gate="OPEN")
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        code=q.json(code_name)
        a.fields(code,dict(state="PASS_CURRENT_SUCCESSOR_CODE_NOT_FULL_PREFLIGHT_NATIVE_OR_PRODUCT",index=index,physical_run=run,
            contracts=dict(run=74,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            product_or_Native_executed=False,accepted_count_delta=0,GO_authorized=False),"EXACT_CURRENT_WHOLE_CODE")
        a.require(code["fresh_inputs"]==code["final_fresh_hashes"],"CLOSED_CURRENT_CODE_HASHES")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_UNCHANGED_CODE_AND_TEST_SOURCES")
        import flat_current_queue_metadata_runtime as original_metadata
        import flat_current_queue_metadata_acceptance as original_acceptance
        original_test_name="tools/p09/tests/test_flat_current_queue_metadata_connection.py"
        original_test_pin=q.pin(original_test_name)
        a.exact(original_test_pin,ORIGINAL_PREFLIGHT_TEST_PIN,"ORIGINAL_ACCEPTED_PREFLIGHT_TEST_BYTES_BEFORE_EXECUTION")
        test_namespaces,test_proofs=loader.load(c.ROOT,[original_test_pin],{
            "flat_current_queue_metadata_runtime":original_metadata,
            "flat_current_queue_metadata_acceptance":original_acceptance})
        tests=test_namespaces.test_flat_current_queue_metadata_connection
        owner=NS(lock=threading.Lock(),samples=guard.samples,checkpoint_io=guard.check)
        binding=tests.r.MetadataCheckpoint(q,owner)
        with patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')),patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
                patch.object(tests.r.base,"CONFIG",tests.r.base.CONFIG):
            result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        a.exact(dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            dict(run=10,errors=0,failures=0,skipped=0),"ALL_ORIGINAL_PREFLIGHT_CONTRACT10")
        report_name=f"implementation/p09/evidence/p09-361-case{index}-successor-connections{run:03}.v1.json"
        report=q.json(report_name);step=report["step"]
        a.fields(report,dict(state="PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO",index=index,
            cleanup_confirmed=True,accepted_count_delta=0,GO_authorized=False),"CURRENT_GRAPH_DECLARATION")
        actual_step=q.json(f"implementation/p09/evidence/p09-361-case{index}-step-config001.v1.json")
        a.exact(actual_step,step,"ACTUAL_STEP_BYTES_BEFORE_DECLARED_SCOPE_CAPTURE")
        hint=q.json(f"implementation/p09/evidence/p09-361-case{index}-successor-worker-bootstrap{run:03}.v1.json")
        actual,buffer=q._read(report["capsule_pin"]["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,report["capsule_pin"],"EXACT_PREFLIGHT_CURRENT_CAPSULE")
        graph,decoder=runtime.reconstruct_worker_graph(c.ROOT,loader,scope,bytes_policy,hint,bytes(buffer),guard.check)
        a.exact(hint["step"],step,"SAME_PARENT_AND_WORKER_STEP")
        a.exact(hint["manifest_pin"],report["manifest_pin"],"SAME_PARENT_AND_WORKER_MANIFEST")
        old.old.base.configure(index)
        template,identity,factory=runtime.connect_factory(c.ROOT,loader,old.old.prior,index,run,guard.check)
        engine,engine_proof=template()
        declared=dict(q.snapshots)
        callback=lambda reader:runtime.current_input_scope(reader,graph,step,q.snapshots[report_name],report["manifest_pin"],declared)
        required,rust=callback(q)
        parent,parent_state,parent_proof=runtime.compose_parent(lambda:(engine,engine_proof),graph,callback,guard.check)
        for directory,name,size,digest in engine.run_owned.__globals__["FAILED_PREIMAGES"]:
            path="implementation/p09/evidence/"+directory+"/"+name
            a.exact(q.pin(path),dict(path=path,bytes=size,sha256=digest),"ORIGINAL_FAILURE_ARCHIVE")
        names=imported_sources(c.ROOT);out["runtime_default_imports"]=len(names)
        a.require(len(names)<=64,"ORIGINAL_PREFLIGHT_HELPER_BOUND")
        for name in sorted(names):q.pin(name)
        native=engine.run_owned.__globals__["native"]
        for pin in native.SOURCES:a.exact(q.pin(pin["path"]),pin,"ALL_NATIVE_DEFINITION_PINS")
        required=scope.extend(required,q.snapshots);required,aliases=graph.binding.semantic_union(required,q.checkpoint)
        build=engine.run_owned.__globals__["build"]
        pacer=build.QueryPacer(q.checkpoint)
        a.exact(build.base.inputs.rust_inputs(c.ROOT,pacer.reserve),rust,"FRESH_WHOLE_RUST787_INVENTORY")
        model=graph.binding.runtime_budget(required,pacer.requests,old.old.prior.DIRECT.runtime_budget,q.checkpoint)
        independent,proof=oracle.connect(old.CURRENT,graph,old.old.base.CONFIG,identity,required,q.checkpoint)
        independent.environment["only159"]()
        a.require(parent_state.attempts==0 and not parent_state.frames,"NO_NATIVE_FRAME_OR_PRODUCT_IN_PREFLIGHT")
        q.finish();guard.check(force=True)
        projection,proof=graph.binding.project(required,q.checkpoint)
        out.update(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            original_preflight_contracts=10,code_pin=q.snapshots[code_name],current_source_pins=list(q.snapshots.values()),
            complete_semantic_source_scope=[dict(p) for p in projection.semantic_pins.values()],
            complete_physical_source_scope=[dict(p) for p in projection.physical_pins.values()],
            complete_runtime_budget=model,source_inputs=len(required),Rust_inputs=len(rust),runtime_default_imports=len(names),
            imported_source_paths=sorted(names),whole_Rust_inventory=pacer.summary(),independent_oracle_connected=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,actual_read_passes=q.read_passes,actual_bytes_read=q.bytes_read)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,NameError) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        if binding is not None:binding.restore();out["original_metadata_checkpoint"]=binding.summary()
        guard.close();out.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            resource_samples=guard.samples,CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    a.require(guard.cleanup,"CURRENT_PREFLIGHT_CLEANUP")
    raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0<len(raw)<=2*1048576,"BOUNDED_WHOLE_PREFLIGHT_REPORT")
    for ancestor in (output.parent,*output.parent.parents):
        a.require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),"DIRECT_PREFLIGHT_ANCESTORS")
        if ancestor==c.ROOT:break
    with output.open("xb") as stream:a.exact(stream.write(raw),len(raw),"ALL_PREFLIGHT_REPORT_BYTES");stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","source_inputs","Rust_inputs","runtime_default_imports","fresh_inputs",
        "final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);parser.add_argument("--run",type=int,required=True)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument("--code",action="store_true")
    mode.add_argument("--preflight",action="store_true");parser.add_argument("--attempt",type=int,required=True)
    parser.add_argument("--code-attempt",type=int)
    args=parser.parse_args()
    if args.code:raise SystemExit(run_code(args.case,args.run,args.attempt))
    if args.code_attempt is None:parser.error("--preflight requires --code-attempt")
    raise SystemExit(run_preflight(args.case,args.run,args.code_attempt,args.attempt))
