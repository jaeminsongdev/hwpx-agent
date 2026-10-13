"""Exclusive case131 lossless derivative for current160 cost, not a test replay."""
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
import runtime_successor_binding_v2 as successor

SELF="tools/p09/produce_cost_selected_three_r363.py"
DIAGNOSTIC="implementation/p09/evidence/p09-361-case160-run002-complete-cost-observation-r799.v1.json"
WRITER="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"


def main():
    g=pressure.guard_type(distinct.guard_type(a.Guard))()
    out=dict(state="FAILED_NOT_ACCEPTED",accepted_count_delta=0,actual_product_or_Native_executed=False,
        original_receipts_rewritten=False,files_created=[],P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check);q.pin(SELF)
        observed=q.json(DIAGNOSTIC)
        a.fields(observed,dict(state="OBSERVED_ORIGINAL_RUN002_COMPLETE_COST_NOT_RUNTIME_OR_GO",
            original_budget_rejection="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5",
            original600_guard_retained=True,cleanup_confirmed=True,accepted_count_delta=0),"EXACT_COST_OVERFLOW_DIAGNOSTIC")
        a.require(observed["fresh_inputs"]==observed["final_fresh_hashes"]>0,"ALL_DIAGNOSTIC_FINAL_HASHES")
        for pin in observed["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_DIAGNOSTIC_SOURCES")
        selected_rows=observed["top_unaliased_prior_runtime_pins"][1:4]
        a.exact([p["path"] for p in selected_rows],["implementation/p09/evidence/p09-361-case%03d-current-runtime-run001.v1.json"%i for i in (133,138,137)],"EXACT_MEASURED_THREE_UNALIASED_PRIORS")
        authority=a.read_exact(q,successor.AUTHORITY)
        a.fields(authority,dict(accepted_count_after=153,next_runtime_index=160,runtime_candidate_pin=successor.ROOT),
            "UNCHANGED_AUTHORITY153")
        prior=a.read_exact(q,successor.ROOT)
        scope=physical.source.scope.pins(prior["source_input_representation"]["semantic_source_freeze"])
        for selected in selected_rows:a.exact(scope.get(selected["path"]),selected,"SELECTED_ORIGINAL_IN_REAL_PRIOR159_WHOLE_SCOPE")
        code=q.json(WRITER)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_WRITER_CODE13")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_ORIGINAL_CODEC_WRITER")
        published=[]
        for selected in selected_rows:
            actual,buffer=q._read(selected["path"],parse=True);q._bind(actual["path"],actual)
            a.exact(actual,selected,"EXACT_CURRENT_ORIGINAL131")
            raw=bytes(buffer);encoded=physical.source.codec.encode(raw,q.checkpoint)
            output=dict(path=physical.source.PREFIX+Path(selected["path"]).name.replace("p09-361-","").replace("current-","").replace(".v1.json",".envelope.v1.json"),
                bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            desc=physical.source.descriptor(selected,output,next_case=160)
            projection=physical.source.Projection({selected["path"]:selected},[desc],next_case=160,checkpoint=q.checkpoint)
            for _ in range(2):a.exact(projection.decode_fresh(selected["path"],output,encoded,q.checkpoint),raw,"TWO_EXACT_ORIGINAL131_DECODES")
            pacer=physical.bytes_policy.OwnedPacer()
            if (a.c.ROOT/output["path"]).exists():a.exact(q.fresh_pin(output["path"]),output,"EXISTING_EXACT_DERIVATIVE_ONLY")
            else:
                physical.publish_exclusive(a.c.ROOT,encoded,output,q.checkpoint,write_pacer=pacer)
                out["files_created"].append(output["path"])
            a.exact(q.fresh_pin(output["path"]),output,"ACTUAL_EXCLUSIVE_LOSSLESS131")
            published.append(dict(original_pin=selected,physical_pin=output,descriptor=desc,representation_bytes_saved=len(raw)-len(encoded)))
        q.finish();g.check(force=True)
        out.update(state="PASS_COST_SELECTED_THREE_EXCLUSIVE_LOSSLESS_DERIVATIVES_NOT_ADOPTED_CURRENT_RUNTIME_OR_GO",
            selected_outputs=published,source_pair_count=3,
            representation_bytes_saved=sum(p["representation_bytes_saved"] for p in published),
            diagnostic_pin=q.snapshots[DIAGNOSTIC],authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT,
            source_pins=[q.snapshots[SELF],*observed["source_pins"],*code["source_pins"]],
            decode_passes=6,write_rate_bytes_per_second=2097152,
            current_scope_cost_after_adoption_qualified=False,fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes)
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
