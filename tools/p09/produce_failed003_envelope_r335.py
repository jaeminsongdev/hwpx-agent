"""Publish a new exact failed003 derivative, never rewrite the failure root."""
import ctypes
import hashlib
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
import runtime_failed_receipt_projection_v1 as failed
import runtime_envelope_namespace_bundle_v1 as bundle
import runtime_envelope_physical_io_v1 as physical_io
import current_stored_runtime_scope as scope

SELF="tools/p09/produce_failed003_envelope_r335.py"
CODE="implementation/p09/evidence/p09-361-case158-failed003-role-projection-code9-r691.v1.json"


def main():
    g=distinct.guard_type(a.Guard)();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",actual_product_or_Native_executed=False,
        original_receipts_rewritten=False,current_physical_source_scope_adopted=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        code=q.json(CODE)
        a.fields(code,dict(state="PASS_EXACT_FAILED003_ROLE_CODE9_AND_TWO_MEMORY_PROJECTION_DECODES_NOT_CURRENT_RUNTIME_OR_GO",
            contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"CODE9_ONLY")
        for p in code["new_code_pins"]+code["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_ROLE_SOURCE_BYTES")
        admitted=failed.admission(q,a)
        class_pins=[p for p in code["source_pins"] if p["path"] in (
            "tools/p09/runtime_record_envelope_v1.py","tools/p09/runtime_record_envelope_v2.py",
            "tools/p09/runtime_envelope_source_projection_v1.py","tools/p09/runtime_envelope_scope_binding_v1.py")]
        a.require(len(class_pins)==4,"ALL_FOUR_PRIVATE_SOURCE_CLASSES")
        graph,_=bundle.load(a.c.ROOT,class_pins,{"current_stored_runtime_scope":scope})
        source=graph.runtime_envelope_source_projection_v1;binding=graph.runtime_envelope_scope_binding_v1
        failed.connect(source,binding,admitted)
        pin,raw=q._read(failed.ROOT["path"],parse=True);q._bind(pin["path"],pin);a.exact(pin,failed.ROOT,"ORIGINAL_FAILED003")
        encoded=source.codec.encode(bytes(raw),g.check)
        produced=dict(path=failed.PHYSICAL,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        a.exact(produced,code["memory_candidate"]["physical_pin"],"SAME_QUALIFIED_MEMORY_FORMAT")
        desc=source.descriptor(failed.ROOT,produced,next_case=158)
        for _ in range(2):a.exact(source.codec.decode(encoded,g.check),bytes(raw),"LOSSLESS_ORIGINAL_FAILURE")
        for name in (SELF,physical_io.SELF,physical_io.TEST):q.pin(name)
        write=physical_io.publish_exclusive(a.c.ROOT,encoded,produced,g.check)
        a.exact(q.fresh_pin(write["path"]),produced,"ACTUAL_EXCLUSIVE_DERIVATIVE_BYTES")
        q.finish();g.check(force=True)
        out.update(state="PASS_EXCLUSIVE_FAILED003_LOSSLESS_DERIVATIVE_NOT_CURRENT_RUNTIME_OR_GO",
            original_pin=failed.ROOT,physical_pin=produced,descriptor=desc,explicit_failure_admission=admitted,
            exact_original_failure_retained=True,decode_passes=2,write_rate_bytes_per_second=2097152,
            source_pins=[q.snapshots[SELF],q.snapshots[physical_io.SELF],q.snapshots[physical_io.TEST]],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            CPU_max=max(s["system_cpu_percent"] for s in g.samples),RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            code=str(error);out["error_code"]=code if re.fullmatch("[A-Za-z0-9_]{1,256}",code) else "REDACTED_FAILED_DERIVATIVE_PRODUCER"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False));return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
