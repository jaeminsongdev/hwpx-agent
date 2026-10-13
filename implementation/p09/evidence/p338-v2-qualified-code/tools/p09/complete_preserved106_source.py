"""P338: 완료106 자식 증거를 보존하고 독립 full-source 마감만 수행한다.
실패/부분/빈 body 원본을 변경하지 않는다. review/source/accept는 제품 자식을 시작하지 않는다.
원 600/720/CPU98x4/RAM 비율/획득14·byte20/1·2MiB/두 전체 byte/identity/정리 유지.
"""
import resume_admission_classified_queue_runtime as m
import argparse,hashlib,io,json,re,sys,unittest
from pathlib import PurePosixPath
from unittest.mock import patch
SELF='tools/p09/complete_preserved106_source.py'
TEST='tools/p09/tests/test_preserved106_source.py'
ROOT=dict(path=m.p.DIR+'/p335-case-106-run012.v1.json',bytes=1025232,
 sha256='41b553fc2d006ee1b17323deba5a8c10f91f256fb70e03f978859b5c196b18e8')
BODY=dict(path=m.p.DIR+'/cases/p335-failure-106-run012.json',bytes=636884,
 sha256='79c712145aa973c9ccdfafa980945f2f4b4fe74c8a59f9be2637f9e86a37e686')
ZERO=dict(path=m.p.DIR+'/cases/p335-case-106-run012.json',bytes=0,sha256=hashlib.sha256(b'').hexdigest())
NAME='actual_import::fresh_acl_revocation_blocks_import_verification_and_policy_binding'
PRIOR_FRESH={"path":"implementation/p09/evidence/locked-r07/p335-light-review-run011.v1.json","bytes":40554,"sha256":"c385b8a1c3d69060d2870c2d28112fa7e36c63f67f27df7acd8cf9ef916da4dc"}
PRIOR_REVIEW={"path":"implementation/p09/evidence/locked-r07/p335-stop-review-run004.v1.json","bytes":44230,"sha256":"708a19314d817034c138a77cc0345a8427605f2f0c6c675c04cb6a5df7bf77f1"}
ACTUAL104={"path":"implementation/p09/evidence/locked-r07/p335-case-104-run006.v1.json","bytes":667184,"sha256":"1ceb8955c548d5defe07f5f4aca97180a637c5cc55441e7e7eab75cae01c5fd9"}
ACTUAL105={"path":"implementation/p09/evidence/locked-r07/p335-case-105-run009.v1.json","bytes":668176,"sha256":"e3a3047caa98ff92bc7e7dd2f2c15ee13b98d658c9940b548965df2f2ec15837"}
CODE91=m.FROZEN89+[
 dict(path=m.SELF,bytes=91588,sha256='5752160e18cad873a027733990a09b3817987425e2e7e5faeac8c271d472a2de'),
 dict(path=m.TEST,bytes=67362,sha256='55c1ba9003b6bcdc86ac6345bdd9ec3a4fa436ddf174f7277be496f41854a9af')]
SCHEMA='hwpx-agent.p09-preserved106-source-closing/v2'
REVIEW_PASS='PASS_PRESERVED106_REVIEW_NOT_SOURCE_RUNTIME_OR_GATE'
SOURCE_PASS='PASS_PRESERVED106_INDEPENDENT_FULL_SOURCE_NOT_RUNTIME_OR_GATE'
ACCEPT_PASS='PASS_EXACT100_PRESERVED106_COMPOUND_NOT_WHOLE_OR_GATE'
N=1656
DIRECTORIES=308
COUNT=61

def require(ok,code):m.require(ok,'PRESERVED106_'+code)

def review(root,body):
    require(root['schema_version']==m.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']==root['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and root['resource_watcher_cleanup_confirmed'] is True
        and root['accepted_exact_product_body_count']==0 and root['runtime_contract_executions']==528
        and root['selected_test_index']==106 and root['selected_test_name']==NAME
        and root['failure_diagnostic']['stage']=='owned_parent'
        and root['failure_diagnostic']['exception_class']=='ValueError','ORIGINAL_FAILED_ROOT_NOT_ACCEPTANCE')
    require(root['terminal_parent_failure_sidecar_pin']==BODY and root['case_receipt_path']==ZERO['path']
        and root['original_failure_body_placeholder_preserved'] is True
        and root.get('terminal_failure_write_error') is None and 'case_receipt_pin' not in root
        and 'runtime_plan' not in root and 'closing_component' not in root,'IMMUTABLE_FAILURE_SIDECAR_NOT_CLOSED_PAIR')
    plan=root['prior_runtime_plan']
    require(plan['runtime_source_qualified_individual_cases']==99 and plan['next_runtime_index']==106
        and plan['runtime_remaining_individual_cases']==150 and NAME not in plan['runtime_qualified_test_names'],
        'PRIOR94_PENDING106_UNCHANGED')
    require(body['state']=='STOPPED_NOT_ACCEPTED' and body['stop_reason']==body['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and body['operation_phase']=='final_source_freeze' and body['policy']==m.p.c.POLICY
        and body['maximum_seconds']==1200,'ORIGINAL_POST_SOURCE_STOP_NOT_PASS')
    require(body['binding']==root['binding'] and body['selected_test_names']==body['passed_test_names']==[NAME]
        and body['test_arguments']==m.p.v.arguments(NAME) and body['task']==body['minimal_worker_task']=='p204-r07-case-106-tests'
        and body['minimal_owned_worker_path']==m.p.m.SELF,'EXACT_BODY_IDENTITY')
    require(type(body['exit_code']) is int and body['exit_code']==0 and body.get('tests_passed') is None
        and body['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and body['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False)
        and body['actual_product_child_executed'] is True,'COMPLETE_ONE_TEST_CANDIDATE_NOT_SOURCE_PASS')
    require(all(body[k] is True for k in ('cleanup_confirmed','owned_tree_empty','worker_created','job_assigned',
        'writer_authorized','owned_limits_verified','actual_job_membership_checked'))
        and body['job_final']['active_processes']==0 and body['job_final']['owned_processes']==[]
        and body['job_final']['job_cpu_seconds']==0.281 and body['job_final']['peak_job_private_mib']==22.32,
        'ORIGINAL_JOB_CLEANUP_READBACK_NOT_INVENTED_ZERO')
    m.m.job_contract(body)
    required=m.p.v.pins(body['source_freeze'])
    require(len(required)==1654 and sum(x['bytes'] for x in required.values())==120895337
        and required[m.p.m.EXE['path']]==m.p.m.EXE and required[m.p.m.SELF]==m.p.prior.WORKER_PIN
        and all(required.get(n)==dict(path=n,**pin) for n,pin in m.p.m.CORE_PINS.items()),'FULL_ORIGINAL_EXECUTED_INPUTS')
    passes=body['owned_source_reader_passes']
    require(len(passes)==2 and passes[0]['read_passes']==1654 and passes[0]['bytes_read']==120895337
        and passes[1]['read_passes']==1172 and passes[1]['bytes_read']==84584950
        and all(row['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and row['original_owned_read_operations_preserved'] is True
            and row['extra_sampler_or_native_query_started'] is False for row in passes),'ORIGINAL_POST1172_NOT_FULL1654')
    frame=root['terminal_source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1654 and frame['input_bytes']==120895337
        and len(frame['actual_byte_boundaries'])==1 and frame['actual_byte_boundaries'][0]['role']=='before'
        and m.p.v.pins(frame['actual_byte_boundaries'][0]['actual_byte_pins'])==required,
        'CLOSED_PARTIAL_FRAME_NOT_COMMITTED_TWO_BOUNDARIES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==1962
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==307
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2826
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0,
        'ALL_OPENED_NATIVE_AND_PARTIAL_DUPLICATES_CLOSED')
    m.profile.phase_contract(h['acquisition_phase_pressure'],1962,True)
    error=h['lock_timing_diagnostic']['first_original_error']
    require(error['original_error_code']=='STOP_SUSTAINED_SYSTEM_CPU' and error['phase']=='final_fresh_hash'
        and error['original_lock_limit_seconds']==600 and 0<error['original_lock_elapsed_seconds']<600,
        'ORIGINAL600_WITHOUT_EXTENSION')
    prep=root['preparation_IO']
    require(prep['finished'] is True and prep['read_passes']==278
        and prep['bound_inputs']==prep['final_fresh_hashes']==139 and prep['bytes_read']==16595086,
        'ORIGINAL_PREPARATION_COMPLETE_NOT_POST_SOURCE')
    rows=root['metadata_observation']['samples']
    require(len(rows)==776 and all(98<=x['system_cpu_percent']<=100 for x in rows[-4:])
        and all(x['parent_cpu_machine_percent']==x['audited_logical_read_bytes_delta']==0 for x in rows[-3:]),
        'ORIGINAL_HARD_CPU_STOP_NOT_REMOVED')
    m.m.early_contract(root['early_source_checkpoint'])
    stats=root['terminal_parent_failure_statistics']
    require(stats['characters_written']==BODY['bytes'] and stats['semantic_fields_intentionally_removed']==0
        and stats['terminal_failed_evidence_only'] is True and stats['runtime_accepted'] is False
        and stats['original_files_rewritten'] is False and stats['original_live_frame_guard_restarted'] is False
        and stats['maximum_write_batch_chars']<=32768,'BOUNDED_COMPLETE_TERMINAL_FAILURE_ONLY')
    for doc in (root,body):
        require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
            and all(doc[k] is False for k in ('full249_current_qualified','signed16_current_qualified',
                'product_complete','PC_freeze_resolved')),'NO_GATE_OR_PRODUCT_PROMOTION')
    return dict(selected_test_index=106,semantic_body_capture_complete=True,validated_original_terminal_pass_count=1,
        original_failed_root_preserved=True,original_stopped_parent_preserved=True,original_zero_placeholder_preserved=True,
        original_partial_post_source_hash_completed=False,independent_full_source_closing_required=True,
        original_executed_source_inputs=1654,source_closing_candidate_count=1,accepted_runtime_subset=99,next_runtime_index=106,
        runtime_acceptance_changed=False,same_product_body_reexecution_allowed=False,original_Job_cleanup_confirmed=True,
        CPU_cause_or_PC_freeze_resolution_established=False)


PRIOR_SOURCE_FAILURE=dict(path=m.p.DIR+'/p338-source-run002.v1.json',bytes=706878,
 sha256='b7967fc1e225f99bd11daaf12d7fe66104bdfc9692d1ae9610424caeb3addd6a')
PRIOR_SUPPORT_CODE=[
 dict(path=SELF,bytes=28010,sha256='ea1e12c87c297d9967fd1bd0044bdd8ff552652cbce22d65301c1940b8a7fc43'),
 dict(path=TEST,bytes=10165,sha256='1eff838d233a9da7ec44dff13d8feafb114ea69ceb3727274803c0794f806b2b')]
PRIOR_SUPPORT_ARCHIVES=[dict(v,path='implementation/p09/evidence/p338-v1-source-code/'+PurePosixPath(v['path']).name)
 for v in PRIOR_SUPPORT_CODE]

def review_source_attempt(doc,original):
    require(doc['schema_version']=='hwpx-agent.p09-preserved106-source-closing/v1'
        and doc['state']=='FAILED_NOT_ACCEPTED' and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['failure_diagnostic']['stage']=='source_acquire' and doc['resource_watcher_cleanup_confirmed'] is True
        and doc['actual_product_child_executed'] is False and doc['actual_source_frame_executed'] is False
        and doc['contract_tests_passed']==54 and doc['current93_code_pins']==CODE91+PRIOR_SUPPORT_CODE
        and doc['original_root_pin']==ROOT and doc['original_parent_pin']==BODY and doc['original_zero_pin']==ZERO,
        'ORIGINAL_FAILED_SOURCE_NOT_REVIEW_OR_NATIVE_PASS')
    required={**original,**{v['path']:v for v in PRIOR_SUPPORT_CODE}}
    require(m.p.v.pins(doc['extended_source_pins'])==required and len(required)==1656,'OLD1656_NOT_CURRENT_SOURCE_ALIAS')
    frame=doc['source_frame'];h=frame['handles']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1656 and frame['input_bytes']==120933512
        and frame['actual_byte_boundaries']==[] and frame['held_identity_after_owned_cleanup'] is None
        and h['input_lock_handles_opened']==h['input_lock_handles_closed']==612
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['handle_close_failed_attempts']==0 and h['input_lock_cleanup_confirmed'] is True
        and h['borrowed_byte_streams'] is None,'ACTUAL612_ACQUIRED_CLOSED_NOT_NATIVE_FALSE')
    io=doc['IO'];require(io['finished'] is True and io['bound_inputs']==io['final_fresh_hashes']==140
        and io['read_passes']==371 and io['bytes_read']==21648155,'ORIGINAL_EXTRA91_READS_DIAGNOSTIC_NOT_REPLACED')
    rows=doc['observation']['samples']
    require(len(rows)==131 and all(row['system_cpu_percent']==100 for row in rows[-4:])
        and all(row['parent_cpu_machine_percent']==row['audited_logical_read_bytes_delta']==0 for row in rows[-4:]),
        'ORIGINAL_IDLE_PARENT_SATURATED_SYSTEM_STOP')
    return dict(original_pin=PRIOR_SOURCE_FAILURE,original_declared_native_false_preserved=True,
        actual_Native_acquisition_happened=True,opened_and_closed=612,actual_byte_boundaries_completed=0,
        actual_product_reexecuted=False,original_FAILED_not_promoted=True,
        duplicate91_source_reads_identified=True,CPU_or_freeze_solution_established=False)

def previous_source_review(q,original):
    for logical,archive in zip(PRIOR_SUPPORT_CODE,PRIOR_SUPPORT_ARCHIVES):
        require(q.pin(archive['path'])==archive and logical['bytes']==archive['bytes']
            and logical['sha256']==archive['sha256'],'EXACT_V1_CODE_PREIMAGE')
    failed=m.m.m.review.bound_json(q,PRIOR_SOURCE_FAILURE)
    return review_source_attempt(failed,original)

def contract_qualification(doc):
    row=doc['qualified_review_contract_statistics']
    require(doc['qualified_contract_tests']==COUNT and row['started_tests']==row['stopped_tests']==
        row['successful_before_test_checks']==row['successful_after_test_checks']==COUNT,'EXACT_REVIEW_CONTRACT_CHECKPOINTS')
    if doc['state']==REVIEW_PASS:
        require(doc['contract_tests_passed']==COUNT and doc['reused_review_contract_executions']==0
            and doc['contracts_checkpoint_statistics']==row,'REVIEW_ACTUAL_EXECUTIONS_NOT_REUSE')
    else:
        require(doc['contract_tests_passed']==0 and doc['reused_review_contract_executions']==COUNT
            and doc['contracts_checkpoint_statistics'] is None and doc.get('review_pin') is not None,
            'QUALIFIED_SAME_CODE_REVIEW_REUSED_NOT_NEW_EXECUTION')

def mark_native_attempt(out):
    out['actual_source_frame_executed']=True
    out['source_frame_qualified']=False


def pin_argument(value,mode):
    pin=json.loads(value) if isinstance(value,str) else value
    require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and type(pin['bytes']) is int
        and 0<pin['bytes']<=16777216 and re.fullmatch('[0-9a-f]{64}',pin['sha256']) is not None
        and re.fullmatch(re.escape(m.p.DIR)+r'/p338-'+mode+r'-run[0-9]{3}\.v1\.json',pin['path']) is not None,
        'EXACT_SCOPED_RECEIPT_PIN')
    return pin

def code(q):
    # anchor가 같은 Reader에서 이미 실제 bind한91개. extra hash91회만 제거하고 원 finish fresh는 유지한다.
    observed=m.current_code(q)
    require(observed==CODE91,'ORIGINAL91_BYTES_UNCHANGED')
    return observed+[q.pin(n) for n in (SELF,TEST)]

def load(q):
    legacy,base,names,expected,exe,required,extras,baseline,added,healthy,healthy_body,oldstop=m.anchor(q)
    binding=m.p.v.identity(names,expected,exe);codes=code(q);bound=m.m.m.review.bound_json
    first=bound(q,ACTUAL104)
    body104=bound(q,first['case_receipt_pin'])
    failed=bound(q,dict(path=m.p.DIR+'/p335-case-104-run003.v1.json',bytes=215398,
        sha256='ea547ac25f744bdc1eebbebe5e43233a4c4ed106536ba9b22e1ec7974f518b6d'))
    reviewed=bound(q,PRIOR_REVIEW)
    m.review_contract(reviewed,dict(path=m.p.DIR+'/p335-case-104-run003.v1.json',bytes=215398,
        sha256='ea547ac25f744bdc1eebbebe5e43233a4c4ed106536ba9b22e1ec7974f518b6d'),
        failed,base,required,binding,extras,baseline,added,names,CODE91)
    base=m.record(first,body104,first['case_receipt_pin'],required,binding,extras,names,legacy,base,baseline,added)
    latest=bound(q,ACTUAL105);latest_body=bound(q,latest['case_receipt_pin'])
    base=m.record(latest,latest_body,latest['case_receipt_pin'],required,binding,extras,names,legacy,base,baseline,added)
    fresh=bound(q,PRIOR_FRESH)
    light=bound(q,fresh['reviewed_light_pin']);m.light_review_contract(fresh,light,fresh['reviewed_light_pin'],CODE91)
    require(base==fresh['prior_runtime_plan'] and base['runtime_source_qualified_individual_cases']==99
        and base['next_runtime_index']==106 and names[105]==NAME,'INDEPENDENT99_NEXT106')
    root=bound(q,ROOT);body=bound(q,BODY);require(q.pin(ZERO['path'])==ZERO,'ORIGINAL_ZERO_UNCHANGED')
    checked=review(root,body)
    q.previous_source_failure_review=previous_source_review(q,required)
    require(base==root['prior_runtime_plan'] and body['binding']==root['binding']==binding
        and m.p.v.pins(body['source_freeze'])==required,'EXACT_EXECUTED1654_AND_QUEUE99')
    require(m.current_code(q)==CODE91,'CURRENT91_NATIVE_QUALIFIED_PINS')
    folder=m.p.c.ROOT/m.p.DIR
    require(sorted(v.name for v in folder.glob('p335-case-*-run*.v1.json'))==
        ['p335-case-104-run003.v1.json','p335-case-104-run006.v1.json','p335-case-105-run009.v1.json','p335-case-106-run012.v1.json'],
        'NO_UNKNOWN_PRODUCT_OR_REPLAY')
    extended={**required,SELF:codes[-2],TEST:codes[-1]}
    return legacy,base,names,binding,required,extended,root,body,checked,codes,latest

def budget(required):
    require(len(required)==N and required[m.p.m.EXE['path']]==m.p.m.EXE
        and all(n in required for n in (SELF,TEST)),'FULL1654_PLUS2_NOT_REDUCED')
    binary=m.p.m.EXE['bytes'];other=sum(v['bytes'] for v in required.values())-binary
    total=(N+DIRECTORIES)/14+2*N/20+2*binary/1048576+2*other/2097152+60+15+60
    require(total<600 and sum(required[n]['bytes'] for n in (SELF,TEST))<=1048576,'UNCHANGED600_ESTIMATE')
    return dict(inputs=N,ancestor_directories=DIRECTORIES,acquisition_rate=14,byte_native_rate=20,
        source_bytes=sum(v['bytes'] for v in required.values()),nominal_combined_seconds=total,
        unchanged_actual_deadline_seconds=600,estimate_not_completion_guarantee=True,
        unbounded_pressure_may_still_STOP=True)

def prepared(doc,required):
    contract_qualification(doc)
    require(doc['schema_version']==SCHEMA and doc['state'] in (REVIEW_PASS,SOURCE_PASS,ACCEPT_PASS)
        and doc['original_root_pin']==ROOT and doc['original_parent_pin']==BODY and doc['original_zero_pin']==ZERO
        and doc['actual_product_child_executed'] is False and doc['successful_body_reexecution_allowed'] is False

        and doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['resource_stop_reason'] is None
        and doc['source_budget']==budget(required) and m.p.v.pins(doc['extended_source_pins'])==required
        and all(doc[k]=='OPEN' for k in ('P09_gate','A12_gate','A13_gate'))
        and all(doc[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'FULL_SCOPE_QUALIFIED_SUPPORT_NOT_PRODUCT_REPLAY')



def validate_source(doc,required):
    prepared(doc,required)
    require(doc['state']==SOURCE_PASS and len(required)==N,'FULL_SOURCE_NOT_PREPARATION')
    frame=doc['source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams'];total=sum(x['bytes'] for x in required.values())
    require(frame['frame_state']=='COMMITTED' and frame['registered_live_frame'] is False
        and frame['input_count']==N and frame['input_bytes']==total
        and frame['original_owned_cleanup_confirmed_before_release'] is True
        and frame['original_two_actual_per_case_byte_reads_retained'] is True
        and all(frame[k] is False for k in ('serialized_pin_reused_as_live_handle','input_exclusions_added','security_sandbox_claimed')),
        'FULL_LIVE_COMMITTED_NOT_CACHE')
    boundaries=frame['actual_byte_boundaries']
    require(len(boundaries)==2 and [b['role'] for b in boundaries]==['before','after']
        and all(m.p.v.pins(b['actual_byte_pins'])==required and b['reader_diagnostics']['read_passes']==N
            and b['reader_diagnostics']['bytes_read']==total
            and b['reader_diagnostics']['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and b['reader_diagnostics']['original_owned_read_operations_preserved'] is True
            and b['reader_diagnostics']['extra_sampler_or_native_query_started'] is False for b in boundaries),
        'TWO_COMPLETE_ACTUAL_BYTE_BOUNDARIES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==N+DIRECTORIES
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['probe_handles_opened']==h['probe_handles_closed']==h['probe_handles_remaining']==0
        and h['byte_stream_identity_checks']==2*N and h['separate_pathname_reopens']==0
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==DIRECTORIES-1
        and h['native_open_pacing']['maximum_opens_per_second']==20
        and h['native_open_pacing']['open_reservations']==3*N+DIRECTORIES
        and h['handle_metadata_checks']==4*N+2*DIRECTORIES
        and h['file_write_or_delete_operation_executed'] is False,'ALL_NATIVE_LIMITS_AND_CLOSE')
    require(dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2*N
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0
        and dup['original_pre_read_stream_identity_check_retained'] is True
        and dup['original_held_handles_closed_by_borrower'] is False,'ALL_SERIAL_DUPLICATES_IDENTITIES')
    require(frame['held_identity_after_owned_cleanup']==dict(held_identity_checks_complete=True,
        separate_pathname_reopens=0,regular_file_count=N,directory_count=DIRECTORIES),'ALL_POST_CLEANUP_HELD_IDENTITIES')
    m.profile.phase_contract(h['acquisition_phase_pressure'],N+DIRECTORIES,True)
    pressure=h['native_open_backpressure']
    require(all(pressure[k] is True for k in ('original_hard_resource_decisions_unmodified','original_IO_deadline_unmodified',
        'original_sampler_windows_reused','cleanup_not_guarded_by_pressure')) and pressure['original_read_checks_skipped'] is False,
        'ORIGINAL_NATIVE_PRESSURE')
    m.m.early_contract(doc['early_source_checkpoint'])
    require(doc['early_source_runtime_connection_verified'] is True
        and doc['early_source_native_and_byte_guard_connected'] is True,'LIVE_EARLY_CONNECTION')
    timing=h['lock_timing_diagnostic']
    require(timing['first_original_error'] is None and timing['original_lock_limit_seconds']==600
        and timing['original_check_invoked_without_replacement'] is True and timing['unknown_measurements_not_zeroed'] is True
        and all(timing[k] is False for k in ('extra_CPU_RAM_or_native_query_started','original_resource_guard_or_deadline_extended',
            'cleanup_callback_wrapped','CPU_or_PC_freeze_improvement_established')),'ORIGINAL_TIMING_GUARD')
    events=timing['explicit_phase_events']
    require([x['label'] for x in events]==['before_acquire','after_acquire','before_release']
        and all(type(x['original_lock_elapsed_seconds']) in (float,int) and 0<=x['original_lock_elapsed_seconds']<=600 for x in events)
        and all(events[i]['original_lock_elapsed_seconds']<=events[i+1]['original_lock_elapsed_seconds']
            and events[i]['guard_check_number']<events[i+1]['guard_check_number'] for i in range(2)),
        'THREE_SOURCE_BOUNDARIES_NO_PARENT_OR_INVENTED_EVENT')

def review_receipt(doc,required,checked,codes):
    prepared(doc,required)
    require(doc['state']==REVIEW_PASS and doc['review']==checked and doc['current93_code_pins']==codes
        and doc['actual_source_frame_executed'] is False and doc.get('source_frame') is None,'INDEPENDENT_REVIEW_ONLY')

def source_receipt(doc,required,checked,codes):
    validate_source(doc,required)
    require(doc['review']==checked and doc['current93_code_pins']==codes
        and doc['actual_source_frame_executed'] is True and doc['source_frame_qualified'] is True,'NEW_FULL_AFTER_FRAME_NOT_PARTIAL_REPLAY')

def advance(legacy,base,names):
    require(base['runtime_source_qualified_individual_cases']==99 and base['next_runtime_index']==106
        and NAME not in base['runtime_qualified_test_names'],'EXACT_NEXT_PENDING_NOT_DUPLICATE')
    plan=m.g.advance(legacy,base,names,106)
    require(plan['runtime_source_qualified_individual_cases']==100 and plan['runtime_remaining_individual_cases']==149
        and plan['next_runtime_index']==107 and plan['runtime_remaining_regular_cases']==143
        and plan['runtime_remaining_corpus_cases']==6 and plan['all_successful_bodies_pending_whole_reconciliation']==97,
        'COMPOUND100_NOT_WHOLE_OR_GATE')
    return plan

def contracts(fixtures,q):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    import test_preserved106_source as t
    with m.WarmTestIsolation(),m.guarded.bind(q.reader.checkpoint) as statistics,patch.object(t,'FIXTURES',fixtures), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_PRODUCT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_PRODUCT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_CONTRACT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
        if not result.wasSuccessful():q.contract_failures=[str(t) for t,_ in result.failures+result.errors][:8]
        require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'ALL_ORIGINAL_CHECKPOINT_CONTRACTS')
    return COUNT,statistics.summary()

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=('review','source','accept'),required=True);ap.add_argument('--run',type=int,required=True)
    ap.add_argument('--review-pin');ap.add_argument('--source-pin')
    args=ap.parse_args(argv);require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=999,'CWD_RUN')
    require((args.mode!='review')==(args.review_pin is not None) and (args.mode=='accept')==(args.source_pin is not None),'EXPLICIT_MODE_PINS')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p338-{args.mode}-run{args.run:03}.v1.json';require(not destination.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context)
    q=frame=early=proposed=None;stage='admission';out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),
        original_root_pin=ROOT,original_parent_pin=BODY,original_zero_pin=ZERO,
        successful_body_reexecution_allowed=False,actual_source_frame_executed=False,
        source_kind='INDEPENDENT_AFTER_COMPLETED_WORKER_NOT_ORIGINAL_PARTIAL_AFTER',source_frame_qualified=False,
        startup_limits=m.STARTUP_LIMITS)
    try:
        owner.admit();q=m.Reader(owner,context);stage='metadata'
        legacy,base,names,binding,original,required,root,body,checked,codes,latest=load(q)
        out.update(review=checked,current93_code_pins=codes,original_executed_source_pins=list(original.values()),
            extended_source_pins=list(required.values()),source_budget=budget(required),prior_runtime_plan=base,binding=binding,
            previous_source_failure_review=q.previous_source_failure_review)
        if args.mode!='review':
            rp=pin_argument(args.review_pin,'review');reviewed=m.m.m.review.bound_json(q,rp)
            review_receipt(reviewed,required,checked,codes);out['review_pin']=rp
        if args.mode=='accept':
            sp=pin_argument(args.source_pin,'source');source=m.m.m.review.bound_json(q,sp)
            source_receipt(source,required,checked,codes);require(source['review_pin']==rp,'SAME_QUALIFIED_REVIEW_SOURCE')
            out['separate_source_frame_pin']=sp
        stage='contract_qualification'
        if args.mode=='review':
            with context.scope('contract_tests'):
                out['contract_tests_passed'],out['contracts_checkpoint_statistics']=contracts((root,body,original,required,latest),q)
            out.update(qualified_contract_tests=COUNT,reused_review_contract_executions=0,
                qualified_review_contract_statistics=out['contracts_checkpoint_statistics'])
        else:
            # 同じ code93 / original immutable pins / queue / extended1656 を review_receipt で再確認済み。
            out.update(contract_tests_passed=0,contracts_checkpoint_statistics=None,
                qualified_contract_tests=COUNT,reused_review_contract_executions=COUNT,
                qualified_review_contract_statistics=reviewed['qualified_review_contract_statistics'])
        stage='metadata_final_fresh';q.finish()
        if args.mode=='review':proposed=dict(state=REVIEW_PASS)
        elif args.mode=='accept':
            out.update(runtime_plan=advance(legacy,base,names),accepted_exact_compound_case_count=1,
                original_failed_root_accepted=False,original_partial_after_hash_completed=False,
                semantic_body_capture_pass_count=1,additional_source_frame_executed=False)
            proposed=dict(state=ACCEPT_PASS)
        else:
            early=m.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
            held=m.profile.InputLocks(m.p.c.ROOT,early,owner,context)
            require(held.checkpoint is early and held.api.pacer.rate==20 and held.open_pressure.resources is owner,'ORIGINAL_NATIVE_OWNER')
            frame=m.p.frames.Frame(m.p.frames.Registry(),required,early,held=held)
            context.reader=m.p.frames.Counters(q.reader,frame.readers);out['early_source_native_and_byte_guard_connected']=True
            mark_native_attempt(out)
            stage='source_acquire';held.mark('before_acquire')
            with context.scope('metadata_hash'):frame.acquire()
            held.mark('after_acquire')
            def factory(checkpoint):
                return m.p.core.run.owned.OwnedReader(m.p.c.ROOT,checkpoint,samples=owner,protected={m.p.m.EXE['path']})
            for phase in ('metadata_hash','final_fresh_hash'):
                stage=phase
                with context.scope(phase):frame.read_boundary(factory,owner.checkpoint_io)
            stage='source_commit';held.mark('before_release')
            out.update(source_frame=frame.commit(body),early_source_runtime_connection_verified=True,source_frame_qualified=True)
            proposed=dict(state=SOURCE_PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out.update(error_code=m.p.b.run.original.closed_error(error),failure_diagnostic=m.m.diagnostic(error,stage));proposed=None
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='SOURCE_FRAME_CLEANUP_FAILED';proposed=None
            out['source_frame']=frame.summary()
        if early is not None:out['early_source_checkpoint']=early.summary()
        if q is not None:
            q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
            if hasattr(q,'contract_failures'):out['contract_failures']=q.contract_failures
        out['observation']=m.g.observation.summary(owner)
        def validate(doc):
            prepared(doc,required)
            if doc['state']==REVIEW_PASS:review_receipt(doc,required,checked,codes)
            elif doc['state']==SOURCE_PASS:source_receipt(doc,required,checked,codes)
            else:
                require(doc['state']==ACCEPT_PASS and doc['runtime_plan']==advance(legacy,base,names)
                    and doc['review']==checked and doc['current93_code_pins']==codes
                    and doc['accepted_exact_compound_case_count']==1 and doc['semantic_body_capture_pass_count']==1
                    and doc['original_failed_root_accepted'] is False and doc['original_partial_after_hash_completed'] is False
                    and doc['additional_source_frame_executed'] is False,'ONLY_HASH_BOUND_CLOSED_COMPOUND')
                source_receipt(source,required,checked,codes)
        m.complete_runtime(out,owner,proposed,validate)
        with destination.open('x',encoding='utf-8') as stream:
            writer=m.r.packed.dump if out['state'] in (REVIEW_PASS,SOURCE_PASS,ACCEPT_PASS) else m.r.compact.dump
            def terminal():require(owner.done.is_set(),'NO_RESOURCE_RESTART')
            writer(out,stream,checkpoint=terminal,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','contract_tests_passed')}))
    return 0 if out['state'] in (REVIEW_PASS,SOURCE_PASS,ACCEPT_PASS) else 2

if __name__=='__main__':
    sys.modules.setdefault('complete_preserved106_source',sys.modules[__name__])
    raise SystemExit(main())
