"""Actual template dependency graph and seven new contracts, no engine body."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import flat_current_queue_envelope_runtime_v19 as m
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import reviewed_case158_attempt_v3 as attempt
SELF="tools/p09/qualify_case158_distinct_attempt_r331.py"
def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",actual_product_or_Native_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        code=q.json("implementation/p09/evidence/p09-361-case158-distinct-physical-run002-code7-r668.v1.json")
        a.fields(code,dict(state="PASS_REVIEWED158_RUN002_TEMPLATE_DEPENDENCY_CODE7_NOT_ACTUAL_PRODUCT",
            contracts=dict(run=7,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CODE7_COMPONENT_ONLY")
        for p in code["new_code_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_ATTEMPT_SOURCES")
        q.pin(SELF);q.pin(m.SELF);q.pin(m.TEST)
        m.base.configure(158)
        a.read_exact(q,m.worker_policy.AUTHORITY);a.read_exact(q,m.worker_policy.ROOT)
        failure=attempt.reviewed_failure(q,a)
        original15=m.prior.OLD17.OLD16.OLD15
        before=original15.RETRY.physical_run(158)
        fn,proof=attempt.connect_template(m.prior)
        engine,template_proof=fn()
        actual=m.prior.OLD17.ATTEMPT_STATES[-1]
        a.require(actual.physical_product_run==2 and actual.actual_engine_calls==0,"REAL_TEMPLATE_ADAPTER_RUN002_NOT_EXECUTED")
        a.exact(original15.RETRY.physical_run(158),before,"ORIGINAL_NAMESPACE_UNCHANGED")
        a.require(before==1 and engine.worker.__code__.co_filename=="tools/p09/run_case112_current_stored.py","ORIGINAL_WORKER_CODE")
        for p in m.NAMESPACE_SOURCE_PINS+[m.PRIOR_WINDOW_PIN,m.LEAN_PIN,m.BUNDLE_PIN,m.ADMISSION_PIN]:
            a.exact(q.pin(p["path"]),p,"ALL_PRIVATE_NAMESPACE_SOURCE_BYTES")
        q.finish();g.check(force=True)
        out.update(state="PASS_REAL_CURRENT158_TEMPLATE_DISTINCT_RUN002_ADAPTER_NOT_PRODUCT_OR_NEW_CONTROLLER",
            original_failure_001_preserved_and_unaccepted=True,real_argument_adapter_physical_run=2,
            actual_engine_calls=0,original_retry_namespace_physical_run=1,original_worker_code_retained=True,
            template_projection=proof,whole_current_run002_controller_or_runtime_or_acceptance_qualified=False,
            source_pin=q.snapshots[SELF],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out["error_type"]=type(e).__name__
        if isinstance(e,ValueError):
            import re
            msg=str(e);out["error_code"]=msg if re.fullmatch("[A-Za-z0-9_]{1,256}",msg) else "REDACTED_ATTEMPT_QUAL_ERROR"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
