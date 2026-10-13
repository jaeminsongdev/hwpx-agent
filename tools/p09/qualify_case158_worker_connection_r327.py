"""New worker CODE12 + actual eleven-pair capsule, not product dispatch."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
# This launcher applies one logical CPU and BelowNormal before helper imports.
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_source_manifest_v2 as manifest
import runtime_envelope_worker_connection_v1 as connection

SELF="tools/p09/qualify_case158_worker_connection_r327.py"


def main():
    a=launch.a;guard=launch.distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        current158_product_or_Native_executed=False,worker_process_dispatched=False)
    try:
        guard.acquire();q=a.AcceptanceReader(a.c.ROOT,guard.check)
        pins=[q.pin(name) for name in (SELF,connection.SELF,connection.TEST,
            connection.raw_policy.SELF,connection.raw_policy.TEST,
            "tools/p09/tests/test_runtime_envelope_scope_binding_v1.py")]
        suite=unittest.defaultTestLoader.discover(str(a.c.ROOT/"tools/p09/tests"),
            pattern="test_runtime_envelope_worker_connection_v1.py")
        tests=unittest.TestResult();suite.run(tests);guard.check()
        result["contracts"]=dict(run=tests.testsRun,errors=len(tests.errors),
            failures=len(tests.failures),skipped=len(tests.skipped))
        if tests.errors or tests.failures:
            result["failed_test_names"]=[t.id().split(".")[-1] for t,_ in tests.errors+tests.failures]
        a.exact(result["contracts"],dict(run=12,errors=0,failures=0,skipped=0),"NEW_WORKER_CODE12")
        binding,_,admission=manifest.load(q,q.pin(manifest.PATH),a)
        a.exact(q.snapshots[connection.AUTHORITY["path"]],connection.AUTHORITY,"ACTUAL151_AUTHORITY")
        a.exact(q.snapshots[connection.ROOT["path"]],connection.ROOT,"ACTUAL157_ROOT")
        data,pin=connection.encode(binding,connection.AUTHORITY,connection.ROOT,guard.check)
        decoded,proof=connection.decode(data,pin,guard.check)
        a.exact(decoded.descriptors(),binding.descriptors(),"ALL_ACTUAL11_WORKER_DESCRIPTORS")
        a.exact(dict(decoded.manifest_pin),dict(binding.manifest_pin),"ACTUAL_MANIFEST_PIN_RETAINED")
        a.exact(len(decoded.originals),11,"ACTUAL11_NOT_SUBSET")
        q.finish();guard.check(force=True)
        result.update(state="PASS_WORKER_POLICY_CODE12_ACTUAL11_CAPSULE_NOT_WORKER_DISPATCH_OR_PRODUCT",
            new_code_pins=[p for p in pins if p["path"] in (connection.SELF,connection.TEST)],
            source_pins=pins,actual_authority151_pin=connection.AUTHORITY,actual157_pin=connection.ROOT,
            actual_manifest_pin=dict(binding.manifest_pin),actual_descriptor_count=11,
            policy_capsule_pin=pin,policy_capsule_proof=proof,
            existing_source_manifest_admission_preserved=admission["base_manifest_preserved"],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in guard.samples),
            RAM_min=min(s["available_ram_percent"] for s in guard.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            message=str(error);result["error_code"]=message if re.fullmatch("[A-Za-z0-9_]{1,256}",message) else "REDACTED_WORKER_COMPONENT_ERROR"
    finally:
        guard.close();result["cleanup_confirmed"]=guard.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
