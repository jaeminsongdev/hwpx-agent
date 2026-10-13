"""Fourteen new slot contracts; reuse frozen CODE24, no full/product run."""
import ctypes
import json
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
_k=ctypes.WinDLL("kernel32",use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct

SELF="tools/p09/qualify_case158_preflight_slot_r334.py"


def main():
    g=distinct.guard_type(a.Guard)();q=None;out=dict(state="FAILED_NOT_ACCEPTED",
        actual_product_or_Native_executed=False,accepted_count_delta=0,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        import run_case158_preflight_slot_r334 as m
        pins=[q.pin(p) for p in (m.SELF,m.TEST,m.slots.SELF,m.slots.TEST)]
        q.pin(SELF);a.exact(q.pin(m.slots.SELF),m.SLOT_PIN,"EXACT_RAW_SLOT_BOOTSTRAP")
        old=q.json(m.m.QUAL)
        a.fields(old,dict(state=m.m.QUAL_STATE,contracts=dict(run=24,errors=0,failures=0,skipped=0),
            cleanup_confirmed=True,actual_product_or_Native_executed=False),"PRESERVED_CURRENT_CODE24")
        for p in old["source_pins"]:a.exact(q.pin(p["path"]),p,"ALL_CURRENT_CODE24_SOURCE_BYTES")
        suite=unittest.TestSuite()
        for pattern in ("test_preflight_output_slot_v1.py","test_case158_preflight_slot_r334.py"):
            suite.addTests(unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern=pattern))
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=14,errors=0,failures=0,skipped=0),"ALL_SLOT_CODE14")
        q.finish();g.check(force=True)
        out.update(state=m.QUAL_STATE,new_code_pins=pins,
            source_pins=[q.snapshots[SELF]]+old["source_pins"],old_CODE24_reexecuted=False,
            whole_original_preflight_code_retained=True,old_failed_outputs_preserved=True,
            full_current_slot_preflight_or_product_qualified=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_SLOT_QUAL_FAILURE"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
