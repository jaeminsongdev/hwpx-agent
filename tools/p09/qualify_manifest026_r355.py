"""Actual manifest026 full admission; no current controller or worker GO."""
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
import runtime_failed160_partial_projection_v2 as role
import runtime_successor_manifest_v4 as manifest
import runtime_successor_binding_v2 as successor
import runtime_successor_worker_capsule_v2 as capsule
import successor_runtime_graph_v2 as factory

SELF="tools/p09/qualify_manifest026_r355.py"
TEST="tools/p09/tests/test_runtime_successor_manifest_v4.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        current160_worker_capsule_or_controller_qualified=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (manifest.SELF,TEST,SELF,role.SELF,role.TEST,
            successor.SELF,successor.TEST,pressure.SELF,pressure.TEST)]
        tests=unittest.TestResult()
        unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_runtime_successor_manifest_v4.py").run(tests)
        g.check();out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=5,errors=0,failures=0,skipped=0),"MANIFEST026_CODE5")
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;m.base.configure(159);old=m.old
        graph=factory.build(q,old,successor,capsule)
        admitted=role.admission(q,a)
        connected=role.connect(graph.binding_module.source,graph.binding_module,admitted)
        pin=q.pin(manifest.PATH)
        live,scope,proof=manifest.load(q,pin,a,controller=m,new_module=graph.binding_module,successor=successor)
        projection,union=live.project(scope,q.checkpoint)
        represented=live.representation(projection)
        a.exact(represented["same_case_failed160_partial_receipt_provenance"],admitted,
            "ACTUAL_PARTIAL_FAILURE_PROVENANCE_EXPOSED_NOT_ACCEPTED_PRODUCT")
        a.require(len(live.descriptors())==25,"ACTUAL25_NOT_OLD24_CAPSULE")
        for p in old.NAMESPACE_SOURCE_PINS:a.exact(q.pin(p["path"]),p,"ALL_ORIGINAL_CORE_CODE")
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL160_MANIFEST026_CODE5_FULL_ADMISSION_NOT_RUN002_CAPSULE_CONTROLLER_OR_GO",
            source_pins=pins+old.NAMESPACE_SOURCE_PINS,manifest_pin=pin,source_pairs=25,
            partial_failure_admission=admitted,partial_role_connection=connected,
            original_manifest_admission=proof,scope_union=union,
            semantic_input_count=len(projection.semantic_pins),physical_input_count=len(projection.physical_pins),
            actual_original_failure_bytes_preserved=True,old24_capsule_not_relabelled_as25=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
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
                if s.get("parent_cpu_machine_percent") is not None),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
