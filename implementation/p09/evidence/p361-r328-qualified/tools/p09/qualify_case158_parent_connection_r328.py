"""CODE9 and exact whole-engine namespace connection, not product execution."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_parent_connection_v1 as parent
import runtime_envelope_worker_connection_v1 as worker
import flat_current_queue_product_window_runtime_v18 as prior

SELF="tools/p09/qualify_case158_parent_connection_r328.py"
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case158-worker-policy-capsule001.v1.json",
    bytes=6383,sha256="37279afffea965613e416cb951d17da4c2c1ec7656bd28d9c58ef8042930b04c")


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_current158_parent_or_worker_or_Native_executed=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(name) for name in (SELF,parent.SELF,parent.TEST,worker.SELF,worker.TEST,
            "tools/p09/tests/test_runtime_envelope_frame_connection_v1.py",
            "tools/p09/tests/test_runtime_envelope_scope_binding_v1.py")]
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_runtime_envelope_parent_connection_v1.py")
        tests=unittest.TestResult();suite.run(tests);g.check()
        result["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            result["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(result["contracts"],dict(run=9,errors=0,failures=0,skipped=0),"NEW_PARENT_CODE9")
        authority=a.read_exact(q,worker.AUTHORITY)
        a.fields(authority,dict(accepted_count_after=151,next_runtime_index=158,
            resource_cleanup_confirmed=True,P09_gate="OPEN"),"CURRENT151")
        a.exact(authority["runtime_candidate_pin"],worker.ROOT,"ACTUAL157")
        a.read_exact(q,worker.ROOT)
        pin,data=q._read(CAPSULE["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,CAPSULE,"ACTUAL_RAW_CAPSULE_FILE")
        binding,_=worker.decode(bytes(data),{k:pin[k] for k in ("bytes","sha256")},g.check)
        step=q.json(prior.M.base.config_path(158))
        prior.M.base.validate_config(step,158);prior.M.base.configure(158)
        for p in prior.COMPONENT_PINS:a.exact(q.pin(p["path"]),p,"ALL_EXISTING_NATIVE_WINDOW_COMPONENTS")
        q.pin(prior.SELF);q.pin(prior.TEST)
        engine,_=prior.template();connected,state=parent.connect_engine(engine,binding)
        a.require(connected.worker is engine.worker and state.original is engine.run_owned
            and connected.run_owned.__globals__ is engine.run_owned.__globals__,"FULL_TEMPLATE_FUNCTION_AND_ENV_IDENTITIES")
        a.require(state.attempts==0 and state.frames==[],"QUALIFICATION_DID_NOT_EXECUTE_ENGINE")
        q.finish();g.check(force=True)
        result.update(state="PASS_PARENT_CODE9_REAL158_WHOLE_ENGINE_NAMESPACE_CONNECTED_NOT_PRODUCT",
            new_code_pins=[p for p in pins if p["path"] in (parent.SELF,parent.TEST)],source_pins=pins,
            parent_connection_evidence=parent.evidence(state),all_original_Native_window_components_fresh=True,
            actual_authority151_pin=worker.AUTHORITY,actual157_pin=worker.ROOT,
            actual_worker_capsule_pin=CAPSULE,actual_descriptor_count=len(binding.originals),
            existing_worker_function_identity_retained=True,private_engine_environment_shared=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_PARENT_COMPONENT_FAILURE"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
