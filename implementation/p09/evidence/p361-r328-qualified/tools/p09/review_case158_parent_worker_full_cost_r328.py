"""Full inherited union plus current connection material; no GO or frame."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_source_manifest_v2 as manifest
import runtime_envelope_worker_connection_v1 as worker
import flat_current_queue_product_window_runtime_v18 as prior

SELF="tools/p09/review_case158_parent_worker_full_cost_r328.py"
EVIDENCE="implementation/p09/evidence/"
RECEIPTS=[
    "p09-361-case158-raw-live-access-policy-code10-r640.v1.json",
    "p09-361-case158-full-oracle-connection-code9-r642.v1.json",
    "p09-361-case158-actual-policy-projected-frame12-r643.v1.json",
    "p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json",
    "p09-361-case158-step-capsule-preparation-r646.v1.json",
    "p09-361-case158-owned-worker-policy-diagnostic-r647.v1.json",
    "p09-361-authority151-case158-worker-connection-r327-final-r649.v1.json",
    "p09-361-case158-parent-connection-code9-r651.v1.json"]


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_current158_product_or_Native_or_queue_acceptance_executed=False,
        full_current158_controller_DATA_or_preflight_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        binding,inherited,_=manifest.load(q,q.pin(manifest.PATH),a)
        for filename in RECEIPTS:
            row=q.json(EVIDENCE+filename)
            a.require(row["state"].startswith("PASS_") and row["cleanup_confirmed"] is True,"PRESERVED_SUPPORT_NOT_PRODUCT")
            for pin in row.get("new_code_pins",[])+row.get("source_pins",[]):
                a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_CONNECTION_SOURCES")
        q.pin("tools/p09/runtime_envelope_full_oracle_connection_v1.py")
        q.pin("tools/p09/tests/test_runtime_envelope_full_oracle_connection_v1.py")
        q.pin("tools/p09/audit_case158_worker_connection_r327.py")
        q.pin("tools/p09/prepare_case158_worker_data_r327.py")
        for name in ("p09-361-case158-step-config001.v1.json","p09-361-case158-worker-policy-capsule001.v1.json",
            "p09-361-case158-full-oracle-code9-attempt001-failed-r641.v1.json",
            "p09-361-case158-worker-namespace-inspection-failed-r644.v1.json",
            "p09-361-case158-r327-document-position-audit-failed-r648.v1.json",
            "p09-361-case158-parent-code9-attempt001-failed-r650.v1.json"):
            q.pin(EVIDENCE+name)
        # All new qualified code archives and failed code preimages are kept in
        # this conservative candidate too; no old/native input is excluded.
        base=q.json(EVIDENCE+"p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json")
        sources=["tools/p09/runtime_envelope_raw_access_policy_v1.py",
            "tools/p09/tests/test_runtime_envelope_raw_access_policy_v1.py",
            "tools/p09/runtime_envelope_full_oracle_connection_v1.py",
            "tools/p09/tests/test_runtime_envelope_full_oracle_connection_v1.py",
            "tools/p09/probe_case158_policy_frame_r326.py",
            "tools/p09/runtime_envelope_worker_connection_v1.py",
            "tools/p09/tests/test_runtime_envelope_worker_connection_v1.py",
            "tools/p09/qualify_case158_worker_connection_r327.py",
            "tools/p09/prepare_case158_worker_data_r327.py",
            "tools/p09/probe_case158_owned_worker_policy_r327.py"]
        for name in sources:
            p=q.pin(name);a.exact(q.pin(EVIDENCE+"p361-r327-qualified/"+name),dict(p,path=EVIDENCE+"p361-r327-qualified/"+name),"EXACT_QUALIFIED_ARCHIVE")
        for name in ("tools/p09/runtime_envelope_parent_connection_v1.py",
            "tools/p09/tests/test_runtime_envelope_parent_connection_v1.py"):
            q.pin(EVIDENCE+"p361-r328-failed-parent001/"+name)
        q.pin(EVIDENCE+"p361-r326-oracle-failed-test/test_runtime_envelope_full_oracle_connection_v1.py")
        q.pin(EVIDENCE+"p361-r327-failed-final-audit/audit_case158_worker_connection_r327.py")
        required=manifest.original.scope_binding.source.scope.extend(inherited,q.snapshots)
        projection,proof=binding.project(required,g.check)
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        original_budget=prior.DIRECT.runtime_budget(physical,167)
        raw_total=original_budget["predicted_runtime_combined_seconds"]+5.0
        result.update(candidate_semantic_inputs=len(projection.semantic_pins),
            candidate_semantic_bytes=sum(p["bytes"] for p in projection.semantic_pins.values()),
            candidate_physical_inputs=len(physical),candidate_physical_bytes=sum(p["bytes"] for p in physical.values()),
            exact_alias_reconciliation=proof,complete_current_connection_candidate_seconds=raw_total,
            candidate_shared_decoder_allowance_seconds=5.0,unchanged_Native_deadline_seconds=600,
            current_candidate_fits_unchanged600=raw_total<600,
            new_immutable_controller_DATA_and_qualification_costs_not_yet_present=True,
            current_input_scope_reduction_or_guard_rate_relaxation=False)
        q.finish();g.check(force=True)
        result.update(state="PASS_CURRENT_PARENT_WORKER_FULL_SOURCE_COST_REVIEW_NOT_CURRENT158_PREFLIGHT_OR_PRODUCT",
            source_pin=q.snapshots[SELF],authority151_pin=worker.AUTHORITY,actual157_pin=worker.ROOT,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_FULL_COST_FAILURE"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
