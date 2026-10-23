"""Fixed006 composition using original source/owner/Job/channel/cleanup implementations.

No generation selector, saved-session admission, fallback or retry. The legacy
Boundary current004 flag selects only the qualified555 two-image Python host
profile, not a capture namespace or a Native approval; all output paths here are006.
"""
import crossref_external_batch_runtime as original
import crossref_capture006_worker as capture

r,require=original.r,original.require
installed=original.installed
INPUT_PINS,SOURCE=original.INPUT_PINS,original.SOURCE
SELF='tools/p09/crossref_external006_runtime.py'
ENTRY='tools/p09/run_external_crossref_fixed_batch006.py'
CASE_PATHS=(original.CASE_PATHS-{'tools/p09/run_external_crossref_fixed_batch.py'})|set(capture.SOURCES)|{
    SELF,ENTRY,'tools/p09/crossref_capture006_worker.py','tools/p09/crossref_capture006_namespace.py',
    'tools/p09/crossref_capture003_worker.py','tools/p09/crossref_capture003_namespace.py',
    'tools/p09/crossref_capture004_worker.py','tools/p09/crossref_capture004_namespace.py',
    'tools/p09/crossref_runtime004_admission.py','tools/p09/crossref_python_current555.py',
    'tools/p09/crossref_generation006_publication.py','tools/p09/crossref_inline_receipt567.py'}

def fixed_input_pins():return {**INPUT_PINS,capture.namespace.PROBE:capture.PROBE_PIN}
def absent_attempts():capture.namespace.require_absent(r.c.ROOT)

class Boundary(original.Boundary):
    def __init__(self,guard,manifest,paths,label,shell_expected):
        super().__init__(guard,manifest,paths,label,shell_expected,current004=True)
        pin=self.source.snapshots.get(capture.namespace.PROBE)
        require(type(pin)is dict and(pin['bytes'],pin['sha256'])==capture.PROBE_PIN,'FIXED006_CURRENT_QUALIFIED_PROBE')

class CaseInputs(original.CaseInputs):
    def __init__(self,guard,manifest,shell_expected):
        super().__init__(guard,manifest,shell_expected,fixed_capture004=True)
        self.paths=CASE_PATHS
    def begin(self,index):
        capture.namespace.directory(index)
        require(self.current is None and index==len(self.rows)+1,'FIXED_CASE_SOURCE_ORDER')
        self.current=Boundary(self.guard,self.manifest,self.paths,'case'+str(index),self.shell_expected)

def capture_artifacts(guard,host):
    require(host.protocol.protocol.case_index==9 and not host.protocol.protocol.stopped and len(host.scope.sessions)==16,'ALL_EIGHT_NATIVE_CALLBACKS_AND16_CLOSED_SESSIONS')
    q=r.a.AcceptanceReader(r.c.ROOT,guard.check);rows=[]
    for index in range(1,9):
        base=capture.namespace.directory(index)
        pins={name:q.pin(base+'/'+name)for name in('opened.hwpx','saved.hwpx','reopened.hwpx','target-trace.json','owner-identities.json')}
        trace=q.json(base+'/target-trace.json');side=q.json(base+'/owner-identities.json')
        require(trace['schema_version']=='hwpx-agent.private.crossref-native-case-trace/v1'and trace['source_identity_preserved']is True
            and trace['source_sha256']==INPUT_PINS[SOURCE][1]and len(trace['sessions'])==2 and len(trace['producer_events'])==3,'EXACT_ORIGINAL_SOURCE_TRACE_SESSIONS_PRODUCERS')
        require(side['original_trace']==pins['target-trace.json']and len(side['admissions'])==2,'CANONICAL_SIDECAR_EXACT_RAW_TRACE')
        for offset,label in enumerate(('save','reopen')):
            original=trace['sessions'][offset];admission=side['admissions'][offset]['evidence'];observed=admission['observation']
            native=host.scope.sessions[(index-1)*2+offset]['startup_profile']
            require(original['label']==label and original['quit_invoked']is True and original['close_without_dirty_prompt_returned']is True
                and type(original['remaining_owned_process_count'])is int and original['remaining_owned_process_count']==0 and original['cleanup_error']is None,
                'ORIGINAL_VERIFIED_SESSION_CLOSE')
            require(admission['channel_message_returned']is True and observed['compatibility_identity']==original['process']
                and observed['kernel_identity']['process_id']==native['process_id']
                and observed['kernel_creation_filetime_100ns']==str(native['process_birth_100ns'])
                and observed['kernel_identity']['session_id']==native['session_id']and native['cleanup_confirmed']is True
                and native['assigned_before_initial_thread']is True and native['owner_bound']is True,'CANONICAL_IDENTITY_TO_ACTUAL_PREASSIGNED_KERNEL_LIFETIME')
        for offset,name in enumerate(('opened','saved','reopened')):
            event=trace['producer_events'][offset];pin=pins[name+'.hwpx']
            require(event['stage']==name and event['artifact_sha256']==pin['sha256']and event['artifact_bytes']==pin['bytes']
                and event['observed_owner_identity']==trace['sessions'][0 if offset<2 else 1]['process'],'ACTUAL_FILE_DIGEST_AND_ORIGINAL_PRODUCER_OWNER')
        rows.append(dict(case_index=index,artifacts=pins,execution_capture_bound=True,reference_semantics_qualified=False))
    q.finish();return dict(cases=rows,fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
        native_capture_bound=True,crossref_semantics_qualified=False,P09_complete=False)

def execute(guard,manifest,all_paths,shell_expected,env,notify,record):
    require(CASE_PATHS<=set(all_paths),'COMPLETE_CAPTURE006_INPUT_CLOSURE')
    absent_attempts();before=installed.current_identity(guard.windows)
    qualification=Boundary(guard,manifest,all_paths,'current_session_qualification',shell_expected)
    record['qualification_boundary']=qualification.summary()
    worker=original.candidate.SessionWorker(guard)
    qualifier=original.session.SessionQualifier(guard,worker,qualification.native_pin,qualification.shell_pin)
    attempt={};record['qualification_worker']=attempt
    outcome=original.io.run(guard,worker,qualification.source,worker.start_session_worker,original.SessionHandler(qualifier),
        'hwpx-agent.private.crossref-session-worker-result/v1',env,lambda value:notify('qualification',value),attempt)
    require(attempt['exit_code']==0,'CURRENT_SESSION_WORKER_FAILED_NO_BATCH')
    qualification.finish();record['qualification_boundary']=qualification.summary()
    after=installed.current_identity(guard.windows)
    handoff=original.batch.issue_handoff(guard,qualifier,outcome,qualification.closed,before,after,qualification.fingerprint)
    absent_attempts();current=Boundary(guard,manifest,all_paths,'current_fixed_eight',shell_expected)
    cases=CaseInputs(guard,manifest,shell_expected);full=capture.Fixed006Worker(guard)
    host=original.batch.FixedEightHost(guard,full,handoff,installed.current_identity(guard.windows),qualification.fingerprint,
        cases.native_pin,current.shell_pin,cases.begin,cases.end)
    attempt={};record['fixed_worker']=attempt
    try:
        result=original.io.run(guard,full,current.source,full.start_fixed_worker,original.BatchHandler(host),
            'hwpx-agent.private.crossref-fixed-worker-result/v1',env,lambda value:notify('fixed_eight',value),attempt)
        require(attempt['exit_code']==0 and result['state']=='fixed_eight_callbacks_returned_semantics_unqualified'
            and result['completed_callback_cases']==8 and result['host_messages']==152 and result['retained_live_or_uncertain_owners']==0
            and result['probe_lease_closed']is True and len(cases.rows)==8 and cases.current is None,'CURRENT_WHOLE_EIGHT_RETURNED_AND_ALL_CASE_SOURCE_BOUNDARIES_CLOSED')
        current.finish();require(installed.current_identity(guard.windows)==before,'SAME_LIVE_CREATOR_AFTER_BATCH')
        original.session.startup.parent_without_prompt_kill(guard.windows)
        record['artifacts']=capture_artifacts(guard,host)
    finally:
        record.update(fixed_boundary=current.summary(),case_source_boundaries=cases.rows,
            partial_case_source_boundary=None if cases.current is None else cases.current.summary(),same_invocation_handoff_consumed=handoff.consumed)
    return record['artifacts']
