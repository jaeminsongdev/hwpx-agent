"""P269 r2: 원 표본을 먼저 획득한 P208 parent bridge에 새 실패 보존 연결 + 원600초 잠금 계측.

실제 작은3파일 Native probe와 합성 parent만 실행한다. 제품/전체scope/CPU stress
아님. 원 Job/guard/PASS/CPU 실패 수용은 불변; 실제 full runtime 연결은 NOT_RUN.
"""
import argparse
import hashlib
import io
import json
import math
import re
import sys
import time
import unittest
from unittest.mock import patch
import review_rejected_parent_diagnostic as a
import qualify_rejected_parent_connection as original
m=a.m
SELF='tools/p09/qualify_rejected_parent_connection_r2.py'
TEST='tools/p09/tests/test_rejected_parent_connection_r2.py'
REPORT='implementation/p09/P09-269_ORIGINAL_PARENT_SAMPLED_CONNECTION_REPORT.md'
QUALIFIED=dict(path=m.p.DIR+'/p267-case094-failure-review-run01.v1.json',bytes=160731,
    sha256='b0e307c3548c41f843565d87bdfa9a073dc47fd8c722883c875ba332e0afc06d')
SCHEMA='hwpx-agent.p09-original-parent-sampled-connection-r2/v1'
PASS='PASS_ORIGINAL_PARENT_SAMPLED_CONNECTION_R2_SMALL_NATIVE_NOT_RUNTIME_OR_GATE'
COUNT=88
LABELS=('before_acquire','after_acquire','before_parent','after_parent','before_release')


def require(ok,code):a.require(ok,'CONNECTION_'+code)


def closed_code(error):
    value=str(error)
    return value if re.fullmatch(r'[A-Z0-9_]{1,256}',value) else 'ORIGINAL_VALUE_ERROR_DETAILS_REDACTED'


class TimedInputLocks(m.m.lower.InputLocks):
    """추가 시계 읽기는 phase 경계/첫 예외에서만; 기존 check는 매번 그대로 호출.

    elapsed는 관측값이지 새 deadline이 아니다. 예외/cleanup 중 자원 sample이나
    guard를 재시작하지 않는다. 미측정 값은 None; 원 예외를 바꾸지 않는다.
    """
    def __init__(self,root,checkpoint,resources,context,**keywords):
        self.timing_context=context;self.timing_checks=0;self.timing_events=[];self.timing_first_error=None
        super().__init__(root,checkpoint,resources,**keywords)
    def elapsed(self):
        try:
            value=time.monotonic()-self.started
            return value if type(value) in (int,float) and math.isfinite(value) and value>=0 else None
        except Exception:return None
    def check(self):
        self.timing_checks+=1
        try:return super().check()
        except ValueError as error:
            if self.timing_first_error is None:
                self.timing_first_error=dict(original_error_code=closed_code(error),
                    original_lock_elapsed_seconds=self.elapsed(),phase=getattr(self.timing_context,'phase',None),
                    guard_check_number=self.timing_checks,original_lock_limit_seconds=self.maximum_seconds)
            raise
    def mark(self,label):
        require(label in LABELS and len(self.timing_events)<16,'BOUNDED_EXPLICIT_PHASE')
        self.check()
        self.timing_events.append(dict(label=label,phase=getattr(self.timing_context,'phase',None),
            original_lock_elapsed_seconds=self.elapsed(),guard_check_number=self.timing_checks))
    def summary(self):
        row=super().summary()
        row['lock_timing_diagnostic']=dict(original_guard_checks=self.timing_checks,
            explicit_phase_events=[dict(x) for x in self.timing_events],first_original_error=self.timing_first_error,
            original_lock_limit_seconds=self.maximum_seconds,original_check_invoked_without_replacement=True,
            extra_clock_only_at_boundary_or_first_error=True,extra_CPU_RAM_or_native_query_started=False,
            original_resource_guard_or_deadline_extended=False,cleanup_callback_wrapped=False,
            unknown_measurements_not_zeroed=True,CPU_or_PC_freeze_improvement_established=False)
        return row


class ParentConnection:
    """Caller의 Capture를 예외 후에도 유지. 원 parent 함수/RAW_DUMP만 연결."""
    def __init__(self,frame,writes,index,name,binding):
        require(type(index) is int and 1<=index<=249 and m.p.v.NAME.fullmatch(name)
            and not name.startswith(m.p.v.CORPUS_PREFIX),'EXACT_REGULAR_PARENT')
        self.capture=a.Capture(frame,writes,index,name,binding);self.used=False
    def run(self,destination,context):
        require(not self.used,'ONE_ORIGINAL_PARENT_CALL_NO_RETRY');self.used=True
        c=self.capture
        with patch.object(m.p,'RAW_DUMP',c.writer):
            return m.p.run_parent(c.frame,c.index,c.name,destination,context,c.binding)
    def write_rejected(self,stream,owner,out):
        require(self.used and self.capture.rejected,'ONLY_ORIGINAL_REJECTED_ROW')
        return self.capture.write_rejected(stream,owner,out)


def validate_probe(snapshot,required,timing):
    require(len(required)==3 and sum(p['bytes'] for p in required.values())<=131072,'SMALL_THREE_SCOPE')
    h=snapshot['handles'];d=h['borrowed_byte_streams'];b=snapshot['actual_byte_boundaries']
    require(snapshot['frame_state']=='CLOSED' and snapshot['registered_live_frame'] is False
        and snapshot['input_count']==3 and snapshot['input_bytes']==sum(p['bytes'] for p in required.values())
        and snapshot['held_identity_after_owned_cleanup'] is None
        and snapshot['original_owned_cleanup_confirmed_before_release'] is False,'SMALL_NOT_PRODUCT_COMMIT')
    require(len(b)==2 and [r['role'] for r in b]==['before','after']
        and all(m.p.v.pins(r['actual_byte_pins'])==required and r['reader_diagnostics']['read_passes']==3
            and r['reader_diagnostics']['bytes_read']==snapshot['input_bytes']
            and r['reader_diagnostics']['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and r['reader_diagnostics']['original_owned_read_operations_preserved'] is True for r in b),
        'ORIGINAL_TWO_SMALL_ACTUAL_BYTE_PASSES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==7
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==h['handle_close_failed_attempts']==0
        and h['input_lock_cleanup_confirmed'] is True and h['maximum_lock_seconds']==600
        and h['byte_stream_identity_checks']==6 and h['handle_metadata_checks']==20
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==13
        and d['duplicate_handles_opened']==d['duplicate_handles_closed']==d['shared_offset_resets']==6
        and d['duplicate_handles_remaining']==d['duplicate_close_failed_attempts']==d['byte_stream_pathname_reopens']==0,
        'ORIGINAL_SMALL_NATIVE_CLEANUP_AND_LIMITS')
    trace=h['lock_timing_diagnostic']
    require(trace==timing and trace['first_original_error'] is None and trace['original_lock_limit_seconds']==600
        and trace['original_guard_checks']>0 and [x['label'] for x in trace['explicit_phase_events']]==list(LABELS)
        and all(type(x['original_lock_elapsed_seconds']) in (int,float)
            and math.isfinite(x['original_lock_elapsed_seconds']) and 0<=x['original_lock_elapsed_seconds']<=600
            for x in trace['explicit_phase_events']),'CONNECTED_ORIGINAL_TIMING_NO_EXTENDED_GUARD')
    for key in ('extra_CPU_RAM_or_native_query_started','original_resource_guard_or_deadline_extended',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established'):
        require(trace[key] is False,'NO_GUARD_CHANGE_OR_FREEZE_CLAIM')


def contracts(fixtures):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    import test_rejected_parent_connection as retained
    with patch.object(retained,'m',sys.modules[__name__]):
        require(original.contracts(fixtures)==80,'ORIGINAL80_CURRENT_CONNECTION_RETAINED')
    with patch('subprocess.Popen',side_effect=AssertionError('NO_R2_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_R2_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_R2_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromName('test_rejected_parent_connection_r2'))
    require(result.wasSuccessful() and result.testsRun==8 and not result.skipped,'NEW8_NO_SKIP')
    return COUNT


def fake_original_row(task):
    # 합성 parent는 제품을 실행하지 않는다. Job 미측정 값은 None을 유지한다.
    return dict(state='STOPPED_NOT_ACCEPTED',stop_reason='OWNED_RUNNER_FAILURE',task=task,
        cleanup_confirmed=None,owned_tree_empty=None,job_final=None,tests_passed=None,exit_code=None,
        synthetic_original_parent_only=True,original_Job_cleanup_measured=False)


def preserve(connection,destination,owner,out):
    require(not destination.exists(),'DIAGNOSTIC_FRESH_ONLY')
    digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            n=self.stream.write(block);require(type(n) is int and n==len(block),'ONE_COMPLETE_WRITE')
            digest.update(block.encode('ascii'));written+=n;return n
    with destination.open('x',encoding='utf-8') as stream:
        stats=connection.write_rejected(Output(stream),owner,out)
    require(stats['characters_written']==written and stats['diagnostic_only'] is True
        and stats['runtime_accepted'] is False,'ONLY_ACCOUNTED_DIAGNOSTIC')
    return dict(path=destination.relative_to(m.p.c.ROOT).as_posix(),bytes=written,sha256=digest.hexdigest()),stats



FAILED=dict(path=m.p.DIR+'/p268-rejected-parent-connection-run01.v1.json',bytes=147778,
    sha256='2c3a6fbe93444e56af7e293fcebe35574911dfb37e79f1b78ff99307a599fcf3')


class OriginalParentSamples:
    """작은 합성 parent의 원 Windows 표본/decision/admission/간격만 명시 재사용.

    원 p.run_parent가 만든 Windows를 받으므로 비공개 LatestOriginalSample도
    원 sample 메서드가 갱신한다. CPU 값을 만들어 넣거나 원 압력 검사를 대체하지 않는다.
    실제 full c.run을 대체하는 클래스가 아니며 작은 probe의 원 sample 최대16개다.
    """
    def __init__(self,windows,clock=time.monotonic,sleep=time.sleep):
        self.windows=windows;self.clock=clock;self.sleep=sleep
        self.started=self.last=clock();self.hot=0;self.rows=[]
    def observe(self,force=False):
        now=self.clock()
        require(type(now) in (int,float) and math.isfinite(now) and now>=self.last>=self.started,
            'ORIGINAL_PARENT_CLOCK')
        require(now-self.started<=1200,'ORIGINAL_PARENT1200_NOT_EXTENDED')
        if not force and now-self.last<m.p.c.POLICY['sample_seconds']:return None
        require(len(self.rows)<16,'SMALL_PARENT_SAMPLE_BOUND16')
        for attempt in range(6):
            try:row=dict(self.windows.sample());break
            except ValueError as error:
                if str(error)!='CPU_SAMPLE_INTERVAL_MISSING' or attempt==5:raise
                self.sleep(0.02)
        self.rows.append(row);self.last=self.clock()
        self.hot,reason=m.p.c.decision(row,self.hot)
        if reason:raise ValueError(reason)
        return row
    def admit(self):
        count=0
        while self.clock()-self.started<m.p.c.POLICY['admission_max_seconds']:
            self.sleep(m.p.c.POLICY['sample_seconds']);row=self.observe(True)
            require(row['system_cpu_percent']<m.p.c.POLICY['emergency_cpu_percent'],'ORIGINAL_PARENT_ALREADY_SATURATED')
            count=m.p.c.admitted_count(row,count)
            if count>=m.p.c.POLICY['start_consecutive_samples']:break
        require(count>=m.p.c.POLICY['start_consecutive_samples'],'ORIGINAL_PARENT_STABLE_WINDOW')
        return count
    def checkpoint(self):self.observe(False)
    def summary(self):
        return dict(original_parent_completed_sample_count=len(self.rows),
            system_cpu_max_percent=max((r['system_cpu_percent'] for r in self.rows),default=None),
            original_parent_sample_method_and_decision_reused=True,CPU_samples_manufactured=False,
            parent_sample_thread_started=False,original_half_second_debounce_retained=True,
            original_admission_policy_retained=True,maximum_small_probe_samples=16,
            real_product_or_Job_executed=False,Job_CPU_measurement=None)


def review_failed_probe(doc):
    require(doc['schema_version']==original.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']=='P208_POST_STOP_RUNTIME_MONOTONIC_RUNTIME_REJECTED_PARENT_CONNECTION_EXACT_ORIGINAL_REJECTION'
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['connection_contract_tests_passed']==80
        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==176,
        'ORIGINAL_P268_FAILED_NOT_PROMOTED')
    f=doc['small_native_probe'];h=f['handles'];d=h['borrowed_byte_streams']
    require(f['frame_state']=='CLOSED' and f['registered_live_frame'] is False and f['input_count']==3
        and f['actual_byte_boundaries']==[] and h['byte_stream_identity_checks']==0
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==7
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True
        and d['duplicate_handles_opened']==d['duplicate_handles_closed']==d['duplicate_handles_remaining']==0,
        'OLD_SMALL_ACQUISITION_ONLY_CLEANUP')
    require(doc['actual_product_body_or_full_source_executed'] is False and doc['actual_current_case94_reexecuted'] is False,
        'NO_ORIGINAL94_RETRY_OR_BODY_PASS')
    return dict(original_failed_probe_preserved=True,original_small_byte_boundaries_completed=0,
        no_original_sample_code_reproduced_in_separate_synthetic_bridge=True,
        masked_original_error_not_reconstructed_from_receipt=True,original94_failure_reason_still_unavailable=True)



def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p269-rejected-parent-connection-run{args.run:02}.v1.json'
    sidecar=m.p.c.ROOT/f'{m.p.DIR}/cases/p269-rejected-parent-probe-run{args.run:02}.json'
    require(not destination.exists() and not sidecar.exists(),'NO_OVERWRITE')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context)
    q=held=frame=connection=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),qualified_diagnostic_review_pin=QUALIFIED,preserved_failed_probe_pin=FAILED,
        actual_product_body_or_full_source_executed=False,actual_current_case94_reexecuted=False,
        actual_full_runtime_connection_qualified=False,synthetic_original_parent_only=True,
        failed_case94_accepted=False,original_parent_Job_cleanup_not_measured=True)
    try:
        owner.admit();q=m.m.Reader(owner,context)
        plan,required,binding=a.qualified_before_failure(q)
        root=m.m.review.bound_json(q,a.FAILURE);require(q.pin(a.ZERO['path'])==a.ZERO,'ZERO_UNCHANGED')
        checked=a.review(root,a.ZERO,plan,required,binding);qualified=m.m.review.bound_json(q,QUALIFIED)
        require(qualified['schema_version']==a.SCHEMA and qualified['state']==a.PASS
            and qualified['resource_stop_reason'] is None and qualified['resource_watcher_cleanup_confirmed'] is True
            and qualified['IO']['finished'] is True and qualified['IO']['bound_inputs']==qualified['IO']['final_fresh_hashes']==180
            and qualified['diagnostic_contract_tests_passed']==52 and qualified['review']==checked
            and qualified['runtime_plan']==plan and qualified['failed_case94_accepted'] is False
            and qualified['diagnostic_candidate_actual_runtime_connection_qualified'] is False,'LITERAL_P267_CLOSED_ONLY')
        old_probe=m.m.review.bound_json(q,FAILED);out['old_probe_review']=review_failed_probe(old_probe)
        old_code=m.p.v.pins(old_probe['bound_input_pins'])
        for name in (original.SELF,original.TEST):require(q.pin(name)==old_code[name],'OLD_P268_CODE_UNCHANGED')
        frozen=m.p.v.pins(qualified['bound_input_pins'])
        for name in (a.SELF,a.TEST):require(q.pin(name)==frozen[name],'FROZEN_P267_CODE')
        small={name:q.pin(name) for name in (SELF,TEST,a.SELF)}
        report=q.text(REPORT);require(QUALIFIED['sha256'] in report and a.FAILURE['sha256'] in report
            and all(w in report for w in ('runtime 수용87/249','다음index94','P09·A12·A13 OPEN',
                '실제 full runtime 연결 NOT_RUN','원600초·CPU/RAM 기준은 변경하지 않음')),'REPORT_BOUNDARY')
        out.update(connection_contract_tests_passed=contracts((root,a.ZERO,plan,required,binding)),runtime_plan=plan,
            original_failure_review=checked,small_required_pins=list(small.values()))
        q.finish()
        early=m.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
        held=TimedInputLocks(m.p.c.ROOT,early,owner,context)
        frame=m.p.frames.Frame(m.p.frames.Registry(),small,early,held=held)
        counter=m.p.frames.Counters(q.reader,frame.readers);context.reader=counter
        held.mark('before_acquire')
        with context.scope('metadata_hash'):frame.acquire()
        held.mark('after_acquire');connection=ParentConnection(frame,[],94,a.NAME,binding)
        held.mark('before_parent');empty=io.StringIO();calls=[];parent_samples=[]
        def synthetic_parent(task,unused,seconds):
            require(task=='p204-r07-case-094-tests' and seconds==1200,'ORIGINAL_TASK_AND1200');calls.append(task)
            # 원 bridge의 두 pins 호출이 Frame.read_boundary로 이어짐을 실제 byte로 확인.
            sampler=OriginalParentSamples(m.p.c.Windows());parent_samples.append(sampler)
            sampler.admit()
            before=m.p.c.pins(sampler.checkpoint);after=m.p.c.pins(sampler.checkpoint)
            require(m.p.v.pins(before)==m.p.v.pins(after)==small,'REAL_SMALL_SOURCE_NOT_SYNTHETIC_PINS')
            json.dump(fake_original_row(task),empty,ensure_ascii=False,indent=2)
            raise AssertionError('REJECTION_MUST_PROPAGATE')
        with patch.object(m.p,'ORIGINAL_RUN',synthetic_parent), \
                patch('subprocess.Popen',side_effect=AssertionError('NO_PROBE_PRODUCT')), \
                patch('subprocess.run',side_effect=AssertionError('NO_PROBE_PRODUCT')), \
                patch('threading.Thread.start',side_effect=AssertionError('NO_PROBE_THREAD')):
            try:connection.run(None,context)
            except ValueError as error:
                out['original_probe_exception_code']=closed_code(error)
                require(str(error)=='TERMINAL_FAILURE_EXACT_STOP_NOT_PASS','EXACT_ORIGINAL_REJECTION')
            else:require(False,'ORIGINAL_REJECTION_REQUIRED')
        require(calls==['p204-r07-case-094-tests'] and connection.capture.rejected
            and not connection.capture.pending and empty.getvalue()=='','ONCE_NO_LIVE_SERIALIZATION')
        held.mark('after_parent');held.verify_two_byte_passes(small);held.verify_held_identities();held.mark('before_release')
        require(frame.close(),'SMALL_FRAME_CLOSED')
        out.update(original_parent_bridge_called_once_with_synthetic_run=True,original_error_rethrown_unchanged=True,
            no_live_original_parent_stream_written=True,real_small_native_probe_complete=True,
            real_original_parent_samples=parent_samples[0].summary(),
            small_native_probe=frame.summary(),lock_timing=held.summary()['lock_timing_diagnostic'],
            original_early_source_checkpoint=early.summary())
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='CONNECTION_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='CONNECTION_FRAME_CLEANUP_FAILED';proposed=None
            out['small_native_probe']=frame.summary()
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            validate_probe(doc['small_native_probe'],m.p.v.pins(doc['small_required_pins']),doc['lock_timing'])
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and doc['connection_contract_tests_passed']==COUNT and doc['actual_current_case94_reexecuted'] is False
                and doc['real_original_parent_samples']['original_parent_completed_sample_count']>=2
                and doc['real_original_parent_samples']['CPU_samples_manufactured'] is False,
                'ALL_BOUND_FRESH_AND88_NOT_BODY')
        m.g.complete(out,owner,proposed,validate)
        if connection is not None and connection.capture.rejected:
            try:
                pin,stats=preserve(connection,sidecar,owner,out)
                out.update(small_terminal_diagnostic_pin=pin,small_terminal_diagnostic_statistics=stats,
                    only_small_real_native_and_synthetic_parent_connection_qualified=out['state']==PASS)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
                out.update(state='FAILED_NOT_ACCEPTED',terminal_diagnostic_write_error=m.p.b.run.original.closed_error(error))
        out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','connection_contract_tests_passed','error_code',
            'terminal_diagnostic_write_error','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':
    sys.modules.setdefault('qualify_rejected_parent_connection_r2',sys.modules[__name__])
    raise SystemExit(main())
