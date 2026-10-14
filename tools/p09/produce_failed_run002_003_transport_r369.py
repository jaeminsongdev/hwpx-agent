"""Preserve two exact failures as explicit lossless inputs, not admitted aliases."""
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
import time
SELF="tools/p09/produce_failed_run002_003_transport_r369.py"
OUTPUT="implementation/p09/evidence/p09-361-case160-failed002003-transport-producer-r844.v1.json"
WRITER="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"
SECOND=dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run002.v1.json",
    bytes=4217213,sha256="cec8b6269f552bf9c50fc528d85a1a87bd0a188925d82a0cccbcbf43ab7778c5")
SECOND_REVIEW="implementation/p09/evidence/p09-361-case160-run002-shared-metadata-stop-review-r810.v1.json"
THIRD_REVIEW="implementation/p09/evidence/p09-361-case160-run003-shared-metadata-stop-review-r843.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not(k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import runtime_envelope_physical_io_v1 as physical
    import review_failed_run003_v1 as review
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"FAILED_TRANSPORT_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    result=dict(state="FAILED_FAILURE_TRANSPORT_NOT_ACCEPTED",accepted_count_delta=0,
        original_failures_rewritten=False,failures_promoted=False,actual_product_or_Native_executed=False,
        GO_authorized=False,files_created=[],P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        for path in (review.SELF,review.TEST):q.pin(path)
        code=q.json(WRITER)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_WRITER_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_WRITER_CODEC")
        second=q.json(SECOND_REVIEW);third=q.json(THIRD_REVIEW)
        a.fields(second,dict(state="REVIEW_ACTUAL160_RUN002_SHARED_METADATA_DEADLINE_NOT_RUNTIME_OR_ACCEPTANCE_PASS",
            runtime_pin=SECOND,cleanup_confirmed=True,accepted_count_after=153,accepted_count_delta=0,
            whole_Runtime_or_two_byte_boundary_qualified=False),"EXACT_SECOND_REVIEW")
        a.fields(third,dict(state=review.STATE,runtime_pin=review.ROOT,contracts=dict(run=10,errors=0,failures=0,skipped=0),
            cleanup_confirmed=True,accepted_count_after=153,accepted_count_delta=0,
            whole_Runtime_or_two_byte_boundary_qualified=False),"EXACT_THIRD_CODE10_REVIEW")
        a.require(third["fresh_inputs"]==third["final_fresh_hashes"]==4,"THIRD_ALL_FINAL_HASHES")
        for pin in third["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_THIRD_REVIEW_CODE")
        published=[];budget=physical.DecoderBudget(q.checkpoint)
        for number,original in ((2,SECOND),(3,review.ROOT)):
            actual,buffer=q._read(original["path"],parse=True);q._bind(actual["path"],actual)
            a.exact(actual,original,"EXACT_PRESERVED_FAILED_RUNTIME")
            raw=bytes(buffer);failed=json.loads(raw.decode("utf-8"),object_pairs_hook=physical.source.codec.unique)
            a.fields(failed,dict(state="STOPPED_NOT_ACCEPTED",selected_test_index=160,
                task="case160-current-r%03d-tests"%number,stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",
                operation_phase="final_source_freeze",cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"EXACT_FAILED_KIND_NOT_SUCCESS")
            if number==3:a.fields(third,review.review(failed,a),"SAME_WHOLE_THIRD_REVIEW")
            encoded=physical.source.codec.encode(raw,q.checkpoint)
            target=dict(path=physical.source.PREFIX+"case160-runtime-run%03d.failed.envelope.v1.json"%number,
                bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            for _ in range(2):a.exact(budget.run(lambda check:physical.source.codec.decode(encoded,check)),raw,"TWO_EXACT_FAILED_ORIGINAL_RESTORATIONS")
            physical.publish_exclusive(a.c.ROOT,encoded,target,q.checkpoint)
            result["files_created"].append(target["path"])
            a.exact(q.fresh_pin(target["path"]),target,"ACTUAL_EXCLUSIVE_FAILURE_TRANSPORT")
            published.append(dict(original_pin=original,physical_pin=target,
                independent_review_pin=q.snapshots[SECOND_REVIEW if number==2 else THIRD_REVIEW],
                representation_bytes_saved=len(raw)-len(encoded),
                explicit_kind="same_case_partial_post_product_source_failure_not_accepted"))
        q.finish();g.check(force=True)
        result.update(state="PASS_EXCLUSIVE_FAILED002003_TRANSPORT_NOT_ADMITTED_MANIFEST_RUNTIME_OR_GO",
            selected_outputs=published,exact_original_restore_passes=4,original_aggregate_decoder_limit_seconds=5.0,
            elapsed_decoder_seconds=budget.elapsed,write_rate_bytes_per_second=2097152,
            representation_bytes_saved=sum(p["representation_bytes_saved"] for p in published),
            source_pins=[q.snapshots[x] for x in (SELF,review.SELF,review.TEST)]+code["source_pins"]+third["source_pins"],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,
            same_case_failure_alias_role_independent_qualification_required=True,
            new_actual_manifest_controller_or_runtime_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            result["error_code"]=error.args[0]
    finally:
        g.close();result.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"FAILED_TRANSPORT_PRODUCER_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(result,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:result.get(key) for key in ("state","selected_outputs","representation_bytes_saved",
        "fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
