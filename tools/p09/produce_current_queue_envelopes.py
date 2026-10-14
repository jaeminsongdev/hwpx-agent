"""Lossless historical receipt preparation for successors161..249.

The qualified codec and paced exclusive publisher are reused unchanged.
Original inputs, full source scope and product/Native obligations remain.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

SELF="tools/p09/produce_current_queue_envelopes.py"
TEST="tools/p09/tests/test_produce_current_queue_envelopes.py"
CODE="implementation/p09/evidence/p09-361-case158-envelope-physical-code13-r625.v1.json"


def output_path(pin, next_case):
    if type(next_case) is not int or not 161 <= next_case <= 249:
        raise ValueError("CLOSED_SUCCESSOR_ENVELOPE_CONTEXT")
    if type(pin) is not dict or type(pin.get("path")) is not str:
        raise ValueError("ORIGINAL_RECEIPT_PIN")
    match=re.fullmatch(r"implementation/p09/evidence/p09-361-case([0-9]{3})-current-runtime-run([0-9]{3})\.v1\.json",pin["path"])
    if match is None or not 112 <= int(match[1]) < next_case or not 1 <= int(match[2]) <= 999:
        raise ValueError("ONLY_HISTORICAL_RECEIPT")
    return f"implementation/p09/evidence/p361-lossless-runtime-inputs/case{match[1]}-runtime-run{match[2]}.envelope.v1.json"


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True);args=parser.parse_args()
    if not 161 <= args.case <= 249:raise ValueError("CLOSED_SUCCESSOR_INDEX")
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import runtime_envelope_physical_io_v1 as physical
    guard=pressure.guard_type(distinct.guard_type(a.Guard))()
    selection_name=f"implementation/p09/evidence/p09-361-case{args.case}-successor-selection001.v1.json"
    destination=c.ROOT/f"implementation/p09/evidence/p09-361-case{args.case}-lossless-receipts001.v1.json"
    a.require(not destination.exists() and not destination.is_symlink(),"EXCLUSIVE_SUCCESSOR_ENVELOPE_REPORT")
    out=dict(state="FAILED_SUCCESSOR_ENVELOPES_NOT_ADOPTED",accepted_count_delta=0,P09_gate="OPEN",
        product_or_Native_executed=False,GO_authorized=False,original_receipts_rewritten=False,files_created=[])
    q=None
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF);q.pin(TEST)
        selected=q.json(selection_name)
        a.fields(selected,dict(state="PREPARED_EXACT_SUCCESSOR_STEP_AND_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
            accepted_count_delta=0,product_or_Native_executed=False,GO_authorized=False,cleanup_confirmed=True),"ACTUAL_SUCCESSOR_SELECTION")
        a.require(selected["fresh_inputs"] == selected["final_fresh_hashes"] > 0,"COMPLETE_SELECTION_FRESH_READS")
        step=selected["step"]
        a.fields(step,dict(index=args.case,before=args.case-7),"EXACT_SUCCESSOR_CURSOR")
        a.exact(q.pin(selected["step_pin"]["path"]),selected["step_pin"],"IMMUTABLE_SELECTED_STEP")
        for pin in selected["fresh_input_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_SELECTED_INPUTS")
        prior=a.read_exact(q,step["prior_candidate_pin"])
        scope=physical.source.scope.extend(physical.source.scope.pins(prior["source_input_representation"]["semantic_source_freeze"]),
            physical.source.scope.pins([step["prior_candidate_pin"],step["prior_queue_pin"]]))
        code=q.json(CODE)
        a.fields(code,dict(state="PASS_ENVELOPE_PHYSICAL_WRITER_SHARED_DECODER_BOUNDARY_CODE13_NOT_ACTUAL_IO_OR_PRODUCT",
            contracts=dict(run=13,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL_QUALIFIED_CODEC_AND_PUBLISHER")
        for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_CODEC_AND_PUBLISHER")
        originals=selected["selected_originals"]
        a.require(type(originals) is list and len(originals) == 4,"ALL_FOUR_SELECTED_PRIORS")
        pacer=physical.bytes_policy.OwnedPacer();descriptors=[];original_total=encoded_total=0
        for pin in originals:
            a.exact(scope.get(pin["path"]),pin,"ORIGINAL_IN_INDEPENDENT_PREDECESSOR_SCOPE")
            name=output_path(pin,args.case)
            actual,buffer=q._read(pin["path"],parse=True);q._bind(actual["path"],actual)
            a.exact(actual,pin,"EXACT_FRESH_ORIGINAL")
            raw=bytes(buffer);encoded=physical.source.codec.encode(raw,guard.check)
            output=dict(path=name,bytes=len(encoded),sha256=hashlib.sha256(encoded).hexdigest())
            descriptor=physical.source.descriptor(pin,output,next_case=args.case)
            projection=physical.source.Projection({pin["path"]:pin},[descriptor],next_case=args.case,checkpoint=guard.check)
            for _ in range(2):a.exact(projection.decode_fresh(pin["path"],output,encoded,guard.check),raw,"FRESH_EXACT_LOSSLESS_RESTORE")
            if (c.ROOT/name).exists():a.exact(q.fresh_pin(name),output,"EXISTING_DERIVATIVE_ONLY_IF_EXACT")
            else:
                physical.publish_exclusive(c.ROOT,encoded,output,guard.check,write_pacer=pacer);out["files_created"].append(name)
            a.exact(q.fresh_pin(name),output,"ACTUAL_PHYSICAL_DERIVATIVE")
            descriptors.append(descriptor);original_total+=len(raw);encoded_total+=len(encoded)
            del raw,encoded,buffer
        q.finish();guard.check(force=True)
        out.update(state="PREPARED_FOUR_LOSSLESS_SUCCESSOR_RECEIPTS_NOT_ADOPTED_RUNTIME_OR_GO",
            next_case=args.case,authority_pin=step["prior_queue_pin"],prior_runtime_pin=step["prior_candidate_pin"],
            selection_pin=q.snapshots[selection_name],explicit_descriptors=descriptors,
            original_bytes=original_total,encoded_bytes=encoded_total,bytes_saved=original_total-encoded_total,
            decode_passes=8,write_rate_bytes_per_second=pacer.rate,write_bytes_paced=pacer.bytes_paced,
            source_pins=[q.snapshots[SELF],q.snapshots[TEST],*code["source_pins"]],
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    a.require(guard.cleanup,"SUCCESSOR_ENVELOPE_CLEANUP")
    for parent in (destination.parent,*destination.parent.parents):
        a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_REPORT_ANCESTORS")
        if parent == c.ROOT:break
    raw=(json.dumps(out,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
    a.require(0 < len(raw) <= 262144,"BOUNDED_ENVELOPE_REPORT")
    with destination.open("xb") as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    print(json.dumps({k:out.get(k) for k in ("state","original_bytes","encoded_bytes","bytes_saved","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("PREPARED_") else 1


if __name__=="__main__":raise SystemExit(main())
