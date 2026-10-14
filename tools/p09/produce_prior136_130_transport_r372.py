"""Two exact unaliased priors from the actual full scope; never product replay."""
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
import time
SELF="tools/p09/produce_prior136_130_transport_r372.py"
OUTPUT="implementation/p09/evidence/p09-361-case160-prior136130-producer-r854.v1.json"
PREPARED=dict(path="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json",bytes=2693611,
    sha256="73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233")
PRIORS=(dict(path="implementation/p09/evidence/p09-361-case136-current-runtime-run001.v1.json",bytes=2461083,
    sha256="b1a7b13d76de8946340dca11e21dcf7480c17a8999117b08102138aaba8d4043"),
    dict(path="implementation/p09/evidence/p09-361-case130-current-runtime-run001.v1.json",bytes=2417619,
    sha256="4596a1972a5f5e0cfa1160d9672ce3d01c6feaef7e62cf83d800317eef351a26"))
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
    destination=a.c.ROOT/OUTPUT;a.require(not destination.exists(),"PRIORS_EXCLUSIVE_REPORT")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();started=time.monotonic()
    out=dict(state="FAILED_PRIORS_NOT_ACCEPTED",accepted_count_delta=0,original_receipts_rewritten=False,
        product_or_Native_reexecuted=False,GO_authorized=False,files_created=[])
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        prepared=a.read_exact(q,PREPARED)
        a.fields(prepared,dict(state="PREPARED_FULL_METADATA_CHECKPOINT_NOT_RUNTIME_OR_GO",
            fresh_inputs=1145,final_fresh_hashes=1145,cleanup_confirmed=True),"ACTUAL_COMPLETE_SCOPE")
        scope=a.scope.pins(prepared["checkpoint"]["complete_scope"])
        old_aliases={d["semantic_original_pin"]["path"] for d in prepared["checkpoint"]["representation"]["descriptors"]}
        code=q.json(WRITER)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_CODE13")
        for p in code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_CODEC_WRITER")
        published=[];budget=physical.DecoderBudget(q.checkpoint)
        for original in PRIORS:
            a.exact(scope.get(original["path"]),original,"SELECTED_PRIOR_IN_REAL_SCOPE")
            a.require(original["path"] not in old_aliases,"ONLY_REAL_UNALIASED_PRIOR")
            actual,buffer=q._read(original["path"],parse=True);q._bind(actual["path"],actual)
            a.exact(actual,original,"EXACT_UNMODIFIED_PRIOR_BYTES")
            raw=bytes(buffer);encoded=physical.source.codec.encode(raw,q.checkpoint)
            number="136" if original==PRIORS[0] else "130"
            target=dict(path=physical.source.PREFIX+"case"+number+"-runtime-run001.envelope.v1.json",
                bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            descriptor=physical.source.descriptor(original,target,next_case=160)
            for _ in range(2):a.exact(budget.run(lambda check:physical.source.codec.decode(encoded,check)),raw,"ALL_ORIGINAL_BYTES_RESTORED")
            physical.publish_exclusive(a.c.ROOT,encoded,target,q.checkpoint);out["files_created"].append(target["path"])
            a.exact(q.fresh_pin(target["path"]),target,"ACTUAL_EXCLUSIVE_PRIOR")
            published.append(dict(original_pin=original,physical_pin=target,descriptor=descriptor,bytes_saved=len(raw)-len(encoded)))
        q.finish();g.check(force=True)
        out.update(state="PASS_REAL_PRIOR136130_EXCLUSIVE_LOSSLESS_NOT_ADOPTED_MANIFEST_OR_GO",
            selected_outputs=published,prepared_scope_pin=PREPARED,exact_original_restore_passes=4,
            representation_bytes_saved=sum(p["bytes_saved"] for p in published),write_rate_bytes_per_second=2097152,
            elapsed_decoder_seconds=budget.elapsed,source_pins=[q.snapshots[SELF]]+code["source_pins"],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    a.require(g.cleanup,"PRIORS_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(out,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:out.get(key) for key in ("state","selected_outputs","representation_bytes_saved","fresh_inputs",
        "final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")},allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
