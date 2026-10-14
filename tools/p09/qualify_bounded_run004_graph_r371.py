"""Actual32 single bounded-reader graph and unchanged namespace connection."""
import ctypes
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
SELF="tools/p09/qualify_bounded_run004_graph_r371.py"
OUTPUT="implementation/p09/evidence/p09-361-run004-bounded32-code5-r851.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    p=k.GetCurrentProcess()
    if not(k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parent/"tests"))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import successor_bounded_graph_bootstrap_v6 as bootstrap
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"BOUNDED32_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_BOUNDED32_NOT_ACCEPTED",accepted_count_delta=0,
        actual_engine_worker_or_Native_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        source_paths=(SELF,bootstrap.SELF,bootstrap.TEST,bootstrap.manifest.SELF,bootstrap.manifest.TEST,
            bootstrap.factory.SELF,bootstrap.factory.TEST,bootstrap.extras.SELF,bootstrap.extras.TEST)
        for path in source_paths:q.pin(path)
        tests=unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_successor_bounded_graph_bootstrap_v6"))
        a.require(tests.wasSuccessful() and tests.testsRun==5 and not tests.skipped,"ALL_BOUNDED_CODE5")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160)
        graph,proof=bootstrap.load(c.old,q.checkpoint)
        a.require(proof["bounded_reader_reads"]==25 and proof["bounded_reader_bytes"]<=262144
            and proof["historical_runtime_or_review_body_files_read_by_this_reader"]==0,"ACTUAL_ONE_BOUNDED25_READER")
        for pin in proof["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"ACTUAL_BOUNDED_SOURCE_BYTES_FINAL_CHECKED")
        a.require(len(graph.binding.descriptors())==32 and graph.worker.TASK=="case160-current-r004-tests",
            "ACTUAL_EXACT32_AND_RUN004_TASK")
        a.exact(dict(graph.binding.manifest_pin),bootstrap.MANIFEST,"REAL_MANIFEST029")
        a.require(graph.parent.access.source is graph.binding_module and
            graph.parent.original.frames.binding_module is graph.binding_module and
            graph.worker.source is graph.binding_module and graph.worker.raw_policy.source is graph.binding_module and
            graph.full_oracle.binding_module is graph.binding_module,"ONE_COMPLETE_SOURCE_GRAPH_NOT_SUBSET")
        q.finish();g.check(force=True)
        out.update(state="PASS_RUN004_ACTUAL32_ONE_BOUNDED25_READER_CODE5_NOT_CONTROLLER_NATIVE_OR_GO",
            contracts=dict(run=5,errors=0,failures=0,skipped=0),actual_bounded_graph=proof,
            manifest_pin=bootstrap.MANIFEST,capsule_pin=bootstrap.CAPSULE,source_pairs=32,
            source_pins=[q.snapshots[path] for path in source_paths],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original64_reads_262144_bytes_limits_retained=True,whole_parent_frame_worker_oracle_same_module=True,
            original_full_parent_admission_and_actual_two_boundaries_still_required=True,
            run004_whole_controller_preflight_or_independent_product_oracle_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"BOUNDED32_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","source_pairs","fresh_inputs","final_fresh_hashes","CPU_max",
        "RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
