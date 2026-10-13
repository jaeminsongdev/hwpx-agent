"""P226: 고정 case060 STOP/빈 body/새 실패 writer 계약 조사. 제품 재시도 없음."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_packed_pressure_runtime as r
import review_packed_cpu_peak_r2 as peak
import terminal_failure_receipt as failure_writer

SELF = 'tools/p09/review_packed_cpu_stop.py'
ROOT = dict(path=r.p.DIR+'/p222-case-060-run020.v1.json', bytes=208007,
    sha256='78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0')
EMPTY = dict(path=r.p.DIR+'/cases/p222-case-060-run020.json', bytes=0,
    sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
LAST = dict(path=r.p.DIR+'/p222-case-059-run019.v1.json', bytes=588180,
    sha256='c7cf3da34fff99b65716bda258bf73d797b1537a7f63f36391743a2c8ed6cea6')
PASS = 'PASS_BOUNDED_STOP_REVIEW_AND_FAILURE_WRITER_SUPPORT_NOT_RUNTIME_OR_GATE'


def contracts():
    sys.path.insert(0, str(r.p.c.ROOT/'tools/p09/tests'))
    import test_terminal_failure_receipt as tests
    with patch('subprocess.Popen', side_effect=AssertionError('NO_STOP_REVIEW_CHILD')), \
         patch('subprocess.run', side_effect=AssertionError('NO_STOP_REVIEW_CHILD')), \
         patch('threading.Thread.start', side_effect=AssertionError('NO_STOP_REVIEW_THREAD')):
        count = peak.contracts()
        result = unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
    r.require(count == 8 and result.wasSuccessful() and result.testsRun == 16 and not result.skipped,
        'STOP_SUPPORT_CONTRACTS')
    return 16


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run',type=int,required=True); args=parser.parse_args()
    r.require(r.p.c.Path.cwd().resolve()==r.p.c.ROOT and 1<=args.run<=99,'STOP_REVIEW_CWD_RUN')
    destination=r.p.c.ROOT/f'{r.p.DIR}/p226-stop-review-run{args.run:02}.v1.json'
    r.require(not destination.exists(),'STOP_REVIEW_FRESH_ONLY')
    context=r.g.observation.Context(); owner=r.g.observation.Resources(context); q=candidate=None
    out=dict(schema_version='hwpx-agent.p09-packed-stop-review/v1',state='FAILED_NOT_ACCEPTED',**r.p.r.flags(),
        product_body_reexecuted=False, original_files_rewritten=False, failure_writer_actual_connection=False,
        failure_writer_support_only=True, runtime_resume_authorized=False,
        CPU_cause_or_PC_freeze_resolution_established=False)
    try:
        owner.admit(); q=r.Reader(owner,context)
        for path in (SELF,failure_writer.SELF,failure_writer.TEST,peak.SELF,peak.TEST,r.compact.SELF,
                     r.p.SELF,r.SELF,r.p.frames.SELF): q.pin(path)
        out['failure_writer_contract_tests_passed']=contracts(); out['peak_summary_contract_tests_passed']=8
        for pin in (ROOT,EMPTY,LAST): r.require(q.pin(pin['path'])==pin,'STOP_LITERAL_PIN')
        stop=q.json(ROOT['path']); last=q.json(LAST['path']); r.closed_attempt(last)
        r.require(stop['state']=='FAILED_NOT_ACCEPTED' and stop['selected_test_index']==60
            and stop['error_code']=='P206_LOCK_P208_FRAME_LIVE_STATE'
            and stop['resource_stop_reason']==failure_writer.STOP
            and stop['resource_watcher_cleanup_confirmed'] is True,'STOP_ORIGINAL_FAILURE')
        frame=stop['terminal_source_frame']; handles=frame['handles']; borrowed=handles['borrowed_byte_streams']
        r.require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
            and handles['input_lock_handles_opened']==handles['input_lock_handles_closed']==1809
            and handles['input_lock_handles_remaining']==handles['active_byte_streams']==handles['active_reader_bindings']==0
            and handles['input_lock_cleanup_confirmed'] is True
            and handles['handle_close_failed_attempts']==0
            and borrowed['duplicate_handles_opened']==borrowed['duplicate_handles_closed']==2210
            and borrowed['duplicate_handles_remaining']==borrowed['duplicate_close_failed_attempts']==0,
            'STOP_ALL_LOCKS_AND_STREAMS_CLOSED')
        r.require(last['runtime_plan']['runtime_source_qualified_individual_cases']==53
            and last['runtime_plan']['next_runtime_index']==60
            and stop['prior_runtime_plan']==last['runtime_plan'],'STOP_NEXT_UNACCEPTED_NOT_REPEAT')
        plan=last['runtime_plan']
        out.update(original_stop_pin=ROOT,empty_body_pin=EMPTY,last_accepted_pin=LAST,
            runtime_plan=plan, stop_peak_review=peak.summarize(stop['metadata_observation']['samples']),
            source_handles_closed=1809,duplicate_streams_closed=2210,
            original_failure_preserved=True,empty_body_semantic_or_job_result_established=False,
            system_CPU_peak=stop['metadata_observation']['system_cpu_max_percent'],
            own_CPU_machine_peak=stop['metadata_observation']['own_cpu_max_machine_percent'],
            available_RAM_min_percent=stop['metadata_observation']['available_ram_min_percent'],
            failure_writer_live_frame_check_removed_only_after_terminal_cleanup=True,
            failure_writer_gzip_removed_only_for_terminal_failure=True)
        q.finish(); candidate=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=r.p.b.run.original.closed_error(e)
    finally:
        if q is not None: out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        r.g.complete(out,owner,candidate,lambda row:r.require(row['IO']['finished'] is True
            and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']
            and row['failure_writer_contract_tests_passed']==16,'STOP_REVIEW_ALL_FRESH'))
        with destination.open('x',encoding='utf-8') as stream: json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason',
            'resource_watcher_cleanup_confirmed','failure_writer_contract_tests_passed','stop_peak_review')},ensure_ascii=True))
    return 0 if out['state']==PASS else 2


if __name__=='__main__': raise SystemExit(main())
