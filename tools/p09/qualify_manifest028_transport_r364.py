"""Actual26 manifest/capsule adoption with original full admission, no GO."""
import ctypes
import json
from pathlib import Path
import re
import sys
import traceback
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
import runtime_failed160_partial_projection_v2 as partial
import runtime_successor_manifest_v6 as manifest
import runtime_successor_worker_capsule_v5 as capsule
import runtime_successor_binding_v2 as successor
import successor_runtime_graph_v4 as factory

SELF="tools/p09/qualify_manifest028_transport_r364.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        new_current_controller_cost_or_preflight_qualified=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,manifest.SELF,manifest.original.SELF,capsule.SELF,capsule.original.SELF,
            capsule.TEST,capsule.original.TEST,"tools/p09/tests/test_runtime_successor_worker_capsule_v2.py",
            partial.SELF,partial.TEST,successor.SELF,pressure.SELF,pressure.TEST)
        pins=[q.pin(path) for path in paths]
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;m.base.configure(159);old=m.old
        graph=factory.build(q,old,successor,capsule.original,partial)
        import unittest
        suite=unittest.TestSuite([unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern=name)
            for name in ("test_runtime_successor_worker_capsule_v4.py","test_runtime_successor_worker_capsule_v5.py")])
        tests=unittest.TestResult();suite.run(tests);g.check()
        contracts=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        a.exact(contracts,dict(run=18,errors=0,failures=0,skipped=0),"ORIGINAL_AND_RUN003_CAPSULE18")
        mf=q.pin(manifest.PATH)
        live,scope,proof=manifest.load(q,mf,a,controller=m,new_module=graph.binding_module,successor=successor)
        projected,union=live.project(scope,q.checkpoint)
        represented=live.representation(projected)
        a.exact(represented["same_case_failed160_partial_receipt_provenance"],graph.partial_admission,
            "PARTIAL_FAILURE_RETAINED_NOT_PRODUCT_PASS")
        api,connection=capsule.connect(graph.core.runtime_envelope_worker_connection_v1,graph.binding_module,
            successor.AUTHORITY,successor.ROOT,successor)
        encoded,transport=api.encode(live,successor.AUTHORITY,successor.ROOT,q.checkpoint)
        decoded,decoded_proof=api.decode(encoded,transport,q.checkpoint)
        a.require(type(decoded) is type(live) and len(decoded.descriptors())==29,"SAME_TYPED26_BINDING")
        a.exact(decoded.descriptors(),live.descriptors(),"EVERY_ACTUAL26_PAIR_TRANSPORTED")
        a.exact(dict(decoded.manifest_pin),mf,"REAL_MANIFEST027_TRANSPORTED")
        for pin in old.NAMESPACE_SOURCE_PINS:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_PRIVATE_CORE_SOURCES")
        q.finish();g.check(force=True)
        a.exact(len(q.snapshots),q.final_fresh_hashes,"ALL_QUALIFIED_INPUTS_FINAL_FRESH_BEFORE_RESULT")
        out.update(state="PASS_ACTUAL160_MANIFEST028_AND29_RUN003_TRANSPORT_NOT_CONTROLLER_COST_PREFLIGHT_OR_GO",
            contracts=contracts,source_pins=pins+old.NAMESPACE_SOURCE_PINS,manifest_pin=mf,source_pairs=29,
            original_manifest_admission=proof,scope_union=union,capsule_connection=connection,
            memory_transport_pin=transport,decode_proof=decoded_proof,encoded_capsule_ascii=encoded.decode("ascii"),
            actual_old_capsule002_not_relabelled=True,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
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
