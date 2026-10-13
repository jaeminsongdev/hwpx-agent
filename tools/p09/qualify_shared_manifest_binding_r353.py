"""Whole160 binding with shared159 declaration, unchanged final hashes."""
import ctypes
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
import successor_manifest_shared_admission_v1 as shared
import successor_current_binding_v2 as original
import same_reader_manifest_declaration_once_v1 as declaration
import trace_successor160_binding_reads_r352 as trace

SELF="tools/p09/qualify_shared_manifest_binding_r353.py"
QUAL="implementation/p09/evidence/p09-361-case160-manifest-declaration-code19-r773.v1.json"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))();q=None
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=trace.Reader(a.c.ROOT,g.check)
        pins=[q.pin(path) for path in (shared.SELF,SELF,declaration.SELF,declaration.TEST,
            original.SELF,trace.SELF,pressure.SELF,pressure.TEST)]
        code=q.json(QUAL)
        a.fields(code,dict(state="PASS_MANIFEST_DECLARATION_REUSE_CODE19_NOT_FULL_BINDING_PREFLIGHT_NATIVE_OR_GO",
            contracts=dict(run=19,errors=0,failures=0,skipped=0),cleanup_confirmed=True),
            "QUALIFIED_DECLARATION19_ONLY")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_DECLARATION_CODE19")
        import flat_current_queue_envelope_runtime_v28 as controller
        controller.M.base.configure(160);m=controller.M
        m.own_inputs(q)
        (complete,rust,graph,live,original_proof),proof=shared.bind(q,controller.PRIOR159,original)
        out.update(binding_reads_before_final=trace.summary(q),complete_scope_count=len(complete),
            rust_source_count=len(rust),source_pairs=len(live.descriptors()),shared_declaration_proof=proof)
        q.finish();g.check(force=True)
        out.update(state="PASS_SHARED159_MANIFEST_ACTUAL160_FULL_BINDING_FINAL_FRESH_NOT_CONTROLLER_PREFLIGHT_OR_GO",
            source_pins=pins,original_full_binding_proof=original_proof,
            all_reads_including_final=trace.summary(q),fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        if q is not None:out["observed_reads_at_terminal"]=trace.summary(q)
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
