"""Actual26 bootstrap/full Binding and original600 cost, not whole preflight."""
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
import successor_current_binding_v4 as binding
import successor_bounded_graph_bootstrap_v4 as bootstrap

SELF="tools/p09/qualify_adopted26_binding_cost_r359.py"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,Native_or_product_executed=False,
        new_controller_DATA_whole_preflight_qualified=False,queue_acceptance_called=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        paths=(SELF,binding.SELF,binding.original.SELF,bootstrap.SELF,bootstrap.original.SELF,
            binding.manifest.SELF,binding.capsule.SELF,binding.factory.SELF,pressure.SELF,pressure.TEST)
        pins=[q.pin(path) for path in paths]
        import flat_current_queue_envelope_runtime_v29 as controller
        m=controller.M;m.base.configure(160)
        m.own_inputs(q)
        graph,small=bootstrap.load(m.old,q.checkpoint)
        complete,rust,fresh,live,proof=binding.bind(q,controller.PRIOR160.PRIOR159)
        a.exact(live.descriptors(),graph.binding.descriptors(),"ACTUAL26_FULL_BINDING_AND_BOOTSTRAP")
        a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"SAME_ACTUAL_MANIFEST027")
        projection,_=live.project(complete,q.checkpoint)
        represented=live.representation(projection)
        a.exact(represented["same_case_failed160_partial_receipt_provenance"],fresh.partial_admission,
            "UNCHANGED_FAILED160_PROVENANCE")
        cost=live.runtime_budget(complete,167,m.prior.DIRECT.runtime_budget,q.checkpoint)
        a.require(cost["predicted_runtime_combined_seconds"]<600 and
            cost["unallocated_margin_seconds"]==60 and cost["aggregate_envelope_decoder_allowance_seconds"]==5,
            "WHOLE_ADOPTED_SCOPE_ORIGINAL600_MARGIN60_DECODER5")
        q.finish();g.check(force=True)
        out.update(state="PASS_ADOPTED26_BOOTSTRAP_WHOLE_BINDING_AND_ORIGINAL600_COST_NOT_NEW_CONTROLLER_PREFLIGHT_OR_GO",
            source_pins=pins,manifest_pin=dict(live.manifest_pin),source_pairs=26,rust_source_count=len(rust),
            complete_scope_count=len(complete),bounded_bootstrap=small,original_binding_proof=proof,
            complete_adopted_scope_cost=cost,new_DATA_and_preflight_receipt_not_yet_included=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
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
    return 0 if out["state"].startswith("PASS_") else 1


if __name__=="__main__":raise SystemExit(main())
