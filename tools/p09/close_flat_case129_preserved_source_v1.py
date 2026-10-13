"""Independent complete source closing for the preserved case129 child.

Source-only: no product/Native receipt rewrite, child, queue change or retry.
Every original input is retained, then code/review receipts are added. Original
14/20 acquisition/open pacing, 1/2MiB reads, two actual full boundaries, fresh
held identities, 600-second limits and CPU/RAM decisions stay in force.
Separate compound acceptance is required and is NOT implemented here.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from types import SimpleNamespace as NS

import flat_current_queue_source_stat_runtime_v2 as runtime
import retained_read_streams as retained
import reusable_audit_chunk_v1 as chunk
import review_flat_completed_body_stop_v1 as completed
import build_case112_current_stored as build
import run_case112_current_stored as original_runtime

a, c, scope = runtime.a, runtime.c, runtime.base.scope
SELF = "tools/p09/close_flat_case129_preserved_source_v1.py"
TEST = "tools/p09/tests/test_close_flat_case129_preserved_source_v1.py"
QUALIFICATION = "implementation/p09/evidence/p09-361-case129-preserved-source-code-qualification-r307.v1.json"
REVIEW_PIN = dict(path="implementation/p09/evidence/p09-361-case129-completed-stop-review-streaming-typed-raw-r305.v1.json",
    bytes=5325,sha256="73537902273ef6243f5eb9653f97e1222a11bbc38df87cb35976eb055f0cbd6f")
STOP_PIN = dict(path="implementation/p09/evidence/p09-361-case129-current-runtime-run001.v1.json",
    bytes=1718306,sha256="43290326df21ca883814aed325f3c4e33fcfb59df0aeec27375e449b6e901c49")
AUTHORITY_PIN = dict(path="implementation/p09/evidence/p09-361-case128-current-epoch-accept001.v1.json",
    bytes=292643,sha256="54d52e0909763d133e9e24e7f6b06e9b8a7689e250274e5da15cb5768f23d876")
CASE = "actual_import::source_bookmarks::native_capture_is_only_negative_bookmark_evidence_and_stays_source_fresh"
PASS = "PASS_PRESERVED129_INDEPENDENT_FULL_NATIVE_SOURCE_NOT_RUNTIME_ACCEPTANCE_OR_GATE"
PREFLIGHT_PASS = "PASS_PRESERVED129_WHOLE_SOURCE_PREFLIGHT_NOT_NATIVE_OR_ACCEPTANCE"
SCHEMA = "hwpx-agent.p09-preserved129-independent-source/v1"


def require(ok, code):
    if not ok:
        raise ValueError("PRESERVED129_SOURCE_" + code)


def expected_scope(original, additions):
    before = scope.pins(original)
    after = scope.extend(before, scope.pins(additions))
    require(all(after[name] == pin for name, pin in before.items()), "NO_REMOVED_OR_REBASED_ORIGINAL_INPUT")
    return after


def source_budget(required):
    result = retained.model(required, 167, PDH_seconds=2.05)
    result["final_postcleanup_distinct_sample_wait_allowance_seconds"] = .5
    result["predicted_runtime_combined_seconds"] += .5
    result["final_postcleanup_same_owner_actual_sample_required"] = True
    require(result["predicted_runtime_combined_seconds"] < 600, "UNCHANGED600_COMPLETE_COST")
    return result


def validate_frame(frame, required, path_guards, checkpoint):
    """Original full Native predicates, with physical retained-open accounting."""
    n = len(required); total = sum(p["bytes"] for p in required.values())
    directories = len({p.as_posix() for name in required for p in Path(name).parents})
    a.fields(frame, dict(frame_state="COMMITTED", registered_live_frame=False,
        input_count=n, input_bytes=total, original_owned_cleanup_confirmed_before_release=True,
        original_two_actual_per_case_byte_reads_retained=True, serialized_pin_reused_as_live_handle=False,
        input_exclusions_added=False, security_sandbox_claimed=False), "SOURCE_FRAME")
    a.fields(frame["held_identity_after_owned_cleanup"], dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=n,directory_count=directories), "SOURCE_FINAL_IDENTITIES")
    bounds = frame["actual_byte_boundaries"]
    require(type(bounds) is list and len(bounds) == 2, "TWO_FULL_BOUNDARIES")
    binary = sum(p["bytes"] for name,p in required.items() if name.lower().endswith(".exe"))
    for boundary, role in zip(bounds, ("before", "after")):
        checkpoint()
        a.exact(boundary["role"], role, "SOURCE_ORDER")
        a.exact(scope.pins(boundary["actual_byte_pins"]), required, "SOURCE_EVERY_BYTE")
        diagnostics = boundary["reader_diagnostics"]
        a.fields(diagnostics, dict(read_passes=n,bytes_read=total,
            read_rates_by_kind=dict(binary=1048576,other=2097152),
            bytes_read_by_kind=dict(binary=binary,other=total-binary),
            original_owned_read_operations_preserved=True,extra_sampler_or_native_query_started=False), "SOURCE_READS")
        a.fields(diagnostics["near_saturation_read_backpressure"], dict(
            warning_system_CPU_percent=95,cool_distinct_sample_windows=2,maximum_pause_windows_per_entry=8,
            original_hard_resource_decisions_unmodified=True,original_IO_deadline_unmodified=True,
            original_sampler_windows_reused=True,new_native_query_or_sampler_thread_started=False,
            original_read_checks_skipped=False), "SOURCE_BYTE_PRESSURE")
        workspace = diagnostics["reusable_chunk_workspace"]
        a.fields(workspace, dict(workspace_used=True,workspace_allocations=1,workspace_bytes=65536,
            active_lease=False,leases=n,lease_returns=n,returned_bytes=total,invalid_readinto_returns=0,
            unread_tail_exposed=False,file_bytes_or_hash_or_JSON_cache=False,
            original_MRO_wrappers_preserved=True,original_stream_open_and_identity_binding_preserved=True,
            original_checkpoints_pacing_parse_budget_and_final_hashes_preserved=True,
            added_sampler_query_thread_or_process=False), "SOURCE_WORKSPACE")
        require(type(workspace["readinto_attempts"]) is int and
            workspace["readinto_attempts"] == workspace["readinto_completed"] and
            workspace["readinto_completed"] >= n, "ALL_FRESH_READINTO")
    h = frame["handles"]; held = n + directories
    a.fields(h, dict(input_lock_handles_opened=held,input_lock_handles_closed=held,
        input_lock_handles_remaining=0,input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,
        active_reader_bindings=0,active_byte_streams=0,maximum_lock_seconds=600,
        handle_metadata_checks=2*held+2*n,byte_stream_identity_checks=2*n,separate_pathname_reopens=0,
        file_write_or_delete_operation_executed=False,input_scope_reduced=False,
        kernel_or_malicious_bypass_protection_claimed=False,probe_handles_opened=0,probe_handles_closed=0,
        probe_handles_remaining=0,probe_handle_close_failed_attempts=0,historical_runner_top_level_imported=False,
        lean_exact_definition_sources=list(retained.SOURCES)), "SOURCE_HANDLE_CLEANUP")
    borrower = h["borrowed_byte_streams"]
    a.fields(borrower, dict(duplicate_handles_opened=n,duplicate_handles_closed=n,
        duplicate_handles_remaining=0,duplicate_close_failed_attempts=0,shared_offset_resets=2*n,
        active_borrow_binding=False,byte_stream_pathname_reopens=0,original_held_handles_closed_by_borrower=False,
        original_pre_read_stream_identity_check_retained=True,input_scope_reduced=False,
        original_resource_guards_and_pacing_retained=True,retained_within_one_live_frame_only=True,
        unbuffered_raw_streams=True,parsed_JSON_hash_or_byte_cache=False,new_duplicate_open_reservations=n,
        reused_stream_pressure_checkpoints=n,logical_read_leases=2*n,logical_read_lease_returns=2*n,
        pending_open_reservation=False,resource_callback_retained_on_reuse=True,
        cursor_reset_and_fresh_identity_on_each_pass=True), "SOURCE_RETAINED_STREAMS")
    a.fields(h["native_open_pacing"], dict(maximum_opens_per_second=20,open_reservations=held+n,
        idle_time_cannot_accumulate_multiple_open_credits=True), "SOURCE_PHYSICAL_PACING")
    a.fields(h["acquisition_phase_pressure"],dict(acquisition_maximum_reservations_per_second=14,
        original_global_and_byte_reservation_ceiling_per_second=20,acquisition_used=True,
        acquisition_complete=True,acquisition_reservations=held,restored_original_rate=20,
        same_original_pacer=True,clock_and_sleeper_and_checkpoint_retained=True,
        clock_previous_credit_or_reservation_counter_reset=False,extra_sampler_or_thread_started=False,
        original_CPU_RAM600_and_all_byte_identity_guards_preserved=True), "SOURCE_ACQUISITION")
    a.fields(h["acquisition_source_warning_fail_fast"],dict(original_source_warning_percent=90,
        checks=held,latched_warnings=0,original_hard_resource_guard_called_first=True,
        original_lock_deadline_checked=True,warning_acquisition_resumes_after_cooldown=False,
        extra_native_query_or_sampler_started=False,successful_original_take_open_and_identity_checks_retained=True,
        byte_boundary_cooling_policy_changed=False), "SOURCE_FIRST_WARNING")
    a.fields(h["one_way_native_saturation_circuit_breaker"],dict(saturation_seen=False,
        native_open_or_identity_checks_skipped_for_success=False,policy_stop_code=None), "SOURCE_NO_RESTART")
    require(type(path_guards) is list and len(path_guards)==2, "SOURCE_TWO_PATH_GUARDS")
    for guard in path_guards:
        a.fields(guard,dict(native_metadata_queries_attempted=n,fresh_held_metadata_queries=n,
            original_path_guard_predicates=3*n,original_reader_root_restored=True,active_path_guard_adapter=False,
            pathname_metadata_probes=0,original_stream_identity_check_retained=True,
            metadata_reused_between_source_requests=False), "SOURCE_FRESH_PATH_GUARD")
    return dict(inputs=n,bytes=total,directories=directories,two_complete_actual_byte_boundaries=True,
        original_owned_cleanup_and_fresh_held_identities=True,source_scope_or_rates_or_deadlines_reduced=False)


def prepare(q, qualification_pin):
    runtime.base.configure(129)
    qualification = a.read_exact(q, qualification_pin)
    a.fields(qualification,dict(state="PASS_PRESERVED129_SOURCE_CODE_CONTRACTS_AND_FRESH_BINDING_NOT_NATIVE",
        accepted_count_after=122,accepted_count_delta=0,cleanup_confirmed=True), "SOURCE_CODE_QUALIFICATION")
    for pin in qualification["source_controller_pins"]:
        a.exact(q.pin(pin["path"]),pin,"SOURCE_QUALIFIED_CODE")
    original = a.read_exact(q, STOP_PIN)
    authority = a.read_exact(q, AUTHORITY_PIN)
    a.fields(authority,dict(state=runtime.prior.accepted.original.PASS,accepted_count_after=122,
        next_runtime_index=129,accepted_count_delta=1,accepted_current_generation_case_count=17), "SOURCE_AUTHORITY122")
    listing = a.read_exact(q, scope.LIST_PIN)
    current = scope.listing_inputs(listing)
    a.exact(listing["source_test_names"][128],CASE,"SOURCE_EXACT129")
    review = a.read_exact(q, REVIEW_PIN)
    proof = completed.review(original,STOP_PIN,case=CASE,index=129,prior_count=122)
    a.exact(completed.compact(original,proof),review["summary"],"SOURCE_TYPED_BODY_REVIEW")
    runtime.actual_source_binding(original)
    prior = scope.pins(original["source_freeze"])
    require(all(prior[name]==pin for name,pin in current.items()),"CURRENT_COMPILED826_RETAINED")
    api = retained.load(q,14,c)
    imported = set()
    for module in tuple(sys.modules.values()):
        name=getattr(module,"__file__",None)
        if name:
            path=Path(name).absolute()
            if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":
                imported.add(path.relative_to(c.ROOT).as_posix())
    require(len(imported)<=64,"ORIGINAL_HELPER_CEILING")
    for name in sorted(imported|{SELF,TEST}):q.pin(name)
    required=expected_scope(original["source_freeze"],list(q.snapshots.values()))
    rust={n for n in current if n.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
        and (n.endswith(".rs") or n.endswith("/Cargo.toml"))}
    require(len(rust)==787,"WHOLE_RUST787")
    enumerator=retained.definitions(q.text("tools/p09/current_issuer_build_inputs.py"),("rust_inputs",),
        dict(os=os,Path=Path,require=require))
    return original,proof,required,rust,api,enumerator,sorted(imported)


def close_frame_once(frame):
    """STOP 뒤 자원 checkpoint 없이 정리. 실패해도 원본 진단과 mutex 정리 유지."""
    if frame is None:
        return None, True
    closed = False
    try:
        closed = bool(frame.close())
    except BaseException:
        closed = False
    try:
        summary = frame.summary()
    except BaseException:
        summary = None
        closed = False
    return summary, closed


def run(mode, run_number, qualification_pin):
    require(Path.cwd().resolve()==c.ROOT,"REPOSITORY_ROOT")
    require(mode in ("preflight","source") and type(run_number) is int and 1<=run_number<=999,"ONE_EXPLICIT_ATTEMPT")
    suffix="preflight" if mode=="preflight" else "run"
    destination=c.ROOT/f"implementation/p09/evidence/p09-361-case129-independent-full-source-{suffix}{run_number:03}.v1.json"
    build.direct_path(destination.parent)
    require(not destination.exists() and not destination.is_symlink(),"FRESH_NO_OVERWRITE")
    g=a.Guard();q=frame=b=early=None;out=dict(schema_version=SCHEMA,state="FAILED_NOT_QUALIFIED",
        accepted_count_after=122,accepted_count_delta=0,product_child_executed=False,
        Native_frame_attempted=False,independent_source_frame_qualified=False,
        original_failed_root_accepted=False,original_product_body_replayed=False,
        independent_compound_acceptance_qualified=False,P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",
        full249_current_qualified=False,signed16_current_qualified=False,P10_started=False,PC_freeze_resolved=False)
    started=time.monotonic();last_progress=0.;path_guards=[];inventory=[]
    owner=NS(lock=threading.Lock(),samples=g.samples,checkpoint_io=g.check)
    context=NS(phase="metadata_hash")
    def progress(stage,count=0):
        nonlocal last_progress
        now=time.monotonic()
        if now-last_progress>=15:
            print(json.dumps(dict(stage=stage,completed=count,case=129,accepted_count_delta=0,product_replayed=False)),flush=True)
            last_progress=now
    try:
        g.acquire()
        Reader,_=chunk.reader_type(a.AcceptanceReader,runtime.prior.leaf_bytes())
        q=Reader(c.ROOT,g.check)
        b=runtime.prior.prior.metadata.MetadataCheckpoint(q,owner)
        original,proof,required,rust,api,enumerator,imports=prepare(q,qualification_pin)
        budget=source_budget(required)
        opener=build.QueryPacer(q.checkpoint)
        a.exact(enumerator.rust_inputs(c.ROOT,opener.reserve),rust,"SOURCE_PRE_RUST787")
        require(opener.requests==167,"ORIGINAL167_DIRECTORY_CHECKPOINTS")
        inventory.append(opener.summary())
        q.finish()
        b.restore()
        out.update(required_source_pins=list(required.values()),original_stopped_runtime_pin=STOP_PIN,
            prior_queue_authority_pin=AUTHORITY_PIN,body_review_pin=REVIEW_PIN,source_qualification_pin=qualification_pin,
            completed_child_review=proof,source_budget=budget,imported_controller_paths=imports)
        if mode=="preflight":
            out["state"]=PREFLIGHT_PASS
        else:
            early=api.EarlySourceCheckpoint(g.check,owner)
            class ProgressLocks(api.InputLocks):
                def take(self,*args,**kw):
                    result=super().take(*args,**kw);progress("source_native_acquisition",len(self.owned));return result
            held=ProgressLocks(c.ROOT,early,owner,context)
            frame=retained.frames.Frame(retained.frames.Registry(),required,early,held=held)
            out["Native_frame_attempted"]=True
            held.mark("before_acquire");frame.acquire();held.mark("after_acquire")
            Boundary,_=chunk.reader_type(original_runtime.BoundaryReader,runtime.prior.leaf_bytes())
            class BoundaryReader(Boundary):
                def diagnostics(self):
                    return dict(super().diagnostics(),reusable_chunk_workspace=dict(workspace_used=True,**chunk.summary(self)))
            def factory(guard):
                return BoundaryReader(c.ROOT,guard,owner=owner,api=api)
            held.mark("before_parent")
            for phase in ("metadata_hash","final_fresh_hash"):
                context.phase=phase;progress("source_"+phase,len(required))
                api.read_with_held_path_guards(frame,factory,g.check,path_guards)
            final_opener=build.QueryPacer(frame.check)
            a.exact(enumerator.rust_inputs(c.ROOT,final_opener.reserve),rust,"SOURCE_FINAL_RUST787")
            require(final_opener.requests==167,"FINAL167_DIRECTORY_CHECKPOINTS")
            inventory.append(final_opener.summary())
            held.mark("after_parent");held.mark("before_release")
            committed=frame.commit(original)  # The actual preserved STOP row, NEVER a fabricated PASS.
            validation=validate_frame(committed,required,path_guards,g.check)
            time.sleep(.5);g.check(force=True)  # Distinct final original-owner sample.
            out.update(state=PASS,independent_source_frame_qualified=True,validation=validation)
        out.update(metadata_IO=dict(inputs=len(q.snapshots),read_passes=q.read_passes,bytes_read=q.bytes_read,
            final_fresh_hashes=q.final_fresh_hashes,reusable_workspace=chunk.summary(q)),
            Rust_inventory_observations=inventory,source_path_guard_diagnostics=path_guards)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as exc:
        out["error_code"]=str(exc) if isinstance(exc,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(exc)) else "REDACTED_SOURCE_FAILURE"
    finally:
        if b:
            b.restore();out["metadata_guard"]=b.summary()
        if frame:
            summary, closed = close_frame_once(frame)
            out["source_frame"] = summary
            out["source_frame_cleanup_confirmed"] = closed
            if not closed:
                out["state"] = "FAILED_NOT_QUALIFIED"
                out["independent_source_frame_qualified"] = False
                out["error_code"] = "NATIVE_CLEANUP_FAILED"
        if early:out["early_source_checkpoint"]=early.summary()
        g.close();out["resource_cleanup_confirmed"]=g.cleanup
        out["resource_samples"]=g.samples;out["elapsed_seconds"]=time.monotonic()-started
        out["CPU_max"]=max((x["system_cpu_percent"] for x in g.samples),default=None)
        out["RAM_min"]=min((x["available_ram_percent"] for x in g.samples),default=None)
    require(g.cleanup,"SOURCE_FINAL_CLEANUP")
    with destination.open("x",encoding="utf-8") as stream:
        json.dump(out,stream,ensure_ascii=True,indent=2)
    print(json.dumps({k:out.get(k) for k in ("state","error_code","accepted_count_after","accepted_count_delta",
        "Native_frame_attempted","independent_source_frame_qualified","CPU_max","RAM_min","resource_cleanup_confirmed")}))
    return 0 if out["state"] in (PASS,PREFLIGHT_PASS) else 2


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--preflight",type=int)
    parser.add_argument("--source-run",type=int)
    parser.add_argument("--qualification-bytes",type=int,required=True)
    parser.add_argument("--qualification-sha256",required=True)
    args=parser.parse_args()
    require((args.preflight is None)!=(args.source_run is None),"ONE_MODE")
    pin=dict(path=QUALIFICATION,bytes=args.qualification_bytes,sha256=args.qualification_sha256)
    scope.pins([pin],1)
    sys.exit(run("preflight" if args.preflight is not None else "source",
        args.preflight if args.preflight is not None else args.source_run,pin))
