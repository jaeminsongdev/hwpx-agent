"""P275: 원95 CPU STOP 검토와 획득 구간14/s 후보의 작은 Native 자격검증.

원 P273/통과94/실패95 불변. 제품 본체·전체 입력 frame을 재실행하지 않는다.
하나의 기존 pacer만 사용하며 획득 뒤20/s를 복구하되 clock/credit을 초기화하지 않는다.
"""
import argparse
import io
import json
import math
import sys
import unittest
from unittest.mock import patch
import resume_diagnostic_guarded_runtime_r3 as runtime
import readonly_parent_file_observation as observed
import near_saturation_read_backpressure as pressure
import lower_native_acquisition_pressure as lower

p=runtime.p;g=runtime.g
SELF='tools/p09/qualify_acquisition_phase_pressure.py'
TEST='tools/p09/tests/test_acquisition_phase_pressure.py'
SCHEMA='hwpx-agent.p09-acquisition-phase-pressure-qualification/v1'
PASS='PASS_ORIGINAL95_STOP_REVIEW_AND_SMALL_NATIVE_PHASE14_NOT_RUNTIME_OR_GATE'
RATE=14
UPPER=20
COUNT=32
SUCCESS=dict(path=p.DIR+'/p273-case-094-run002.v1.json',bytes=624020,
    sha256='4c8b5cb8db208be26487e966653747a2ad92c3bc37d1c5268047957b6b166eb5')
FAILURE=dict(path=p.DIR+'/p273-case-095-run003.v1.json',bytes=223604,
    sha256='7880cdce8abe86f32c337d77ab3accd7fae46e4e6a81c8e1a773e4fd11e3d61e')
LIGHT=dict(path=p.DIR+'/p273-light-run001.v1.json',bytes=39522,
    sha256='a241c4dd90793a7c57dd03bfcc656ae9dc49933acc575229e3e3d30ca4826811')
STOP='STOP_SUSTAINED_SYSTEM_CPU'


def require(ok,code):runtime.require(ok,'ACQUISITION_PHASE_'+code)


class InputLocks(runtime.connection.TimedInputLocks):
    def __init__(self,*args,**keywords):
        self.phase_used=False;self.phase_complete=False;self.phase_reservations=0
        super().__init__(*args,**keywords)
        pacer=self.api.pacer
        require(type(pacer) is lower.original.borrowed.locks.OpenPacer and pacer.rate==UPPER
            and pacer.opens==0 and pacer.previous is None and pacer.checkpoint is self.open_pressure,
            'UNUSED_ORIGINAL20_PACER')
        self.phase_pacer=pacer;self.phase_clock=pacer.clock;self.phase_sleep=pacer.sleeper
        self.phase_checkpoint=pacer.checkpoint
    def acquire(self,rows):
        pacer=self.api.pacer
        require(not self.phase_used and not self.acquired and not self.closed and not self.owned
            and pacer is self.phase_pacer and pacer.rate==UPPER and pacer.opens==0
            and pacer.previous is None and pacer.checkpoint is self.phase_checkpoint
            and pacer.clock is self.phase_clock and pacer.sleeper is self.phase_sleep,
            'ONE_UNUSED_OWNER_ACQUISITION')
        self.phase_used=True;pacer.rate=RATE;before=pacer.opens
        try:
            result=super().acquire(rows);self.phase_complete=True;return result
        finally:
            self.phase_reservations=pacer.opens-before
            # 정리는 원 super.acquire/close의 보호 없는 경로. clock/previous/counters는 보존.
            pacer.rate=UPPER
    def summary(self):
        row=super().summary();pacer=self.api.pacer
        row['acquisition_phase_pressure']=dict(acquisition_maximum_reservations_per_second=RATE,
            original_global_and_byte_reservation_ceiling_per_second=UPPER,
            acquisition_used=self.phase_used,acquisition_complete=self.phase_complete,
            acquisition_reservations=self.phase_reservations,restored_original_rate=pacer.rate,
            same_original_pacer=pacer is self.phase_pacer,clock_and_sleeper_and_checkpoint_retained=
                pacer.clock is self.phase_clock and pacer.sleeper is self.phase_sleep and pacer.checkpoint is self.phase_checkpoint,
            clock_previous_credit_or_reservation_counter_reset=False,extra_sampler_or_thread_started=False,
            original_CPU_RAM600_and_all_byte_identity_guards_preserved=True,cleanup_callback_wrapped=False,
            nominal_acquisition_density_reduction_percent=30.0,CPU_or_PC_freeze_improvement_established=False)
        return row


def budget(count,binary,other):
    require(type(count) is int and 1579<=count<=1583 and type(binary) is int and binary==14216704
        and type(other) is int and 0<other<=119639255-binary+1048576,'FUTURE_ORIGINAL_FULL_SCOPE_UPPER')
    native=(count+306)/RATE+2*count/UPPER
    total=native+2*binary/1048576+2*other/2097152+60+20+15+60
    require(math.isfinite(total) and total<600,'ORIGINAL600_NOT_EXTENDED')
    return dict(full_scope_upper_inputs=count,acquisition_rate=RATE,original_byte_reservation_rate=UPPER,
        ancestor_directory_count=306,original_IO_scope_seconds=600,original_shared_metadata_read_limit=720,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,margin_seconds=60,
        nominal_seconds=total,prediction_not_completion_guarantee=True,input_or_byte_checks_removed=False)


def review(root,plan):
    f=root['terminal_source_frame'];h=f['handles'];t=h['lock_timing_diagnostic'];o=root['metadata_observation']
    require(root['schema_version']==runtime.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']==root['resource_stop_reason']==STOP and root['resource_watcher_cleanup_confirmed'] is True
        and root['failure_diagnostic']['stage']=='source_frame_acquire'
        and root['failure_diagnostic']['exception_class']=='ValueError'
        and root['selected_test_index']==95 and root['prior_runtime_plan']==plan
        and root['accepted_exact_product_body_count']==0 and root['actual_product_child_executed'] is False
        and root['diagnostic_parent_connection_selected'] is False and root['native_timing_connected'] is False
        and 'terminal_parent_failure_sidecar_pin' not in root and 'terminal_metadata_IO' not in root,
        'ORIGINAL95_ACQUIRE_STOP_NOT_PRODUCT_OR_PASS')
    require(plan['runtime_source_qualified_individual_cases']==88 and plan['next_runtime_index']==95
        and plan['runtime_remaining_individual_cases']==161 and plan['runtime_remaining_regular_cases']==155
        and plan['runtime_remaining_corpus_cases']==6,'SAME88_NO_STOP_ADVANCE')
    require(f['frame_state']=='CLOSED' and f['registered_live_frame'] is False
        and f['input_count']==1579 and f['input_bytes']==119639255 and f['actual_byte_boundaries']==[]
        and f['original_owned_cleanup_confirmed_before_release'] is False and h['borrowed_byte_streams'] is None
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==h['handle_metadata_checks']==737
        and h['input_lock_handles_remaining']==h['handle_close_failed_attempts']==0
        and h['maximum_lock_seconds']==600,'PARTIAL737_CLOSED_DUPLICATE_UNKNOWN_NOT_ZERO_OR_FULL')
    require([x['label'] for x in t['explicit_phase_events']]==['before_acquire']
        and t['original_guard_checks']==3793 and t['first_original_error']['original_error_code']==STOP
        and t['first_original_error']['phase']=='metadata_hash'
        and 40<t['first_original_error']['original_lock_elapsed_seconds']<41
        and t['first_original_error']['original_lock_limit_seconds']==600,'EXACT_ORIGINAL_ACQUISITION_TIMING')
    io=root['preparation_IO'];require(io['finished'] is True and io['read_passes']==412
        and io['bound_inputs']==io['final_fresh_hashes']==199,'ORIGINAL_PREPARATION_FINISHED_NOT_SOURCE')
    hot=o['samples'][-4:]
    require(len(hot)==4 and all(x['system_cpu_percent']==100 and x['parent_cpu_machine_percent']==0
        and x['audited_logical_read_bytes_delta']==0 and x['phase_at_sample']=='metadata_hash' for x in hot),
        'OBSERVED4_CPU100_OWN0_NO_BYTE_CAUSAL_CLAIM')
    early=root['early_source_checkpoint'];require(early['warning_entries']==2 and early['completed_pause_windows']==7
        and early['maximum_observed_pause_windows']==5 and early['requested_pause_seconds']==3.5
        and early['original_hard_CPU_RAM600_guards_preserved'] is True,'EXISTING90_ALREADY_PAUSED')
    require(root['runtime_contract_executions']==650 and root['P09_gate']==root['A12_gate']==root['A13_gate']=='OPEN'
        and all(root[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),'NO_WHOLE_OR_GATE_PROMOTION')
    return dict(original_STOP_preserved=True,failed95_accepted=False,runtime_accepted=88,next_index=95,
        full_source_boundaries_completed=0,original_body_or_Job_not_invoked=True,original_opened_handles_closed=737,
        original_duplicate_measurement=None,own_CPU_in_last4_percent=[x['parent_cpu_machine_percent'] for x in hot],
        observed_system_CPU_in_last4_percent=[x['system_cpu_percent'] for x in hot],CPU_cause_or_freeze_resolution_established=False)


def phase_contract(row,count,complete):
    require(row['acquisition_maximum_reservations_per_second']==RATE
        and row['original_global_and_byte_reservation_ceiling_per_second']==row['restored_original_rate']==UPPER
        and row['acquisition_used'] is True and row['acquisition_complete'] is complete
        and row['acquisition_reservations']==count and row['same_original_pacer'] is True
        and row['clock_and_sleeper_and_checkpoint_retained'] is True
        and row['original_CPU_RAM600_and_all_byte_identity_guards_preserved'] is True
        and all(row[k] is False for k in ('clock_previous_credit_or_reservation_counter_reset',
            'extra_sampler_or_thread_started','cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),
        'SINGLE_ORIGINAL_PACER_ALL_GUARDS')


def validate_probe(f,small):
    h=f['handles'];dup=h['borrowed_byte_streams'];n=len(small)
    require(n==3 and sum(x['bytes'] for x in small.values())<=131072
        and f['frame_state']=='CLOSED' and f['registered_live_frame'] is False
        and f['original_owned_cleanup_confirmed_before_release'] is False
        and [x['role'] for x in f['actual_byte_boundaries']]==['before','after'],'SMALL_ONLY_NOT_COMMITTED_JOB')
    for row in f['actual_byte_boundaries']:
        require(p.v.pins(row['actual_byte_pins'])==small and row['reader_diagnostics']['read_passes']==n
            and row['reader_diagnostics']['bytes_read']==sum(x['bytes'] for x in small.values()),'REAL_SMALL_FULL_BYTES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==7 and h['input_lock_handles_remaining']==0
        and h['handle_close_failed_attempts']==0 and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==13 and h['maximum_lock_seconds']==600
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==6
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0,
        'SMALL_NATIVE_ALL_CLOSE_NO_PATH_REOPEN')
    phase_contract(h['acquisition_phase_pressure'],7,True)


def contracts(failed,plan):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    import test_acquisition_phase_pressure as tests
    import test_lower_native_acquisition_pressure as retained
    suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromModule(tests),
        unittest.defaultTestLoader.loadTestsFromModule(retained)))
    def candidate(root,checkpoint,owner,**kw):
        from types import SimpleNamespace
        return InputLocks(root,checkpoint,owner,SimpleNamespace(phase='qualification'),**kw)
    with patch.object(tests,'FIXTURES',(failed,plan)),patch.object(lower,'InputLocks',candidate), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_PHASE_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_PHASE_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_PHASE_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'ALL32_ORIGINAL6_PLUS_NEW26')
    return result.testsRun


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p275-acquisition-phase-pressure-run{args.run:02}.v1.json'
    require(not destination.exists(),'NO_OVERWRITE')
    context=g.observation.Context();owner=g.observation.Resources(context);q=frame=early=None;proposed=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),original95_failure_pin=FAILURE,
        accepted94_pin=SUCCESS,actual_product_body_reexecuted=False,actual_full_source_executed=False,
        actual_current95_reexecuted=False,actual_full_runtime_connection_qualified=False,CPU_or_PC_freeze_improvement_established=False)
    try:
        owner.admit();stage='reader';q=runtime.Reader(owner,context);stage='review'
        raw=runtime.anchor(q);legacy,base,names,expected,exe,required,extras=raw[:7]
        binding=p.v.identity(names,expected,exe);light=runtime.m.review.bound_json(q,LIGHT);runtime.closed_attempt(light)
        root=runtime.m.review.bound_json(q,SUCCESS);runtime.closed_attempt(root)
        body=runtime.m.review.bound_json(q,root['case_receipt_pin'])
        plan=runtime.record(root,body,root['case_receipt_pin'],required,binding,extras,names,legacy,base)
        failed=runtime.m.review.bound_json(q,FAILURE);checked=review(failed,plan)
        folder=p.c.ROOT/p.DIR
        require(sorted(x.name for x in folder.glob('p273-*.v1.json'))==sorted(pin['path'].split('/')[-1] for pin in (LIGHT,SUCCESS,FAILURE))
            and sorted(x.name for x in (folder/'cases').glob('p273-*.json'))==[root['case_receipt_pin']['path'].split('/')[-1]],
            'ONLY_REVIEWED_ORIGINAL_ATTEMPTS_NO95_BODY')
        for name in runtime.NEW:require(q.pin(name)==required[name],'FROZEN_RUNTIME16')
        small={name:q.pin(name) for name in (SELF,TEST,runtime.SELF)}
        forecast=budget(1583,p.m.EXE['bytes'],119639255-p.m.EXE['bytes']+1048576)
        stage='contract_tests'
        with context.scope('contract_tests'):count=contracts(failed,plan)
        out.update(runtime_plan=plan,original95_review=checked,phase_contract_tests_passed=count,
            future_full_scope_budget=forecast,small_required_pins=list(small.values()))
        q.finish();stage='small_native'
        early=runtime.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
        held=InputLocks(p.c.ROOT,early,owner,context)
        frame=p.frames.Frame(p.frames.Registry(),small,early,held=held)
        context.reader=p.frames.Counters(q.reader,frame.readers)
        held.mark('before_acquire')
        with context.scope('metadata_hash'):frame.acquire()
        held.mark('after_acquire')
        def factory(guard):
            reader=observed.TraceReader(p.c.ROOT,pressure.PressureCheckpoint(guard,owner))
            p.qualification.lower_read_rate(reader);return reader
        for label in ('metadata_hash','final_fresh_hash'):
            with context.scope(label):frame.read_boundary(factory,owner.checkpoint_io)
        held.verify_two_byte_passes(small);held.verify_held_identities();require(frame.close(),'SMALL_CLOSE')
        validate_probe(frame.summary(),small);proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out.update(error_code=p.b.run.original.closed_error(error),failure_diagnostic=runtime.diagnostic(error,stage))
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='PHASE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='PHASE_FRAME_CLEANUP_FAILED';proposed=None
            out['small_native_probe']=frame.summary()
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if early is not None:out['early_source_checkpoint']=early.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            validate_probe(doc['small_native_probe'],small)
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and doc['phase_contract_tests_passed']==COUNT and doc['runtime_plan']==plan
                and doc['actual_full_runtime_connection_qualified'] is False,'FRESH_SMALL_ONLY_NOT_RUNTIME')
        g.complete(out,owner,proposed,validate)
        with destination.open('x',encoding='utf-8') as stream:
            runtime.r.compact.dump(out,stream,checkpoint=lambda:require(owner.done.is_set(),'TERMINAL_ONLY'),indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','phase_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':
    sys.modules.setdefault('qualify_acquisition_phase_pressure',sys.modules[__name__])
    raise SystemExit(main())
