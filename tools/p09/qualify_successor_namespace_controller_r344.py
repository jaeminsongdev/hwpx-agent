"""Actual159 controller code and original private engine/worker; no GO."""
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

SELF="tools/p09/qualify_successor_namespace_controller_r344.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual159_product_or_Native_executed=False,actual159_GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M
        m.base.configure(159);g.check()
        paths=[m.SELF,m.TEST,m.bootstrap.SELF,SELF,m.current_binding.SELF,m.current_binding.TEST,
               m.window.SELF,m.window.TEST,m.old.SELF,m.old.TEST]+[p["path"] for p in m.old.TIMING_PINS]
        pins=[q.pin(path) for path in paths]
        for pin in controller.RAW_PINS+[controller.RAW_TEST_PIN]:a.exact(q.pin(pin["path"]),pin,"ALL_RAW_NAMESPACE_CODE_SOURCES")
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_flat_current_queue_envelope_runtime_v27.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=14,errors=0,failures=0,skipped=0),"CURRENT159_CONTROLLER_CODE14")
        graph=m.graph_value()
        a.require(len(graph.binding.descriptors())==20 and graph.binding.next_case==159,"ACTUAL159_BOUNDED_GRAPH")
        for pin in m.old.NAMESPACE_SOURCE_PINS:a.exact(q.pin(pin["path"]),pin,"CURRENT_EXACT_PRIVATE_CORE_SOURCES")
        a.exact(q.pin(m.MANIFEST["path"]),m.MANIFEST,"ACTUAL_CURRENT159_MANIFEST")
        a.exact(q.pin(m.CAPSULE["path"]),m.CAPSULE,"ACTUAL_CURRENT159_CAPSULE")
        a.require(all(s.attempts==0 and s.frames==[] for s in m.PARENT_STATES),"ZERO_ENGINE_OR_FRAME_EXECUTION")
        q.finish();g.check(force=True)
        out.update(state=m.QUAL_STATE,new_code_pins=pins[:2],source_pins=pins+m.old.NAMESPACE_SOURCE_PINS+controller.RAW_PINS+[controller.RAW_TEST_PIN],
            original_namespace_AST_proofs=controller.SOURCE_PROOFS,
            original_actual_helper_ceiling=64,sys_modules_hidden_or_removed=False,
            source_pair_count=20,actual_engine_calls=0,actual_frames=0,actual_worker_dispatches=0,
            original_same_private_binding_type_connected=True,whole_current159_controller_DATA_scope_preflight_qualified=False,
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
