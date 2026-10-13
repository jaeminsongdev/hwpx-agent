"""Publish one exact partial160 failure envelope with original CODE13 writer."""
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
import traceback
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
import terminal_metadata_pressure_v1 as pressure
import runtime_envelope_physical_io_v1 as physical
import runtime_failed160_partial_projection_v1 as role

SELF="tools/p09/produce_partial160_envelope_r355.py"
ROLE_CODE="implementation/p09/evidence/p09-361-case160-partial-role-code6-r782.v1.json"
WRITER_CODE="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
        original_receipts_rewritten=False,actual_product_or_Native_executed=False,files_created=[])
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (SELF,role.SELF,role.TEST,pressure.SELF,pressure.TEST)]
        proof=q.json(ROLE_CODE)
        a.fields(proof,dict(state="PASS_PARTIAL160_FAILURE_ROLE_CODE6_TWO_MEMORY_DECODES_NOT_REAL_MANIFEST_NATIVE_OR_GO",
            contracts=dict(run=6,errors=0,failures=0,skipped=0),original_failed_runtime_pin=role.ROOT,
            memory_pair_count=25,memory_decode_passes=2,cleanup_confirmed=True),"QUALIFIED_PARTIAL160_ROLE")
        for pin in proof["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_QUALIFIED_ROLE_SOURCES")
        code=q.json(WRITER_CODE)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_WRITER_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_WRITER_CODEC_INPUTS")
        admitted=role.admission(q,a)
        actual,buffer=q._read(role.ROOT["path"],parse=True);q._bind(actual["path"],actual)
        a.exact(actual,role.ROOT,"FRESH_UNMODIFIED_PARTIAL160_ORIGINAL")
        raw=bytes(buffer);encoded=physical.source.codec.encode(raw,q.checkpoint)
        output=dict(path=role.PHYSICAL,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
        a.exact(output,proof["memory_physical_pin"],"SAME_EXACT_ROLE_CODE6_LOSSLESS_BYTES")
        for _ in range(2):a.exact(physical.source.codec.decode(encoded,q.checkpoint),raw,"TWO_LOSSLESS_ORIGINAL_BYTE_DECODES")
        pacer=physical.bytes_policy.OwnedPacer()
        if (a.c.ROOT/role.PHYSICAL).exists():
            a.exact(q.fresh_pin(role.PHYSICAL),output,"EXISTING_FILE_ONLY_IF_EXACT_NO_OVERWRITE")
        else:
            physical.publish_exclusive(a.c.ROOT,encoded,output,q.checkpoint,write_pacer=pacer)
            out["files_created"].append(role.PHYSICAL)
        a.exact(q.fresh_pin(role.PHYSICAL),output,"ACTUAL_PUBLISHED_PHYSICAL_BYTES")
        q.finish();g.check(force=True)
        out.update(state="PASS_EXCLUSIVE_PARTIAL160_FAILURE_ENVELOPE_NOT_CURRENT_RUNTIME_OR_GO",
            original_pin=role.ROOT,physical_pin=output,explicit_failure_admission=admitted,
            original_bytes=len(raw),encoded_bytes=len(encoded),representation_bytes_saved=len(raw)-len(encoded),
            source_pins=pins+proof["source_pins"]+code["source_pins"],
            qualified_role_pin=q.snapshots[ROLE_CODE],writer_code_pin=q.snapshots[WRITER_CODE],
            decode_passes=2,write_rate_bytes_per_second=2097152,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            physical_source_scope_adopted=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
