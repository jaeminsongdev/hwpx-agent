"""Capsule8 and actual25-pair manifest admission, no worker dispatch or GO."""
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
import runtime_successor_worker_capsule_v3 as capsule
import successor_runtime_graph_v2 as factory

SELF="tools/p09/qualify_run002_capsule_r356.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        actual_worker_dispatches=0,actual_encoded_file_published=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(capsule.SELF,capsule.TEST,capsule.original.SELF,capsule.original.TEST,SELF,
            "tools/p09/tests/test_runtime_successor_worker_capsule_v2.py",role.SELF,role.TEST,
            manifest.SELF,successor.SELF,pressure.SELF,pressure.TEST)
        pins=[q.pin(path) for path in paths]
        tests=unittest.TestResult()
        unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_runtime_successor_worker_capsule_v3.py").run(tests)
        g.check();out["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:out["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(out["contracts"],dict(run=8,errors=0,failures=0,skipped=0),"CAPSULE_ORIGINAL6_RUN002_NEW2")
        code=q.json("implementation/p09/evidence/p09-361-case160-manifest026-full-admission-r791.v1.json")
        a.fields(code,dict(state="PASS_ACTUAL160_MANIFEST026_CODE5_FULL_ADMISSION_NOT_RUN002_CAPSULE_CONTROLLER_OR_GO",
            contracts=dict(run=5,errors=0,failures=0,skipped=0),source_pairs=25,cleanup_confirmed=True),
            "QUALIFIED_REAL_MANIFEST026")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_FULL_MANIFEST_SOURCES")
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;m.base.configure(159);old=m.old
        graph=factory.build(q,old,successor,capsule.original)
        admitted=role.admission(q,a);role.connect(graph.binding_module.source,graph.binding_module,admitted)
        mf=q.pin(manifest.PATH)
        bound,scope,proof=manifest.load(q,mf,a,controller=m,new_module=graph.binding_module,successor=successor)
        api,connection=capsule.connect(graph.core.runtime_envelope_worker_connection_v1,
            graph.binding_module,successor.AUTHORITY,successor.ROOT,successor)
        encoded,transport=api.encode(bound,successor.AUTHORITY,successor.ROOT,q.checkpoint)
        decoded,decode=api.decode(encoded,transport,q.checkpoint)
        a.require(type(decoded) is type(bound) and len(decoded.descriptors())==25,"EXACT_SAME_PRIVATE_TYPE25")
        a.exact(decoded.descriptors(),bound.descriptors(),"ALL_ACTUAL25_PAIRS_TRANSPORTED")
        a.exact(dict(decoded.manifest_pin),mf,"EXACT_ACTUAL_MANIFEST026_TRANSPORTED")
        a.require(api.connect_worker.__code__ is graph.core.runtime_envelope_worker_connection_v1.connect_worker.__code__,
            "ENTIRE_ORIGINAL_WORKER_DISPATCH_CODE")
        q.finish();g.check(force=True)
        out.update(state="PASS_CURRENT160_RUN002_CAPSULE_CODE8_ACTUAL25_MANIFEST_TRANSPORT_NOT_DISPATCH_CONTROLLER_OR_GO",
            source_pins=pins+old.NAMESPACE_SOURCE_PINS,new_code_pins=pins[:2],manifest_pin=mf,
            source_pairs=25,task=capsule.TASK,connection_proof=connection,manifest_admission=proof,
            memory_transport_pin=transport,decode_proof=decode,encoded_capsule_ascii=encoded.decode("ascii"),
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
