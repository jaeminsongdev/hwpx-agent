"""One current lifecycle and one fixed source document, never an authority issuer."""
import json
import re
from pathlib import Path
import prepared_bookmark_native631 as prior
import block_bookmark_source647_host as host_code
import block_selection_probe664_worker as worker_code
import block_bookmark_source650_sections as sections
from block_bookmark_source_plan643 import cases as planned_cases

r=prior.r
base=prior.base
SELF='tools/p09/block_selection_probe664.py'
ENTRY='tools/p09/run_block_selection_probe664.py'
DIRECTORY='implementation/p09/evidence/private/p09-361-block-selection-probe664-document001'
NAMES={'created.hwpx','reopened.hwpx','created-page-001.bmp','reopened-page-001.bmp'}
SOURCES=set(prior.base.candidate.SOURCES)|worker_code.SOURCES|{SELF,ENTRY,
    'tools/p09/block_bookmark_source650_sections.py','tools/p09/block_bookmark_source647_host.py',
    'tools/p09/block_selection_probe664_worker.py','tools/p09/prepared_bookmark631_evidence.py',
    'tools/p09/block_bookmark_source_plan643.py'}

def require(ok,code):
    if not ok:raise ValueError('XREF_PROBE664_'+code)

def absent():prior.prepared.require_absent(r.c.ROOT,DIRECTORY)

LABELS=('mode_at_entry','caret_before','full_seed_text_digest','selected_text_digest',
    'PowerShell_six_OUT','explicit_dotnet_six_OUT','ParameterSet_selection','caret_and_mode_after')

def diagnostic_producer(trace,profiles):
    require(len(profiles)==len(trace['sessions'])==len(trace['dual_identity_evidence'])==1,'ONE_CLOSED_DIAGNOSTIC_OWNER_NOT_REOPEN')
    profile=profiles[0]['startup_profile'];session=trace['sessions'][0];admission=trace['dual_identity_evidence'][0]
    observed=admission['observation']
    require(session['label']=='save'and session['quit_invoked']is True and session['close_without_dirty_prompt_returned']is True
        and type(session['remaining_owned_process_count'])is int and session['remaining_owned_process_count']==0
        and session['cleanup_error']is None and admission['channel_message_returned']is True
        and observed['compatibility_identity']==session['process']and observed['kernel_identity']['process_id']==profile['process_id']
        and observed['kernel_creation_filetime_100ns']==str(profile['process_birth_100ns'])
        and profile['cleanup_confirmed']is True and profile['owner_bound']is True
        and profile['assigned_before_initial_thread']is True,'EXACT_DIAGNOSTIC_KERNEL_PRODUCER_CLEANUP')

def capture_metadata(reader,host):
    require(host.schedule.stopped and host.schedule.finish_attempted and not host.schedule.done
        and host.scope.closed and host.scope.current is None and not host.scope.pending_admission
        and host.source_case is None and host.scope.finished==[dict(case_index=1,case_status='failed')],
        'DIAGNOSTIC_STOP_AND_CLEANUP_ONLY')
    trace=reader.json(DIRECTORY+'/case-trace.json')
    require(trace['schema_version']=='hwpx-agent.private.block-selection-probe664-trace/v1'
        and type(trace['case_index'])is int and trace['case_index']==1
        and trace['phase']=='create_bookmarks'and trace['error_code']==worker_code.EXPECTED_STOP
        and trace['cleanup_error']is None and trace['input_leases_closed']is True and trace['probe_complete']is True
        and trace['artifacts']=={}and trace['block_ranges']==[]and trace['block_content_support_qualified']is False
        and trace['P09_complete']is False,'OBSERVATIONS_NOT_SOURCE_CAPTURE')
    diagnostic_producer(trace,host.scope.sessions)
    rows=trace['selection_probe']
    require(type(rows)is list and len(rows)==8 and [v.get('label')for v in rows]==list(LABELS),'FIXED_EIGHT_OBSERVATIONS')
    for row in rows:
        require(set(row)=={'label','read_returned','value','error_kind','hresult'}and type(row['read_returned'])is bool,'OBSERVATION_SHAPE')
        if row['read_returned']:
            require(type(row['value'])is dict and row['error_kind']is None and row['hresult']is None,'RETURNED_OBSERVATION')
        else:
            require(row['value']is None and row['error_kind']in ('COMException','RuntimeException','InvalidOperationException',
                'ArgumentException','MissingMethodException','OtherException')
                and type(row['hresult'])is str and re.fullmatch(r'0x[0-9A-F]{8}',row['hresult']),'BOUNDED_ERROR_WITHOUT_MESSAGE')
    pin=reader.pin(DIRECTORY+'/case-trace.json');require(0<pin['bytes']<=262144,'PRIVATE_TRACE_BOUND')
    reader.finish()
    return dict(trace=pin,diagnostic_producer_bound=True,observations_recorded=8,source_capture_executed=False,
        selection_API_qualified=False,block_content_support_qualified=False,reference_semantics_qualified=False,P09_complete=False)

class OneCase(base.CaseInputs):
    def __init__(self,guard,manifest,shell_expected,paths):
        super().__init__(guard,manifest,shell_expected,fixed_capture004=True)
        self.paths=paths
    def begin(self,index):
        require(type(index)is int and index==1 and not self.rows,'ONE_SOURCE_NO_CASE_REPLAY')
        super().begin(index)

def execute(guard,manifest,paths,shell_expected,env,notify,record):
    absent();before=base.installed.current_identity(guard.windows)
    q=base.Boundary(guard,manifest,paths,'probe664_current_session',shell_expected,current004=True)
    worker=base.candidate.SessionWorker(guard)
    qualifier=base.session.SessionQualifier(guard,worker,q.native_pin,q.shell_pin)
    attempt={};record['qualification_worker']=attempt
    result=prior.io.run(guard,worker,q.source,worker.start_session_worker,base.SessionHandler(qualifier),
        'hwpx-agent.private.crossref-session-worker-result/v1',env,lambda v:notify('qualification',v),attempt)
    require(attempt['exit_code']==0 and attempt['cleanup']is True,'CURRENT_SESSION_RETURN_AND_CLEANUP_NO_BATCH_ON_FAILURE')
    q.finish();record['qualification_boundary']=q.summary()
    handoff=base.batch.issue_handoff(guard,qualifier,result,q.closed,before,base.installed.current_identity(guard.windows),q.fingerprint)
    guard.advance('capture',lambda:sections.closed_boundary(record['qualification_boundary']))
    absent();current=base.Boundary(guard,manifest,paths,'probe664_observations',shell_expected,current004=True)
    cases=OneCase(guard,manifest,shell_expected,paths);full=worker_code.Worker(guard)
    host=host_code.Host(guard,full,handoff,base.installed.current_identity(guard.windows),q.fingerprint,
        cases.native_pin,current.shell_pin,cases.begin,cases.end,notify=lambda v:notify('capture',v))
    attempt={};record['capture_worker']=attempt
    def notice(value):
        # io603 records the original result before calling legacy result_notice.
        # Replace that notice for THIS new profile, not by weakening old io.
        if value.get('state')=='NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP'and isinstance(attempt.get('result'),dict):
            value=worker_code.source_result_notice(attempt['result'])
        notify('capture',value)
    try:
        result=prior.io.run(guard,full,current.source,full.start_fixed_worker,base.BatchHandler(host),worker_code.RESULT,env,notice,attempt)
        require(attempt['exit_code']==2 and attempt['requests']==13 and attempt['cleanup']is True
            and result['state']=='block_source_callbacks_failed_or_partial'
            and result['error_code']==worker_code.EXPECTED_STOP and result.get('diagnostic_only')is True
            and result.get('probe_complete')is True and result.get('source_capture_executed')is False
            and type(result['completed_callback_cases'])is int and result['completed_callback_cases']==0
            and result['planned_cases']==1 and result['planned_block_ranges']==0 and result['retained_live_or_uncertain_owners']==0
            and result['block_content_support_qualified']is False and len(cases.rows)==1 and cases.current is None,
            'ONE_COMPLETE_DIAGNOSTIC_STOP_NOT_CAPTURE_SUCCESS')
        require(full.closed and host.scope.closed and host.worker_lease.closed and handoff.consumed,'ALL_OWNER_WORKER_HANDOFF_CLOSED')
        current.finish();require(base.installed.current_identity(guard.windows)==before,'SAME_KERNEL_CREATOR')
        guard.advance('batch_close',lambda:sections.closed_boundary(current.summary())and all(sections.closed_boundary(v)for v in cases.rows))
        artifacts=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        record['artifacts']=capture_metadata(artifacts,host)
        record['artifact_boundary']=dict(fresh_inputs=len(artifacts.snapshots),final_fresh_hashes=artifacts.final_fresh_hashes)
        record['batch_closed_for_final_audit']=True
    finally:
        record.update(capture_boundary=current.summary(),case_source_boundaries=cases.rows,
            partial_case_source_boundary=None if cases.current is None else cases.current.summary(),same_invocation_handoff_consumed=handoff.consumed)
    return record['artifacts']



