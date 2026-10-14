"""Actual immutable run003 review with CODE10; no replay or retry grant."""
import ctypes
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
SELF="tools/p09/qualify_failed_run003_review_r369.py"
OUTPUT="implementation/p09/evidence/p09-361-case160-run003-shared-metadata-stop-review-r843.v1.json"

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
    import review_failed_run003_v1 as review
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"RUN003_REVIEW_REFUSE_OVERWRITE")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    result=dict(state="FAILED_RUN003_REVIEW_NOT_ACCEPTED",accepted_count_delta=0,GO_authorized=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        for path in (SELF,review.SELF,review.TEST):q.pin(path)
        tested=unittest.TextTestRunner(stream=io.StringIO()).run(
            unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests.test_review_failed_run003_v1"))
        a.require(tested.wasSuccessful() and tested.testsRun==10 and not tested.skipped,"ALL_REVIEW_CODE10")
        row=a.read_exact(q,review.ROOT);result=review.review(row,a)
        q.finish();g.check(force=True)
        result.update(contracts=dict(run=10,errors=0,failures=0,skipped=0),
            source_pins=[q.snapshots[x] for x in (SELF,review.SELF,review.TEST)],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,
            actual_product_or_Native_reexecuted=False,P09_gate="OPEN")
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            result["error_code"]=error.args[0]
    finally:
        g.close();result.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"RUN003_REVIEW_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(result,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:result.get(key) for key in ("state","contracts","fresh_inputs","final_fresh_hashes",
        "CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if result["state"]==review.STATE else 1
if __name__=="__main__":raise SystemExit(main())
