"""Preserved failed003 inherited cost and memory-only lossless experiment.

The complete next controller/DATA is not yet composed. Preserve the original
600-second/decoder5/whole-scope rules; no Native/product execution or adoption.
"""
import ctypes
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
_k=ctypes.WinDLL("kernel32",use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
import accept_case112_current_epoch as a
import distinct_final_sample_guard_v1 as distinct
import runtime_record_envelope_v2 as codec

SELF="tools/p09/review_case158_failed003_cost_r335.py"
ROOT_PIN=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run003.v1.json",
    bytes=2209026,sha256="e93a86080ad9fce059fe8eba26aa4d0c0f343d0c2530677dd86340d52334e609")
REVIEW="implementation/p09/evidence/p09-361-case158-run003-native-stop-review-code8-r688.v1.json"


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_product_or_Native_executed=False,original_receipts_rewritten=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        import flat_current_queue_envelope_runtime_v22 as m
        code=q.json(m.QUAL)
        a.fields(code,dict(state=m.QUAL_STATE,contracts=dict(run=24,errors=0,failures=0,skipped=0),
            cleanup_confirmed=True),"QUALIFIED_V22_CODE_NOT_REEXECUTED")
        for p in code["source_pins"]:a.exact(q.pin(p["path"]),p,"UNCHANGED_V22_DEPENDENCIES")
        pin,raw=q._read(ROOT_PIN["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,ROOT_PIN,"PRESERVED_FAILED003_BYTES")
        row=json.loads(raw.decode("utf-8"))
        a.fields(row,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r003-tests",
            stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",product_body_observed=False,
            worker_created=False,cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"FAILED_NOT_CURRENT_PRODUCT")
        reviewed=q.json(REVIEW)
        a.fields(reviewed,dict(state="PASS_EXACT158_RUN003_CLOSED_NATIVE_ACQUISITION_STOP_REVIEW_NOT_GO_OR_PRODUCT",
            contracts=dict(run=8,errors=0,failures=0,skipped=0),original_runtime_pin=ROOT_PIN,cleanup_confirmed=True),
            "INDEPENDENT_STOP_REVIEW_NOT_GO")
        for p in reviewed["new_code_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_STOP_REVIEW_SOURCE")
        physical=m.base.scope.pins(row["source_input_representation"]["physical_source_freeze"])
        def budget(pins):return m.binding_value().runtime_budget(pins,167,m.prior.DIRECT.runtime_budget,g.check)
        actual=budget(physical)
        a.exact(actual["predicted_runtime_combined_seconds"],row["complete_runtime_budget"]["predicted_runtime_combined_seconds"],
            "ORIGINAL_DECLARED_COST_NOT_EXECUTION_PASS")
        extras=[ROOT_PIN,q.snapshots[REVIEW]]+reviewed["new_code_pins"]
        inherited=m.base.scope.extend(physical,m.base.scope.pins(extras))
        future=budget(inherited)
        original=bytes(raw);encoded=codec.encode(original,g.check)
        for _ in range(2):a.exact(codec.decode(encoded,g.check),original,"FRESH_MEMORY_LOSSLESS_FAILED003")
        for name in (SELF,codec.SELF,codec.TEST,"tools/p09/runtime_record_envelope_v1.py"):
            q.pin(name)
        q.finish();g.check(force=True)
        out.update(state="PASS_FAILED003_INHERITED_ONLY_COST_AND_TWO_MEMORY_DECODES_NOT_CURRENT_CONTROLLER_OR_GO",
            failed003_pin=ROOT_PIN,declared_previous_physical_count=len(physical),
            previous_declared_model_seconds=actual["predicted_runtime_combined_seconds"],
            next_inherited_only_physical_count=len(inherited),
            next_inherited_only_model_seconds=future["predicted_runtime_combined_seconds"],
            original_source_extra_pins=extras,current_next_controller_and_DATA_included=False,
            memory_only_candidate=dict(original_bytes=len(original),encoded_bytes=len(encoded),
                bytes_saved=len(original)-len(encoded),fresh_decode_passes=2,
                same_case_failed_receipt_descriptor_currently_supported=False,
                encoded_file_published=False,current_physical_source_scope_adopted=False),
            source_pins=[q.snapshots[SELF]],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),
            RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_FAILED_COST_REVIEW"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
