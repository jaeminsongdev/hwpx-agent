"""Actual full prepared declaration and unchanged Native cost observation.

원 전체 준비를 다시 실행하지 않고 저장된 결과의 scope를 재구성한다.
실제 Native 두 읽기·제품 oracle·GO 연결은 별도 조건으로 남긴다.
"""
import ctypes
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import unittest

SELF="tools/p09/qualify_prepared_scope_handoff_r367.py"
OUTPUT="implementation/p09/evidence/p09-361-prepared-scope-handoff-code46-r836.v1.json"
CHECKPOINT=dict(path="implementation/p09/evidence/p09-361-case160-prepared-input-checkpoint-r834.v1.json",
    bytes=2693611,sha256="73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233")

def main():
    k=ctypes.WinDLL("kernel32",use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
    k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
    k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
    handle=k.GetCurrentProcess()
    if not (k.SetPriorityClass(handle,0x4000) and k.SetProcessAffinityMask(handle,1)):
        raise ValueError("LOCAL_LIMITS_NOT_APPLIED")
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import accept_case112_current_epoch as a
    import distinct_final_sample_guard_v1 as distinct
    import terminal_metadata_pressure_v1 as pressure
    import prepared_scope_handoff_v1 as handoff
    import prepared_input_checkpoint_v1 as prepared
    import preparation_terminal_progress_v1 as progress
    destination=a.c.ROOT/OUTPUT
    a.require(not destination.exists() and not destination.is_symlink(),"HANDOFF_QUAL_REFUSE_OVERWRITE")
    g=pressure.guard_type(distinct.guard_type(a.Guard))();q=None;started=time.monotonic()
    row=dict(state="FAILED_HANDOFF_QUALIFICATION_NOT_ACCEPTED",accepted_count_delta=0,
        Native_or_product_executed=False,GO_authorized=False,runtime_handoff_connected=False,
        P09_gate="OPEN",PC_freeze_resolved=False)
    try:
        g.acquire();q=a.AcceptanceReader(a.c.ROOT,g.check)
        source_paths=(SELF,handoff.SELF,handoff.TEST,prepared.SELF,prepared.TEST,progress.SELF,progress.TEST)
        for path in source_paths:q.pin(path)
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
            ("tools.p09.tests.test_prepared_scope_handoff_v1","tools.p09.tests.test_prepared_input_checkpoint_v1",
             "tools.p09.tests.test_preparation_terminal_progress_v1"))
        result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        a.require(result.wasSuccessful() and result.testsRun==46 and not result.skipped,"ALL_CODE46_CONTRACTS")
        import flat_current_queue_envelope_runtime_v31 as c
        c.M.base.configure(160)
        graph,bootstrap=c.bootstrap.load(c.old,q.checkpoint)
        for pin in bootstrap["reader_source_pins"]:a.exact(q.pin(pin["path"]),pin,"EXACT_BOOTSTRAP_CURRENT_BYTES")
        listing=a.read_exact(q,a.scope.LIST_PIN)
        compiled=a.scope.listing_inputs(listing)
        rust=handoff.rust_inputs(compiled)
        a.require(len(rust)==787,"ALL_COMPILED_RUST787")
        producer_sources=frozenset(("tools/p09/produce_prepared_input_checkpoint_r366.py",prepared.SELF,prepared.TEST,
            progress.SELF,progress.TEST,pressure.SELF,pressure.TEST,distinct.SELF,distinct.TEST))
        successor=c._env["current_binding"].successor
        required,declared_rust,proof=handoff.load(q,CHECKPOINT,graph.binding,
            expected_context=dict(index=160,before=153,physical_product_run=3),
            expected_current_pins=dict(data_pin=q.pin(c.DATA),preflight_pin=q.pin(c.PREFLIGHT),
                authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT),
            expected_rust=rust,expected_source_paths=producer_sources)
        checkpoint=q.snapshots[CHECKPOINT["path"]]
        for path in producer_sources:a.exact(q.pin(path),required[path],"CURRENT_PREPARATION_PRODUCER_SOURCES")
        enumerator="tools/p09/current_issuer_build_inputs.py"
        text=q.text(enumerator);a.exact(q.snapshots[enumerator],required[enumerator],"EXACT_ORIGINAL_RUST_ENUMERATOR")
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
            scope_includes_checkpoint_and_new_qualifier_inputs=True,actual_runtime_completion_qualified=False)
        try:
            budget=graph.binding.runtime_budget(complete,opener.opens,c.old.prior.DIRECT.runtime_budget,q.checkpoint)
            row["unchanged_Native_cost_observation"].update(original_budget_accepts=True,budget=budget)
        except ValueError as error:
            a.require(error.args and error.args[0]=="ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5",
                "ONLY_EXACT_UNCHANGED_COST_REJECTION_OBSERVED")
            row["unchanged_Native_cost_observation"].update(original_budget_accepts=False,error_code=error.args[0])
        q.finish();g.check(force=True)
        row.update(state="PASS_ACTUAL_PREPARED_SCOPE_CODE46_BOUND29_NOT_NATIVE_RUNTIME_BUDGET_OR_GO",
            contracts=dict(run=46,errors=0,failures=0,skipped=0),checkpoint_pin=checkpoint,
            source_pins=[q.snapshots[x] for x in source_paths],actual_source_pairs=29,
            original_bounded_bootstrap=bootstrap,reconstructed_scope_count=len(required),
            required_scope_with_qualifier_inputs=len(complete),physical_scope_count=len(physical),
            current_Rust_input_count=len(rust),actual_Rust_inventory_requests=opener.opens,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            fresh_read_passes=q.read_passes,fresh_bytes_read=q.bytes_read,handoff_declaration_proof=proof,
            preparation_full_original_oracle_reexecuted=False,
            all_complete_scope_inputs_freshly_read_here=False,
            two_actual_Native_byte_boundaries_and_independent_product_oracle_required=True)
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
            parent_private_MiB_max=max((s["parent_private_mib"] for s in g.samples),default=None),
            metadata_warning=pressure.summary(g))
    a.require(g.cleanup,"HANDOFF_QUAL_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:json.dump(row,stream,ensure_ascii=True,indent=2,allow_nan=False)
    print(json.dumps(dict(state=row["state"],output=OUTPUT,error_code=row.get("error_code"),
        fresh_inputs=row.get("fresh_inputs"),final_fresh_hashes=row.get("final_fresh_hashes"),
        unchanged_Native_cost=row.get("unchanged_Native_cost_observation"),
        CPU_max=row["CPU_max"],RAM_min=row["RAM_min"],cleanup_confirmed=g.cleanup),allow_nan=False))
    return 0 if row["state"].startswith("PASS_") else 1

if __name__=="__main__":raise SystemExit(main())
