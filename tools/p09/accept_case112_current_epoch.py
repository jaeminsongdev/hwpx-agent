"""Accept immutable runtime004 exactly once; no product/Native-frame replay.

Historical105 stays in its original epochs. The new epoch accepts only112.
Fresh qualifier reads are not substituted for runtime004's two live boundaries.
The immutable output refuses overwrite and cannot count itself as a new case.
"""
import ctypes
import json
import math
import os
from pathlib import Path
import sys
import time

import conservative_maintenance as c
import current_stored_runtime_scope as scope
import current_stored_native_bridge as native
import locked_runtime_inputs as locks
import owned_source_read_pressure as pressure
import packed_receipt_json as packed

SELF="tools/p09/accept_case112_current_epoch.py"
TEST="tools/p09/tests/test_case112_current_epoch_acceptance.py"
OUTPUT="implementation/p09/evidence/p09-361-case112-current-epoch-accept001.v1.json"
ROOT_PIN=dict(path="implementation/p09/evidence/p09-361-case112-current-runtime-run004.v1.json",
    bytes=1707675,sha256="16b6b25ecd11a543b9b2f2fae8e7a7e7b1456d68858fcbeb23712809633b989d")
FRESH_PIN=dict(path="implementation/p09/evidence/locked-r07/p340-light-review-run131.v1.json",bytes=94990,
    sha256="6d05cb6bf810ff5c19c61d1bc2d76921a00abb00d0f959c51e5fed9402a782ff")
BODY_PIN=dict(path="implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json",bytes=565807,
    sha256="b8495d04c9444875cd500d2941c5b055fab1bab630325cbefb327f9f79ec1e72")
CODE_PINS=[dict(path="tools/p09/current_stored_native_bridge.py",bytes=7987,
    sha256="74e654c4bd1be0142cce7bc74c281727a1f738a6091270b9571062f0a98f8e6b"),
    dict(path="tools/p09/run_case112_current_stored.py",bytes=23159,
    sha256="6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713"),
    dict(path="tools/p09/tests/test_case112_current_stored_runtime.py",bytes=12215,
    sha256="233981cbe341abd528b11027c7dc7d642e6c2397620999069cbd181206babdbb"),
    dict(path="tools/p09/tests/test_current_stored_native_bridge.py",bytes=9020,
    sha256="579088f43ee076b9867c756b0683e72d327ce6092e9cafb812fc8fcad5fdb666")]
PASS="PASS_EXACT112_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE"


def require(ok,code):
    if not ok:raise ValueError("CURRENT_EPOCH_ACCEPT_"+code)


def exact(actual,expected,code):
    # Python otherwise considers True==1 and False==0. No such receipt drift.
    require(type(actual) is type(expected),code)
    if type(expected) is dict:
        require(set(actual)==set(expected),code)
        for key,value in expected.items():exact(actual[key],value,code)
    elif type(expected) is list:
        require(len(actual)==len(expected),code)
        for left,right in zip(actual,expected):exact(left,right,code)
    else:require(actual==expected,code)


def fields(row,expected,code):
    require(type(row) is dict,code)
    for key,value in expected.items():exact(row.get(key),value,code)


def resource_history(samples,hot=0):
    require(type(samples) is list and 0<len(samples)<=4096,"RESOURCE_HISTORY")
    for sample in samples:
        hot,reason=c.decision(sample,hot)
        require(reason is None,"ORIGINAL_RESOURCE_STOP")
        private=sample.get("parent_private_percent")
        require(type(private) in (int,float) and math.isfinite(private)
            and 0<=private<c.POLICY["job_memory_stop_percent"],"PARENT_MEMORY")
        cpu=sample.get("parent_cpu_machine_percent")
        require(cpu is None or (type(cpu) in (int,float) and math.isfinite(cpu) and 0<=cpu<=100),"PARENT_CPU")
    return hot


def validate(row,listing,body,fresh,checkpoint=lambda:None):
    require(callable(checkpoint),"CHECKPOINT")
    fields(row,dict(schema_version="hwpx-agent.p09-case112-current-native-runtime-candidate/v1",
        state="PASS_EXACT112_CURRENT_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",exit_code=0,
        maximum_seconds=1200,policy=c.POLICY,cleanup_confirmed=True,owned_tree_empty=True,
        worker_created=True,job_assigned=True,writer_authorized=True,product_body_observed=True,
        actual_product_child_executed=True,actual_Cargo_SQL_Hangul_run=False,
        Native_source_frame_qualified=True,current_generation_runtime_candidate_qualified=True,
        closing_error_code=None,stop_reason=None,prior_queue_cases=105,accepted_count_delta=0,next_case=112,
        separate_queue_epoch_acceptance_required=True,full249_current_qualified=False,signed16_current_qualified=False,
        P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",PC_freeze_resolved=False,
        prior_queue_fresh_pin=FRESH_PIN,current_compiled_listing_pin=scope.LIST_PIN,
        compiled_test_executable_pin=scope.EXE_PIN,selected_test_index=112,
        selected_test_names=[scope.CASE112],passed_test_names=[scope.CASE112],
        test_arguments=[scope.CASE112,"--exact","--test-threads=1","--format=pretty","--color=never"]),"CANDIDATE")
    fields(fresh,dict(state="PASS_PRESERVED106_DISTINCT_FRESH_NOT_NATIVE_OR_PRODUCT",
        selected_test_index=112,selected_test_name=scope.CASE112,
        resource_watcher_cleanup_confirmed=True,resource_stop_reason=None),"FRESH131")
    fields(fresh["prior_runtime_plan"],dict(runtime_source_qualified_individual_cases=105,
        runtime_remaining_individual_cases=144,next_runtime_index=112,P09_gate="OPEN",
        full249_current_qualified=False),"PRIOR105_NOT_REBASED")
    current=scope.listing_inputs(listing)
    expected=scope.compose(body["source_freeze"],list(current.values()))
    bootstrap=scope.pins(row["bootstrap_metadata"]["input_pins"])
    expected=scope.extend(expected,bootstrap)
    actual=scope.pins(row["source_freeze"],1710)
    exact(actual,expected,"LOSSLESS_WHOLE_SCOPE")
    helpers=row["imported_worker_source_paths"]
    require(type(helpers) is list and len(helpers)==28 and helpers==sorted(set(helpers))
        and all(type(n) is str and n.startswith("tools/p09/") and n.endswith(".py") and n in bootstrap for n in helpers),
        "COMPLETE_IMPORTED_CLOSURE")
    for pin in CODE_PINS+list(native.SOURCES):
        exact(actual.get(pin["path"]),pin,"QUALIFIED_SOURCE_BYTES")
        require(pin["path"] in bootstrap,"BOOTSTRAP_CONTROLLER")
    total=sum(p["bytes"] for p in expected.values());n=len(expected)
    binary=sum(p["bytes"] for name,p in expected.items() if name.lower().endswith(".exe"))
    directories=len({p.as_posix() for name in expected for p in Path(name).parents})
    # Path.as_posix is platform independent for these already checked '/' names.
    exact(directories,335,"COMPLETE_ANCESTRY")
    frame=row["source_frame"]
    fields(frame,dict(frame_state="COMMITTED",registered_live_frame=False,input_count=n,input_bytes=total,
        original_owned_cleanup_confirmed_before_release=True,original_two_actual_per_case_byte_reads_retained=True,
        serialized_pin_reused_as_live_handle=False,input_exclusions_added=False,security_sandbox_claimed=False),"FRAME")
    fields(frame["held_identity_after_owned_cleanup"],dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=n,directory_count=directories),"FINAL_IDENTITIES")
    boundaries=frame["actual_byte_boundaries"]
    require(type(boundaries) is list and len(boundaries)==2,"TWO_BOUNDARIES")
    for boundary,role in zip(boundaries,("before","after")):
        checkpoint();exact(boundary.get("role"),role,"BOUNDARY_ROLE")
        exact(scope.pins(boundary["actual_byte_pins"],n),expected,"ACTUAL_WHOLE_BYTES")
        fields(boundary["reader_diagnostics"],dict(read_passes=n,bytes_read=total,
            read_rates_by_kind=dict(binary=1048576,other=2097152),
            bytes_read_by_kind=dict(binary=binary,other=total-binary),
            original_owned_read_operations_preserved=True,extra_sampler_or_native_query_started=False),"READS")
        fields(boundary["reader_diagnostics"]["near_saturation_read_backpressure"],dict(
            warning_system_CPU_percent=95,cool_distinct_sample_windows=2,maximum_pause_windows_per_entry=8,
            original_hard_resource_decisions_unmodified=True,original_IO_deadline_unmodified=True,
            original_sampler_windows_reused=True,new_native_query_or_sampler_thread_started=False,
            original_read_checks_skipped=False),"BYTE_PRESSURE")
    h=frame["handles"];held=n+directories
    fields(h,dict(input_lock_handles_opened=held,input_lock_handles_closed=held,input_lock_handles_remaining=0,
        input_lock_cleanup_confirmed=True,handle_close_failed_attempts=0,active_reader_bindings=0,
        active_byte_streams=0,maximum_lock_seconds=600,handle_metadata_checks=2*held+2*n,
        byte_stream_identity_checks=2*n,separate_pathname_reopens=0,file_write_or_delete_operation_executed=False,
        input_scope_reduced=False,kernel_or_malicious_bypass_protection_claimed=False,
        probe_handles_opened=0,probe_handles_closed=0,probe_handles_remaining=0,probe_handle_close_failed_attempts=0,
        historical_runner_top_level_imported=False,lean_exact_definition_sources=list(native.SOURCES)),"HANDLE_CLEANUP")
    fields(h["borrowed_byte_streams"],dict(duplicate_handles_opened=2*n,duplicate_handles_closed=2*n,
        duplicate_handles_remaining=0,duplicate_close_failed_attempts=0,shared_offset_resets=2*n,
        active_borrow_binding=False,byte_stream_pathname_reopens=0,original_held_handles_closed_by_borrower=False,
        original_pre_read_stream_identity_check_retained=True,input_scope_reduced=False,
        original_resource_guards_and_pacing_retained=True),"BORROWED_STREAMS")
    fields(h["native_open_pacing"],dict(maximum_opens_per_second=20,open_reservations=held+2*n,
        idle_time_cannot_accumulate_multiple_open_credits=True),"NATIVE_PACING")
    fields(h["acquisition_phase_pressure"],dict(acquisition_maximum_reservations_per_second=14,
        original_global_and_byte_reservation_ceiling_per_second=20,acquisition_used=True,
        acquisition_complete=True,acquisition_reservations=held,restored_original_rate=20,same_original_pacer=True,
        clock_and_sleeper_and_checkpoint_retained=True,clock_previous_credit_or_reservation_counter_reset=False,
        extra_sampler_or_thread_started=False,original_CPU_RAM600_and_all_byte_identity_guards_preserved=True),"PHASE")
    fields(h["acquisition_source_warning_fail_fast"],dict(original_source_warning_percent=90,checks=held,
        latched_warnings=0,original_hard_resource_guard_called_first=True,original_lock_deadline_checked=True,
        warning_acquisition_resumes_after_cooldown=False,extra_native_query_or_sampler_started=False,
        successful_original_take_open_and_identity_checks_retained=True,byte_boundary_cooling_policy_changed=False),"FAIL_FAST")
    fields(h["one_way_native_saturation_circuit_breaker"],dict(saturation_seen=False,
        native_open_or_identity_checks_skipped_for_success=False,policy_stop_code=None),"NO_SATURATION_RESTART")
    guards=row["source_path_guard_diagnostics"]
    require(type(guards) is list and len(guards)==2,"PATH_GUARDS")
    for guard in guards:
        fields(guard,dict(native_metadata_queries_attempted=n,fresh_held_metadata_queries=n,
            original_path_guard_predicates=3*n,original_reader_root_restored=True,active_path_guard_adapter=False,
            pathname_metadata_probes=0,original_stream_identity_check_retained=True,
            metadata_reused_between_source_requests=False),"ACTUAL_FRESH_PATH_GUARDS")
    fields(row,dict(current_Rust_input_count=787,terminal_summary=dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)),"TERMINAL")
    cap=row["capture_diagnostics"]
    fields(cap,dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_log_content_included=False),"CAPTURE")
    exact(cap["received_bytes"],cap["buffered_bytes"],"NO_TRUNCATION")
    exact(cap["buffered_bytes"],dict(stdout=228,stderr=0),"EXACT_COMPLETE_CAPTURE")
    fields(row["owned_limits_readback"],dict(verified=True,cpu_hard_cap_machine_percent=6.25,
        affinity_mask=1,priority_class=16384,active_process_limit=16,kill_on_close=True,breakaway_disabled=True),"JOB_READBACK")
    fields(row["job_final"],dict(active_processes=0,owned_processes=[]),"JOB_EMPTY")
    inventory=row["current_Rust_inventory_observations"]
    require(type(inventory) is list and len(inventory)==2,"RUST_INVENTORY")
    for phase in inventory:
        fields(phase,dict(request_limit_per_second=20,requests=167,requests_skipped=False,cleanup_paced=False),"WHOLE_RUST")
    budget=row["complete_runtime_budget"]
    model=scope.cost(expected,14)
    fields(budget,model,"BASE_COMPLETE_COST")
    fields(budget,dict(product_allowance_seconds=20,pre_GO_and_assignment_allowance_seconds=3,
        final_inventory_checkpoint_count=167,final_inventory_pacing_seconds=167/20,
        additional_early_source_wait_allowance_seconds=11,post_cleanup_identity_allowance_seconds=5,
        unknown_pressure_waits_included=False,actual_completion_guaranteed=False),"RUNTIME_COST")
    exact(budget["predicted_runtime_combined_seconds"],model["predicted_combined_seconds"]+20+3+167/20+11+5,"NO_HIDDEN_COST")
    require(budget["predicted_runtime_combined_seconds"]<600,"UNCHANGED600")
    hot=resource_history(row["samples"])
    resource_history(row["post_Job_cleanup_resource_samples"],hot)
    checkpoint()
    return dict(whole_runtime_input_count=n,whole_runtime_input_bytes=total,ancestor_directory_count=directories,
        actual_full_byte_passes=2,original_resource_samples=len(row["samples"]),
        post_Job_cleanup_resource_samples=len(row["post_Job_cleanup_resource_samples"]),
        lossless_historical_current_union_validated=True,actual_owned_Native_cleanup_validated=True)


class Guard:
    """Sole serial original sampler, original mutex, below-normal single CPU."""
    def __init__(self):
        self.windows=c.Windows();self.samples=[];self.hot=0;self.last=0.;self.cpu=None
        self.deadline=time.monotonic()+600;self.mutex=None;self.cleanup=False
    def acquire(self):
        ctypes.set_last_error(0)
        handle=self.windows.k.CreateMutexW(None,True,"Local\\HwpxAgentP149ConservativeMaintenance")
        error=ctypes.get_last_error();require(bool(handle),"MUTEX_CREATE")
        if error==183:
            self.windows.k.CloseHandle(handle);require(False,"OTHER_MAINTENANCE_ACTIVE")
        self.mutex=handle
        stable=0;admission=time.monotonic()+c.POLICY["admission_max_seconds"]
        while stable<c.POLICY["start_consecutive_samples"]:
            require(time.monotonic()<admission,"ADMISSION_TIMEOUT")
            time.sleep(.5);self.check(force=True)
            stable=c.admitted_count(self.samples[-1],stable)
    def check(self,force=False):
        now=time.monotonic();require(now<self.deadline,"ORIGINAL600_TIMEOUT")
        if not force and now-self.last<.5:return
        row=self.windows.sample();memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
        require(self.windows.k.K32GetProcessMemoryInfo(self.windows.k.GetCurrentProcess(),ctypes.byref(memory),memory.size),"PARENT_MEMORY_SAMPLE")
        cpu=time.process_time();machine=None if self.cpu is None else 100*(cpu-self.cpu)/(now-self.last)/self.windows.processors
        row.update(parent_cpu_machine_percent=machine,parent_private_mib=memory.private/1048576,
            parent_private_percent=100*memory.private/self.windows.total_ram)
        self.cpu=cpu;self.last=now;self.samples.append(row)
        self.hot=resource_history([row],self.hot)
    def close(self):
        if self.mutex is not None:
            released=bool(self.windows.k.ReleaseMutex(self.mutex))
            closed=bool(self.windows.k.CloseHandle(self.mutex));self.mutex=None
            self.cleanup=released and closed;require(self.cleanup,"MUTEX_CLEANUP")
        else:self.cleanup=True


def read_exact(reader,pin):
    value=reader.json(pin["path"]);exact(reader.snapshots[pin["path"]],pin,"IMMUTABLE_RECEIPT")
    return value


class AcceptanceReader(pressure.WeightedReader):
    def __init__(self,root,checkpoint):
        super().__init__(root,checkpoint)
        self.open_pacer=locks.OpenPacer(checkpoint,rate=20)
    def _read(self,name,parse=False):
        # Closing fresh_hash도 첫 읽기와 같은 open20/s. 두 pacer를 쌓지 않는다.
        self.open_pacer.reserve()
        return super()._read(name,parse=parse)


def run():
    destination=c.ROOT/OUTPUT
    require(not destination.exists() and not destination.is_symlink(),"IMMUTABLE_ACCEPT_ALREADY_EXISTS")
    guard=Guard();reader=None;result=None;error=None;started=time.monotonic()
    try:
        guard.acquire();reader=AcceptanceReader(c.ROOT,guard.check)
        row=read_exact(reader,ROOT_PIN);listing=read_exact(reader,scope.LIST_PIN)
        body=read_exact(reader,BODY_PIN);fresh=packed.unpack(read_exact(reader,FRESH_PIN),guard.check)
        validation=validate(row,listing,body,fresh,guard.check)
        current=scope.listing_inputs(listing)
        inventory_name="tools/p09/current_issuer_build_inputs.py"
        original_inventory=native.definitions(reader.text(inventory_name),("rust_inputs",),
            dict(os=os,Path=Path,require=require))
        exact(reader.snapshots[inventory_name],scope.pins(row["source_freeze"])[inventory_name],"EXACT_RUST_ENUMERATOR")
        rust={n for n in current if n.startswith(("crates/","protocol/generated/rust/","tools/xtask/"))
            and (n.endswith(".rs") or n.endswith("/Cargo.toml"))}
        opener=reader.open_pacer
        require(original_inventory.rust_inputs(c.ROOT,opener.reserve)==rust,"FRESH_RUST_INVENTORY")
        required=scope.pins(row["source_freeze"])
        # 새 수용경계: 현재787 Rust + binary + runtime helper closure만 fresh 확인.
        # 과거1710 Native 전체의 두 실제 byte/identity 경계는 root004 증거 그대로 보존.
        names=rust|set(row["imported_worker_source_paths"])|{scope.EXE_PIN["path"]}
        for name in sorted(names):
            exact(reader.pin(name),required[name],"CURRENT_EPOCH_INPUT_DRIFT")
        for module in tuple(sys.modules.values()):
            name=getattr(module,"__file__",None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/"tools/p09") and path.suffix==".py":
                    reader.pin(path.relative_to(c.ROOT).as_posix())
        reader.pin(SELF);reader.pin(TEST)
        reader.finish()
        require(original_inventory.rust_inputs(c.ROOT,opener.reserve)==rust,"FINAL_RUST_INVENTORY")
        guard.check(force=True)
        result=dict(schema_version="hwpx-agent.p09-case112-current-epoch-acceptance/v1",state=PASS,
            runtime_candidate_pin=ROOT_PIN,prior_queue_authority_pin=FRESH_PIN,current_compiled_listing_pin=scope.LIST_PIN,
            accepted_epoch_key=ROOT_PIN["sha256"]+":112",accepted_test_indices=[112],accepted_test_names=[scope.CASE112],
            accepted_count_before=105,accepted_count_delta=1,accepted_count_after=106,runtime_remaining_individual_cases=143,
            next_runtime_index=113,prior105_historical_epochs_preserved=True,prior105_current_generation_rebased=False,
            accepted_current_generation_case_count=1,duplicate_acceptance_refuses_overwrite=True,
            successful_product_cases_reexecuted=False,product_child_executed=False,Native_frame_reexecuted=False,
            actual_historical_current_runtime_frame_validation=validation,current_Rust_input_count=787,
            current_Rust_inventory_checked_before_after=True,fresh_input_pins=list(reader.snapshots.values()),
            fresh_read_passes=reader.read_passes,fresh_bytes_read=reader.bytes_read,final_fresh_hashes=reader.final_fresh_hashes,
            qualifier_read_rates_by_kind=dict(binary=1048576,other=2097152),file_open_ceiling_per_second=20,
            fresh_qualifier_is_not_new_native_or_product_evidence=True,full249_current_qualified=False,
            signed16_current_qualified=False,whole_runtime_reconciliation_required=True,
            P09_gate="OPEN",A12_gate="OPEN",A13_gate="OPEN",P10_started=False,PC_freeze_resolved=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError):
        # 원 receipt/로그/예외값은 출력하지 않는다. 실패는 수용권위가 아니다.
        error="FAILED_CURRENT_EPOCH_ACCEPTANCE_NOT_QUEUE_ADVANCE"
    finally:guard.close()
    if error:
        print(json.dumps(dict(state=error,cleanup_confirmed=guard.cleanup,queue_unchanged=105)))
        return 2
    require(result is not None and guard.cleanup,"FINAL_CLEANUP")
    result.update(resource_samples=guard.samples,resource_cleanup_confirmed=guard.cleanup,
        sole_serial_sampler=True,parallel_observer_started=False,elapsed_seconds=time.monotonic()-started)
    with destination.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,ensure_ascii=True,indent=2)
    print(json.dumps(dict(state=PASS,accepted=106,remaining=143,next_case=113,cleanup_confirmed=True)))
    return 0


if __name__=="__main__":raise SystemExit(run())
