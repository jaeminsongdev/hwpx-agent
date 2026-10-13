"""P326: explicit fresh-reviewed pre-product CPU STOP만 재개할 수 있는 고정 queue.
기존1650 + 새runtime/test2 =1652/code89; 미래STOP마다 controller 소스를 추가하지 않는다.
실패는 수용/진전이 아니다. 원두byte/identity/CPU98x4/RAM/600/720/Job/cleanup 유지.
"""
import argparse
import copy
import hashlib
import io
import json
import re
import sys
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch
import resume_completed102_guarded_contract_runtime as old
import review_compact_completed103_anchor as compact
import resume_compact_completed103_runtime as prior_runtime
import resume_recorded_parent_return_runtime as prior323
m=old.m;p=old.p;g=old.g;r=old.r
accepted=old.accepted;leading=old.leading;inner=old.inner;counter=old.counter;guarded=old.guarded
profile=old.profile;connection=old.connection;review=old.review;early_review=old.early_review
Reader=old.Reader
SELF='tools/p09/resume_reviewed_stop_queue_runtime.py'
TEST='tools/p09/tests/test_reviewed_stop_queue_runtime.py'
ANCHOR=old.ANCHOR;RETAINED_QUALIFIER=old.RETAINED_QUALIFIER;INNER_QUALIFIER=old.INNER_QUALIFIER
FROZEN66=old.FROZEN66;FROZEN70=old.FROZEN70;FROZEN75=old.FROZEN75
NATIVE_STOP=old.NATIVE_STOP;SUPPORT_STATUS=old.SUPPORT_STATUS;IDLE=old.IDLE
COUNTER_QUALIFIER=old.COUNTER_QUALIFIER;COUNTER_REAL=old.COUNTER_REAL
COMPLETED102=old.COMPLETED102;PREPARATION103_STOP=old.PREPARATION103_STOP
GUARDED_QUALIFIER=old.GUARDED_QUALIFIER;STATUS_STOP=old.STATUS_STOP
COMPACT_QUALIFIER={"path":"implementation/p09/evidence/locked-r07/p318-compact-checkpoint-actual103-accepted-run02.v1.json","bytes":71816,"sha256":"8ad8c1da2fc26e4bd873e0c73b75d7e834fbf66ae519521120f0a993dc791c07"}
COMPACT_STATUS={"path":"implementation/p09/evidence/locked-r07/p319-compact103-accepted-status-doc-r0126-run01.v1.json","bytes":71372,"sha256":"5804600b10201fc9c8be08b48fa62f230532a5282619bc2e6f94ce56189b4174"}
COMPACT_CODE=[{"path":"tools/p09/review_compact_completed103_anchor.py","bytes":11588,"sha256":"f7ef6580d7e6982aaaa3e9753aa1a376a1f27628e8413d08a0d873ba3f5efe21"},{"path":"tools/p09/tests/test_compact_completed103_anchor.py","bytes":3454,"sha256":"b3f62d89d71ec9820f518c399c7de3406815f655a2b02c3b766002aef43c3624"}]
PRIOR104={"path":"implementation/p09/evidence/locked-r07/p320-case-104-run002.v1.json","bytes":492480,"sha256":"f7c9a7a9e18bb436fc572fd87f2d62510afa0c51ada5c825b8683c85861250d4"}
PRIOR104_SIDECAR={"path":"implementation/p09/evidence/locked-r07/cases/p320-failure-104-run002.json","bytes":87572,"sha256":"99d5c8d3bf85a7388e8a8702d97159d789688fd39a6707116687fa05a766ef66"}
PRIOR104_REVIEW={"path":"implementation/p09/evidence/locked-r07/p321-compact-runtime104-stop-review-run01.v1.json","bytes":41468,"sha256":"cf67d1446568b012152b88c1db7e01618400eb6b8cc3441da3e796b676854a30"}
PRIOR104_STATUS={"path":"implementation/p09/evidence/locked-r07/p322-compact104-stop-status-doc-r0127-run02.v1.json","bytes":82443,"sha256":"90b48a3fc6b8fe1f1e9114fd28f2e5091d2505f4c63eefc8235b83bcbfcd502f"}
PRIOR104_CODE=[{"path":"tools/p09/resume_compact_completed103_runtime.py","bytes":28353,"sha256":"6df8769314caa3b641ba5ed7a0153001a626a849927ff13ed71eea2a221b36df"},{"path":"tools/p09/tests/test_compact_completed103_runtime.py","bytes":19358,"sha256":"0d98a8f6c2bed3a875548b0321ff02177b6cca8a18fb22bf99e6ea3df615bdba"}]
RETURN_POLICY=dict(parent_return_and_capture_booleans_recorded_before_original_after_parent_guard=True,
    original_after_parent_guard_called_once_without_replacement=True,
    extra_native_query_or_sampler_or_child_started=False,
    CPU_cause_or_PC_freeze_improvement_established=False)
PRIOR323_STOP={"path":"implementation/p09/evidence/locked-r07/p323-case-104-run003.v1.json","bytes":163476,"sha256":"ec440376ecc9ee92c634a8f1ae716347e7778df2c7604576e21506f797b17c84"}
PRIOR323_STATUS={"path":"implementation/p09/evidence/locked-r07/p325-parent-return268-acquisition-stop-status-doc-r0128-run01.v1.json","bytes":110409,"sha256":"30be8b45175826d6df1552ec6f7fb38935edfeaf3cd9e4f23a223a3e28758008"}
PRIOR323_CODE=[{"path":"tools/p09/resume_recorded_parent_return_runtime.py","bytes":37079,"sha256":"b91bada47ceff9bd8861603f310642015bdf1e8befaa1a14782167f618fb31a1"},{"path":"tools/p09/tests/test_recorded_parent_return_runtime.py","bytes":26985,"sha256":"c90818a5d2790f1abf576b519eea09abd879ebf8248f477085ef15b8a421c84b"}]
REVIEW_SCHEMA='hwpx-agent.p09-reviewed-pre-product-stop/v1'
REVIEW_PASS='PASS_FRESH_REVIEWED_PRE_PRODUCT_CPU_STOP_NOT_ACCEPTANCE'
STOP_POLICY=dict(explicit_independent_review_pin_required=True,
    only_CPU_STOP_before_product_is_retryable=True,original_failed_roots_and_empty_bodies_preserved=True,
    accepted_cases_not_replayed=True,failed_rows_do_not_advance_cursor=True,
    current_source_code_and_scope_do_not_grow_per_STOP=True,original_guards_and_complete_source_reads_preserved=True,
    CPU_cause_or_freeze_solution_claimed=False)
FROZEN87=compact.FROZEN81+COMPACT_CODE+PRIOR104_CODE+PRIOR323_CODE
NEW=(compact.SELF,compact.TEST,prior_runtime.SELF,prior_runtime.TEST,prior323.SELF,prior323.TEST,SELF,TEST)
N=1652
DIRECTORIES=308
SCHEMA='hwpx-agent.p09-reviewed-stop-queue-runtime-pair/v1'
PASS='PASS_EXACT_R07_REVIEWED_STOP_QUEUE_RUNTIME_NOT_WHOLE_OR_GATE'
LIGHT='PASS_REVIEWED_STOP_QUEUE_SELECTION_NOT_ACTUAL_OR_GATE'
FILE=re.compile(r'p326-case-([0-9]{3})-run([0-9]{3})\.v1\.json')
COUNT=182
EXECUTED=2*COUNT

def require(ok,code):m.require(ok,'REVIEWED_STOP_QUEUE_RUNTIME_'+code)

def record_return_before_original_guard(out,capture,code,held):
    # capture 원 객체와 부모 반환값만 사용한다. 기록 뒤 같은 原 guard를 반드시 호출한다.
    pending=bool(capture.pending);rejected=bool(capture.rejected)
    out.update(original_parent_return_code=code,
        original_parent_pending_failure_before_after_parent_guard=pending,
        original_parent_rejected_failure_before_after_parent_guard=rejected,
        original_parent_STOP_captured_not_accepted=pending,
        parent_return_status_recorded_before_after_parent_guard=True)
    held.mark('after_parent')

def prior104_contract(root,sidecar,reviewed,status,plan,required,extras,binding):
    require(root.get('schema_version')==prior_runtime.SCHEMA and root.get('state')=='FAILED_NOT_ACCEPTED'
        and root.get('error_code')==root.get('resource_stop_reason')=='STOP_SUSTAINED_SYSTEM_CPU'
        and root.get('resource_watcher_cleanup_confirmed') is True
        and root['accepted_exact_product_body_count']==0
        and root['selected_test_index']==104 and root['prior_runtime_plan']==plan
        and root['binding']==binding and root['scope_budget']==prior_runtime.budget(required,
            {n:p for n,p in required.items() if n not in {v['path'] for v in COMPACT_CODE+PRIOR104_CODE}},
            {v['path']:v for v in COMPACT_CODE+PRIOR104_CODE})
        and root['extra_frame_controller_pins']==list(extras.values())
        and root['scope_added_four_pins']==COMPACT_CODE+PRIOR104_CODE
        and root['terminal_parent_failure_sidecar_pin']==PRIOR104_SIDECAR,
        'EXACT_FAILED104_BOUND_SCOPE_NOT_PASS')
    prior_runtime.guarded_contract(root['contract_checkpoint_statistics'])
    prep=root['preparation_IO']
    require(root['runtime_contract_executions']==200 and prep['finished'] is True
        and prep['bound_inputs']==prep['final_fresh_hashes']==95 and prep['read_passes']==190,
        'PRIOR200_QUALIFIED_REUSED_NOT_EXECUTED')
    frame=root['terminal_source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1648 and frame['input_bytes']==120579465
        and frame['actual_byte_boundaries']==[] and frame['held_identity_after_owned_cleanup'] is None
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==1956
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==1155
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0,
        'FAILED_NATIVE_ALL_HANDLES_CLOSED_NOT_COMMITTED')
    require(sidecar['state']=='DEFERRED_NOT_STARTED' and sidecar['task']=='p204-r07-case-104-tests'
        and sidecar['actual_product_child_executed'] is False and sidecar['exit_code'] is None
        and sidecar['resource_stop_reason']==sidecar['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and sidecar['owned_tree_empty'] is True and sidecar['cleanup_confirmed'] is True
        and len(sidecar['owned_source_reader_passes'])==1
        and sidecar['owned_source_reader_passes'][0]['read_passes']==1155
        and sidecar['owned_source_reader_passes'][0]['bytes_read']==76579293,
        'DEFERRED_BEFORE_PRODUCT_PARTIAL_SOURCE_NOT_QUALIFIED')
    require(reviewed['state']=='ACTUAL104_STOP_REVIEW_NOT_ACCEPTANCE'
        and reviewed['root_pin']==PRIOR104 and reviewed['sidecar_pin']==PRIOR104_SIDECAR
        and reviewed['resource_watcher_cleanup_confirmed'] is True and reviewed['resource_stop_reason'] is None
        and reviewed['IO']['finished'] is True
        and reviewed['IO']['bound_inputs']==reviewed['IO']['final_fresh_hashes']==3
        and reviewed['IO']['read_passes']==6 and reviewed['actual_product'] is False,
        'QUALIFIED_STOP_REVIEW_NO_PRODUCT_REPLAY')
    require(status['state']=='PASS_EXACT97_AND_R127_COMPACT104_STOP_DOCUMENTS_NOT_PRODUCT_OR_GATE'
        and status['runtime_plan']==plan and status['new_runtime_cases_accepted']==0
        and status['failed104_root_pin']==PRIOR104 and status['failed104_sidecar_pin']==PRIOR104_SIDECAR
        and status['stop_review_pin']==PRIOR104_REVIEW
        and status['resource_watcher_cleanup_confirmed'] is True and status['resource_stop_reason'] is None
        and status['IO']['finished'] is True
        and status['IO']['bound_inputs']==status['IO']['final_fresh_hashes']==103
        and status['prior81_Native_covered_code_pins']==compact.FROZEN81
        and status['new4_metadata_qualified_code_pins']==COMPACT_CODE+PRIOR104_CODE
        and status['full1648_two_byte_Native_qualification_completed'] is False,
        'R127_ACCEPTED97_AND_METADATA85_NOT_FULL_NATIVE_PASS')
    return True

def budget(required,baseline,added):
    require(len(baseline)==1644 and len(required)==N and len(added)==8 and list(added)==list(NEW)
        and not set(baseline)&set(added) and required=={**baseline,**added}
        and baseline[p.m.EXE['path']]==p.m.EXE and sum(x['bytes'] for x in baseline.values())==120516712
        and sum(x['bytes'] for x in added.values())<=1048576,'ALL_PRIOR1644_PLUS_EIGHT_NOT_SUBSET')
    binary=p.m.EXE['bytes'];other=sum(x['bytes'] for x in required.values())-binary
    total=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+20+15+60
    require(total<600,'NOMINAL_UNCHANGED600')
    return dict(full_runtime_inputs=N,baseline_full_source_inputs=1644,new_inputs=8,
        actual_ancestor_directory_count=DIRECTORIES,native_rate=20,acquisition_native_rate=14,metadata_rate=32,
        original_IO_scope_seconds=600,shared_metadata_read_limit=720,extra_new_bytes_upper_bound=1048576,
        metadata_allowance_seconds=60,product_allowance_seconds=20,early_yield_allowance_seconds=15,
        margin_seconds=60,nominal_combined_seconds=total,prediction_not_completion_guarantee=True)

def anchor(q):
    fixtures=compact.load(q);prior,root,body,names,expected,legacy,current81,prior_body=fixtures
    plan,baseline,old_extras,old_baseline,old_added=compact.validate(*fixtures)
    bound=m.m.review.bound_json
    qualification=bound(q,COMPACT_QUALIFIER);status=bound(q,COMPACT_STATUS)
    require(qualification['state']==compact.PASS and qualification['runtime_plan']==plan
        and qualification['root_pin']==compact.ROOT and qualification['body_pin']==compact.BODY
        and qualification['accepted_checkpoint_pin']==compact.PRIOR and qualification['policy']==compact.policy()
        and qualification['actually_executed_mutation_contracts']==26
        and qualification['resource_stop_reason'] is None and qualification['resource_watcher_cleanup_confirmed'] is True
        and qualification['IO']['finished'] is True and qualification['IO']['bound_inputs']==qualification['IO']['final_fresh_hashes']==92
        and qualification['IO']['read_passes']==184 and qualification['product_or_Native_reexecuted'] is False
        and qualification['current81_Native_covered_code_pins']==compact.FROZEN81
        and qualification['new2_metadata_only_code_pins']==COMPACT_CODE,'QUALIFIED_COMPACT97_AND26_NO_REPLAY')
    require(status['state']=='PASS_EXACT97_COMPACT_CHECKPOINT_AND_R126_DOCUMENTS_NOT_WHOLE_OR_GATE'
        and status['runtime_plan']==plan and status['compact_accepted_checkpoint_qualification_pin']==COMPACT_QUALIFIER
        and status['resource_stop_reason'] is None and status['resource_watcher_cleanup_confirmed'] is True
        and status['IO']['finished'] is True and status['IO']['bound_inputs']==status['IO']['final_fresh_hashes']==97
        and status['current81_Native_covered_code_pins']==compact.FROZEN81
        and status['new2_metadata_only_code_pins']==COMPACT_CODE and status['contract_tests_reexecuted'] is False,
        'R126_NOT_FAILED_STATUS_AND_SAME97_SOURCE')
    current2={pin['path']:q.pin(pin['path']) for pin in COMPACT_CODE}
    current_prior={pin['path']:q.pin(pin['path']) for pin in PRIOR104_CODE}
    current323={pin['path']:q.pin(pin['path']) for pin in PRIOR323_CODE}
    require(list(current2.values())==COMPACT_CODE and list(current_prior.values())==PRIOR104_CODE
        and list(current323.values())==PRIOR323_CODE
        and list(current81.values())+list(current2.values())+list(current_prior.values())+list(current323.values())==FROZEN87,
        'ALL85_DISTINCT_CURRENT_PINS')
    # 변경되지 않은78계약은 actual103의254실행 및 독립qualification에 근거해 재사용한다.
    # 현재364실행에 더하지 않는다. 변경한 queue/classifier/기록은182+182를 실행한다.
    old.closed_attempt(root)
    require(root['runtime_contract_executions']==254 and root['contract_checkpoint_statistics']['started_tests']==254
        and root['resource_stop_reason'] is None and root['resource_watcher_cleanup_confirmed'] is True
        and all(baseline[pin['path']]==pin for pin in compact.FROZEN81),'FROZEN_OLD_GUARD78_QUALIFIED_NOT_EXECUTED_NOW')
    prior_added={**current2,**current_prior};prior_required={**baseline,**prior_added};prior_extras={**old_extras,**prior_added}
    stopped=bound(q,PRIOR104);sidecar=bound(q,PRIOR104_SIDECAR);reviewed=bound(q,PRIOR104_REVIEW);stop_status=bound(q,PRIOR104_STATUS)
    prior104_contract(stopped,sidecar,reviewed,stop_status,plan,prior_required,prior_extras,p.v.identity(names,expected,p.m.EXE))
    require(sorted(v.name for v in (p.c.ROOT/p.DIR).glob('p320-case-*-run*.v1.json'))==['p320-case-104-run002.v1.json']
        and sorted(v.name for v in (p.c.ROOT/p.DIR/'cases').glob('p320-*.json'))==
        ['p320-case-104-run002.json','p320-failure-104-run002.json'],'NO_UNKNOWN_PRIOR104_CASE_OR_REPLAY')
    prior323_added={**prior_added,**current323};prior323_required={**baseline,**prior323_added};prior323_extras={**old_extras,**prior323_added}
    root323=bound(q,PRIOR323_STOP);status323=bound(q,PRIOR323_STATUS)
    require(root323['schema_version']==prior323.SCHEMA and root323['state']=='FAILED_NOT_ACCEPTED'
        and root323['error_code']==root323['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and root323['resource_watcher_cleanup_confirmed'] is True
        and root323['accepted_exact_product_body_count']==0 and root323['actual_product_child_executed'] is False
        and root323['failure_diagnostic']['stage']=='source_frame_acquire'
        and root323['selected_test_index']==104 and root323['prior_runtime_plan']==plan
        and root323['scope_budget']==prior323.budget(prior323_required,baseline,prior323_added)
        and root323['scope_added_six_pins']==list(prior323_added.values())
        and root323['extra_frame_controller_pins']==list(prior323_extras.values()),'PRIOR323_STOP_SCOPE_NOT_PASS')
    prior323.guarded_contract(root323['contract_checkpoint_statistics'])
    h323=root323['terminal_source_frame']['handles']
    require(h323['input_lock_handles_opened']==h323['input_lock_handles_closed']==194
        and h323['input_lock_handles_remaining']==0 and h323['active_reader_bindings']==h323['active_byte_streams']==0
        and root323['terminal_source_frame']['frame_state']=='CLOSED'
        and root323['terminal_source_frame']['registered_live_frame'] is False
        and root323['terminal_source_frame']['actual_byte_boundaries']==[],'PRIOR323_ALL194_CLOSED')
    require(status323['state']=='PASS_EXACT97_R128_PARENT_RETURN268_AND_ACQUISITION_STOP_DOCS_NOT_PRODUCT_OR_GATE'
        and status323['runtime_plan']==plan and status323['failed104_root_pin']==PRIOR323_STOP
        and status323['current87_metadata_code_pins']==FROZEN87
        and status323['resource_stop_reason'] is None and status323['resource_watcher_cleanup_confirmed'] is True
        and status323['IO']['finished'] is True
        and status323['IO']['bound_inputs']==status323['IO']['final_fresh_hashes']==112
        and status323['full1650_two_byte_Native_qualification_completed'] is False,'R128_QUALIFIED87_NOT_NATIVE_PASS')
    require(sorted(v.name for v in (p.c.ROOT/p.DIR).glob('p323-case-*-run*.v1.json'))==['p323-case-104-run003.v1.json']
        and not list((p.c.ROOT/p.DIR/'cases').glob('p323-*.json')),'PRIOR323_NO_BODY_OR_UNKNOWN_REPLAY')
    added={**prior323_added,SELF:q.pin(SELF),TEST:q.pin(TEST)};required={**baseline,**added};extras={**old_extras,**added}
    directories={PurePosixPath('.')}
    for name in required:directories.update(PurePosixPath(name).parents)
    require(len(directories)==DIRECTORIES and len(extras)==185 and required=={**baseline,**added},
        'ALL1644_PLUS8_AND308_ANCESTORS_AND185_CONTROLLERS')
    require(sorted(x.name for x in (p.c.ROOT/p.DIR).glob('p317-case-*-run*.v1.json'))==
        ['p317-case-103-run002.v1.json']
        and sorted(x.name for x in (p.c.ROOT/p.DIR/'cases').glob('p317-*.json'))==
        ['p317-case-103-run002.json'],'NO_UNKNOWN_PRIOR_P317_BODY_OR_REPLAY')
    budget(required,baseline,added)
    return legacy,plan,names,expected,p.m.EXE,required,extras,baseline,added,root,body,(stopped,sidecar,reviewed,stop_status,plan,prior_required,prior_extras,p.v.identity(names,expected,p.m.EXE))

def guarded_contract(row,expected=EXECUTED):
    require(type(row) is dict and row['started_tests']==row['stopped_tests']==
        row['successful_before_test_checks']==row['successful_after_test_checks']==expected
        and row['runner_calls']==row['returned_runner_calls']==row['successful_before_runner_checks']==row['successful_after_runner_checks']==2
        and row['original_unittest_results_preserved'] is True
        and row['new_sampler_or_thread_or_sleep_started'] is False
        and row['original_guard_or_test_coverage_relaxed'] is False
        and row['test_results_are_not_product_acceptance'] is True,'EVERY_TEST_ORIGINAL_CHECKPOINT_NOT_ACCEPTANCE')

inner_contract=old.inner_contract
leading_contract=old.leading_contract
live_pins=old.live_pins

def native_pair(component,body,pin,required,binding,extras):
    p.validate_closing(component,body,pin,required,binding,extras)
    f=component['source_frame'];h=f['handles'];dup=h['borrowed_byte_streams']
    require(len(required)==N and h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==DIRECTORIES-1
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+DIRECTORIES
        and h['handle_metadata_checks']==4*N+2*DIRECTORIES
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==dup['byte_stream_pathname_reopens']==0
        and f['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
            separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'FULL1652_NATIVE_TWO_BYTE_AND_CLEANUP')
    m.m.r.h.h.pressure_contract(h['native_open_backpressure']);m.m.lower_contract(h)
    m.timing_contract(h['lock_timing_diagnostic']);profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)

def closed_attempt(d):
    require(d.get('stop_resume_policy')==STOP_POLICY and d.get('prior323_STOP_pin')==PRIOR323_STOP
        and d.get('prior323_status_pin')==PRIOR323_STATUS and d.get('reused_prior323_contract_executions')==268,
        'STABLE_QUEUE_POLICY_AND_PRIOR323_QUALIFIED')
    require(d.get('previous104_STOP_pin')==PRIOR104 and d.get('previous104_STOP_review_pin')==PRIOR104_REVIEW
        and d.get('previous104_STOP_status_pin')==PRIOR104_STATUS and d.get('previous104_STOP_reviewed') is True
        and d.get('reused_previous104_contract_executions')==200 and d.get('parent_return_record_policy')==RETURN_POLICY,
        'PRIOR104_QUALIFIED_STOP_AND_RECORD_POLICY')
    require(type(d) is dict and d.get('schema_version')==SCHEMA and d.get('state') in (PASS,LIGHT),
        'CLOSED_SCHEMA_STATE_BEFORE_STATISTICS')
    guarded_contract(d['contract_checkpoint_statistics'])
    require(d['compact_qualification_pin']==COMPACT_QUALIFIER and d['compact_status_pin']==COMPACT_STATUS
        and d['compact_checkpoint_policy']==compact.policy()
        and d['compact_checkpoint_selected'] is True and d['reused_compact_contract_executions']==26
        and d['reused_original_guard_contract_executions']==78
        and d['reused_original_guard_qualification_root_pin']==compact.ROOT,
        'COMPACT_QUALIFIED_AND78_REUSED_NOT_EXECUTED')
    require(d['completed102_anchor_pin']==COMPLETED102 and d['previous103_preparation_STOP_pin']==PREPARATION103_STOP
        and d['guarded_contract_qualification_pin']==GUARDED_QUALIFIER
        and d['previous_status_STOP_pin']==STATUS_STOP and d['previous103_STOP_reviewed'] is True
        and d['per_test_original_checkpoint_selected'] is True
        and d['reused_helper_contract_executions']==21,'CLOSED_GUARDED_MARKERS_AND_REUSE_NOT_EXECUTED')
    require(d['schema_version']==SCHEMA and d['state'] in (PASS,LIGHT)
        and d.get('error_code') is None and d['resource_stop_reason'] is None
        and d['resource_watcher_cleanup_confirmed'] is True and d['runtime_contract_executions']==EXECUTED
        and d['reused_retained_contract_executions']==1486 and d['retained_contract_qualification_pin']==RETAINED_QUALIFIER
        and d['compound_anchor_pin']==ANCHOR and d['original_successful_bodies_not_reexecuted'] is True
        and d['previous_preparation_STOP_pin']==inner.FAILURE and d['inner_metadata_qualification_pin']==INNER_QUALIFIER
        and d['compound_anchor_verified_without_body_reexecution'] is True
        and d['metadata_entry_pressure_connection_selected'] is True and d['packed_root_writer_selected'] is True
        and d['previous_Native_STOP_pin']==NATIVE_STOP and d['counter_support_status_pin']==SUPPORT_STATUS
        and d['idle_support_pin']==IDLE and d['counter_qualification_pin']==COUNTER_QUALIFIER
        and d['counter_two_queries_pin']==COUNTER_REAL and d['previous_Native_STOP_reviewed'] is True
        and d['counter_code_qualification_selected'] is True
        and d['counter_role']=='SEPARATE_DIAGNOSTIC_NOT_RESOURCE_GUARD_OR_PRODUCT_ACCEPTANCE',
        'CLOSED_EXACT_CURRENT_NO_FAILED_RETRY')

def record(doc,body,pin,required,binding,extras,names,legacy,base,baseline,added):
    closed_attempt(doc);index,name=g.old.select(base,names)
    require(doc['state']==PASS and doc['selected_test_index']==index and doc['selected_test_name']==name
        and name not in base['runtime_qualified_test_names'] and doc['binding']==binding and doc['prior_runtime_plan']==base
        and doc['case_receipt_pin']==pin and doc['receipt_serialization_policy']==r.policy()
        and doc['monotonic_binding_policy']==review.policy() and doc['scope_budget']==budget(required,baseline,added)
        and doc['scope_added_eight_pins']==list(added.values()) and doc['extra_frame_controller_pins']==list(extras.values())
        and doc['accepted_exact_product_body_count']==1 and doc['runtime_plan']==g.advance(legacy,base,names,index),
        'EXACT_NEXT_ONE_QUALIFIED_NOT_DUPLICATE')
    require(doc['parent_return_status_recorded_before_after_parent_guard'] is True
        and type(doc['original_parent_return_code']) is int and doc['original_parent_return_code']==0
        and doc['original_parent_pending_failure_before_after_parent_guard'] is False
        and doc['original_parent_rejected_failure_before_after_parent_guard'] is False
        and doc['original_parent_STOP_captured_not_accepted'] is False,'RETURN_RECORDED_AND_NO_PENDING_FAILURE')
    require(doc['own_queue_contract_tests_passed']==doc['synthetic_following_queue_contract_tests_passed']==COUNT
        and doc['native_timing_connected'] is True and doc['early_source_guard_connected'] is True
        and doc['aggregate_post_reader_connection_verified'] is True and doc['diagnostic_parent_connection_selected'] is True
        and doc['original_parent_capture_adapter_selected'] is True and doc['acquisition_phase_connection_selected'] is True
        and doc['actual_product_child_executed'] is True and body['task']==f'p204-r07-case-{index:03}-tests'
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['preparation_IO']['read_passes']+doc['closing_component']['metadata_IO']['read_passes']<=720
        and doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'ALL_CLOSED_BINDING_JOB_METADATA_GUARDS_NOT_GATE')
    leading_contract(doc['preparation_IO']);leading_contract(doc['closing_component']['metadata_IO'])
    m.job_contract(body);m.early_contract(doc['early_source_checkpoint'])
    native_pair(doc['closing_component'],body,pin,required,binding,extras);r.stats_contract(doc['packed_parent_write_statistics'],pin)
    return doc['runtime_plan']

def current_code(q):
    return [q.reader.snapshots[p['path']] for p in FROZEN87]+[q.reader.snapshots[n] for n in (SELF,TEST)]

def pin_argument(value,review=False):
    pin=json.loads(value) if isinstance(value,str) else value
    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'}
        and type(pin['bytes']) is int and 0<pin['bytes']<=16*1048576
        and isinstance(pin['sha256'],str) and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None
        and isinstance(pin['path'],str),'EXACT_PIN_ARGUMENT')
    leaf=PurePosixPath(pin['path']).name
    pattern=r'p326-stop-review-run[0-9]{3}\.v1\.json' if review else r'p326-(?:case-[0-9]{3}|admission)-run[0-9]{3}\.v1\.json'
    require(re.fullmatch(pattern,leaf) is not None and pin['path']==p.DIR+'/'+leaf,'SCOPED_PIN_ARGUMENT')
    return pin

def stopped_before_product(doc,plan,required,binding,extras,baseline,added,names,sidecar=None):
    require(doc['schema_version']==SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc.get('error_code')==doc.get('resource_stop_reason')=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['accepted_exact_product_body_count']==0 and doc['actual_product_child_executed'] is False
        and doc.get('original_successful_bodies_not_reexecuted') is True
        and doc.get('stop_resume_policy')==STOP_POLICY,'PRE_PRODUCT_CPU_STOP_ONLY_NOT_ACCEPTED')
    stage=doc['failure_diagnostic']['stage']
    safe={'admission','reader_constructor','anchor','selection','contract_tests','final_fresh_preparation','source_frame_acquire','owned_parent'}
    require(stage in safe,'NO_POST_PRODUCT_OR_UNKNOWN_RETRY')
    require(stage not in {'final_fresh_preparation','source_frame_acquire','owned_parent'}
        or type(doc.get('selected_test_index')) is int,'SELECTED_PRE_PRODUCT_STAGE_REQUIRED')
    if doc.get('selected_test_index') is not None:
        index,name=g.old.select(plan,names)
        require(doc['selected_test_index']==index and doc['selected_test_name']==name
            and doc['prior_runtime_plan']==plan and doc['binding']==binding
            and doc['scope_budget']==budget(required,baseline,added)
            and doc['extra_frame_controller_pins']==list(extras.values())
            and doc['scope_added_eight_pins']==list(added.values()),'STOP_SAME_EXACT_QUEUE_SCOPE')
    frame=doc.get('terminal_source_frame')
    require(stage not in {'source_frame_acquire','owned_parent'} or frame is not None,'NATIVE_STAGE_CLEANUP_FRAME_REQUIRED')
    if frame is not None:
        h=frame['handles'];dup=h.get('borrowed_byte_streams')
        require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
            and frame['input_count']==len(required)==N and frame['input_bytes']==sum(v['bytes'] for v in required.values())
            and frame['held_identity_after_owned_cleanup'] is None and frame['actual_byte_boundaries']==[]
            and h['input_lock_handles_opened']==h['input_lock_handles_closed']
            and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
            and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
            and (dup is None or (dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
                and dup['duplicate_handles_opened']==dup['duplicate_handles_closed'])),'STOP_ALL_NATIVE_CLEANED_NOT_COMMITTED')
    if stage=='owned_parent':
        require(frame['handles']['input_lock_handles_opened']==N+DIRECTORIES
            and frame['handles']['acquisition_phase_pressure']['acquisition_complete'] is True
            and sidecar is not None and doc.get('terminal_parent_failure_sidecar_pin') is not None
            and sidecar['state']=='DEFERRED_NOT_STARTED' and sidecar['actual_product_child_executed'] is False
            and sidecar['exit_code'] is None and sidecar['worker_created'] is False and sidecar['job_assigned'] is False
            and sidecar['owned_tree_empty'] is True and sidecar['cleanup_confirmed'] is True
            and sidecar['resource_stop_reason']==sidecar['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU',
            'OWNED_PRE_PRODUCT_DEFERRED_NO_WORKER_NOT_PRODUCT_REPLAY')
    else:
        require(sidecar is None and doc.get('terminal_parent_failure_sidecar_pin') is None
            and doc['original_parent_capture_adapter_selected'] is False
            and doc['diagnostic_parent_connection_selected'] is False,'NO_PARENT_IN_PRE_PRODUCT_STAGE')
    require(doc.get('terminal_failure_write_error') is None,'FAILURE_CAPTURE_COMPLETE')
    return dict(stage=stage,selected_test_index=doc.get('selected_test_index'),
        selected_test_name=doc.get('selected_test_name'),accepted_count_delta=0,actual_product_reexecution_authorized=False,
        pre_product_retry_candidate_only=True,original_cleanup_confirmed=True)

def review_contract(doc,root_pin,root,plan,required,binding,extras,baseline,added,names,codes,sidecar=None):
    require(doc['schema_version']==REVIEW_SCHEMA and doc['state']==REVIEW_PASS
        and doc['reviewed_root_pin']==root_pin and doc['stop_resume_policy']==STOP_POLICY
        and doc['runtime_plan_at_review']==plan and doc['current89_metadata_code_pins']==codes
        and doc['resource_stop_reason'] is None and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['preparation_IO']['finished'] is True
        and doc['preparation_IO']['bound_inputs']==doc['preparation_IO']['final_fresh_hashes']
        and doc['preparation_IO']['bound_inputs']>=len(codes)==89
        and doc['accepted_exact_product_body_count']==0 and doc['actual_product_child_executed'] is False
        and doc['actual_Native_or_product_started_in_review'] is False
        and doc['contract_tests_reexecuted_in_review'] is False
        and doc.get('terminal_source_frame') is None,'INDEPENDENT_REVIEW_COMPLETE_NOT_ACCEPTANCE')
    result=stopped_before_product(root,plan,required,binding,extras,baseline,added,names,sidecar)
    require(doc['reviewed_failure_classification']==result,'REVIEW_CLASSIFICATION_RECOMPUTED')
    return result

def zero_placeholder(q,doc):
    name=doc.get('case_receipt_path')
    if not name:return None
    index=doc.get('selected_test_index')
    require(type(index) is int and 1<=index<=249
        and re.fullmatch(re.escape(p.DIR)+r'/cases/p326-case-'+f'{index:03}'+r'-run[0-9]{3}\.json',name) is not None,
        'SCOPED_ORIGINAL_PLACEHOLDER')
    if not (p.c.ROOT/name).exists():return None
    pin=q.pin(name)
    require(pin['bytes']==0 and pin['sha256']==hashlib.sha256(b'').hexdigest(),'ONLY_ZERO_PRE_PRODUCT_BODY_NOT_REPLAY')
    return pin

def review_approvals(q,pins,codes):
    require(len(pins)<=64,'BOUNDED64_EXPLICIT_REVIEWS')
    approved={}
    for pin in pins:
        parsed=pin_argument(pin,True);doc=m.m.review.bound_json(q,parsed);rp=pin_argument(doc['reviewed_root_pin'])
        require(rp['path'] not in approved and doc['current89_metadata_code_pins']==codes,
            'UNIQUE_EXPLICIT_REVIEW_AND_CURRENT_CODE')
        approved[rp['path']]=(parsed,doc)
    return approved

def progress(q,legacy,base,names,required,binding,extras,baseline,added,approved=None,target=None):
    approved={} if approved is None else approved;codes=current_code(q);used=set();target_result=None
    folder=p.c.ROOT/p.DIR
    supports=sorted((*folder.glob('p326-light-run*.v1.json'),*folder.glob('p326-admission-run*.v1.json')))
    rows=sorted(folder.glob('p326-case-*-run*.v1.json'));require(len(supports)+len(rows)<=4096,'BOUNDED_NAMESPACE')
    plan=base
    for path in supports+rows:
        name=path.relative_to(p.c.ROOT).as_posix();d=q.json(name);rp=q.reader.snapshots[name]
        if path in rows:
            match=FILE.fullmatch(path.name);require(match is not None,'FAILED_OR_PASSED_CASE_FILENAME')
            index,number=map(int,match.groups())
            require(d.get('selected_test_index')==index and 1<=index<=249 and 1<=number<=999,'CASE_FILENAME_CURSOR_IDENTITY')
            require(d.get('case_receipt_path') in (None,f'{p.DIR}/cases/p326-case-{index:03}-run{number:03}.json'),
                'FAILED_OR_PASSED_BODY_FILENAME_IDENTITY')
            if d.get('terminal_parent_failure_sidecar_pin') is not None:
                require(d['terminal_parent_failure_sidecar_pin']['path']==f'{p.DIR}/cases/p326-failure-{index:03}-run{number:03}.json',
                    'FAILED_SIDECAR_FILENAME_IDENTITY')
        if d.get('state')=='FAILED_NOT_ACCEPTED':
            side=m.m.review.bound_json(q,d['terminal_parent_failure_sidecar_pin']) if d.get('terminal_parent_failure_sidecar_pin') else None
            if target is not None and name==target['path']:
                require(rp==target and target_result is None,'EXACT_TARGET_ONCE')
                placeholder=zero_placeholder(q,d)
                target_result=(rp,d,side,copy.deepcopy(plan),stopped_before_product(d,plan,required,binding,extras,baseline,added,names,side),placeholder)
            else:
                require(name in approved,'UNREVIEWED_STOP_BLOCKS_GO')
                ap,reviewed=approved[name];review_contract(reviewed,rp,d,plan,required,binding,extras,baseline,added,names,codes,side)
                require(zero_placeholder(q,d)==reviewed['reviewed_body_placeholder_pin'],'SAME_PRESERVED_ZERO_BODY_NOT_REPLAY')
                used.add(name)
            continue
        closed_attempt(d)
        frozen={v['path']:v for v in d['bound_preparation_input_pins']}
        require(all(frozen[v['path']]==v for v in codes),'ALL89_MATCH_QUALIFIED_ROW')
        if path in supports:
            require(d['state']==LIGHT,'NO_PRODUCT_IN_SUPPORT_NAMESPACE');continue
        match=FILE.fullmatch(path.name);require(match is not None,'FILENAME')
        index,number=map(int,match.groups());require(1<=index<=249 and 1<=number<=999,'INDEX_RUN')
        require(d['selected_test_index']==index and d['case_receipt_pin']['path']==
            f'{p.DIR}/cases/p326-case-{index:03}-run{number:03}.json','FILENAME_BODY_IDENTITY')
        bp=d['case_receipt_pin'];body=m.m.review.bound_json(q,bp)
        plan=record(d,body,bp,required,binding,extras,names,legacy,plan,baseline,added)
    require(used==set(approved) and (target is None or target_result is not None),'NO_UNUSED_REVIEW_OR_MISSING_TARGET')
    return (plan,target_result) if target is not None else plan

def contracts(fixtures,stop,q):
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_reviewed_stop_queue_runtime as t
    statistics=None
    try:
        with guarded.bind(q.reader.checkpoint) as statistics, \
                patch('subprocess.Popen',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('subprocess.run',side_effect=AssertionError('NO_CONTRACT_CHILD')), \
                patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
            for following in (False,True):
                with patch.object(t,'FIXTURES',fixtures),patch.object(t,'FOLLOWING',following),patch.object(t,'PRIOR_STOP',stop):
                    rr=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
                if not rr.wasSuccessful():
                    q.contract_failed_test_ids=[str(test) for test,_ in (rr.failures+rr.errors)][:8]
                require(rr.wasSuccessful() and rr.testsRun==COUNT and not rr.skipped,'CURRENT182_AND_FOLLOWING182')
        row=statistics.summary();guarded_contract(row)
        require(unittest.TextTestRunner is guarded._ORIGINAL_RUNNER and guarded._ACTIVE is False,'ORIGINAL_RUNNER_RESTORED')
        return EXECUTED,row
    finally:
        q.contract_checkpoint_statistics=statistics.summary() if statistics is not None else None

def preserve_failure(capture,frame,owner,out,index,number):
    path=p.c.ROOT/f'{p.DIR}/cases/p326-failure-{index:03}-run{number:03}.json';digest=hashlib.sha256();written=0
    class Output:
        def __init__(self,stream):self.stream=stream
        def write(self,block):
            nonlocal written
            count=self.stream.write(block);require(type(count) is int and count==len(block),'SIDECAR_ONCE')
            digest.update(block.encode('ascii'));written+=count;return count
    with path.open('x',encoding='utf-8') as stream:stats=capture.write_rejected(Output(stream),owner,out) if capture.rejected else capture.write_terminal(Output(stream),owner,out)
    out.update(terminal_parent_failure_sidecar_pin=dict(path=path.relative_to(p.c.ROOT).as_posix(),bytes=written,
        sha256=digest.hexdigest()),terminal_parent_failure_statistics=stats,original_failure_body_placeholder_preserved=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','actual','stop-review'),default='light');ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--review-pin',action='append',default=[]);ap.add_argument('--stop-root-pin')
    args=ap.parse_args();require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p326-{args.mode if args.mode in ('light','stop-review') else 'admission'}-run{args.run:03}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=g.observation.Context();owner=g.observation.Resources(context)
    q=meta=frame=early=capture=parent=proposed=None;body=None;writes=[]
    out=dict(schema_version=REVIEW_SCHEMA if args.mode=='stop-review' else SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),compound_anchor_pin=ANCHOR,
        retained_contract_qualification_pin=RETAINED_QUALIFIER,reused_retained_contract_executions=1486,
        previous_preparation_STOP_pin=inner.FAILURE,inner_metadata_qualification_pin=INNER_QUALIFIER,
        previous104_STOP_pin=PRIOR104,previous104_STOP_review_pin=PRIOR104_REVIEW,
        previous104_STOP_status_pin=PRIOR104_STATUS,previous104_STOP_reviewed=False,
        prior323_STOP_pin=PRIOR323_STOP,prior323_status_pin=PRIOR323_STATUS,reused_prior323_contract_executions=268,
        stop_resume_policy=STOP_POLICY,explicit_review_pins=[],
        reused_previous104_contract_executions=200,parent_return_record_policy=RETURN_POLICY,
        parent_return_status_recorded_before_after_parent_guard=False,
        compact_qualification_pin=COMPACT_QUALIFIER,compact_status_pin=COMPACT_STATUS,
        compact_checkpoint_policy=compact.policy(),compact_checkpoint_selected=False,reused_compact_contract_executions=26,
        reused_original_guard_contract_executions=78,reused_original_guard_qualification_root_pin=compact.ROOT,
        completed102_anchor_pin=COMPLETED102,previous103_preparation_STOP_pin=PREPARATION103_STOP,
        guarded_contract_qualification_pin=GUARDED_QUALIFIER,previous_status_STOP_pin=STATUS_STOP,
        previous103_STOP_reviewed=False,per_test_original_checkpoint_selected=False,reused_helper_contract_executions=21,
        previous_Native_STOP_pin=NATIVE_STOP,counter_support_status_pin=SUPPORT_STATUS,idle_support_pin=IDLE,
        counter_qualification_pin=COUNTER_QUALIFIER,counter_two_queries_pin=COUNTER_REAL,
        previous_Native_STOP_reviewed=False,counter_code_qualification_selected=False,
        counter_role='SEPARATE_DIAGNOSTIC_NOT_RESOURCE_GUARD_OR_PRODUCT_ACCEPTANCE',
        own_queue_contract_tests_passed=0,synthetic_following_queue_contract_tests_passed=0,
        original_successful_bodies_not_reexecuted=True,compound_anchor_verified_without_body_reexecution=False,
        early_source_guard_connected=False,original_parent_capture_adapter_selected=False,
        packed_root_writer_selected=True,accepted_exact_product_body_count=0,receipt_serialization_policy=r.policy(),
        monotonic_binding_policy=review.policy(),aggregate_post_reader_connection_verified=False,diagnostic_parent_connection_selected=False,
        native_timing_connected=False,acquisition_phase_connection_selected=False,metadata_entry_pressure_connection_selected=False)
    stage='admission'
    try:
        owner.admit();stage='reader_constructor';q=Reader(owner,context)
        out['metadata_entry_pressure_connection_selected']=type(q.entry_early_binding) is m.entry_pressure.Binding and q.entry_binding.pacer.checkpoint is q.reader.checkpoint
        stage='anchor'
        legacy,base,names,expected,exe,required,extras,baseline,added,healthy,healthy_body,stop=anchor(q)
        stage='selection';binding=p.v.identity(names,expected,exe);approved=review_approvals(q,args.review_pin,current_code(q))
        target=pin_argument(args.stop_root_pin) if args.stop_root_pin else None
        require((args.mode=='stop-review')==(target is not None),'TARGET_REVIEW_ONLY')
        selected=progress(q,legacy,base,names,required,binding,extras,baseline,added,approved,target)
        plan,target_result=selected if target is not None else (selected,None);index,name=g.old.select(plan,names)
        out['explicit_review_pins']=[v[0] for v in approved.values()]
        if args.mode!='stop-review':
            stage='contract_tests'
            with context.scope('contract_tests'):
                out['runtime_contract_executions'],out['contract_checkpoint_statistics']=contracts((legacy,plan,names,required,extras,baseline,added,healthy,healthy_body),stop,q)
            out['per_test_original_checkpoint_selected']=True
            out['own_queue_contract_tests_passed']=COUNT
            out['synthetic_following_queue_contract_tests_passed']=COUNT
        out.update(binding=binding,selected_test_index=index,selected_test_name=name,prior_runtime_plan=plan,
            extra_frame_controller_pins=list(extras.values()),scope_added_eight_pins=list(added.values()),
            compound_anchor_verified_without_body_reexecution=True,scope_budget=budget(required,baseline,added),
            previous_Native_STOP_reviewed=True,counter_code_qualification_selected=True,previous103_STOP_reviewed=True,compact_checkpoint_selected=True,
            previous104_STOP_reviewed=True)
        stage='final_fresh_preparation'
        if args.mode=='stop-review':
            require(bool(list((p.c.ROOT/p.DIR).glob('p326-light-run*.v1.json'))),'QUALIFIED_LIGHT_REQUIRED_FOR_REVIEW')
            rp,stopped,stopped_side,at_plan,classification,placeholder_pin=target_result
            out.update(reviewed_root_pin=rp,runtime_plan_at_review=at_plan,current89_metadata_code_pins=current_code(q),
                reviewed_failure_classification=classification,reviewed_body_placeholder_pin=placeholder_pin,
                actual_Native_or_product_started_in_review=False,contract_tests_reexecuted_in_review=False)
            q.finish();proposed=dict(state=REVIEW_PASS)
        elif args.mode=='light':q.finish();proposed=dict(state=LIGHT)
        else:
            destination=p.c.ROOT/f'{p.DIR}/p326-case-{index:03}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_CASE')
            known_zero={v[1]['reviewed_body_placeholder_pin']['path']:v[1]['reviewed_body_placeholder_pin']
                for v in approved.values() if v[1].get('reviewed_body_placeholder_pin') is not None}
            for existing in (p.c.ROOT/p.DIR/'cases').glob(f'p326-case-{index:03}-run*.json'):
                ename=existing.relative_to(p.c.ROOT).as_posix()
                require(ename in known_zero and q.pin(ename)==known_zero[ename],'ONLY_REVIEWED_ZERO_PLACEHOLDERS_NOT_PRODUCT_REPLAY')
            body_path=p.c.ROOT/f'{p.DIR}/cases/p326-case-{index:03}-run{args.run:03}.json';q.finish()
            require(q.shared_budget['read_calls']<=m.m.META_READ_LIMIT-2,'POST_BODY_TWO_READS_RESERVED')
            early=early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner);held=profile.InputLocks(p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'EXACT_OWNER_EARLY_NATIVE20')
            frame=p.frames.Frame(p.frames.Registry(),required,early,held=held);counter=p.frames.Counters(q.reader,frame.readers);context.reader=counter
            out.update(early_source_guard_connected=True,acquisition_phase_connection_selected=type(held) is profile.InputLocks,case_receipt_path=body_path.relative_to(p.c.ROOT).as_posix())
            stage='source_frame_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            parent=connection.ParentConnection(frame,writes,index,name,binding);capture=parent.capture
            out['original_parent_capture_adapter_selected']=isinstance(capture,m.m.support.candidate.Capture)
            out['diagnostic_parent_connection_selected']=type(parent) is connection.ParentConnection and type(capture) is m.a.Capture
            out['native_timing_connected']=isinstance(held,connection.TimedInputLocks)
            stage='owned_parent';held.mark('before_parent');code=parent.run(body_path,context);record_return_before_original_guard(out,capture,code,held)
            if capture.pending:
                out['original_parent_STOP_captured_not_accepted']=True
                raise ValueError('ORIGINAL_PARENT_STOP_DEFERRED_NOT_ACCEPTED')
            stage='post_reader_constructor';meta=review.construct(Reader,owner,context,counter)
            require(context.reader is counter and counter.metadata==[meta.reader],'MONOTONIC_ORIGINAL_AGGREGATE')
            out['aggregate_post_reader_connection_verified']=True
            body=meta.json(body_path.relative_to(p.c.ROOT).as_posix());pin=meta.reader.snapshots[body_path.relative_to(p.c.ROOT).as_posix()]
            require(code==0 and len(writes)==1,'ORIGINAL_PARENT_COMPLETE_ONCE')
            p.validate_parent(body,name,binding,required);m.job_contract(body);r.stats_contract(writes[0],pin);meta.finish()
            stage='source_frame_closing';held.mark('before_release')
            component=dict(schema_version=p.CLOSING_SCHEMA,state=p.PASS,**p.r.flags(),selected_test_name=name,
                binding=binding,case_receipt_pin=pin,metadata_IO=meta.summary(),source_frame=frame.commit(body),
                extra_frame_controller_pins=list(extras.values()),sealed_whole_before_anchor=p.b.BASE_CLOSE)
            out.update(case_receipt_pin=pin,closing_component=component,packed_parent_write_statistics=writes[0],
                actual_product_child_executed=body.get('actual_product_child_executed') is True)
            proposed=dict(state=PASS,runtime_plan=g.advance(legacy,plan,names,index),accepted_exact_product_body_count=1)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt,p.c.subprocess.SubprocessError) as error:
        out['error_code']=p.b.run.original.closed_error(error);out['failure_diagnostic']=m.diagnostic(error,stage);proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='MONOTONIC_RUNTIME_FRAME_CLEANUP_FAILED';proposed=None
            out['terminal_source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        for reader in (q,meta):
            if reader is not None:reader.close_entry()
        if q is not None:
            out.update(preparation_IO=q.summary(),bound_preparation_input_pins=list(q.reader.snapshots.values()))
            if hasattr(q,'contract_checkpoint_statistics'):out['contract_checkpoint_statistics']=q.contract_checkpoint_statistics
            if hasattr(q,'contract_failed_test_ids'):out['contract_failed_test_ids']=q.contract_failed_test_ids
        if meta is not None:out['terminal_metadata_IO']=meta.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            if doc['state']!=REVIEW_PASS:closed_attempt(doc)
            if doc['state']==REVIEW_PASS:
                rp,stopped,stopped_side,at_plan,classification,placeholder_pin=target_result
                review_contract(doc,rp,stopped,at_plan,required,binding,extras,baseline,added,names,current_code(q),stopped_side)
            elif doc['state']==PASS:
                doc['closing_component'].update(resource_stop_reason=doc['resource_stop_reason'],resource_watcher_cleanup_confirmed=doc['resource_watcher_cleanup_confirmed'])
                record(doc,body,pin,required,binding,extras,names,legacy,plan,baseline,added)
            else:
                require(doc['state']==LIGHT and doc['preparation_IO']['finished'] is True
                    and doc['runtime_contract_executions']==EXECUTED and doc['monotonic_binding_policy']==review.policy()
                    and doc['compound_anchor_pin']==ANCHOR and doc['reused_retained_contract_executions']==1486
                    and doc['retained_contract_qualification_pin']==RETAINED_QUALIFIER
                    and doc['metadata_entry_pressure_connection_selected'] is True,
                    'LIGHT_FULL_FRESH_CURRENT_CONTRACTS_NOT_REPLAY')
                leading_contract(doc['preparation_IO'])
        g.complete(out,owner,proposed,validate)
        if capture is not None and (capture.pending or capture.rejected):
            try:preserve_failure(capture,frame,owner,out,index,args.run)
            except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:out.update(state='FAILED_NOT_ACCEPTED',terminal_failure_write_error=p.b.run.original.closed_error(error))
        try:
            with destination.open('x',encoding='utf-8') as stream:
                writer=r.packed.dump if out['state'] in (PASS,LIGHT,REVIEW_PASS) else r.compact.dump
                def terminal():require(owner.done.is_set(),'NO_RESOURCE_RESTART')
                writer(out,stream,checkpoint=terminal,indent=2)
        except (ValueError,OSError,TypeError):
            print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code='MONOTONIC_RUNTIME_TERMINAL_SERIALIZATION_FAILED')));return 2
        print(json.dumps({k:out.get(k) for k in ('state','runtime_contract_executions','selected_test_index','error_code','resource_stop_reason')}))
    return 0 if out['state'] in (PASS,LIGHT,REVIEW_PASS) else 2


if __name__=='__main__':
    sys.modules.setdefault('resume_reviewed_stop_queue_runtime',sys.modules[__name__])
    raise SystemExit(main())

