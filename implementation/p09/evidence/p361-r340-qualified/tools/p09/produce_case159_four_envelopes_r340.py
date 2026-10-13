"""Four exclusive lossless receipts from actual152/158, not case159 product."""
import ctypes
import hashlib
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
import runtime_envelope_physical_io_v1 as physical
import prepare_case159_step_selection_r340 as selector

SELF="tools/p09/produce_case159_four_envelopes_r340.py"
SELECTION="implementation/p09/evidence/p09-361-case159-step-and-lossless-selection-r727.v1.json"
CODE="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"


def main():
    g=distinct.guard_type(a.Guard)();latched=False
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        actual_product_or_Native_executed=False,original_receipts_rewritten=False,files_created=[])
    def check():
        nonlocal latched
        g.check();a.require(not latched,"STOP_LATCHED_SUCCESSOR_PRODUCER_PRESSURE")
        if g.samples and g.samples[-1]["system_cpu_percent"]>=75:
            latched=True;raise ValueError("STOP_SUCCESSOR_PRODUCER_PRESSURE_NO_COOLING")
    try:
        g.acquire();check();q=a.AcceptanceReader(a.c.ROOT,check);q.pin(SELF)
        selected=q.json(SELECTION)
        a.fields(selected,dict(state="PASS_ACTUAL152_SUCCESSOR159_STEP_AND_FOUR_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
            authority152_pin=selector.AUTHORITY,actual158_pin=selector.ROOT,cleanup_confirmed=True),"EXACT_SUCCESSOR_SELECTION")
        for pin in selected["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_SELECTION_CODE")
        a.require(len(selected["selected_originals"])==4,"FOUR_EXACT_PRIOR_RECEIPTS")
        authority=a.read_exact(q,selector.AUTHORITY)
        a.fields(authority,dict(accepted_count_after=152,next_runtime_index=159,runtime_candidate_pin=selector.ROOT),"ACTUAL152")
        prior=a.read_exact(q,selector.ROOT)
        scope=physical.source.scope.extend(physical.source.scope.pins(prior["source_input_representation"]["semantic_source_freeze"]),
            physical.source.scope.pins([selector.ROOT,selector.AUTHORITY]))
        code=q.json(CODE)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_CODE13_PUBLISHER")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ORIGINAL_CODEC_AND_WRITER_SOURCE")
        pacer=physical.bytes_policy.OwnedPacer();descriptors=[];original_total=encoded_total=0
        for pin in selected["selected_originals"]:
            a.exact(scope.get(pin["path"]),pin,"PRIOR_ORIGINAL_IN_INDEPENDENT_SUCCESSOR_SCOPE")
            actual,buffer=q._read(pin["path"],parse=True);q._bind(actual["path"],actual)
            a.exact(actual,pin,"CURRENT_FRESH_ORIGINAL")
            match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",pin["path"])
            a.require(match is not None and int(match[1])<159,"PRIOR_RECEIPT_NOT_CURRENT159")
            raw=bytes(buffer);encoded=physical.source.codec.encode(raw,check)
            name=physical.source.PREFIX+f"case{match[1]}-runtime-run{match[2]}.envelope.v1.json"
            output=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            desc=physical.source.descriptor(pin,output,next_case=159)
            projection=physical.source.Projection({pin["path"]:pin},[desc],next_case=159,checkpoint=check)
            for _ in range(2):a.exact(projection.decode_fresh(pin["path"],output,encoded,check),raw,"FRESH_LOSSLESS_ALL_ORIGINAL_BYTES")
            if (a.c.ROOT/name).exists():a.exact(q.fresh_pin(name),output,"EXISTING_DERIVATIVE_ONLY_IF_EXACT")
            else:
                physical.publish_exclusive(a.c.ROOT,encoded,output,check,write_pacer=pacer)
                out["files_created"].append(name)
            a.exact(q.fresh_pin(name),output,"ACTUAL_EXCLUSIVE_PHYSICAL_BYTES")
            descriptors.append(desc);original_total+=len(raw);encoded_total+=len(encoded)
            del raw,encoded,buffer
        q.finish();g.check(force=True);check()
        out.update(state="PASS_FOUR_SUCCESSOR159_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_RUNTIME_OR_GO",
            authority152_pin=selector.AUTHORITY,actual158_pin=selector.ROOT,selection_pin=q.snapshots[SELECTION],
            explicit_descriptors=descriptors,original_bytes=original_total,encoded_bytes=encoded_total,
            bytes_saved=original_total-encoded_total,decode_passes=8,
            write_rate_bytes_per_second=pacer.rate,write_bytes_paced=pacer.bytes_paced,
            source_pins=[q.snapshots[SELF],*code["source_pins"],*selected["source_pins"]],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):out["error_code"]=error.args[0]
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
