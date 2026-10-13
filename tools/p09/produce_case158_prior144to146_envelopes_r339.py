"""Three additional lossless receipts; existing CODE13 publisher retained.

No original overwrite/deletion, Native or product. Existing derivatives are
accepted only after fresh exact physical pin validation, never overwritten.
"""
import ctypes
_k=ctypes.WinDLL('kernel32',use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit('LOCAL_LIMITS_NOT_APPLIED')
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch
import runtime_envelope_physical_io_v1 as physical
SELF="tools/p09/produce_case158_prior144to146_envelopes_r339.py"
SELECTION="implementation/p09/evidence/p09-361-case158-prior144to146-lossless-selection-r713.v1.json"


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)();result=dict(state="FAILED_NOT_ACCEPTED",P09_gate="OPEN",
        accepted_count_delta=0,actual_Native_product_or_acceptance_executed=False,files_created=[])
    latched=False
    def check():
        nonlocal latched
        g.check();a.require(not latched,"STOP_LATCHED_EXTRA_PRODUCER_PRESSURE")
        if g.samples and g.samples[-1]["system_cpu_percent"]>=75:
            latched=True;raise ValueError("STOP_EXTRA_PRODUCER_PRESSURE_NO_COOLING")
    try:
        g.acquire();check();q=a.AcceptanceReader(a.c.ROOT,check);q.pin(SELF)
        code_path="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"
        code=q.json(code_path);a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"QUALIFIED_PUBLISHER")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CURRENT_PUBLISHER")
        root=a.read_exact(q,launch.review.ROOT_PIN);scope=a.scope.pins(root["source_freeze"])
        ar=a.read_exact(q,launch.review.AUTHORITY_PIN);a.fields(ar,dict(accepted_count_after=151,next_runtime_index=158),"CURRENT151")
        selected=q.json(SELECTION)
        for pin in selected["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_EXACT_SELECTION_CODE")
        a.exact(selected["selected_indices"],[144,145,146],"ONLY_THREE_REVIEWED_PRIOR_RECEIPTS")
        a.fields(selected,dict(state="PASS_EXACT_THREE_EXTRA_RECEIPT_SIZE_SELECTION_NOT_DERIVATIVES_OR_NATIVE",cleanup_confirmed=True),"THREE_SIZE_SELECTION")
        selected=selected["top_additional_candidates"];a.require(len(selected)==3,"THREE_ONLY")
        pacer=physical.bytes_policy.OwnedPacer();descriptors=[];raw_total=encoded_total=0
        for pin in selected:
            a.exact(scope[pin["path"]],pin,"ORIGINAL_INSIDE_REAL_PRIOR_NATIVE_SCOPE")
            actual,buffer=q._read(pin["path"],parse=True);q._bind(actual["path"],actual);a.exact(actual,pin,"FRESH_ORIGINAL")
            raw=bytes(buffer);encoded=physical.source.codec.encode(raw,check)
            name=pin["path"].split("case",1)[1].split("-",1)[0]
            path=physical.source.PREFIX+f"case{name}-runtime-run001.envelope.v1.json"
            p=dict(path=path,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            desc=physical.source.descriptor(pin,p,next_case=158)
            projection=physical.source.Projection({pin["path"]:pin},[desc],next_case=158,checkpoint=check)
            for _ in range(2):a.exact(projection.decode_fresh(pin["path"],p,encoded,check),raw,"EXACT_ORIGINAL_ALL_BYTES")
            if (a.c.ROOT/path).exists():a.exact(q.fresh_pin(path),p,"EXISTING_ONLY_IF_EXACT")
            else:
                physical.publish_exclusive(a.c.ROOT,encoded,p,check,write_pacer=pacer);result["files_created"].append(path)
            a.exact(q.fresh_pin(path),p,"FRESH_ACTUAL_DERIVATIVE")
            raw_total+=len(raw);encoded_total+=len(encoded);descriptors.append(desc);del raw,encoded,buffer
        q.finish();g.check(force=True);check()
        result.update(state="PASS_THREE_EXTRA_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_NATIVE_OR_PRODUCT",
            explicit_descriptors=descriptors,original_receipt_bytes=raw_total,encoded_bytes=encoded_total,
            bytes_saved=raw_total-encoded_total,decode_passes=6,write_bytes_paced=pacer.bytes_paced,write_rate_bytes_per_second=pacer.rate,
            original_receipts_rewritten=False,source_pins=[q.snapshots[SELF],*code["source_pins"]],qualification_pin=q.snapshots[code_path],
            selection_pin=q.snapshots[SELECTION],authority151_pin=launch.review.AUTHORITY_PIN,actual157_pin=launch.review.ROOT_PIN,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError) as error:
        result["state"]="FAILED_NOT_ACCEPTED";result["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            message=str(error);result["error_code"]=message if re.fullmatch("[A-Za-z0-9_]{1,256}",message) else "REDACTED_EXTRA_PRODUCER_ERROR"
    finally:g.close();result["cleanup_confirmed"]=g.cleanup
    print(json.dumps(result,ensure_ascii=True,allow_nan=False));return 0 if result["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
