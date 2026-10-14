"""Actual lossless checkpoint loading, full declaration and original cost test."""
import ctypes
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import unittest

SELF="tools/p09/qualify_prepared_checkpoint_transport_r368.py"
OUTPUT="implementation/p09/evidence/p09-361-prepared-checkpoint-transport-code58-r840.v1.json"
SEMANTIC=dict(path="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json",
    bytes=2693611,sha256="73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233")
PHYSICAL=dict(path="implementation/p09/evidence/p361-lossless-runtime-inputs/case160-prepared-r834.envelope.v1.json",
    bytes=973539,sha256="499ee01169ea94b7fbb5ddab8ac95f3160cc55215fff26d7bd3093d5c086b394")
PRODUCER="implementation/p09/evidence/p09-361-prepared-checkpoint-transport-producer-r839.v1.json"

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not (k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):
        raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import prepared_checkpoint_transport_v1 as transport
    import prepared_scope_handoff_v1 as handoff
    import prepared_input_checkpoint_v1 as prepared
    import preparation_terminal_progress_v1 as progress
    destination=a.c.ROOT/OUTPUT
    a.require(not destination.exists() and not destination.is_symlink(),"TRANSPORT_QUAL_REFUSE_OVERWRITE")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();q=None;started=time.monotonic()
    row=dict(state="FAILED_TRANSPORT_QUALIFICATION_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,runtime_handoff_connected=False,P09_gate="OPEN")
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        source_paths=(SELF,transport.SELF,transport.TEST,handoff.SELF,handoff.TEST,
            prepared.SELF,prepared.TEST,progress.SELF,progress.TEST)
        for path in source_paths:q.pin(path)
        suites=("test_prepared_checkpoint_transport_v1","test_prepared_scope_handoff_v1",
            "test_prepared_input_checkpoint_v1","test_preparation_terminal_progress_v1")
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName("tools.p09.tests."+name) for name in suites)
        result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(result.wasSuccessful() and result.testsRun==58 and not result.skipped,"ALL_CODE58_CONTRACTS")
        producer=q.json(PRODUCER)
        a.fields(producer,dict(state="PASS_EXCLUSIVE_PREPARED_CHECKPOINT_TRANSPORT_NOT_RUNTIME_OR_GO",
            original_pin=SEMANTIC,physical_pin=PHYSICAL,exact_original_restore_passes=2,
            cleanup_confirmed=True,Native_or_product_executed=False,GO_authorized=False),"EXACT_ACTUAL_PRODUCER")
        a.require(producer["fresh_inputs"]==producer["final_fresh_hashes"]>0,"ALL_PRODUCER_FINAL_HASHES")
        for pin in producer["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CODEC_AND_PRODUCER_SOURCES")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160)
        graph,bootstrap=c.bootstrap.load(c.old,q.checkpoint)
        for pin in bootstrap["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_BOUNDED_GRAPH_SOURCE")
        listing=a.read_exact(q,a.scope.LIST_PIN);rust=handoff.rust_inputs(a.scope.listing_inputs(listing))
        a.require(len(rust)==787,"COMPILED_RUST787")
        producer_sources=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",prepared.SELF,prepared.TEST,
            progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,distinct.SELF,distinct.TEST))
        successor=c._env["current_binding"].successor
        required,declared_rust,proof=transport.load(q,SEMANTIC,PHYSICAL,graph.binding,
            expected_context=dict(index=160,before=153,physical_product_run=3),
            expected_current_pins=dict(data_pin=q.pin(c.DATA),preflight_pin=q.pin(c.PREFLIGHT),
                authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT),
            expected_rust=rust,expected_source_paths=producer_sources)
        a.require(SEMANTIC["path"] not in q.snapshots,"NO_FABRICATED_RAW_DISK_READ")
        for path in producer_sources:a.exact(q.pin(path),required[path],"UNCHANGED_ORIGINAL_PREPARATION_SOURCES")
        enumerator="tools/p09/current_issuer_build_inputs.py"
        text=q.text(enumerator);a.exact(q.snapshots[enumerator],required[enumerator],"ORIGINAL_RUST_ENUMERATOR")
        inventory=a.native.definitions(text,("rust_inputs",),dict(os=os,Path=Path,require=a.require))
        opener=a.locks.OpenPacer(q.checkpoint,rate=20)
        a.require(frozenset(inventory.rust_inputs(a.c.ROOT,opener.reserve))==declared_rust,"ACTUAL_CURRENT_RUST_INVENTORY")
        complete=c.M.base.scope.extend(required,q.snapshots)
        projection,_=graph.binding.project(complete,q.checkpoint)
        physical={n:dict(p) for n,p in projection.physical_pins.items()}
        original=c.old.prior.DIRECT.runtime_budget(physical,opener.opens)
        row["unchanged_Native_cost_observation"]=dict(
            predicted_runtime_combined_seconds_including_decoder5=original["predicted_runtime_combined_seconds"]+5.0,
            unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
            actual_runtime_completion_qualified=False,producer_qualifier_inputs_differ_from_future_runtime=True)
        try:
            budget=graph.binding.runtime_budget(complete,opener.opens,c.old.prior.DIRECT.runtime_budget,q.checkpoint)
            row["unchanged_Native_cost_observation"].update(original_budget_accepts=True,budget=budget)
        except ValueError as error:
            a.require(error.args and error.args[0]=="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5",
                "ONLY_ORIGINAL_COST_REJECTION_RECORDED")
            row["unchanged_Native_cost_observation"].update(original_budget_accepts=False,error_code=error.args[0])
        q.finish();g.check(force=True)
        row.update(state="PASS_ACTUAL_PREPARED_CHECKPOINT_TRANSPORT_CODE58_NOT_NATIVE_RUNTIME_BUDGET_OR_GO",
            contracts=dict(run=58,errors=0,failures=0,skipped=0),semantic_original_pin=SEMANTIC,physical_pin=PHYSICAL,
            source_pins=[q.snapshots[x] for x in source_paths],producer_source_pins=producer["source_pins"],
            current_Rust_input_count=len(rust),actual_Rust_inventory_requests=opener.opens,source_pairs=29,
            original_bounded_bootstrap=bootstrap,reconstructed_scope_count=len(required),
            required_scope_with_qualifier_inputs=len(complete),physical_scope_count=len(physical),
            transport_declaration_proof=proof,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,
            original_raw_checkpoint_reported_as_read_here=False,all_source_scope_fresh_read_here=False,
            actual_Native_semantic_relation_and_independent_runtime_oracle_required=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row["error_type"]=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch("[A-Za-z_][A-Za-z0-9_]{1,160}",error.args[0]):
            row["error_code"]=error.args[0]
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s["system_cpu_percent"] for s in g.samples),default=None),
            RAM_min=min((s["available_ram_percent"] for s in g.samples),default=None),
            parent_CPU_max=max((s["parent_cpu_machine_percent"] for s in g.samples
                if s.get("parent_cpu_machine_percent") is not None),default=None),
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None))
    a.require(g.cleanup,"TRANSPORT_QUAL_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(row,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps({key:row.get(key) for key in ("state","error_code","fresh_inputs","final_fresh_hashes",
        "unchanged_Native_cost_observation","CPU_max","RAM_min","cleanup_confirmed")},allow_nan=False))
    return 0 if row["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
