"""Exact prior-scope selection; no input exclusion, replay or derivative IO."""
import ctypes
import json
from pathlib import Path
import sys

k=ctypes.WinDLL("kernel32",use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
p=k.GetCurrentProcess()
if not (k.SetPriorityClass(p,0x4000) and k.SetProcessAffinityMask(p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qualify_case158_envelope_projection_r323 as launch

SELF="tools/p09/select_prior144to146_envelopes_r339.py"
INDICES=(144,145,146)


def main():
    a=launch.a;g=launch.distinct.guard_type(a.Guard)()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,P09_gate="OPEN",
             actual_Native_product_or_acceptance_executed=False,input_scope_reduced=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        authority=a.read_exact(q,launch.review.AUTHORITY_PIN)
        a.fields(authority,dict(accepted_count_after=151,next_runtime_index=158),"CURRENT_AUTHORITY151")
        prior=a.read_exact(q,launch.review.ROOT_PIN)
        scope=a.scope.pins(prior["source_freeze"])
        selected=[]
        for index in INDICES:
            path=f"implementation/p09/evidence/p09-361-case{index}-current-runtime-run001.v1.json"
            a.require(path in scope,"ORIGINAL_PRIOR_WHOLE_SCOPE_INCLUDES_RECEIPT")
            pin=scope[path];a.exact(q.pin(path),pin,"CURRENT_EXACT_PRIOR_RECEIPT_BYTES")
            selected.append(pin)
        q.finish();g.check(force=True)
        out.update(state="PASS_EXACT_THREE_EXTRA_RECEIPT_SIZE_SELECTION_NOT_DERIVATIVES_OR_NATIVE",
                   top_additional_candidates=selected,selected_indices=list(INDICES),
                   prior_whole_scope_pin=launch.review.ROOT_PIN,authority151_pin=launch.review.AUTHORITY_PIN,
                   source_pins=[q.snapshots[SELF]],fresh_inputs=len(q.snapshots),
                   final_fresh_hashes=q.final_fresh_hashes,
                   CPU_max=max(s["system_cpu_percent"] for s in g.samples),
                   RAM_min=min(s["available_ram_percent"] for s in g.samples))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        if isinstance(error,ValueError):
            import re
            value=str(error);out["error_code"]=value if re.fullmatch("[A-Za-z0-9_]{1,256}",value) else "REDACTED_PRIOR_RECEIPT_SELECTION_FAILURE"
    finally:g.close();out["cleanup_confirmed"]=g.cleanup
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
