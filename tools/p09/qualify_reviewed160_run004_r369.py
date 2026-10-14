"""Original identity tests and one actual run004 adapter, never engine execution."""
import ctypes
import io
import json
from pathlib import Path
import re
import sys
import time
from types import FunctionType
import unittest
SELF="tools/p09/qualify_reviewed160_run004_r369.py"
OUTPUT="implementation/p09/evidence/p09-361-case160-run004-identity-code38-r845.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not(k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import reviewed_case160_attempt_v3 as attempt
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"RUN004_IDENTITY_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_RUN004_IDENTITY_NOT_ACCEPTED",accepted_count_delta=0,
        actual_engine_calls=0,actual_worker_calls=0,Native_or_product_executed=False,GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,attempt.SELF,attempt.TEST,attempt.third.SELF,attempt.third.TEST,
            attempt.original.SELF,attempt.original.TEST,attempt.original.original.SELF,attempt.original.original.TEST)
        for path in paths:q.pin(path)
        names=("test_reviewed_case160_attempt_v1","test_reviewed_case160_attempt_v2",
            "test_reviewed_case160_attempt_v3","test_review_failed_run003_v1")
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests."+n) for n in names)
        tested=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(tested.wasSuccessful() and tested.testsRun==38 and not tested.skipped,"ALL_ORIGINAL_AND_NEW_CODE38")
        admission=attempt.reviewed_failure(q,a)
        a.require(not(a.c.ROOT/attempt.ROOT).exists(),"RUN004_ROOT_ABSENT")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160)
        for pin in c.RAW_PINS+[c.RAW_TEST_PIN]:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_TEMPLATE_RAW_SOURCES")
        q.pin(c.SELF);q.pin(c.TEST)
        # Use the unadapted original window, not the run003-adapted facade.
        template,identity,proof=attempt.connect_template(c.old.prior)
        a.require(identity.physical_run(160)==4 and identity.root_path(c.M.base.CONFIG)==attempt.ROOT
            and identity.task(160)==attempt.TASK and identity.public_run(160,4)==1,"ALL_EXACT_RUN004_IDENTITIES")
        engine,engine_proof=template();state=c.old.prior.ATTEMPT_STATES[-1]
        a.require(state.physical_product_run==4 and state.actual_engine_calls==0,"ONE_ACTUAL_RUN004_ADAPTER_NO_ENGINE")
        a.require(engine.worker.__code__ is state.original_worker_code,"ORIGINAL_WORKER_BODY")
        seen=set();pending=[engine.run_owned];adapters=[]
        while pending:
            a.require(len(seen)<16,"BOUNDED_ORIGINAL_WRAPPER_GRAPH")
            fn=pending.pop()
            if id(fn) in seen:continue
            seen.add(id(fn));values=[cell.cell_contents for cell in fn.__closure__ or ()]
            functions=[v for v in values if type(v) is FunctionType]
            matching=[v for v in functions if v.__code__ is state.original_engine_code]
            if any(v is state for v in values):adapters.append((fn,matching))
            pending.extend(functions)
            original=fn.__globals__.get("original")
            if type(original) is FunctionType:pending.append(original)
        a.require(len(adapters)==1 and len(adapters[0][1])==1 and
            adapters[0][0].__globals__ is adapters[0][1][0].__globals__,"ONE_ADAPTER_SAME_ORIGINAL_PRIVATE_GLOBALS")
        q.finish();g.check(force=True)
        out.update(state="PASS_REVIEWED160_RUN004_IDENTITY_CODE38_ACTUAL_SINGLE_TEMPLATE_NOT_NATIVE_OR_GO",
            contracts=dict(run=38,errors=0,failures=0,skipped=0),physical_product_run=4,qualification_run=1,
            failure_admission=admission,template_proof=proof,original_engine_proof=engine_proof,
            source_pins=[q.snapshots[p] for p in paths]+c.RAW_PINS+[c.RAW_TEST_PIN,q.snapshots[c.SELF],q.snapshots[c.TEST]],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            sole_adapter_and_original_engine_share_exact_private_globals=True,run004_controller_or_GO_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"RUN004_IDENTITY_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","contracts","fresh_inputs","final_fresh_hashes","CPU_max",
        "RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
