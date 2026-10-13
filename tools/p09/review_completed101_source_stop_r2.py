"""P297: source-acquire STOP의 제한된 수치 검토. 수용/재시도/새 Native 실행 없음."""
import copy
import hashlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import close_completed101_source_frame_r4 as c
m=c.m
SELF='tools/p09/review_completed101_source_stop_r2.py'
TEST='tools/p09/tests/test_completed101_source_stop_r2.py'
PIN=dict(path=m.p.DIR+'/p295-r4-case101-source-actual-run02.v1.json',bytes=300662,
    sha256='e19a2c8cbef7a83953fc68b83952700e204235e11a7fe571c5d6ef51bea9fd04')
SCHEMA='hwpx-agent.p09-completed101-source-acquire-stop-review-r2/v1'
PASS='PASS_SOURCE_ACQUIRE_STOP_REVIEW_ONLY_NOT_SOURCE_RUNTIME_OR_GATE'
COUNT=14

def require(ok,code):c.require(ok,'STOP_REVIEW_'+code)

def review(d):
    require(d['schema_version']==c.SCHEMA and d['state']=='FAILED_NOT_ACCEPTED'
        and d['error_code']==d['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and d['resource_watcher_cleanup_confirmed'] is True
        and d['failure_diagnostic']['stage']=='source_acquire','EXACT_STOP_NOT_ACCEPTED')
    original=m.p.v.pins(d['original_executed_source_pins']);extras=m.p.v.pins(d['extra_controller_pins'])
    # STOP은 준비 PASS validator로 검증할 수 없다. 실제 실패 상태를 유지하며 범위만 검토.
    require(len(original)==1599 and sum(x['bytes'] for x in original.values())==119993724
        and set(extras)==set(c.EXTRAS) and not set(original)&set(extras)
        and all(extras.get(p['path'])==p for p in c.OLD_CODE)
        and d['original_failed_root_pin']==c.review.ROOT and d['original_stopped_parent_pin']==c.review.BODY
        and d['original_zero_placeholder_pin']==c.review.ZERO and d['stop_review_pin']==c.REVIEW_PIN
        and d['closing_contract_tests_passed']==27 and d['nominal_scope_budget']==c.budget({**original,**extras})
        and d['preparation_IO']['finished'] is True
        and d['preparation_IO']['bound_inputs']==d['preparation_IO']['final_fresh_hashes']==26
        and d['preparation_IO']['maximum_scope_seconds']==600,'FULL_SCOPE_PREPARATION_RETAINED')
    require(d['early_source_native_and_byte_guard_connected'] is True
        and d['early_source_runtime_connection_verified'] is False
        and d['actual_product_body_executed'] is False and d['runtime_acceptance_changed'] is False,
        'SOURCE_ONLY_NO_RUNTIME_ADVANCE')
    f=d['source_frame'];h=f['handles'];t=h['lock_timing_diagnostic'];e=t['first_original_error']
    require(f['frame_state']=='CLOSED' and f['registered_live_frame'] is False
        and f['input_count']==1617 and f['input_bytes']==120176339
        and f['actual_byte_boundaries']==[] and f['held_identity_after_owned_cleanup'] is None,
        'NO_FULL_SOURCE_OR_IDENTITY_ACCEPTANCE')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==111
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['borrowed_byte_streams'] is None and h['byte_stream_identity_checks']==0
        and h['separate_pathname_reopens']==0 and h['file_write_or_delete_operation_executed'] is False,
        'ALL111_CLOSED_WITHOUT_BYTE_BOUNDARY')
    require(t['original_guard_checks']==2063 and e['guard_check_number']==2063
        and e['original_error_code']=='STOP_SUSTAINED_SYSTEM_CPU'
        and e['original_lock_elapsed_seconds']==10.482585999998264
        and e['original_lock_limit_seconds']==h['maximum_lock_seconds']==600
        and t['original_resource_guard_or_deadline_extended'] is False
        and t['extra_CPU_RAM_or_native_query_started'] is False,'GUARDS_UNCHANGED')
    ac=h['acquisition_phase_pressure'];early=d['early_source_checkpoint']
    require(ac['acquisition_maximum_reservations_per_second']==14
        and ac['original_global_and_byte_reservation_ceiling_per_second']==ac['restored_original_rate']==20
        and ac['acquisition_complete'] is False and ac['acquisition_reservations']==111
        and ac['extra_sampler_or_thread_started'] is False
        and early['warning_entries']==1 and early['completed_pause_windows']==5
        and early['requested_pause_seconds']==2.5 and early['original_hard_CPU_RAM600_guards_preserved'] is True,
        'PACED_STOP_NOT_BLIND_RETRY')
    obs=d['metadata_observation'];rows=obs['samples']
    require(len(rows)==obs['completed_sample_count']==29
        and obs['system_cpu_max_percent']==100 and obs['own_cpu_max_machine_percent']==2.111324
        and obs['own_private_max_bytes']==33923072 and obs['own_working_set_max_bytes']==44093440
        and obs['available_ram_min_percent']==23.494607605443335
        and obs['foreign_PID_query_executed'] is False and obs['new_sampler_thread_started'] is False,
        'BOUND_NUMERIC_OBSERVATION')
    require(all(x['system_cpu_percent']==100 and x['parent_cpu_machine_percent']==0
        and x['audited_logical_read_bytes_delta']==0 for x in rows[-4:]),'SATURATION_WITH_ZERO_OWN_WORK_LAST4')
    require(d['P09_gate']==d['A12_gate']==d['A13_gate']=='OPEN'
        and all(d[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'NO_GATE_OR_CAUSE_PROMOTION')
    return dict(selected_case=101,body_reexecution_allowed=False,source_retry_performed=False,
        original_failed_source_receipt_preserved=True,full_source_closing_accepted=False,runtime_advance=False,
        reviewed_stage='source_acquire',source_byte_boundaries_completed=0,opened_and_closed_handles=111,
        lock_elapsed_seconds=e['original_lock_elapsed_seconds'],guard_checks=2063,scope_deadline_seconds=600,
        host_CPU_max_percent=100,own_CPU_max_machine_percent=2.111324,
        own_private_max_bytes=33923072,own_working_set_max_bytes=44093440,
        minimum_available_RAM_percent=23.494607605443335,last4_own_CPU_and_read_delta_zero=True,
        direct_own_CPU_saturation_not_demonstrated=True,indirect_or_external_cause_not_excluded=True,
        CPU_cause_or_PC_freeze_resolution_established=False,all_original_guards_retained=True,
        runtime_qualified_cases=94,pending_source_closing_candidates=1,next_unaccepted_case=101,
        remaining_runtime_cases=155,regular_remaining=149,corpus_remaining=6)

def contracts(d):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'));import test_completed101_source_stop_r2 as tests
    with patch.object(tests,'FIXTURE',d),patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
        patch('subprocess.run',side_effect=AssertionError('NO_CHILD')),patch('threading.Thread.start',side_effect=AssertionError('NO_NEW_THREAD')):
        r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(r.wasSuccessful() and r.testsRun==COUNT and not r.skipped,'CONTRACT14')
    return COUNT

def main():
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT,'CWD')
    dst=m.p.c.ROOT/(m.p.DIR+'/p297-r2-case101-source-stop-review-run01.v1.json');require(not dst.exists(),'FRESH_ONLY')
    ctx=m.g.observation.Context();o=m.g.observation.Resources(ctx);q=None;proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),failed_source_pin=PIN,
        actual_product_body_executed=False,actual_source_frame_executed=False)
    try:
        o.admit();q=m.Reader(o,ctx);d=m.m.review.bound_json(q,PIN)
        bad=m.m.review.bound_json(q,dict(path=m.p.DIR+'/p297-case101-source-stop-review-run01.v1.json',
            bytes=6396,sha256='7d2637a66941af644e9ef4124bf9bd00af6fcc47382a07e9c3b44a4adeb4e7c1'))
        require(bad['state']=='FAILED_NOT_ACCEPTED' and bad['resource_stop_reason'] is None
            and bad['resource_watcher_cleanup_confirmed'] is True
            and bad['error_code']=='P208_POST_STOP_RUNTIME_DIAGNOSTIC_RUNTIME_COMPLETED101_SOURCE_SOURCE_ONLY_NO_PROMOTION',
            'PRIOR_REVIEW_STOP_PASSED_TO_PREPARATION_VALIDATOR_REJECTED_NOT_ACCEPTED')
        out['prior_failed_review_preserved_not_accepted']=True
        out['review']=review(d);out['review_contract_tests_passed']=contracts(d)
        out['review_code_pins']=[q.pin(n) for n in (SELF,TEST,c.SELF,c.TEST,
            'tools/p09/accept_completed101_compound_r4.py','tools/p09/tests/test_completed101_compound_r4.py')]
        q.finish();proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as err:
        out['error_code']=m.p.b.run.original.closed_error(err)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['review']==review(d) and doc['review_contract_tests_passed']==COUNT
                and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']==8
                and doc['actual_product_body_executed'] is False and doc['actual_source_frame_executed'] is False,
                'REVIEW_ONLY')
        m.g.complete(out,o,proposed,validate)
        # 원 표본은 실패 receipt에 그대로 보존. 새 review는 전체 로그를 복제하지 않는다.
        obs=m.g.observation.summary(o)
        out['review_observation']={k:v for k,v in obs.items() if k!='samples'}
        with dst.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','review_contract_tests_passed')}))
    return 0 if out['state']==PASS else 2
if __name__=='__main__':raise SystemExit(main())
