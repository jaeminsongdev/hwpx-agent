"""Reject plans that fit Native600 but cannot fit declared shared720.

The original Native model already reserves margin60 and decoder5. Add only
the optimistic minimum metadata pacing, allowing all metadata open/byte work
to overlap with each other, but never with the later held Native phase. This
is a necessary model check, not a runtime guarantee or permission to weaken IO.
"""
import math

SELF = 'tools/p09/whole_runtime_metadata_budget_v1.py'
TEST = 'tools/p09/tests/test_whole_runtime_metadata_budget_v1.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
NATIVE = dict(path=PREFIX+'current-runtime-run009.v1.json', bytes=5046802,
    sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753')


def require(ok, label):
    if not ok: raise ValueError('WHOLE_RUNTIME_METADATA_'+label)


def assess(native_budget, *, metadata_open_limit=20, fastest_metadata_rate=2097152, burst_bytes=65536,
           readiness_seconds=15, shared_seconds=720):
    require(type(metadata_open_limit) is int and metadata_open_limit == 20 and type(fastest_metadata_rate) is int
        and fastest_metadata_rate == 2097152 and type(burst_bytes) is int and burst_bytes == 65536,
        'ORIGINAL_METADATA_PACING_NOT_A_RATE_CHANGE')
    require(type(readiness_seconds) is int and readiness_seconds == 15 and type(shared_seconds) is int
        and shared_seconds == 720, 'ORIGINAL_READY15_AND_SHARED720')
    inputs = native_budget['inputs']; binary = native_budget['binary_bytes']; other = native_budget['other_bytes']
    work = native_budget['predicted_runtime_combined_seconds']
    require(all(type(n) is int and n >= 0 for n in (inputs, binary, other)) and inputs > 0
        and type(work) in (int, float) and math.isfinite(work) and work > 0, 'TYPED_FINITE_COMPLETE_NATIVE_MODEL')
    require(type(native_budget['unchanged_lock_deadline_seconds']) is int and native_budget['unchanged_lock_deadline_seconds'] == 600
        and type(native_budget['unallocated_margin_seconds']) is int and native_budget['unallocated_margin_seconds'] == 60
        and type(native_budget['aggregate_envelope_decoder_allowance_seconds']) is float
        and native_budget['aggregate_envelope_decoder_allowance_seconds'] == 5.0, 'ORIGINAL_NATIVE600_MARGIN60_SHARED5')
    # Every current input must be admitted before the original Frame exists.
    # Give metadata the most optimistic legal initial open and byte credits.
    opens = max(0, inputs-1)/metadata_open_limit
    byte_work = max(0, binary+other-burst_bytes)/fastest_metadata_rate
    metadata_floor = max(opens, byte_work)
    native_total = work+readiness_seconds
    total = native_total+metadata_floor
    return dict(state=('REJECT_SHARED720_DECLARED_MODEL' if total >= shared_seconds else 'NECESSARY_SHARED720_MODEL_CHECK_ONLY_NOT_QUALIFICATION'),
        original_Native_model_with_additional_readiness_seconds=native_total,
        Native600_nominal_fits=native_total < 600, minimum_metadata_input_count=inputs,
        optimistic_metadata_open_seconds=opens, optimistic_metadata_byte_seconds=byte_work,
        optimistic_metadata_seconds=metadata_floor, minimum_combined_declared_model_seconds=total,
        unchanged_shared_deadline_seconds=shared_seconds, shared720_nominal_fits=total < shared_seconds,
        metadata_open_and_byte_work_assumed_fully_overlapped=True,
        metadata_work_overlapped_with_later_Native=False,
        slower_binary_IO_optimistically_charged_at_fastest_legal_metadata_rate=True,
        original_margin60_and_shared_decoder5_already_in_Native_model=True,
        original_initial_open_and_chunk_credit_allowed=True,
        additional_metadata_parse_source_checks_OS_latency_or_repeated_reads_not_charged=True,
        estimate_not_completion_guarantee=True, protection_or_IO_policy_changed=False,
        product_execution_or_replay_authorized=False)


def main():
    import argparse, importlib.util, io, json, re, sys, time, unittest
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conservative_maintenance as c
    c.Windows()
    denied=[]
    def audit(event,args):
        if event=='subprocess.Popen': denied.append(1); raise ValueError('WHOLE_RUNTIME_MODEL_ALL_SUBPROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import prepared_run_closure_v1 as host
    import terminal_metadata_pressure_v1 as pressure
    import distinct_final_sample_guard_v1 as distinct
    import owned_cpu_baseline_v1 as baseline
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    parser=argparse.ArgumentParser(); parser.add_argument('--attempt',type=int,required=True)
    attempt=parser.parse_args().attempt; require(type(attempt) is int and 1<=attempt<=8,'FINITE_ATTEMPT')
    output=PREFIX+f'native009-whole720-model-review{attempt:03}.v1.json'
    require(not(c.ROOT/output).exists(),'EXCLUSIVE_REVIEW')
    guard=baseline.guard_type(pressure.guard_type(distinct.guard_type(a.Guard)))()
    started=time.monotonic(); q=None
    row=dict(state='FAILED_SHARED720_MODEL_REVIEW_NOT_ACCEPTED',accepted_count_delta=0,
        Native_or_product_or_GO_executed=False, protection_or_IO_policy_changed=False)
    try:
        guard.acquire(); q=a.AcceptanceReader(c.ROOT,guard.check); q.pin(SELF); q.pin(TEST)
        for dependency in (c,a,host,pressure,distinct,baseline,publisher):
            q.pin(Path(dependency.__file__).absolute().relative_to(c.ROOT).as_posix())
        actual=a.read_exact(q,NATIVE)
        a.fields(actual,dict(state='STOPPED_NOT_ACCEPTED',stop_reason='FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE',
            operation_phase='final_source_freeze',product_body_observed=True,actual_product_child_executed=True,
            cleanup_confirmed=True,owned_tree_empty=True,Native_source_frame_qualified=False,
            current_generation_runtime_candidate_qualified=False,accepted_count_delta=0),'PRESERVED_ACTUAL_NATIVE009_STOP')
        a.fields(actual['terminal_summary'],dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248),'ONE_BODY_PASS_NOT_ACCEPTED')
        require(len(actual['source_frame']['actual_byte_boundaries'])==1,'ONE_COMPLETED_BOUNDARY_NOT_TWO')
        a.fields(actual['source_frame']['handles'],dict(input_lock_handles_opened=3642,input_lock_handles_closed=3642,
            input_lock_handles_remaining=0,active_reader_bindings=0,active_byte_streams=0,handle_close_failed_attempts=0),'REAL_TERMINAL_CLEANUP')
        a.fields(actual['strict_product_window'],dict(actual_GO_writes=1,actual_capture_count=1,actual_complete_capture_within_window=True),'ACTUAL_GO_AND_COMPLETE_CAPTURE')
        spec=importlib.util.spec_from_file_location('whole_runtime_metadata_budget_contracts',c.ROOT/TEST)
        tests=importlib.util.module_from_spec(spec); spec.loader.exec_module(tests); tests.MODULE=sys.modules[__name__]
        result=unittest.TextTestRunner(stream=io.StringIO(),failfast=True).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        a.exact(row['contracts'],dict(run=7,errors=0,failures=0,skipped=0),'WHOLE720_MODEL7')
        model=assess(actual['complete_runtime_budget'])
        require(model['Native600_nominal_fits'] and not model['shared720_nominal_fits'],'ACTUAL_STOP_EXPOSES_MISSING_GLOBAL_COST')
        row.update(model=model,actual_runtime_pin=NATIVE,actual_stop_reason=actual['stop_reason'],
            actual_operation_phase=actual['operation_phase'],actual_complete_byte_boundaries=1,
            original_product_body_PASS_preserved_but_not_accepted=True,
            actual_GO_to_complete_capture_seconds=actual['strict_product_window']['GO_to_complete_capture_elapsed_seconds'],
            actual_readiness_seconds=actual['strict_product_window']['worker_readiness']['readiness_elapsed_seconds'],
            failed_Native009_replayed=False,whole_current_source_or_acceptance_qualified=False,
            future_entry_must_enforce_shared720_model_before_any_new_GO=True)
        q.finish(); guard.check(force=True)
        row.update(state='PASS_NATIVE009_FAILURE_AND_WHOLE720_MODEL7_NOT_NATIVE_OR_PRODUCT_ACCEPTANCE',
            source_pins=list(q.snapshots.values()),fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        row['error_type']=type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{1,160}',error.args[0]): row['error_code']=error.args[0]
    finally:
        guard.close(); row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            owned_CPU_machine_max=max((s['parent_cpu_machine_percent'] for s in guard.samples if s.get('parent_cpu_machine_percent') is not None),default=None),
            RAM_min=min((s['available_ram_percent'] for s in guard.samples),default=None),subprocess_creation_attempts=len(denied))
    require(guard.cleanup,'REVIEW_GUARD_CLEANUP')
    # Keep the existing bounded exclusive publisher and its freshly read code.
    publisher.publish(c.ROOT,output,row,a)
    print(json.dumps({k:row.get(k) for k in ('state','contracts','fresh_inputs','final_fresh_hashes','model',
        'elapsed_seconds','CPU_max','owned_CPU_machine_max','RAM_min','cleanup_confirmed','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 1


if __name__=='__main__': raise SystemExit(main())
