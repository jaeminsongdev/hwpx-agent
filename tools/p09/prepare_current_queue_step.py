"""Prepare an immutable successor STEP from an accepted predecessor.

Metadata only: no product, Native frame, queue writer or Gate advancement.
One parameterized implementation serves successors161..249 without clones.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys

SELF = "tools/p09/prepare_current_queue_step.py"
TEST = "tools/p09/tests/test_prepare_current_queue_step.py"


def derive_step(index, authority_pin, authority, prior, names):
    def require(value, code):
        if not value: raise ValueError("NEXT_STEP_"+code)
    require(type(index) is int and 161 <= index <= 249, "CLOSED_INDEX")
    require(type(names) is list and len(names) == 249 and names == sorted(set(names))
        and all(type(n) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_:]*", n) for n in names), "COMPILED249_NAMES")
    require(type(authority_pin) is dict and authority_pin.get("path") ==
        f"implementation/p09/evidence/p09-361-case{index-1}-current-epoch-accept001.v1.json", "EXACT_PREDECESSOR_PATH")
    require(authority["state"] == "PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE"
        and type(authority["accepted_count_after"]) is int and authority["accepted_count_after"] == index-7
        and authority["next_runtime_index"] == index and authority["accepted_count_delta"] == 1
        and authority["accepted_test_indices"] == [index-1] and authority["resource_cleanup_confirmed"] is True
        and authority["P09_gate"] == "OPEN" and authority["full249_current_qualified"] is False
        and authority["signed16_current_qualified"] is False and authority["P10_started"] is False,
        "ACCEPTED_PREDECESSOR_NOT_CANDIDATE")
    require(prior["state"] == "PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE"
        and prior["selected_test_index"] == index-1 and prior["cleanup_confirmed"] is True
        and prior["owned_tree_empty"] is True and prior["Native_source_frame_qualified"] is True
        and prior["current_generation_runtime_candidate_qualified"] is True
        and prior["source_frame"]["frame_state"] == "COMMITTED"
        and len(prior["source_frame"]["actual_byte_boundaries"]) == 2, "ACTUAL_COMMITTED_PREDECESSOR")
    require(prior["selected_test_names"] == [names[index-2]], "EXACT_PREDECESSOR_COMPILED_NAME")
    return dict(schema_version="hwpx-agent.p09-flat-current-queue-step/v1", index=index, before=index-7,
        case=names[index-1], prior_queue_pin=authority_pin, prior_candidate_pin=authority["runtime_candidate_pin"])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--case", type=int, required=True)
    parser.add_argument("--authority-bytes", type=int, required=True)
    parser.add_argument("--authority-sha256", required=True)
    args=parser.parse_args()
    if not 161 <= args.case <= 249 or not re.fullmatch(r"[0-9a-f]{64}", args.authority_sha256):
        raise ValueError("CLOSED_CURRENT_STEP_ARGUMENTS")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import flat_current_queue_runtime as runtime
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    guard=pressure.guard_type(distinct.guard_type(a.Guard))()
    authority_pin=dict(path=f"implementation/p09/evidence/p09-361-case{args.case-1}-current-epoch-accept001.v1.json",
        bytes=args.authority_bytes, sha256=args.authority_sha256)
    step_name=runtime.config_path(args.case)
    report_name=f"implementation/p09/evidence/p09-361-case{args.case}-successor-selection001.v1.json"
    for name in (step_name, report_name):
        a.require(not (c.ROOT/name).exists(), "NO_STEP_OR_REPORT_OVERWRITE")
    out=dict(state="FAILED_SUCCESSOR_PREPARATION_NOT_ACCEPTED", accepted_count_delta=0,
        product_or_Native_executed=False, GO_authorized=False, P09_gate="OPEN")
    q=None; step=None
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT, guard.check)
        q.pin(SELF);q.pin(TEST);q.pin(runtime.SELF)
        authority=a.read_exact(q, authority_pin)
        prior_pin=authority["runtime_candidate_pin"]
        prior=a.read_exact(q, prior_pin)
        listing=a.read_exact(q, a.scope.LIST_PIN)
        step=derive_step(args.case, authority_pin, authority, prior, listing["source_test_names"])
        runtime.validate_config(step, args.case)
        representation=prior["source_input_representation"]
        semantic=a.scope.pins(representation["semantic_source_freeze"])
        mapped={row["semantic_original_pin"]["path"] for row in representation["descriptors"]}
        candidates=sorted((pin for name,pin in semantic.items() if name not in mapped and
            re.fullmatch(r"implementation/p09/evidence/p09-361-case[0-9]{3}-current-runtime-run[0-9]{3}\.v1\.json", name)),
            key=lambda pin:(-pin["bytes"],pin["path"]))[:3]
        a.require(len(candidates) == 3, "ALL_THREE_UNMAPPED_PRIORS")
        for pin in candidates:a.exact(q.pin(pin["path"]),pin,"CURRENT_SELECTED_ORIGINAL")
        q.finish();guard.check(force=True)
        out.update(state="PREPARED_EXACT_SUCCESSOR_STEP_AND_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO",
            step=step, selected_originals=candidates+[prior_pin], old_pair_count=len(mapped),
            old_manifest_pin=representation["manifest_pin"], compiled_listing_pin=a.scope.LIST_PIN,
            fresh_input_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            out["error_code"]=error.args[0]
    finally:
        guard.close();out.update(cleanup_confirmed=guard.cleanup,
            CPU_max=max((r["system_cpu_percent"] for r in guard.samples),default=None),
            RAM_min=min((r["available_ram_percent"] for r in guard.samples),default=None))
    a.require(guard.cleanup,"STEP_PREPARATION_CLEANUP")
    def publish(name, value):
        path=c.ROOT/name
        for parent in (path.parent,*path.parent.parents):
            a.require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(),"DIRECT_STEP_ANCESTORS")
            if parent == c.ROOT:break
        raw=(json.dumps(value,ensure_ascii=True,allow_nan=False,indent=2)+"\n").encode("utf-8")
        a.require(0 < len(raw) <= 262144,"BOUNDED_STEP_PUBLICATION")
        with path.open("xb") as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        return dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    if out["state"].startswith("PREPARED_"):out["step_pin"]=publish(step_name,step)
    publish(report_name,out)
    print(json.dumps({k:out.get(k) for k in ("state","step_pin","old_pair_count","fresh_inputs","final_fresh_hashes","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if out["state"].startswith("PREPARED_") else 1


if __name__=="__main__":raise SystemExit(main())
