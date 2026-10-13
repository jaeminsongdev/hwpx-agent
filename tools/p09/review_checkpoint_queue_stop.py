"""P257: case090 STOP 검토와 새 source checkpoint 조기 완화 후보.

본문·전체source 재실행/수용 없음. 수용 코드·98x4/RAM/600초 guard 불변.
새 독립 source 경로에 명시 연결할 때만 90%부터 기존 표본으로 쉰다.
"""
import argparse
import io
import json
import math
import sys
import unittest
from unittest.mock import patch
import resume_checkpoint_metadata_runtime as m
import review_packed_cpu_peak_r2 as peak
import sync_checkpoint_metadata_runtime_documents as docs

SELF='tools/p09/review_checkpoint_queue_stop.py'
TEST='tools/p09/tests/test_checkpoint_queue_stop.py'
ROOT_PIN=dict(path=m.p.DIR+'/p255-case-090-run010.v1.json',bytes=766447,
    sha256='cc598cbc42c399b64eadcd35868f142b3ba51a09d81265029b95f2e4be3595f6')
BODY_PIN=dict(path=m.p.DIR+'/cases/p255-failure-090-run010.json',bytes=483214,
    sha256='8ce9dfaa8a5efc8f7ef5290f254f6e551098dfcc50aa5ba3ec3393831d8e8e4c')
ZERO_PIN=dict(path=m.p.DIR+'/cases/p255-case-090-run010.json',bytes=0,
    sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
PREVIOUS=dict(path=m.p.DIR+'/p256-checkpoint-metadata-status-doc-r0105-run01.v1.json',bytes=57941,
    sha256='987793c7fbef6a1cec7d3916c1f69c6622cb29a824721ede08e3ddca7ab5e5f3')
NAME='actual_import::formula_policy_revocation::changed_current_policy_denies_before_revocation_write'
SCHEMA='hwpx-agent.p09-checkpoint-queue-stop-review/v1'
PASS='PASS_CASE090_STOP_REVIEW_EARLY_SOURCE_CANDIDATE_NOT_RUNTIME_SOURCE_OR_GATE'
STOP='STOP_SUSTAINED_SYSTEM_CPU'
WARNING=90
COOL=2
MAX_WINDOWS=8
REPORT='implementation/p09/P09-257_CASE090_STOP_EARLY_SOURCE_REPORT.md'
STATUS_DOCS=m.MUTABLE_DOCS


def require(ok,code):m.require(ok,'CHECKPOINT_STOP_'+code)


class EarlySourceCheckpoint:
    """원 checkpoint를 매번 먼저 실행; cached sample은 냉각 증거가 아니다."""
    def __init__(self,base,resources,*,sleep=m.entry.locks.time.sleep):
        require(callable(base) and callable(sleep),'SOURCE_CALLBACKS')
        self.base=base;self.resources=resources;self.sleep=sleep
        self.warning_entries=0;self.windows=0;self.maximum=0
    def latest(self):
        with self.resources.lock:
            require(bool(self.resources.samples),'SOURCE_SAMPLE_MISSING')
            row=self.resources.samples[-1]
        value=row['system_cpu_percent']
        require(type(value) in (int,float) and math.isfinite(value) and 0<=value<=100,'SOURCE_CPU_INVALID')
        return row,value
    def __call__(self):
        self.base();row,value=self.latest()
        if value<WARNING:return
        self.warning_entries+=1;cool=windows=0
        while cool<COOL:
            require(windows<MAX_WINDOWS,'STOP_EARLY_SOURCE_NOT_COOLING')
            previous=row;self.sleep(m.p.c.POLICY['sample_seconds'])
            windows+=1;self.windows+=1;self.maximum=max(self.maximum,windows)
            self.base();row,value=self.latest()
            require(row is not previous,'SOURCE_SAMPLE_NOT_ADVANCED')
            cool=cool+1 if value<WARNING else 0
    def summary(self):
        return dict(early_source_warning_CPU_percent=WARNING,cool_distinct_samples=COOL,
            maximum_pause_windows=MAX_WINDOWS,warning_entries=self.warning_entries,
            completed_pause_windows=self.windows,maximum_observed_pause_windows=self.maximum,
            requested_pause_seconds=self.windows*m.p.c.POLICY['sample_seconds'],
            original_guard_called_before_pressure=True,original_hard_CPU_RAM600_guards_preserved=True,
            existing_owner_samples_only=True,new_sampler_or_thread_started=False,
            source_byte_reads_or_identity_checks_skipped=False,
            cleanup_callback_wrapped=False,CPU_or_PC_freeze_improvement_established=False)


def review(root,body):
    require(root['schema_version']==m.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']=='ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED'
        and root['resource_stop_reason']==STOP and root['resource_watcher_cleanup_confirmed'] is True
        and root['original_parent_STOP_captured_not_accepted'] is True
        and root['accepted_exact_product_body_count']==0,'OUTER_STOP_NOT_PASS')
    require(root['terminal_parent_failure_sidecar_pin']==BODY_PIN and root['case_receipt_path']==ZERO_PIN['path']
        and root['original_failure_body_placeholder_preserved'] is True
        and root.get('terminal_failure_write_error') is None,'IMMUTABLE_FAILURE_LINKS')
    plan=root['prior_runtime_plan'];require(root['selected_test_index']==90 and root['selected_test_name']==NAME
        and plan['runtime_source_qualified_individual_cases']==83 and plan['next_runtime_index']==90
        and plan['runtime_remaining_individual_cases']==166,'EXACT_PRIOR83_PENDING90')
    require(body['schema_version']==m.p.SCHEMA and body['state']=='STOPPED_NOT_ACCEPTED'
        and body['stop_reason']==body['resource_stop_reason']==STOP
        and body['operation_phase']=='final_source_freeze','ORIGINAL_POST_SOURCE_STOP')
    require(body['binding']==root['binding'] and body['selected_test_names']==body['passed_test_names']==[NAME]
        and body['test_arguments']==m.p.v.arguments(NAME)
        and body['task']==body['minimal_worker_task']=='p204-r07-case-090-tests'
        and body['minimal_owned_worker_path']==m.p.m.SELF,'EXACT_BODY_IDENTITY')
    require(type(body['exit_code']) is int and body['exit_code']==0 and body.get('tests_passed') is None
        and body['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and body['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False),
        'COMPLETED_BODY_NOT_COMPLETE_PARENT')
    capture=body['capture_diagnostics'];require(capture['error_code'] is None
        and capture['buffered_bytes']==capture['received_bytes']
        and capture['per_stream_limit_bytes']==32768 and capture['raw_log_content_included'] is False,
        'BOUNDED_COMPLETE_CAPTURE')
    require(body['policy']==m.p.c.POLICY and type(body['maximum_seconds']) is int
        and body['maximum_seconds']==1200 and all(body[k] is True for k in
        ('cleanup_confirmed','owned_tree_empty','worker_created','job_assigned','writer_authorized',
         'actual_job_membership_checked','owned_limits_verified','minimal_worker_source_only_import_connected',
         'actual_product_child_executed')),'ORIGINAL_POLICY_GO_CLEANUP')
    limits=body['owned_limits_readback'];require(limits['verified'] is True
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384 and limits['active_process_limit']==16
        and limits['kill_on_close'] is True and limits['breakaway_disabled'] is True
        and type(body['job_final']['active_processes']) is int and body['job_final']['active_processes']==0
        and body['job_final']['owned_processes']==[],'EXACT_JOB_LIMITS_AND_EMPTY')
    frame=root['terminal_source_frame'];pins=m.p.v.pins(body['source_freeze']);bounds=frame['actual_byte_boundaries']
    readers=body['owned_source_reader_passes'];require(len(pins)==frame['input_count']==1545
        and sum(p['bytes'] for p in pins.values())==frame['input_bytes']==119242806
        and pins.get(m.p.m.EXE['path'])==m.p.m.EXE and len(bounds)==1 and bounds[0]['role']=='before'
        and m.p.v.pins(bounds[0]['actual_byte_pins'])==pins,'FULL_ORIGINAL_BEFORE_SOURCE')
    require(len(readers)==2 and readers[0]==bounds[0]['reader_diagnostics']
        and readers[0]['read_passes']==1545 and readers[0]['bytes_read']==119242806
        and readers[1]['read_passes']==321 and readers[1]['bytes_read']==53845255
        and all(row['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and row['original_owned_read_operations_preserved'] is True
            and row['extra_sampler_or_native_query_started'] is False for row in readers),'PARTIAL_AFTER_NOT_FULL')
    h=frame['handles'];dup=h['borrowed_byte_streams'];require(frame['frame_state']=='CLOSED'
        and frame['registered_live_frame'] is False and frame['original_owned_cleanup_confirmed_before_release'] is False
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==1851
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['byte_stream_identity_checks']==1866
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==1866
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False,'CLOSED_PARTIAL_FRAME_NO_RESIDUE')
    pressure=h['native_open_backpressure'];require(pressure['warning_entries']==1
        and pressure['completed_pause_windows']==3 and pressure['requested_pause_seconds']==1.5
        and pressure['original_hard_resource_decisions_unmodified'] is True
        and pressure['original_IO_deadline_unmodified'] is True
        and pressure['original_sampler_windows_reused'] is True
        and pressure['original_read_checks_skipped'] is False,'OBSERVED_ORIGINAL_NATIVE_YIELD')
    require(root['preparation_IO']['finished'] is True
        and root['preparation_IO']['bound_inputs']==root['preparation_IO']['final_fresh_hashes']==134
        and root['preparation_IO']['read_passes']==280,'COMPLETE_PREPARATION_NOT_COMPLETE_SOURCE')
    require(all(row[k] is False for row in (root,body) for k in
        ('full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and all(row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN' for row in (root,body)),
        'NO_GATE_OR_FREEZE_PROMOTION')
    return dict(selected_test_index=90,selected_test_name=NAME,semantic_body_capture_complete=True,
        runtime_previously_accepted=83,new_pending_source_closing_candidates=1,
        runtime_acceptance_changed=False,same_product_body_reexecution_allowed=False,
        original_failed_receipts_preserved=True,independent_full_source_closing_required=True,
        original_partial_source_read_promoted=False,CPU_cause_or_freeze_resolution_established=False)


def contracts(root,body):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    import test_checkpoint_queue_stop as tests
    with patch.object(tests,'FIXTURES',(root,body)),patch('subprocess.Popen',side_effect=AssertionError('NO_STOP_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_STOP_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_STOP_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
        retained=peak.contracts()
    require(result.wasSuccessful() and result.testsRun==32 and not result.skipped and retained==8,'32_PLUS_ORIGINAL_PEAK8')
    return dict(stop_and_early_source_contract_tests_passed=32,original_peak_contract_tests_passed=8)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    path=m.p.c.ROOT/f'{m.p.DIR}/p257-case090-stop-review-run{args.run:02}.v1.json';require(not path.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),
        original_failed_root_pin=ROOT_PIN,original_stopped_parent_pin=BODY_PIN,original_zero_placeholder_pin=ZERO_PIN,
        previous_document_receipt_pin=PREVIOUS,actual_product_body_executed=False,
        independent_full_source_frame_executed=False,early_source_runtime_connection_verified=False,
        original_partial_post_source_hash_completed=False)
    try:
        owner.admit();q=m.Reader(owner,context)
        root=m.review.bound_json(q,ROOT_PIN);body=m.review.bound_json(q,BODY_PIN)
        require(q.pin(ZERO_PIN['path'])==ZERO_PIN,'ZERO_PRESERVED');checked=review(root,body)
        previous=m.review.bound_json(q,PREVIOUS);require(previous['schema_version']==docs.SCHEMA
            and previous['state']==docs.PASS and previous['resource_stop_reason'] is None
            and previous['resource_watcher_cleanup_confirmed'] is True and previous['IO']['finished'] is True
            and previous['runtime_plan']==root['prior_runtime_plan'],'SEALED_PRIOR83_DOCUMENT')
        old=m.p.v.pins(previous['bound_input_pins']);prefixes=[]
        for name in (docs.SELF,docs.TEST):require(q.pin(name)==old[name],'PREVIOUS_DOC_HELPERS_UNCHANGED')
        for name in STATUS_DOCS:
            archive='implementation/p09/evidence/runtime-progress-r105/'+name.split('/')[-1]
            before=bytes(docs.bytes_docs.bound_bytes(q,archive));after=bytes(docs.bytes_docs.bound_bytes(q,name))
            require(q.reader.snapshots[archive]==dict(old[name],path=archive) and after.endswith(before),'EXACT_R105_SUFFIX')
            prefix=after[:-len(before)].decode('utf-8');require(prefix.startswith('> P257 runtime-r106 ')
                and all(w in prefix for w in ('runtime 수용83/249','잔여166(일반160+corpus6)',
                    '독립source 마감대기1','다음index90','P09·A12·A13 OPEN','원 STOP/FAILED 보존')),'STOP_STATUS_NOT_ADVANCE')
            prefixes.append(prefix)
        require(prefixes[0]==prefixes[1],'IDENTICAL_STATUS_PREFIXES')
        report=bytes(docs.bytes_docs.bound_bytes(q,REPORT)).decode('utf-8')
        require(all(pin['sha256'] in report for pin in (ROOT_PIN,BODY_PIN,ZERO_PIN,PREVIOUS))
            and '원600초·CPU/RAM 기준은 변경하지 않음' in report and '본문 재실행 없음' in report,'REPORT_BOUNDARIES')
        for name in (SELF,TEST,peak.SELF,peak.TEST):q.pin(name)
        out.update(contracts(root,body),review=checked,root_peak=peak.summarize(root['metadata_observation']['samples']),
            parent_peak=peak.summarize(body['samples']),early_source_candidate_policy=dict(warning_CPU_percent=WARNING,
                cool_distinct_samples=COOL,maximum_pause_windows=MAX_WINDOWS,
                original_hard_guards_preserved=True,new_sampler_or_thread=False,runtime_connected=False),
            exact_r105_document_bytes_preserved=True,status_revision=106,report_pin=q.reader.snapshots[REPORT])
        q.finish();proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==15
                and doc['stop_and_early_source_contract_tests_passed']==32
                and doc['original_peak_contract_tests_passed']==8,'ALL15_FRESH_AND40_CONTRACTS')
        m.g.complete(out,owner,proposed,validate)
        with path.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason',
            'stop_and_early_source_contract_tests_passed','original_peak_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
