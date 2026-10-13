"""One current graph, full actual manifest admission and window code; no GO."""
import ctypes
import json
from pathlib import Path
import re
import sys
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
import successor_runtime_graph_v1 as factory
import runtime_successor_binding_v1 as successor
import runtime_successor_worker_capsule_v1 as capsule
import runtime_successor_manifest_v1 as manifest
import successor_strict_window_v1 as window

SELF="tools/p09/qualify_successor_full_graph_r342.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual159_Native_or_worker_or_product_executed=False,actual159_GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (SELF,factory.SELF,successor.SELF,successor.TEST,capsule.SELF,capsule.TEST,
            manifest.SELF,manifest.TEST,window.SELF,window.TEST,"tools/p09/flat_current_queue_envelope_runtime_v25.py",
            "tools/p09/strict_product_window_connection_v1.py","tools/p09/tests/test_strict_product_window_connection_v1.py")]
        import flat_current_queue_envelope_runtime_v25 as old
        g.check()
        suite=unittest.TestSuite()
        for pattern in ("test_successor_strict_window_v1.py","test_strict_product_window_connection_v1.py"):
            suite.addTests(unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern=pattern))
        tests=unittest.TestResult();suite.run(tests);g.check()
        out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=21,errors=0,failures=0,skipped=0),"ALL_WINDOW21_ORIGINAL_AND_SUCCESSOR")
        for pin in old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS:a.exact(q.pin(pin["path"]),pin,"EXACT_ORIGINAL_GRAPH_AND_FAILURE_SOURCES")
        graph=factory.build(q,old,successor,capsule)
        pin=q.pin(manifest.PATH)
        live,inherited,proof=manifest.load(q,pin,a,old_manifest=old.manifest,new_module=graph.binding_module,
            successor=successor,failed003=old.failed_role,failed004=old.failed004_role)
        a.require(type(live) is type(graph.binding),"ONE_MANIFEST_PARENT_WORKER_ORACLE_BINDING_TYPE")
        a.exact(live.descriptors(),graph.binding.descriptors(),"ALL_TWENTY_CAPSULE_MANIFEST_PAIRS_EQUAL")
        a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"ACTUAL_MANIFEST_CAPSULE_PIN_EQUAL")
        projected,_=live.project(inherited,g.check)
        a.exact(live.representation(projected)["prior_failure_lineage"],graph.lineage,"FULL_PRIOR_FAILURE_ROLES_NOT_PRODUCT")
        check,window_proof=window.connect(old.prior.WINDOW_LINK.check_evidence)
        a.require(callable(check) and window_proof["original_fifteen_second_checks_retained"],"WHOLE_ORIGINAL_WINDOW159_ORACLE_CONNECTED")
        # Prior158 manifest admission above keeps its separate constructor graph.
        # The original engine template requires an explicit current config.
        old.base.configure(159)
        a.require(old.base.CONFIG.index==159 and old.base.CONFIG.before==152,"EXACT_CURRENT159_ENGINE_CONFIG")
        engine,_=old.prior.template();connected,state=graph.parent.connect_engine(engine,live)
        a.require(connected.worker is engine.worker and state.attempts==0 and state.frames==[],"ORIGINAL_ENGINE_NOT_EXECUTED")
        q.finish();g.check(force=True)
        out.update(state="PASS_SUCCESSOR159_FULL_MANIFEST_SHARED_GRAPH_AND_WINDOW_CODE21_NOT_CURRENT_CONTROLLER_NATIVE_OR_GO",
            source_pins=pins+old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS,source_pair_count=20,
            manifest_admission_proof=proof,window_projection_proof=window_proof,
            private_core_ast_proofs=graph.ast_proof,exact_shared_binding_type=True,
            actual_engine_calls=0,actual_frames=0,actual_worker_dispatches=0,
            current159_complete_controller_scope_and_cost_qualified=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
