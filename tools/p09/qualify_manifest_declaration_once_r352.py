"""New declaration12 plus unchanged original source-admission7 tests only."""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback
import unittest

k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
p=k.GetCurrentProcess()
if not (k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import terminal_metadata_pressure_v1 as pressure
import same_reader_manifest_declaration_once_v1 as helper

SELF="tools/p09/qualify_manifest_declaration_once_r352.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_or_queue_executed=False,current160_full_binding_connected=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (helper.SELF,helper.TEST,SELF,
            "tools/p09/same_reader_source_admission_once_v1.py",
            "tools/p09/tests/test_same_reader_source_admission_once_v1.py",pressure.SELF,pressure.TEST)]
        suite=unittest.TestSuite()
        for name in ("test_same_reader_manifest_declaration_once_v1.py",
                     "test_same_reader_source_admission_once_v1.py"):
            suite.addTests(unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern=name))
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=19,errors=0,failures=0,skipped=0),"DECLARATION12_ORIGINAL7")
        q.finish();g.check(force=True)
        out.update(state="PASS_MANIFEST_DECLARATION_REUSE_CODE19_NOT_FULL_BINDING_PREFLIGHT_NATIVE_OR_GO",
            source_pins=pins,new_code_pins=pins[:2],new_contracts=12,unchanged_original_contracts=7,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            full_manifest_Native_two_byte_and_final_fresh_checks_not_bypassed=True,
            actual_read_bytes_or_runtime_reduction_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
