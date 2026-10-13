"""New CODE7; whole current controller body and GO remain unexecuted."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import flat_current_queue_envelope_runtime_v19 as m
import distinct_final_sample_guard_v1 as distinct
import accept_case112_current_epoch as a

SELF="tools/p09/qualify_case158_controller_v19_r329.py"


def main():
    g=distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_product_or_Native_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(name) for name in (m.SELF,m.TEST,SELF,m.namespace_bundle.SELF)]
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_flat_current_queue_envelope_runtime_v19.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        result["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            result["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(result["contracts"],dict(run=7,errors=0,failures=0,skipped=0),"CURRENT_CONTROLLER_CODE7")
        prior=a.read_exact(q,m.worker_policy.AUTHORITY)
        a.fields(prior,dict(accepted_count_after=151,next_runtime_index=158,
            resource_cleanup_confirmed=True,P09_gate="OPEN"),"ACTUAL151")
        a.exact(prior["runtime_candidate_pin"],m.worker_policy.ROOT,"SAME_ACTUAL157")
        a.read_exact(q,m.worker_policy.ROOT)
        q.finish();g.check(force=True)
        result.update(state=m.QUAL_STATE,new_code_pins=pins[:2],source_pins=pins,
            original_whole_preflight_code_retained=True,parent_private_engine_and_original_worker_identity_retained=True,
            full_current158_preflight_or_product_qualified=False,fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_CONTROLLER_QUALIFICATION_FAILURE"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
