"""Stored34 manifest/capsule through full fresh parent admission; not GO."""
import ctypes
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
SELF="tools/p09/prepare_run004_manifest34_r372.py"
OUTPUT="implementation/p09/evidence/p09-361-run004-manifest34-code11-r855.v1.json"
CAPSULE="implementation/p09/evidence/p09-361-case160-worker-policy-capsule007.compact.v1.json"
BASE32=dict(path="implementation/p09/evidence/p09-361-case160-source-manifest029.v7.json",bytes=742,
    sha256="6e2998cfc5cd7ebb690f1c46f61c6a34bcaa9c211a41d1638521ab23d608fde6")

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    p=k.GetCurrentProcess()
    if not(k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parent/"tests"))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import runtime_successor_manifest_v8 as manifest
    import successor_runtime_graph_v7 as factory
    import prepare_run004_manifest_capsule_r370 as publisher
    import prepared_checkpoint_transport_v1 as transport
    import prepared_scope_handoff_v1 as handoff
    import prepared_input_checkpoint_v1 as prepared
    import preparation_terminal_progress_v1 as progress
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"MANIFEST34_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_MANIFEST34_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        GO_authorized=False,files_created=[],P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,manifest.SELF,manifest.TEST,factory.SELF,factory.TEST,publisher.SELF)
        for path in paths:q.pin(path)
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests."+n) for n in
            ("test_runtime_successor_manifest_v8","test_successor_runtime_graph_v7"))
        tested=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(tested.wasSuccessful() and tested.testsRun==11 and not tested.skipped,"ALL_MANIFEST34_CODE11")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160);base,bootstrap=c.bootstrap.load(c.old,q.checkpoint)
        for p in bootstrap["reader_source_pins"]:a.exact(q.pin(p["path"]),p,"REAL_BASE29_SOURCE")
        prepared_transport=q.json("implementation/p09/evidence/p09-361-prepared-checkpoint-transport-producer-r839.v1.json")
        a.fields(prepared_transport,dict(state="PASS_EXCLUSIVE_PREPARED_CHECKPOINT_TRANSPORT_NOT_RUNTIME_OR_GO",
            cleanup_confirmed=True,Native_or_product_executed=False,GO_authorized=False),"ACTUAL_ORIGINAL_PREPARED_TRANSPORT")
        listing=a.read_exact(q,a.scope.LIST_PIN);rust=handoff.rust_inputs(a.scope.listing_inputs(listing))
        s=c._env["current_binding"].successor
        scope,_,_=transport.load(q,prepared_transport["original_pin"],prepared_transport["physical_pin"],base.binding,
            expected_context=dict(index=160,before=153,physical_product_run=3),
            expected_current_pins=dict(data_pin=q.pin(c.DATA),preflight_pin=q.pin(c.PREFLIGHT),authority_pin=s.AUTHORITY,prior_runtime_pin=s.ROOT),
            expected_rust=rust,expected_source_paths=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",prepared.SELF,prepared.TEST,
                progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,distinct.SELF,distinct.TEST)))
        row=dict(schema_version=manifest.SCHEMA,index=160,before=153,physical_product_run=4,
            base_manifest_pin=BASE32,extra_prior_producer_pin=q.pin(manifest.PRODUCER))
        manifest.validate(row,a,BASE32)
        manifest_pin=publisher.write_exclusive(a.c.ROOT,manifest.PATH,publisher.serialize(row));out["files_created"].append(manifest.PATH)
        a.exact(q.fresh_pin(manifest.PATH),manifest_pin,"ACTUAL_NEW_MANIFEST030")
        bound,scope,proof=manifest.load(q,manifest_pin,a,base_graph=base,base29_pin=c.MANIFEST,base32_pin=BASE32,prepared_scope=scope)
        graph,graph_proof=factory.connect(base,bound)
        wire,wire_pin=graph.worker.encode(bound,s.AUTHORITY,s.ROOT,q.checkpoint)
        capsule_pin=publisher.write_exclusive(a.c.ROOT,CAPSULE,wire);out["files_created"].append(CAPSULE)
        a.exact(q.fresh_pin(CAPSULE),capsule_pin,"REAL_COMPACT34_CAPSULE")
        restored,decoder=graph.worker.decode(wire,wire_pin,q.checkpoint)
        a.exact(restored.descriptors(),bound.descriptors(),"ALL34_ACTUAL_DESCRIPTORS_RESTORED")
        a.exact(dict(restored.manifest_pin),manifest_pin,"CAPSULE34_ACTUAL_MANIFEST030")
        complete=c.M.base.scope.extend(scope,q.snapshots);projection,_=bound.project(complete,q.checkpoint)
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        original=c.old.prior.DIRECT.runtime_budget(physical,167);predicted=original["predicted_runtime_combined_seconds"]+5.0
        budget=None;cost_error=None
        try:budget=bound.runtime_budget(complete,167,c.old.prior.DIRECT.runtime_budget,q.checkpoint)
        except ValueError as error:
            a.require(error.args and error.args[0]=="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5","ONLY_ORIGINAL600_COST_REJECTION")
            cost_error=error.args[0]
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL_RUN004_MANIFEST34_CAPSULE_CODE11_NOT_CONTROLLER_NATIVE_OR_GO",
            contracts=dict(run=11,errors=0,failures=0,skipped=0),actual_manifest_pin=manifest_pin,actual_capsule_pin=capsule_pin,
            source_pairs=34,compact_wire_bytes=len(wire),original_wire_limit=16384,worker_task=graph.worker.TASK,
            all_previous32_retained=True,manifest_loader_proof=proof,graph_connection_proof=graph_proof,decoder_proof=decoder,
            predicted_Native_cost_including_decoder5=predicted,original600_cost_accepted=budget is not None,budget=budget,budget_error=cost_error,
            source_pins=[q.snapshots[p] for p in paths],all_qualifier_source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,complete_scope_count=len(complete),physical_scope_count=len(physical),
            new_controller_or_whole_preflight_or_actual_two_boundaries_or_current160_oracle_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"MANIFEST34_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","actual_manifest_pin","actual_capsule_pin","source_pairs","compact_wire_bytes",
        "predicted_Native_cost_including_decoder5","original600_cost_accepted","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min",
        "cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
