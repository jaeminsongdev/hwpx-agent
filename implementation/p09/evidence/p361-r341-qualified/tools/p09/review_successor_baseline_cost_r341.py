"""Actual159 manifest/full old admission, original guards; no Native/GO."""
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
import runtime_successor_binding_v1 as successor
import runtime_successor_manifest_v1 as manifest

SELF="tools/p09/review_successor_baseline_cost_r341.py"


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        P09_gate="OPEN",actual159_product_or_Native_executed=False,current159_whole_scope_or_GO_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (manifest.SELF,manifest.TEST,SELF,successor.SELF,successor.TEST,
            "tools/p09/flat_current_queue_envelope_runtime_v25.py")]
        import flat_current_queue_envelope_runtime_v25 as old
        g.check()
        for p in old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS:a.exact(q.pin(p["path"]),p,"EXACT_OLD_PRIVATE_NAMESPACE_SOURCES")
        core=[p for p in old.NAMESPACE_SOURCE_PINS if p["path"] in (
            "tools/p09/runtime_record_envelope_v1.py","tools/p09/runtime_record_envelope_v2.py",
            "tools/p09/runtime_envelope_source_projection_v1.py","tools/p09/runtime_envelope_scope_binding_v1.py")]
        a.exact(len(core),4,"ALL_FOUR_NEW_PRIVATE_CORE_CLASSES")
        ns,core_proof=old.namespace_bundle.load(a.c.ROOT,core,{"current_stored_runtime_scope":old.base.scope})
        module=ns.runtime_envelope_scope_binding_v1
        lineage=successor.admission(q,a,old.failed_role,old.failed004_role)
        successor.connect(module,lineage,old.failed_role,old.failed004_role)
        pin=q.pin(manifest.PATH)
        bound,inherited,proof=manifest.load(q,pin,a,old_manifest=old.manifest,new_module=module,
            successor=successor,failed003=old.failed_role,failed004=old.failed004_role)
        projected,_=bound.project(inherited,g.check)
        a.exact(bound.representation(projected)["prior_failure_lineage"],lineage,"BOTH_FAILED158_ROLES_RETAINED")
        required=old.base.scope.extend(inherited,q.snapshots)
        model=bound.runtime_budget(required,167,old.prior.DIRECT.runtime_budget,g.check)
        a.require(model["predicted_runtime_combined_seconds"]<600 and model["unallocated_margin_seconds"]==60,
            "UNCHANGED600_BASELINE_INHERITED_COST")
        q.finish();g.check(force=True)
        out.update(state="PASS_SUCCESSOR159_BASELINE_INHERITED_COST_NOT_COMPLETE_CURRENT_CONTROLLER_SCOPE_OR_GO",
            new_code_pins=pins[:2],source_pins=pins+core,manifest_pin=pin,source_pair_count=20,
            prior_failure_lineage=lineage,manifest_admission_proof=proof,private_core_ast_proofs=core_proof,
            semantic_count=len(projected.semantic_pins),physical_count=len(projected.physical_pins),
            actual_manifest_placeholder_used=False,baseline_runtime_budget=model,
            current159_controller_DATA_imports_and_whole_preflight_qualified=False,
            old_model_or_case158_runtime_relabelled_as159=False,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
