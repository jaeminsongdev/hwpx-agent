"""Exact prior132 from the real prepared scope; exclusive lossless derivative."""
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
import time
SELF="tools/p09/produce_prior132_transport_r370.py"
OUTPUT="implementation/p09/evidence/p09-361-case160-prior132-transport-producer-r848.v1.json"
PREPARED=dict(path="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json",
    bytes=2693611,sha256="73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233")
ORIGINAL=dict(path="implementation/p09/evidence/p09-361-case132-current-runtime-run001.v1.json",
    bytes=2472248,sha256="6ebab43e075e1da55674120b9e5883408b6be63d45ab58170d06c27058d42f4d")
WRITER="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    p=k.GetCurrentProcess()
    if not(k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import runtime_envelope_physical_io_v1 as physical
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"PRIOR132_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    result=dict(state="FAILED_PRIOR132_TRANSPORT_NOT_ACCEPTED",accepted_count_delta=0,
        original_receipt_rewritten=False,product_or_Native_reexecuted=False,GO_authorized=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        prepared=a.read_exact(q,PREPARED)
        a.fields(prepared,dict(state="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO",
            fresh_inputs=1145,final_fresh_hashes=1145,cleanup_confirmed=True),"ACTUAL_COMPLETE_PREPARATION")
        scope=a.scope.pins(prepared["checkpoint"]["complete_scope"])
        a.exact(scope.get(ORIGINAL["path"]),ORIGINAL,"PRIOR132_IN_ACTUAL_WHOLE_SCOPE")
        a.require(all(d["semantic_original_pin"]["path"]!=ORIGINAL["path"] for d in prepared["checkpoint"]["representation"]["descriptors"]),
            "ONLY_UNALIASED132_SELECTED")
        code=q.json(WRITER)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_WRITER_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CODEC_WRITER")
        actual,buffer=q._read(ORIGINAL["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,ORIGINAL,"EXACT_PRIOR132_BYTES")
        raw=bytes(buffer);encoded=physical.source.codec.encode(raw,q.checkpoint)
        target=dict(path=physical.source.PREFIX+"case132-runtime-run001.envelope.v1.json",
            bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        descriptor=physical.source.descriptor(ORIGINAL,target,next_case=160)
        budget=physical.DecoderBudget(q.checkpoint)
        for _ in range(2):a.exact(budget.run(lambda check:physical.source.codec.decode(encoded,check)),raw,"TWO_EXACT_PRIOR132_RESTORATIONS")
        physical.publish_exclusive(a.c.ROOT,encoded,target,q.checkpoint)
        a.exact(q.fresh_pin(target["path"]),target,"ACTUAL_EXCLUSIVE_PRIOR132")
        q.finish();g.check(force=True)
        result.update(state="PASS_PRIOR132_EXCLUSIVE_LOSSLESS_IN_ACTUAL_SCOPE_NOT_ADOPTED_MANIFEST_OR_GO",
            original_pin=ORIGINAL,physical_pin=target,descriptor=descriptor,prepared_scope_pin=PREPARED,
            representation_bytes_saved=len(raw)-len(encoded),exact_original_restore_passes=2,
            elapsed_decoder_seconds=budget.elapsed,write_rate_bytes_per_second=2097152,
            source_pins=[q.snapshots[SELF]]+code["source_pins"],fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        result["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):result["error_code"]=error.args[0]
    finally:
        g.close();result.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"PRIOR132_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(result,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:result.get(key) for key in ("state","physical_pin","representation_bytes_saved","fresh_inputs","final_fresh_hashes",
        "CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if result["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
