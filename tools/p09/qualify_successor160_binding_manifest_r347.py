"""Actual160 manifest and24pairs, original guard; no frame, worker or GO."""
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
import runtime_successor_binding_v2 as successor
import runtime_successor_manifest_v2 as manifest

SELF="tools/p09/qualify_successor160_binding_manifest_r347.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        actual160_product_or_Native_executed=False,actual160_GO_authorized=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (successor.SELF,successor.TEST,manifest.SELF,SELF)]
        import flat_current_queue_envelope_runtime_v27 as controller
        m=controller.M;old=m.old;m.base.configure(159);g.check()
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),pattern="test_runtime_successor_binding_v2.py")
        result=unittest.TestResult();suite.run(result);g.check()
        out["contracts"]=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        a.exact(out["contracts"],dict(run=10,errors=0,failures=0,skipped=0),"SUCCESSOR160_BINDING_CODE10")
        core=[p for p in old.NAMESPACE_SOURCE_PINS if p["path"] in (
            "tools/p09/runtime_record_envelope_v1.py","tools/p09/runtime_record_envelope_v2.py",
            "tools/p09/runtime_envelope_source_projection_v1.py","tools/p09/runtime_envelope_scope_binding_v1.py")]
        for p in core:a.exact(q.pin(p["path"]),p,"EXACT_FOUR_ORIGINAL160_CORE_SOURCES")
        namespaces,proof=old.namespace_bundle.load(a.c.ROOT,core,{"current_stored_runtime_scope":old.base.scope})
        module=namespaces.runtime_envelope_scope_binding_v1
        context=successor.admission(q,a,old.failed_role,old.failed004_role)
        successor.connect(module,context,old.failed_role,old.failed004_role)
        pin=q.pin(manifest.PATH)
        bound,inherited,admission=manifest.load(q,pin,a,controller=m,new_module=module,successor=successor)
        projection,_=bound.project(inherited,g.check)
        representation=bound.representation(projection)
        a.exact(representation["successor_context"],context,"CURRENT160_CONTEXT_NOT159_COPY")
        a.exact(representation["historical_case159_failure_lineage"],context["historical_case159_failure_lineage"],"ORIGINAL159_HISTORY_FIELDS")
        required=old.base.scope.extend(inherited,q.snapshots)
        budget=bound.runtime_budget(required,167,old.prior.DIRECT.runtime_budget,g.check)
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL160_BINDING_CODE10_MANIFEST24_OLD159_FULL_ADMISSION_NOT_CURRENT_CONTROLLER_OR_GO",
            source_pins=pins+core,new_code_pins=pins[:3],manifest_pin=pin,source_pairs=24,
            actual160_context=context,manifest_admission=admission,private_core_ast_proofs=proof,
            baseline_inherited_scope_budget=budget,actual_future_manifest_placeholder_used=False,
            current160_controller_DATA_import_inventory_whole_preflight_qualified=False,
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
