"""Actual complete parent admission and bounded32 graph comparison; not GO."""
import ctypes
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import unittest
SELF="tools/p09/qualify_parent32_binding_r371.py"
OUTPUT="implementation/p09/evidence/p09-361-run004-parent32-binding-code9-r852.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    p=k.GetCurrentProcess()
    if not(k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]));sys.path.insert(0,str(Path(__file__).resolve().parent/"tests"))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import successor_current_binding_v6 as current
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"PARENT32_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_PARENT32_BINDING_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,current.SELF,current.TEST,current.bootstrap.SELF,current.bootstrap.TEST)
        for path in paths:q.pin(path)
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests."+n) for n in
            ("test_successor_current_binding_v6","test_successor_bounded_graph_bootstrap_v6"))
        tested=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(tested.wasSuccessful() and tested.testsRun==9 and not tested.skipped,"ALL_PARENT32_CODE9")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160)
        scope,rust,graph,live,proof=current.bind(q,c)
        enumerator="tools/p09/current_issuer_build_inputs.py"
        text=q.text(enumerator);a.exact(q.snapshots[enumerator],scope[enumerator],"ACTUAL_ORIGINAL_RUST_ENUMERATOR")
        inventory=a.native.definitions(text,("rust_inputs",),dict(os=os,Path=Path,require=a.require))
        opener=a.locks.OpenPacer(q.checkpoint,rate=20)
        a.require(frozenset(inventory.rust_inputs(a.c.ROOT,opener.reserve))==rust,"ALL_CURRENT_RUST787_NAMES")
        complete=c.M.base.scope.extend(scope,q.snapshots);projection,_=live.project(complete,q.checkpoint)
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        original=c.old.prior.DIRECT.runtime_budget(physical,opener.opens)
        predicted=original["predicted_runtime_combined_seconds"]+5.0
        budget=None;cost_error=None
        try:budget=live.runtime_budget(complete,opener.opens,c.old.prior.DIRECT.runtime_budget,q.checkpoint)
        except ValueError as error:
            a.require(error.args and error.args[0]=="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5","ONLY_ORIGINAL600_COST_REJECTION")
            cost_error=error.args[0]
        q.finish();g.check(force=True)
        out.update(state="PASS_RUN004_FULL_PARENT32_BINDING_CODE9_SAME_BOUNDED_GRAPH_NOT_CONTROLLER_OR_GO",
            contracts=dict(run=9,errors=0,failures=0,skipped=0),source_pairs=32,rust_source_count=len(rust),
            current_Rust_inventory_requests=opener.opens,complete_scope_count=len(complete),physical_scope_count=len(physical),
            full_parent_and_bounded_worker_proof=proof,predicted_Native_cost_including_decoder5=predicted,
            original600_cost_accepted=budget is not None,budget=budget,budget_error=cost_error,
            source_pins=[q.snapshots[path] for path in paths],all_qualifier_source_pins=list(q.snapshots.values()),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            run004_controller_or_whole_preflight_or_independent_current160_oracle_qualified=False,
            new_actual_two_Native_boundaries_executed=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"PARENT32_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","source_pairs","rust_source_count","predicted_Native_cost_including_decoder5",
        "original600_cost_accepted","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
