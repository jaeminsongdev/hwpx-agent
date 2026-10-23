"""Independent audit of a completed child and a FAILED outer monitor.

Never rewrites the outer failure, invents live-phase credit, infers an OS exit
code, resumes the child, or converts read-only evidence into product acceptance.
The original full Frame/timing/metadata validator is called without relaxation.
"""
SELF='tools/p09/native011_readonly_terminal_audit.py'
TEST='tools/p09/tests/test_native011_readonly_terminal_audit.py'
RACE='NATIVE011_OWNED_METADATA_AUDIT_NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS'


def require(ok,code):
    if not ok:raise ValueError('READONLY_TERMINAL_AUDIT_'+code)


def inspect(child,parent,validator,read):
    require(parent['state']=='FAILED_OWNED_READONLY_NATIVE_FRAME_NOT_ACCEPTED'
        and parent['failure']['first_error_code']==RACE and parent['cleanup'] is True
        and parent['automatic_retry'] is False and parent['accepted_count_delta']==0
        and parent['GO_authorized'] is False,'ORIGINAL_MONITOR_FAILURE_MUST_STAY_FAILED')
    owned=parent['owned'];job=owned['owned_job'];limits=job['limits_readback']
    require(owned['constructor_entered'] is True and owned['cleanup'] is True
        and owned['cleanup_errors']==[] and job['worker_created'] is job['job_assigned'] is job['target_authorized'] is True
        and job['owned_tree_empty'] is job['cleanup_confirmed'] is job['job_handle_closed'] is True
        and job['last_job_accounting']['active_processes']==0
        and job['last_job_accounting']['owned_processes']==[]
        and limits['verified'] is limits['kill_on_close'] is limits['breakaway_disabled'] is True
        and limits['cpu_hard_cap_machine_percent']==6.25 and limits['affinity_mask']==1
        and limits['priority_class']==16384,'ORIGINAL_OWNED_JOB_EMPTY_WITH_ALL_LIMITS_RETAINED')
    epochs=parent['epochs']
    require(len(epochs)==3
        and [e['stage'] for e in epochs]==['construction','opening','native_readonly']
        and all(e['cleanup_confirmed'] is True and 0<e['elapsed_seconds']<600 for e in epochs),
        'EXACT_THREE_REAL_MONITORED_PHASES_NO_TERMINAL_PHASE_INVENTED')
    # Read every indexed Frame/timing part through the original validator.
    # Source freshness and closing belong to the separate caller's reader.
    result=validator(child,read)
    require(result['accepted_count_delta']==0 and result['product_executed'] is False
        and result['batch_phase']=='BROKEN','READONLY_ABORT_NOT_PRODUCT_ACCEPTANCE')
    return dict(state='CHECKED_TERMINAL_READONLY_CHILD_WITH_FAILED_MONITOR_PRESERVED',
        validated_child=result,original_owned_monitor_state=parent['state'],original_owned_monitor_pass=False,
        original_monitor_failure_reclassified=False,unobserved_live_phase_or_exit_code_inferred=False,
        original_child_OS_exit_code_not_directly_recorded='exit_code' not in owned,
        original_three_monitored_phases_preserved=True,original_owned_tree_cleanup_verified=True,
        new_Native_or_child_or_worker_or_product_executed=False,GO_authorized=False,
        actual_owned_Native_or_product_acceptance_qualified=False,accepted_count_delta=0)
