"""Exact successor STEP/receipt selection from actual epoch152, no product GO."""
import ctypes
import json
from pathlib import Path
import re
import sys

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
import flat_current_queue_runtime as runtime

SELF="tools/p09/prepare_case159_step_selection_r340.py"
AUTHORITY=dict(path="implementation/p09/evidence/p09-361-case158-current-epoch-accept001.v1.json",
    bytes=396156,sha256="ae5968271c2529880cb562a1ae3a48621af39d2af8d747d1ef77f6c245794f34")
ROOT=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run005.v1.json",
    bytes=4404465,sha256="34db0892a40886196a3307ba21decfdcb7ecdede4e6e02feb48422636a54ded4")


def main():
    g=distinct.guard_type(a.Guard)();out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,
        P09_gate="OPEN",actual_product_or_Native_executed=False,current159_SCOPE_or_GO_qualified=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF);q.pin(runtime.SELF)
        authority=a.read_exact(q,AUTHORITY)
        a.fields(authority,dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",
            accepted_count_after=152,next_runtime_index=159,accepted_count_delta=1,
            runtime_candidate_pin=ROOT,resource_cleanup_confirmed=True,
            full249_current_qualified=False,signed16_current_qualified=False,P09_gate="OPEN"),"ACTUAL152_NEXT159")
        prior=a.read_exact(q,ROOT)
        a.fields(prior,dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
            selected_test_index=158,cleanup_confirmed=True,owned_tree_empty=True,
            Native_source_frame_qualified=True,current_generation_runtime_candidate_qualified=True),"ACTUAL158_NOT_REPLAYED")
        a.fields(prior["source_frame"],dict(frame_state="COMMITTED"),"COMMITTED158")
        a.require(len(prior["source_frame"]["actual_byte_boundaries"])==2,"ACTUAL_TWO_WHOLE_BOUNDARIES")
        listing=a.read_exact(q,a.scope.LIST_PIN)
        a.require(len(listing["source_test_names"])==249,"EXACT_COMPILED_ROSTER249")
        step=dict(schema_version="hwpx-agent.p09-flat-current-queue-step/v1",index=159,before=152,
            case=listing["source_test_names"][158],prior_queue_pin=AUTHORITY,prior_candidate_pin=ROOT)
        runtime.validate_config(step,159)
        semantic=a.scope.pins(prior["source_input_representation"]["semantic_source_freeze"])
        mapped={r["semantic_original_pin"]["path"] for r in prior["source_input_representation"]["descriptors"]}
        choices=sorted((p for n,p in semantic.items() if n not in mapped and
            re.fullmatch(r"implementation/p09/evidence/p09-361-case[0-9]{3}-current-runtime-run[0-9]{3}\.v1\.json",n)),
            key=lambda p:(-p["bytes"],p["path"]))[:3]
        a.require(len(choices)==3,"THREE_UNMAPPED_PRIOR_RECEIPTS")
        for pin in choices:a.exact(q.pin(pin["path"]),pin,"CURRENT_PRIOR_ORIGINAL_BYTES")
        q.finish();g.check(force=True)
        out.update(state="PASS_ACTUAL152_SUCCESSOR159_STEP_AND_FOUR_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
            step=step,selected_originals=choices+[ROOT],old_pair_count=len(mapped),
            old_manifest_pin=prior["source_input_representation"]["manifest_pin"],
            authority152_pin=AUTHORITY,actual158_pin=ROOT,compiled_listing_pin=a.scope.LIST_PIN,
            source_pins=[q.snapshots[SELF],q.snapshots[runtime.SELF]],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
