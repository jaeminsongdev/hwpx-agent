"""Known-cost lower bound for the current immutable expanded representation.

Read-only model audit, not full source-byte verification or entry/Native PASS.
Do not launch an inevitably over-budget qualifier or change any limit.
"""
from pathlib import Path
import sys

SELF="tools/p09/check_expanded_entry_cost_floor_v1.py"
OLD=dict(path="tools/p09/case160_run007_controller.py",bytes=10968,
    sha256="98eca8fcce39c906a1459fac0bbf3d344f8bed3c47816d5d8a0aeddc8b8f4826")
UTILS=[
    dict(path="tools/p09/successor_preparation_workspace_v1.py",bytes=9656,sha256="003a0978b515c148d1a7f17ba53cdcab9eb77698535714216c90b53c868bbb98"),
    dict(path="tools/p09/terminal_metadata_pressure_v1.py",bytes=2956,sha256="7b5bb9b890cde566f566857c06f010736519ac6e2551480dcf92bdab6dfdd9dd"),
    dict(path="tools/p09/distinct_final_sample_guard_v1.py",bytes=1683,sha256="8c590aa82c2677d391d6d5781b356641f77c7cdc6e55370ca251d6a809ad67c3")]


def main():
    import argparse,json,math,time
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    import accept_case112_current_epoch as a
    import current_stored_runtime_scope as scope
    import flat_current_queue_envelope_runtime_v25 as envelope
    parser=argparse.ArgumentParser()
    for name in ("case","run","preflight-attempt","attempt"):parser.add_argument("--"+name,type=int,required=True)
    args=parser.parse_args();a.require(165<=args.case<=249 and 4<=args.run<=8 and all(1<=v<=8 for v in (args.preflight_attempt,args.attempt)),"CLOSED_COST_FLOOR_CONTEXT")
    prefix=f"implementation/p09/evidence/p09-361-case{args.case}-"
    pref_name=prefix+f"successor-preflight-run{args.run:03}-attempt{args.preflight_attempt:03}.v1.json"
    output=prefix+f"expanded-entry-cost-floor{args.attempt:03}.v1.json"
    a.require(not (c.ROOT/output).exists(),"EXCLUSIVE_COST_FLOOR_REPORT")
    utilities,_=envelope.namespace_bundle.load(c.ROOT,UTILS,{})
    guard=utilities.terminal_metadata_pressure_v1.guard_type(utilities.distinct_final_sample_guard_v1.guard_type(a.Guard))()
    started=time.monotonic();row=dict(state="FAILED_EXPANDED_ENTRY_COST_FLOOR_AUDIT",product_or_Native_executed=False,accepted_count_delta=0,
        whole_current_source_byte_inventory_rechecked=False,current_qualification_NOT_RUN=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        for pin in UTILS+[OLD]:a.exact(q.pin(pin["path"]),pin,"EXACT_FROZEN_COST_ENGINE_AND_GUARDS")
        pref=q.json(pref_name)
        a.fields(pref,dict(state="PASS_CURRENT_SUCCESSOR_WHOLE_METADATA_PREFLIGHT_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE",
            index=args.case,physical_run=args.run,original_preflight_contracts=10,Rust_inputs=787,cleanup_confirmed=True),"SEALED_WHOLE_PREFLIGHT")
        a.require(pref["fresh_inputs"]==pref["final_fresh_hashes"]>0,"PREFLIGHT_FINAL_HASHES")
        for pin in pref["current_source_pins"]:
            if pin["path"].startswith("tools/p09/") and pin["path"].endswith(".py"):
                a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_MODEL_PROGRAM_SOURCES")
        physical=scope.pins(pref["complete_physical_source_scope"])
        a.require(pref_name not in physical,"PREFLIGHT_RESULT_NOT_ALREADY_IN_BASE_SCOPE")
        known=scope.extend(physical,{pref_name:q.snapshots[pref_name]})
        source,_=envelope.namespace_bundle.load(c.ROOT,[OLD],{"flat_current_queue_envelope_runtime_v25":envelope})
        budget=source.case160_run007_controller.old.prior.DIRECT.runtime_budget
        requests=pref["whole_Rust_inventory"]["requests"]
        before=budget(physical,requests);minimum=budget(known,requests)
        a.exact(before["predicted_runtime_combined_seconds"]+5.0,pref["complete_runtime_budget"]["predicted_runtime_combined_seconds"],"EXACT_QUALIFIED_BASE_MODEL_REPRODUCED")
        a.fields(minimum,dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60),"ORIGINAL_COST_LIMITS")
        floor=minimum["predicted_runtime_combined_seconds"]+5.0
        a.require(type(floor) is float and math.isfinite(floor),"FINITE_SHARED_DECODER_COST_FLOOR")
        q.finish();guard.check(force=True)
        row.update(state="DEFERRED_CURRENT_EXPANDED_ENTRY_KNOWN_COST_FLOOR_NO_NATIVE" if floor>=600 else "PASS_KNOWN_COST_FLOOR_ONLY_NOT_ENTRY_QUALIFICATION",
            preflight_pin=q.snapshots[pref_name],base_inputs=len(physical),minimum_known_inputs=len(known),
            preflight_result_bytes=q.snapshots[pref_name]["bytes"],base_cost_seconds=before["predicted_runtime_combined_seconds"]+5.0,
            minimum_known_cost_seconds=floor,unchanged_deadline_seconds=600,shared_decoder_seconds=5.0,
            qualification_receipt_and_other_future_inputs_not_yet_added=True,
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        import re
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):row["error_code"]=error.args[0]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in guard.samples),default=None),RAM_min=min((s["available_ram_percent"] for s in guard.samples),default=None))
    a.require(guard.cleanup,"COST_FLOOR_CLEANUP");utilities.successor_preparation_workspace_v1.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ("state","base_cost_seconds","minimum_known_cost_seconds","base_inputs","minimum_known_inputs",
        "fresh_inputs","final_fresh_hashes","elapsed_seconds","CPU_max","RAM_min","cleanup_confirmed","error_code")}))
    return 0 if not row["state"].startswith("FAILED_") else 1


if __name__=="__main__":raise SystemExit(main())
