"""Observe actual cost overflow through unchanged Binding budget guard; no GO."""
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

SELF="tools/p09/diagnose_run002_cost_r358.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_DIAGNOSTIC_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        q.pin(SELF)
        import flat_current_queue_envelope_runtime_v29 as controller
        m=controller.M;m.base.configure(160)
        required,rust=m.binding(q);graph=m.graph_value()
        captured=[]
        def original_cost(physical,requests):
            result=m.prior.DIRECT.runtime_budget(physical,requests)
            captured.append(dict(result))
            return result
        error=None
        try:graph.binding.runtime_budget(required,167,original_cost,q.checkpoint)
        except ValueError as stopped:
            if str(stopped)!="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5":raise
            error=str(stopped)
        a.require(len(captured)==1,"ONE_ORIGINAL_COMPLETE_BUDGET_EVALUATION")
        projection,_=graph.binding.project(required,q.checkpoint)
        candidates=[dict(pin) for name,pin in projection.semantic_pins.items()
            if re.fullmatch(r"implementation/p09/evidence/p09-361-case[0-9]{3}-current-runtime-run[0-9]{3}\.v1\.json",name)
            and name not in graph.binding.originals and int(name.split("case")[1][:3])<160]
        out.update(state="OBSERVED_ORIGINAL_RUN002_COMPLETE_COST_NOT_RUNTIME_OR_GO",
            original_cost=captured[0],shared_decoder_allowance_seconds=5,
            predicted_including_shared_decoder=captured[0]["predicted_runtime_combined_seconds"]+5,
            original_budget_rejection=error,original600_guard_retained=True,
            top_unaliased_prior_runtime_pins=sorted(candidates,key=lambda x:x["bytes"],reverse=True)[:12],
            source_pins=[q.snapshots[SELF],q.snapshots[m.SELF],q.snapshots[m.TEST]],
            actual_semantic_scope_count=len(projection.semantic_pins),
            actual_physical_scope_count=len(projection.physical_pins),rust_source_count=len(rust))
        q.finish();g.check(force=True)
        out.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out["error_type"]=type(error).__name__
        out["safe_frames"]=[dict(file=Path(x.filename).name,function=x.name,line=x.lineno)
            for x in traceback.extract_tb(error.__traceback__)[-12:]]
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,128}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        g.close();out.update(cleanup_confirmed=g.cleanup,metadata_warning=pressure.summary(g),
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None))
    print(json.dumps(out,ensure_ascii=True,allow_nan=False))
    return 0 if out["state"].startswith("OBSERVED_") else 1


if __name__=="__main__":raise SystemExit(main())
