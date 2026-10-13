"""Current160 private159 whole oracle under original warning75, no replay."""
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
import isolated_predecessor159_prepare_v1 as helper
import current_successor_acceptance_prepare_v1 as adapter
import runtime_successor_binding_v2 as successor

SELF="tools/p09/qualify_isolated_prior159_r349.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        current160_product_or_Native_executed=False,prior159_replayed=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (helper.SELF,helper.TEST,SELF,adapter.SELF,successor.SELF,pressure.SELF,pressure.TEST)]
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;m.base.configure(160);current=m.base.CONFIG;g.check()
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_isolated_predecessor159_prepare_v1.py")
        result=unittest.TestResult();suite.run(result);g.check()
        out["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        if result.errors or result.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in result.errors+result.failures]
        a.exact(out["contracts"],dict(run=9,errors=0,failures=0,skipped=0),"ISOLATED_PRIOR159_CODE9")
        row,listing,evidence,proof=helper.prepare(q,controller,adapter,successor)
        a.require(m.base.CONFIG is current and current.index==160,"DEFAULT_CURRENT160_CONFIG_OBJECT_PRESERVED")
        q.finish();g.check(force=True)
        out.update(state="PASS_CURRENT160_ISOLATED_PRIOR159_WHOLE_ORACLE_CODE9_NOT_CURRENT160_CONTROLLER_OR_GO",
            source_pins=pins,new_code_pins=pins[:2],prior_runtime_pin=successor.ROOT,authority_pin=successor.AUTHORITY,
            default_current160_CONFIG_mutated=False,oracle_proof=proof,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
