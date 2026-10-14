"""Publish real32 declaration and compact capsule; no controller/GO permission."""
import ctypes
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
SELF="tools/p09/prepare_run004_manifest_capsule_r370.py"
OUTPUT="implementation/p09/evidence/p09-361-run004-manifest32-capsule-code12-r849.v1.json"
CAPSULE="implementation/p09/evidence/p09-361-case160-worker-policy-capsule006.compact.v1.json"

def serialize(value):return (json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode("ascii")

def write_exclusive(root,path,data):
    target=root/path
    if target.exists() or target.is_symlink() or target.parent.is_symlink() or target.parent.is_junction():
        raise ValueError("RUN004_ARTIFACT_REFUSE_OVERWRITE_OR_LINK")
    with target.open("xb") as stream:
        if stream.write(data)!=len(data):raise ValueError("RUN004_ARTIFACT_INCOMPLETE_WRITE")
    return dict(path=path,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    p=k.GetCurrentProcess()
    if not(k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parent/"tests"))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import runtime_successor_manifest_v7 as manifest
    import successor_runtime_graph_v6 as factory
    import prepared_checkpoint_transport_v1 as transport
    import prepared_scope_handoff_v1 as handoff
    import prepared_input_checkpoint_v1 as prepared
    import preparation_terminal_progress_v1 as progress
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"MANIFEST32_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_RUN004_MANIFEST32_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,files_created=[],P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,manifest.SELF,manifest.TEST,factory.SELF,factory.TEST)
        for path in paths:q.pin(path)
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests."+n) for n in
            ("test_runtime_successor_manifest_v7","test_successor_runtime_graph_v6"))
        tested=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(tested.wasSuccessful() and tested.testsRun==12 and not tested.skipped,"MANIFEST_GRAPH_CODE12")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160);base,bootstrap=c.bootstrap.load(c.old,q.checkpoint)
        for pin in bootstrap["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"REAL_BASE29_CORE")
        produced=q.json("implementation/p09/evidence/p09-361-prepared-checkpoint-transport-producer-r839.v1.json")
        a.fields(produced,dict(state="PASS_EXCLUSIVE_PREPARED_CHECKPOINT_TRANSPORT_NOT_RUNTIME_OR_GO",
            cleanup_confirmed=True,GO_authorized=False,Native_or_product_executed=False),"EXACT_PREPARED_TRANSPORT")
        listing=a.read_exact(q,a.scope.LIST_PIN);rust=handoff.rust_inputs(a.scope.listing_inputs(listing))
        s=c._env["current_binding"].successor
        scope,_,_=transport.load(q,produced["original_pin"],produced["physical_pin"],base.binding,
            expected_context=dict(index=160,before=153,physical_product_run=3),
            expected_current_pins=dict(data_pin=q.pin(c.DATA),preflight_pin=q.pin(c.PREFLIGHT),authority_pin=s.AUTHORITY,prior_runtime_pin=s.ROOT),
            expected_rust=rust,expected_source_paths=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",prepared.SELF,prepared.TEST,
                progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,distinct.SELF,distinct.TEST)))
        row=dict(schema_version=manifest.SCHEMA,index=160,before=153,physical_product_run=4,
            base_manifest_pin=c.MANIFEST,extra_failure_producer_pin=q.pin(manifest.extras.PRODUCER),
            prior132_producer_pin=q.pin(manifest.PRIOR_PRODUCER))
        manifest.validate(row,a,c.MANIFEST)
        manifest_pin=write_exclusive(a.c.ROOT,manifest.PATH,serialize(row));out["files_created"].append(manifest.PATH)
        a.exact(q.fresh_pin(manifest.PATH),manifest_pin,"ACTUAL_NEW_MANIFEST029_BYTES")
        bound,scope,proof=manifest.load(q,manifest_pin,a,base_graph=base,base_pin=c.MANIFEST,prepared_scope=scope)
        graph,graph_proof=factory.connect(base,bound)
        wire,wire_pin=graph.worker.encode(bound,s.AUTHORITY,s.ROOT,q.checkpoint)
        capsule_pin=write_exclusive(a.c.ROOT,CAPSULE,wire);out["files_created"].append(CAPSULE)
        a.exact(q.fresh_pin(CAPSULE),capsule_pin,"ACTUAL_COMPACT32_CAPSULE_BYTES")
        restored,decoder=graph.worker.decode(wire,wire_pin,q.checkpoint)
        a.exact(restored.descriptors(),bound.descriptors(),"ACTUAL_ALL32_RESTORED_FROM_CAPSULE")
        a.exact(dict(restored.manifest_pin),manifest_pin,"CAPSULE32_USES_ACTUAL_MANIFEST029")
        complete=c.M.base.scope.extend(scope,q.snapshots);projection,_=bound.project(complete,q.checkpoint)
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        original=c.old.prior.DIRECT.runtime_budget(physical,167)
        predicted=original["predicted_runtime_combined_seconds"]+5.0
        budget=None;budget_error=None
        try:budget=bound.runtime_budget(complete,167,c.old.prior.DIRECT.runtime_budget,q.checkpoint)
        except ValueError as error:
            a.require(error.args and error.args[0]=="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5","ONLY_ORIGINAL600_COST_REJECTION")
            budget_error=error.args[0]
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL_RUN004_MANIFEST32_COMPACT_CAPSULE_CODE12_NOT_CONTROLLER_NATIVE_OR_GO",
            contracts=dict(run=12,errors=0,failures=0,skipped=0),actual_manifest_pin=manifest_pin,actual_capsule_pin=capsule_pin,
            source_pairs=32,compact_wire_bytes=len(wire),original_wire_limit=16384,worker_task=graph.worker.TASK,
            real_manifest_loader_proof=proof,graph_connection_proof=graph_proof,decoder_proof=decoder,
            predicted_Native_cost_including_decoder5=predicted,original600_cost_accepted=budget is not None,
            budget=budget,budget_error=budget_error,source_pins=[q.snapshots[path] for path in paths],
            whole_qualifier_source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            physical_scope_count=len(physical),complete_scope_count=len(complete),
            prepared_scope_used_is_original_run003_not_new_run004_preflight=True,
            run004_controller_or_whole_preflight_or_Native_two_boundaries_qualified=False,
            actual_worker_or_engine_invoked=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"MANIFEST32_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","actual_manifest_pin","actual_capsule_pin","source_pairs",
        "compact_wire_bytes","predicted_Native_cost_including_decoder5","original600_cost_accepted","fresh_inputs","final_fresh_hashes",
        "CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
