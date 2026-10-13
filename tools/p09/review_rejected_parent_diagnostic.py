"""P267: case094 원 parent 유실 검토 및 거절된 row의 종료 후 진단 보존.

P265/P239/CPU 수용 코드 불변. 실패 row는 PASS가 아니며 재실행 허가도 아니다.
새 Capture는 합성 qualification 대상으로만 사용한다. runtime 연결은 NOT_RUN.
"""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import resume_monotonic_compound_runtime as m
import sync_monotonic_compound_runtime_documents as docs
import review_packed_cpu_peak_r2 as peak
import receipt_compact_json as compact

SELF='tools/p09/review_rejected_parent_diagnostic.py'
TEST='tools/p09/tests/test_rejected_parent_diagnostic.py'
SCHEMA='hwpx-agent.p09-rejected-parent-diagnostic-review/v1'
PASS='PASS_REJECTED_PARENT_REVIEW_AND_SYNTHETIC_CAPTURE_NOT_RUNTIME_OR_GATE'
MAX_BYTES=16*1024*1024
FAILURE=dict(path=m.p.DIR+'/p265-case-094-run004.v1.json',bytes=1345290,
    sha256='c347fd3df25cd2b4d52db6f8c27e6325c039f803ab0987f8e0902ac9005f31f9')
ZERO=dict(path=m.p.DIR+'/cases/p265-case-094-run004.json',bytes=0,
    sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
LIGHT=dict(path=m.p.DIR+'/p265-light-run001.v1.json',bytes=27093,
    sha256='13ab50c976f4a0309c4d686a9102e3c30577cc3b03899e0b528897602d6b317e')
PAIRS=(dict(path=m.p.DIR+'/p265-case-092-run002.v1.json',bytes=613296,
    sha256='e5c477adf0ea021a15f80febcd70aef552b0135543bda273366db159095155ab'),
    dict(path=m.p.DIR+'/p265-case-093-run003.v1.json',bytes=599016,
    sha256='633db64d0d75fc206731b45b28c4581fc91161335cb145ef2e56dedb62b36c3a'))
PREVIOUS=dict(path=m.p.DIR+'/p266-monotonic-compound-status-doc-r0109-run01.v1.json',bytes=63618,
    sha256='d8dc2c028d57993631b360a3638cbe0bd7b8cad215209c84d031ec6b1d7f8e80')
NAME='actual_import::formula_policy_revocation::revocation_denies_existing_prepared_formula_callback_and_preserves_original_artifacts'
FLAGS=('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
    'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')
REPORT='implementation/p09/P09-267_CASE094_REJECTED_PARENT_DIAGNOSTIC_R0110_REPORT.md'
COUNT=52


def require(ok,code):m.require(ok,'REJECTED_PARENT_'+code)


def no_promotion(row):
    require(all(row.get(k) is False for k in FLAGS)
        and all(row.get(k)=='OPEN' for k in ('P09_gate','A12_gate','A13_gate')),'NO_PROMOTION')


def signature(row):
    return tuple(row.get(k) for k in ('state','stop_reason','resource_stop_reason'))


class Capture(m.m.support.candidate.Capture):
    """原 CPU/PASS path를 유지하고, 원 validator의 거절을 그대로 다시 발생.

    live 오류 경로에서는 원 row 참조와 닫힌 오류 코드만 보관한다. deep copy,
    IO, 압축, 새 sample, Native query 없음. 종료 진단은 별도 명시 호출만 가능.
    """
    def __init__(self,*args,**keywords):
        super().__init__(*args,**keywords)
        self._rejected=None;self._rejection_code=None;self._signature=None;self._diagnostic_attempted=False

    @property
    def rejected(self):return self._rejected is not None

    def writer(self,document,stream,**keywords):
        require(keywords==dict(ensure_ascii=False,indent=2),'ORIGINAL_OPTIONS')
        require(not self._seen and not self.pending and not self.rejected and not self._written,'ONE_ORIGINAL_ATTEMPT')
        if isinstance(document,dict) and document.get('state') in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED'):
            # 다른 parent나 잘못된 identity는 보존 후보에도 등록하지 않는다.
            self._identity(document)
            try:return super().writer(document,stream,**keywords)
            except ValueError as error:
                require(self._seen and not self.pending,'ORIGINAL_REJECTION_BEFORE_CAPTURE')
                self._rejected=document;self._signature=signature(document)
                code=str(error)
                self._rejection_code=code if re.fullmatch(r'[A-Z0-9_]{1,256}',code) else 'REJECTED_PARENT_VALUE_ERROR'
                raise
        return super().writer(document,stream,**keywords)

    def write_rejected(self,stream,owner,out):
        require(self.rejected and not self.pending and not self._diagnostic_attempted,'ONE_REJECTED_DIAGNOSTIC')
        require(owner.done.is_set(),'OWNER_NOT_LIVE')
        snapshot=self.frame.summary()
        require(snapshot.get('frame_state')=='CLOSED' and snapshot.get('registered_live_frame') is False,
            'ORIGINAL_FRAME_RELEASE_ATTEMPT_COMPLETE')
        row=self._rejected
        def checkpoint():
            self._identity(row);no_promotion(row)
            require(signature(row)==self._signature and row['state'] in ('STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED'),
                'ORIGINAL_CRITICAL_VALUES_UNCHANGED')
            require(owner.done.is_set(),'OWNER_RESTART_DENIED')
        checkpoint()
        envelope=dict(schema_version='hwpx-agent.p09-rejected-parent-terminal-diagnostic/v1',
            state='REJECTED_ORIGINAL_PARENT_DIAGNOSTIC_NOT_ACCEPTED',diagnostic_only=True,runtime_accepted=False,
            original_parent_document=row,original_validation_error=self._rejection_code,
            owner_done=owner.done.is_set(),owner_stop_reason=owner.reason,
            owner_cleanup_confirmed=out.get('resource_watcher_cleanup_confirmed'),original_frame_snapshot=snapshot,
            cleanup_values_retained_not_qualified=True,unknown_measurements_not_zeroed=True,
            original_parent_state_reason_preserved=True,product_body_executed_by_diagnostic=False,
            live_guard_sampler_or_frame_restarted=False,CPU_or_PC_freeze_improvement_established=False)
        written=0
        class Bounded:
            def write(self,block):
                nonlocal written
                require(isinstance(block,str) and block.isascii() and 0<len(block)<=compact.WRITE_CHARS,'ASCII_BOUND')
                require(written+len(block)<=MAX_BYTES,'MAX_BYTES')
                n=stream.write(block)
                require(type(n) is int and n==len(block),'SHORT_WRITE_NO_RETRY')
                written+=n;return n
        # 쓰기 예외 뒤 재시도 금지. Caller는 exclusive-create와 원 파일 보존 필요.
        self._diagnostic_attempted=True
        stats=compact.dump(envelope,Bounded(),checkpoint=checkpoint,indent=2)
        require(stats['characters_written']==written,'ACCOUNTING')
        return dict(**stats,diagnostic_only=True,runtime_accepted=False,maximum_bytes=MAX_BYTES)


def inventory(roots,bodies):
    require(sorted(roots)==sorted(x['path'].split('/')[-1] for x in (LIGHT,*PAIRS,FAILURE))
        and sorted(bodies)==sorted([x['path'].split('/')[-1].replace('.v1.json','.json') for x in PAIRS]
            +[ZERO['path'].split('/')[-1]]),'LITERAL_INVENTORY_NO_NEW_FAILURE_OR_RETRY')


def qualified_before_failure(q):
    legacy,plan,names,expected,exe,required,extras,*unused=m.anchor(q)
    folder=m.p.c.ROOT/m.p.DIR
    inventory([x.name for x in folder.glob('p265-*.v1.json')],
        [x.name for x in (folder/'cases').glob('p265-*.json')])
    light=m.m.review.bound_json(q,LIGHT);m.closed_attempt(light)
    require(light['state']==m.LIGHT and light['selected_test_index']==92 and light['prior_runtime_plan']==plan,
        'ORIGINAL_LIGHT_PRIOR85')
    binding=m.p.v.identity(names,expected,exe)
    for pin in PAIRS:
        root=m.m.review.bound_json(q,pin);m.closed_attempt(root)
        body=m.m.review.bound_json(q,root['case_receipt_pin'])
        plan=m.record(root,body,root['case_receipt_pin'],required,binding,extras,names,legacy,plan)
    require(plan['runtime_source_qualified_individual_cases']==87 and plan['next_runtime_index']==94,
        'ONLY_ORIGINAL92_AND93_ACCEPTED')
    return plan,required,binding


def review(root,zero,plan,required,binding):
    require(plan['runtime_source_qualified_individual_cases']==87 and plan['next_runtime_index']==94
        and plan['runtime_remaining_individual_cases']==162 and plan['runtime_remaining_regular_cases']==156
        and plan['runtime_remaining_corpus_cases']==6 and plan['runtime_successful_candidates_requiring_closing']==0
        and plan['all_successful_bodies_pending_whole_reconciliation']==84,'LITERAL87_NO_FAILURE_ADVANCE')
    require(root['schema_version']==m.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']=='TERMINAL_FAILURE_EXACT_STOP_NOT_PASS'
        and root['resource_stop_reason'] is None and root['resource_watcher_cleanup_confirmed'] is True
        and root['accepted_exact_product_body_count']==0,'FAILED94_NO_OUTER_CPU_STOP_OR_ACCEPTANCE')
    require(root['selected_test_index']==94 and root['selected_test_name']==NAME and root['binding']==binding
        and root['prior_runtime_plan']==plan and root['case_receipt_path']==ZERO['path'] and zero==ZERO,
        'EXACT94_AND_ZERO_BODY')
    require(all(root.get(k) is None for k in ('terminal_parent_failure_sidecar_pin','terminal_failure_write_error',
        'original_parent_STOP_captured_not_accepted')),'ORIGINAL_PARENT_ROW_UNAVAILABLE_NOT_RECONSTRUCTED')
    require(root['runtime_contract_executions']==558 and root['original_retained_contract_executions']==498
        and root['own_queue_contract_tests_passed']==root['synthetic_following_queue_contract_tests_passed']==30
        and root['receipt_serialization_policy']==m.r.policy() and root['monotonic_binding_policy']==m.review.policy(),
        'ORIGINAL_CONTRACTS_AND_POLICIES')
    f=root['terminal_source_frame'];h=f['handles'];d=h['borrowed_byte_streams']
    require(len(required)==1563 and f['frame_state']=='CLOSED' and f['registered_live_frame'] is False
        and f['input_count']==1563 and f['input_bytes']==sum(x['bytes'] for x in required.values())
        and f['held_identity_after_owned_cleanup'] is None
        and f['original_owned_cleanup_confirmed_before_release'] is False,'INCOMPLETE_ORIGINAL_FRAME_NOT_ACCEPTED')
    boundaries=f['actual_byte_boundaries']
    require(len(boundaries)==1 and boundaries[0]['role']=='before'
        and m.p.v.pins(boundaries[0]['actual_byte_pins'])==required,'ONLY_COMPLETED_BEFORE_BOUNDARY')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==1869
        and h['input_lock_handles_remaining']==h['handle_close_failed_attempts']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['maximum_lock_seconds']==600
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==4975
        and h['byte_stream_identity_checks']==3106 and h['handle_metadata_checks']==4975
        and d['duplicate_handles_opened']==d['duplicate_handles_closed']==d['shared_offset_resets']==3106
        and d['duplicate_handles_remaining']==d['duplicate_close_failed_attempts']==d['byte_stream_pathname_reopens']==0,
        'ORIGINAL_NATIVE_CLEANUP_NOT_ORIGINAL_JOB_PROOF')
    m.early_contract(root['early_source_checkpoint']);m.m.metadata_contract(root['preparation_IO'])
    require(root['preparation_IO']['finished'] is True
        and root['preparation_IO']['bound_inputs']==root['preparation_IO']['final_fresh_hashes']==169
        and root['preparation_IO']['read_passes']==350 and root.get('terminal_metadata_IO') is None,
        'PREP_COMPLETE_NO_AFTER_METADATA_CLAIM')
    no_promotion(root)
    return dict(selected_test_index=94,runtime_previously_accepted=87,runtime_acceptance_changed=False,
        semantic_body_PASS_established=False,original_parent_document_available=False,
        exact_original_parent_stop_reason=None,original_Job_cleanup_established=False,
        completed_before_source_boundary_count=1,completed_after_source_boundary_count=0,
        duplicate_streams_opened_and_identity_checked=3106,after_hash_completion_count=None,
        native_lock_and_duplicate_cleanup_established=True,original600_guard_preserved=True,
        runtime_caller_remains_blocked_by_original_failure=True,automatic_retry_allowed=False,
        diagnostic_candidate_actual_runtime_connection_qualified=False,CPU_cause_or_freeze_resolution_established=False)


def words(plan):
    return (*docs.words(plan),'94번 FAILED 수용 불가','본체 PASS·원 parent 중단 사유·원 Job 정리 확인 불가',
        'CPU 이외 실패 진단 보존은 합성 검증만 완료; 실제 runtime 연결 NOT_RUN',
        '94번 자동 재시도 금지')


def contracts(fixtures):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    import test_rejected_parent_diagnostic as tests
    with patch.object(tests,'FIXTURES',fixtures),patch('subprocess.Popen',side_effect=AssertionError('NO_DIAGNOSTIC_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_DIAGNOSTIC_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_DIAGNOSTIC_THREAD')):
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in
            ('test_deferred_parent_failure','test_rejected_parent_diagnostic'))
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'ALL52_NO_SKIP')
    return COUNT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p267-case094-failure-review-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),document_revision=110,
        original_failure_pin=FAILURE,original_zero_body_pin=ZERO,actual_product_body_or_full_source_executed=False,
        failed_case94_accepted=False,diagnostic_candidate_actual_runtime_connection_qualified=False)
    try:
        owner.admit();q=m.m.Reader(owner,context)
        plan,required,binding=qualified_before_failure(q)
        root=m.m.review.bound_json(q,FAILURE);require(q.pin(ZERO['path'])==ZERO,'ZERO_BYTES_PRESERVED')
        checked=review(root,ZERO,plan,required,binding)
        old=m.m.review.bound_json(q,PREVIOUS)
        require(old['schema_version']==docs.SCHEMA and old['state']==docs.PASS and old['document_revision']==109
            and old['resource_stop_reason'] is None and old['resource_watcher_cleanup_confirmed'] is True
            and old['IO']['finished'] is True and old['IO']['bound_inputs']==old['IO']['final_fresh_hashes']
            and old['runtime_plan']['runtime_source_qualified_individual_cases']==86,'PREVIOUS86_NOT_REWRITTEN')
        old_pins=m.p.v.pins(old['bound_input_pins']);prefixes=[]
        for name in (docs.SELF,docs.TEST):require(q.pin(name)==old_pins[name],'FROZEN_DOCUMENT_HELPERS')
        for name in m.m.MUTABLE_DOCS:
            archive='implementation/p09/evidence/runtime-progress-r109/'+name.split('/')[-1]
            before=bytes(docs.byte_docs.bound_bytes(q,archive));after=bytes(docs.byte_docs.bound_bytes(q,name))
            require(q.reader.snapshots[archive]==dict(old_pins[name],path=archive)
                and len(after)>len(before) and after.endswith(before),'EXACT109_SUFFIX_AND_ARCHIVE')
            prefix=after[:-len(before)].decode('utf-8')
            require(prefix.startswith('> P267 runtime-r110 ') and all(w in prefix for w in words(plan)),
                'FAILURE_AND_CURRENT87_PREFIX')
            prefixes.append(prefix)
        require(prefixes[0]==prefixes[1],'IDENTICAL_PREFIX')
        report=q.text(REPORT)
        require(all(pin['sha256'] in report for pin in (FAILURE,ZERO,PREVIOUS,*PAIRS))
            and all(w in report for w in words(plan)),'REPORT_EXACT_PROOF_AND_BOUNDARY')
        out.update(review=checked,runtime_plan=plan,diagnostic_contract_tests_passed=contracts((root,ZERO,plan,required,binding)),
            failed_root_peak=peak.summarize(root['metadata_observation']['samples']),
            previous_document_receipt_pin=PREVIOUS,accepted_actual_pair_pins=list(PAIRS),report_pin=q.reader.snapshots[REPORT])
        for name in (SELF,TEST):q.pin(name)
        q.finish();out['required_bound_input_names']=sorted(q.reader.snapshots)
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeDecodeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and sorted(p['path'] for p in doc['bound_input_pins'])==doc['required_bound_input_names']
                and doc['diagnostic_contract_tests_passed']==COUNT,'ALL_BOUND_FRESH_AND52')
        m.g.complete(out,owner,proposed,validate);out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','diagnostic_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
