"""P293: 보존된101 본체 성공/최종source STOP의 독립 마감 후보 검토.
실패 원문·부분 읽기는 불변이며 runtime/Gate 수용 또는 본체 재실행을 하지 않는다.
"""
import resume_reviewed_anchor_runtime as m

SELF='tools/p09/review_completed101_stop.py'
TEST='tools/p09/tests/test_completed101_stop.py'
ROOT=dict(path=m.p.DIR+'/p291-case-101-run002.v1.json',bytes=977979,
    sha256='20dbb9c846f3b1f719204b9583c51a71cf578a708ab10b2a81c08d61c35495fa')
BODY=dict(path=m.p.DIR+'/cases/p291-failure-101-run002.json',bytes=529451,
    sha256='aeea72d5940d6e0de7f585716101857733d8955c7678017ed141df81816aafff')
ZERO=dict(path=m.p.DIR+'/cases/p291-case-101-run002.json',bytes=0,
    sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
NAME='actual_import::formula_product_request::current_whole_formula_results_are_true_noop_without_fabricating_empty_plan_or_execution'
SCHEMA='hwpx-agent.p09-completed101-final-source-stop-review/v1'
PASS='PASS_COMPLETED101_FAILED_FINAL_SOURCE_REVIEW_NOT_RUNTIME_OR_GATE'

def require(ok,code):m.require(ok,'COMPLETED101_'+code)

def review(root,body):
    require(root['schema_version']==m.SCHEMA and root['state']=='FAILED_NOT_ACCEPTED'
        and root['error_code']==root['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and root['resource_watcher_cleanup_confirmed'] is True
        and root['accepted_exact_product_body_count']==0 and root['runtime_contract_executions']==1486
        and root['selected_test_index']==101 and root['selected_test_name']==NAME
        and root['failure_diagnostic']['stage']=='owned_parent'
        and root['failure_diagnostic']['exception_class']=='ValueError','ORIGINAL_FAILED_ROOT_NOT_ACCEPTANCE')
    require(root['terminal_parent_failure_sidecar_pin']==BODY and root['case_receipt_path']==ZERO['path']
        and root['original_failure_body_placeholder_preserved'] is True
        and root.get('terminal_failure_write_error') is None and 'case_receipt_pin' not in root
        and 'runtime_plan' not in root and 'closing_component' not in root,'IMMUTABLE_FAILURE_SIDECAR_NOT_CLOSED_PAIR')
    plan=root['prior_runtime_plan']
    require(plan['runtime_source_qualified_individual_cases']==94 and plan['next_runtime_index']==101
        and plan['runtime_remaining_individual_cases']==155 and NAME not in plan['runtime_qualified_test_names'],
        'PRIOR94_PENDING101_UNCHANGED')
    require(body['state']=='STOPPED_NOT_ACCEPTED' and body['stop_reason']==body['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and body['operation_phase']=='final_source_freeze' and body['policy']==m.p.c.POLICY
        and body['maximum_seconds']==1200,'ORIGINAL_POST_SOURCE_STOP_NOT_PASS')
    require(body['binding']==root['binding'] and body['selected_test_names']==body['passed_test_names']==[NAME]
        and body['test_arguments']==m.p.v.arguments(NAME) and body['task']==body['minimal_worker_task']=='p204-r07-case-101-tests'
        and body['minimal_owned_worker_path']==m.p.m.SELF,'EXACT_BODY_IDENTITY')
    require(type(body['exit_code']) is int and body['exit_code']==0 and body.get('tests_passed') is None
        and body['terminal_summary']==dict(passed=1,failed=0,ignored=0,measured=0,filtered_out=248)
        and body['capture']==dict(error_code=None,per_stream_limit_bytes=32768,complete_streams=True,raw_logs_saved=False)
        and body['actual_product_child_executed'] is True,'COMPLETE_ONE_TEST_CANDIDATE_NOT_SOURCE_PASS')
    require(all(body[k] is True for k in ('cleanup_confirmed','owned_tree_empty','worker_created','job_assigned',
        'writer_authorized','owned_limits_verified','actual_job_membership_checked'))
        and body['job_final']['active_processes']==0 and body['job_final']['owned_processes']==[]
        and body['job_final']['job_cpu_seconds']==2.172 and body['job_final']['peak_job_private_mib']==27.92,
        'ORIGINAL_JOB_CLEANUP_READBACK_NOT_INVENTED_ZERO')
    m.job_contract(body)
    required=m.p.v.pins(body['source_freeze'])
    require(len(required)==1599 and sum(x['bytes'] for x in required.values())==119993724
        and required[m.p.m.EXE['path']]==m.p.m.EXE and required[m.p.m.SELF]==m.p.prior.WORKER_PIN
        and all(required.get(n)==dict(path=n,**pin) for n,pin in m.p.m.CORE_PINS.items()),'FULL_ORIGINAL_EXECUTED_INPUTS')
    passes=body['owned_source_reader_passes']
    require(len(passes)==2 and passes[0]['read_passes']==1599 and passes[0]['bytes_read']==119993724
        and passes[1]['read_passes']==474 and passes[1]['bytes_read']==56921407
        and all(row['read_rates_by_kind']==dict(binary=1048576,other=2097152)
            and row['original_owned_read_operations_preserved'] is True
            and row['extra_sampler_or_native_query_started'] is False for row in passes),'ORIGINAL_POST474_NOT_FULL1599')
    frame=root['terminal_source_frame'];h=frame['handles'];dup=h['borrowed_byte_streams']
    require(frame['frame_state']=='CLOSED' and frame['registered_live_frame'] is False
        and frame['input_count']==1599 and frame['input_bytes']==119993724
        and len(frame['actual_byte_boundaries'])==1 and frame['actual_byte_boundaries'][0]['role']=='before'
        and m.p.v.pins(frame['actual_byte_boundaries'][0]['actual_byte_pins'])==required,
        'CLOSED_PARTIAL_FRAME_NOT_COMMITTED_TWO_BOUNDARIES')
    require(h['input_lock_handles_opened']==h['input_lock_handles_closed']==1907
        and h['input_lock_handles_remaining']==h['active_reader_bindings']==h['active_byte_streams']==0
        and h['input_lock_cleanup_confirmed'] is True and h['handle_close_failed_attempts']==0
        and h['maximum_lock_seconds']==600 and h['ancestor_walk_steps']==307
        and dup['duplicate_handles_opened']==dup['duplicate_handles_closed']==dup['shared_offset_resets']==2073
        and dup['duplicate_handles_remaining']==dup['duplicate_close_failed_attempts']==0
        and dup['active_borrow_binding'] is False and dup['byte_stream_pathname_reopens']==0,
        'ALL_OPENED_NATIVE_AND_PARTIAL_DUPLICATES_CLOSED')
    m.profile.phase_contract(h['acquisition_phase_pressure'],1907,True)
    error=h['lock_timing_diagnostic']['first_original_error']
    require(error['original_error_code']=='STOP_SUSTAINED_SYSTEM_CPU' and error['phase']=='final_fresh_hash'
        and error['original_lock_limit_seconds']==600 and 0<error['original_lock_elapsed_seconds']<600,
        'ORIGINAL600_WITHOUT_EXTENSION')
    prep=root['preparation_IO']
    require(prep['finished'] is True and prep['read_passes']==669
        and prep['bound_inputs']==prep['final_fresh_hashes']==245 and prep['bytes_read']==77663915,
        'ORIGINAL_PREPARATION_COMPLETE_NOT_POST_SOURCE')
    rows=root['metadata_observation']['samples']
    require(len(rows)==732 and all(x['system_cpu_percent']==100 for x in rows[-4:])
        and all(x['parent_cpu_machine_percent']==x['audited_logical_read_bytes_delta']==0 for x in rows[-3:]),
        'ORIGINAL_HARD_CPU_STOP_NOT_REMOVED')
    m.early_contract(root['early_source_checkpoint'])
    stats=root['terminal_parent_failure_statistics']
    require(stats['characters_written']==BODY['bytes'] and stats['semantic_fields_intentionally_removed']==0
        and stats['terminal_failed_evidence_only'] is True and stats['runtime_accepted'] is False
        and stats['original_files_rewritten'] is False and stats['original_live_frame_guard_restarted'] is False
        and stats['maximum_write_batch_chars']<=32768,'BOUNDED_COMPLETE_TERMINAL_FAILURE_ONLY')
    for doc in (root,body):
        require(doc['P09_gate']==doc['A12_gate']==doc['A13_gate']=='OPEN'
            and all(doc[k] is False for k in ('full249_current_qualified','signed16_current_qualified',
                'product_complete','PC_freeze_resolved')),'NO_GATE_OR_PRODUCT_PROMOTION')
    return dict(selected_test_index=101,semantic_body_capture_complete=True,validated_original_terminal_pass_count=1,
        original_failed_root_preserved=True,original_stopped_parent_preserved=True,original_zero_placeholder_preserved=True,
        original_partial_post_source_hash_completed=False,independent_full_source_closing_required=True,
        original_executed_source_inputs=1599,source_closing_candidate_count=1,accepted_runtime_subset=94,next_runtime_index=101,
        runtime_acceptance_changed=False,same_product_body_reexecution_allowed=False,original_Job_cleanup_confirmed=True,
        CPU_cause_or_PC_freeze_resolution_established=False)
