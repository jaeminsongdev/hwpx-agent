"""Current159 context + original whole158 oracle, no product/Native replay."""
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
import isolated_predecessor158_prepare_v1 as helper
import current_envelope_acceptance_prepare_v1 as adapter
import runtime_successor_binding_v1 as successor

SELF="tools/p09/qualify_isolated_predecessor158_r343.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual159_product_or_Native_executed=False,actual159_GO_authorized=False,
        prior158_product_or_Native_reexecuted=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (helper.SELF,helper.TEST,SELF,adapter.SELF,successor.SELF,
            "tools/p09/flat_current_queue_envelope_runtime_v25.py")]
        import flat_current_queue_envelope_runtime_v25 as old
        old.base.configure(159);current=old.base.CONFIG;g.check()
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_isolated_predecessor158_prepare_v1.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=9,errors=0,failures=0,skipped=0),"ISOLATED_PREDECESSOR_CODE9")
        # Tests may configure the identical immutable step; bind the actual
        # post-test object, not an obsolete object identity from before tests.
        current=old.base.CONFIG
        row,listing,evidence,proof=helper.prepare(q,old,adapter,successor)
        a.require(old.base.CONFIG is current and current.index==159 and current.before==152,"DEFAULT_CURRENT159_CONFIG_RETAINED")
        q.finish();g.check(force=True)
        out.update(state="PASS_CURRENT159_ISOLATED_PRIOR158_WHOLE_ORACLE_CODE9_NOT_CURRENT159_CONTROLLER_OR_GO",
            source_pins=pins,new_code_pins=pins[:2],prior_runtime_pin=successor.ROOT,authority_pin=successor.AUTHORITY,
            original_current_CONFIG_mutated=False,oracle_proof=proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-10:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
