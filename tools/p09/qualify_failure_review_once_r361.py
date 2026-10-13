"""Code14 and the original real failed160 review; no controller or GO."""
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
import reviewed_case160_attempt_v1 as original
import same_reader_failure_review_once_v1 as helper
SELF="tools/p09/qualify_failure_review_once_r361.py"
REVIEW=dict(path=original.REVIEW,bytes=1433,sha256="d36c1b159359c58f5caa0fe03da383f9b95c51047e87c63005ef6fc5ebe159af")

def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        new_controller_or_GO_qualified=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (SELF,helper.SELF,helper.TEST,original.SELF,pressure.SELF,pressure.TEST)]
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_same_reader_failure_review_once_v1.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        contracts=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        a.exact(contracts,dict(run=14,errors=0,failures=0,skipped=0),"FAILURE_REVIEW_METADATA_CODE14")
        checked,counts=helper.connect(original.reviewed_failure,expected_runtime_pin=original.STOPPED,
            expected_review_pin=REVIEW)
        first=checked(q,a);after=q.bytes_read
        second=checked(q,a)
        a.exact(first,second,"SAME_COMPLETE_REAL_FAILED160_REVIEW_DECLARATION")
        a.exact(q.bytes_read,after,"NO_SECOND_FAILURE_FILE_READ_OR_JSON_ROW_CACHE")
        a.exact(counts,dict(original_complete_reviews=1,duplicate_declarations_avoided=1),
            "ORIGINAL_FIRST_FULL_REVIEW_AND_ONE_METADATA_REUSE")
        q.finish();g.check(force=True)
        out.update(state="PASS_SAME_READER_FAILED160_REVIEW_CODE14_AND_REAL_FIRST_REVIEW_NOT_CONTROLLER_NATIVE_OR_GO",
            contracts=contracts,source_pins=pins,failed_runtime_pin=original.STOPPED,review_pin=REVIEW,
            declaration=first,review_counts=dict(counts),fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,file_bytes_parsed_runtime_row_or_hash_cache=False,
            actual_controller_connection_or_runtime_savings_measured=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-10:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
