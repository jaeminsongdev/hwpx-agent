"""Prepare immutable158 step/capsule from actual151; never launch a worker."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_source_manifest_v2 as manifest
import runtime_envelope_worker_connection_v1 as connection

SELF="tools/p09/prepare_case158_worker_data_r327.py"
QUAL="implementation/p09/evidence/p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json"
CONFIG="implementation/p09/evidence/p09-361-case158-step-config001.v1.json"
CAPSULE="implementation/p09/evidence/p09-361-case158-worker-policy-capsule001.v1.json"


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)()
    result=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        product_or_worker_or_Native_executed=False,files_written=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        a.require(not (a.c.ROOT/CONFIG).exists() and not (a.c.ROOT/CAPSULE).exists(),"FRESH158_DATA_ONLY")
        qual=q.json(QUAL)
        a.fields(qual,dict(state="PASS_WORKER_POLICY_CODE12_ACTUAL11_CAPSULE_NOT_WORKER_DISPATCH_OR_PRODUCT",
            contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            actual_authority151_pin=connection.AUTHORITY,actual157_pin=connection.ROOT),"CURRENT_CODE12")
        for p in qual["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_SOURCE_PIN")
        binding,_,_=manifest.load(q,q.pin(manifest.PATH),a)
        authority=a.read_exact(q,connection.AUTHORITY)
        a.fields(authority,dict(accepted_count_after=151,next_runtime_index=158,
            resource_cleanup_confirmed=True,P09_gate="OPEN"),"CURRENT151_NEXT158")
        a.exact(authority["runtime_candidate_pin"],connection.ROOT,"SAME_ACTUAL157")
        listing=a.read_exact(q,launch.review.scope.LIST_PIN)
        names=listing["source_test_names"]
        a.require(type(names) is list and len(names)==249,"COMPILED249_EXACT")
        case=names[157]
        a.exact(case,"actual_import::source_review_assembly::stored_assembly_retains_complete_source_raw_typed_review_and_old_branches_without_publication","EXACT158_COMPILED_TEST")
        step=dict(schema_version="hwpx-agent.p09-flat-current-queue-step/v1",index=158,before=151,
            case=case,prior_queue_pin=connection.AUTHORITY,prior_candidate_pin=connection.ROOT)
        data,pin=connection.encode(binding,connection.AUTHORITY,connection.ROOT,g.check)
        connection.decode(data,pin,g.check)
        a.exact(pin,qual["policy_capsule_pin"],"SAME_ACTUAL11_CAPSULE")
        q.finish();g.check(force=True)
        result.update(state="PASS_PREPARED_CURRENT158_STEP_AND_BOUNDED_WORKER_CAPSULE_NOT_PRODUCT",
            candidate_config_path=CONFIG,candidate_config=step,candidate_capsule_path=CAPSULE,
            candidate_capsule_ascii=data.decode("ascii"),candidate_capsule_pin=dict(pin,path=CAPSULE),
            source_pin=q.snapshots[SELF],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            code=str(error);result["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_WORKER_PREPARATION_FAILURE"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
