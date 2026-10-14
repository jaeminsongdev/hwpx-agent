"""Exclusive lossless derivative of the exact completed preparation, not GO."""
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
import time

SELF="tools/p09/produce_prepared_checkpoint_transport_r368.py"
OUTPUT="implementation/p09/evidence/p09-361-prepared-checkpoint-transport-producer-r839.v1.json"
ORIGINAL=dict(path="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json",
    bytes=2693611,sha256="73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233")
PHYSICAL_PATH="implementation/p09/evidence/p361-lossless-runtime-inputs/case160-prepared-r834.envelope.v1.json"
WRITER="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not (k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):
        raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import prepared_checkpoint_transport_v1 as transport
    import runtime_envelope_physical_io_v1 as physical
    destination=a.c.ROOT/OUTPUT
    a.require(not destination.exists() and not destination.is_symlink(),"TRANSPORT_PRODUCER_REFUSE_OVERWRITE")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();q=None;started=time.monotonic()
    row=dict(state="FAILED_TRANSPORT_PRODUCTION_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,original_checkpoint_rewritten=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        for path in (SELF,transport.SELF,transport.TEST):q.pin(path)
        code=q.json(WRITER)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_WRITER_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_ORIGINAL_WRITER_AND_CODEC")
        actual,buffer=q._read(ORIGINAL["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,ORIGINAL,"EXACT_COMPLETED_PREPARATION_BYTES")
        raw=bytes(buffer);prepared=json.loads(raw.decode("utf-8"),object_pairs_hook=physical.source.codec.unique)
        a.fields(prepared,dict(state="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO",
            fresh_inputs=1145,final_fresh_hashes=1145,cleanup_confirmed=True,
            Native_or_product_executed=False,GO_authorized=False,accepted_count_delta=0),"WHOLE_PREPARATION_NOT_FAILED")
        for pin in prepared["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_ORIGINAL_PREPARATION_SOURCES")
        encoded=physical.source.codec.encode(raw,q.checkpoint)
        output=dict(path=PHYSICAL_PATH,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        budget=physical.DecoderBudget(q.checkpoint)
        for _ in range(2):a.exact(budget.run(lambda check:physical.source.codec.decode(encoded,check)),raw,"TWO_EXACT_ORIGINAL_RESTORATIONS")
        physical.publish_exclusive(a.c.ROOT,encoded,output,q.checkpoint)
        a.exact(q.fresh_pin(output["path"]),output,"ACTUAL_EXCLUSIVE_PHYSICAL_BYTES")
        q.finish();g.check(force=True)
        row.update(state="PASS_EXCLUSIVE_PREPARED_CHECKPOINT_TRANSPORT_NOT_RUNTIME_OR_GO",
            original_pin=ORIGINAL,physical_pin=output,representation_bytes_saved=len(raw)-len(encoded),
            exact_original_restore_passes=2,aggregate_decoder_limit_seconds=5.0,
            elapsed_decoder_seconds=budget.elapsed,write_rate_bytes_per_second=2097152,
            source_pins=[q.snapshots[x] for x in (SELF,transport.SELF,transport.TEST)]+code["source_pins"],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,
            new_runtime_or_Native_semantic_boundary_connection_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            row["error_code"]=error.args[0]
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"TRANSPORT_PRODUCER_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(row,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:row.get(key) for key in ("state","physical_pin","representation_bytes_saved","fresh_inputs",
        "final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if row["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
