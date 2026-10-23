"""One current invocation's source boundaries and Native/fixed-eight composition.

No saved receipt is an execution permit. User entry must supply a current guard,
pin manifest, fixed executable readers, one-shot claim and same kernel creator.
"""
import hashlib,json,sys
from pathlib import Path
import named_style_verification_runtime as r
import crossref_external_host_inspection as installed
import crossref_session_qualification as session
import crossref_session_worker as candidate
import crossref_fixed_worker as fixed
import crossref_qualified_batch as batch
import crossref_native_worker_io as io
import crossref_capture003_worker as capture003
import crossref_capture004_worker as capture004

CORPUS='implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/'
SOURCE=CORPUS+'source-with-bookmark.hwpx'
PACKET=CORPUS+'prepared-sdk-batch.v1.json'
PROBE='target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
INPUT_PINS={SOURCE:(14425,'64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184'),
    PACKET:(42762,'1709c77ac89e8dcb5b319e29db224d1a92dcfbb53868b44c88ce542a0ad206d1'),
    PROBE:(5112832,'0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb')}
CASE_PY=('crossref_external_batch_runtime','run_external_crossref_fixed_batch','crossref_qualified_batch','crossref_native_worker_io',
    'crossref_fixed_worker','crossref_session_worker','crossref_session_qualification','crossref_native_startup','crossref_startup_input_idle','crossref_native_host_limits',
    'crossref_preassigned_session_scope','crossref_preassigned_host_protocol','crossref_native_host_channel','crossref_owned_host_process',
    'conservative_maintenance','accept_case112_current_epoch','distinct_final_sample_guard_v1','owned_cpu_baseline_v1','audit_evidence_io',
    'owned_source_read_pressure','weighted_audit_io','locked_runtime_inputs','prepared_run_closure_v1')
CASE_PATHS=set(fixed.SOURCES)|{SOURCE}|{'tools/p09/'+name+'.py'for name in CASE_PY}
CAPTURE003_CASE_PATHS=CASE_PATHS|set(capture003.SOURCES)|{'tools/p09/crossref_capture003_namespace.py','tools/p09/crossref_capture003_worker.py'}
CAPTURE004_CASE_PATHS=CASE_PATHS|set(capture004.SOURCES)|{'tools/p09/crossref_capture004_namespace.py','tools/p09/crossref_capture004_worker.py'}


def fixed_input_pins(capture003_scope=False,*,capture004_scope=False):
    require(type(capture003_scope)is bool,'EXACT_CAPTURE003_SCOPE_FLAG')
    require(type(capture004_scope)is bool and not(capture003_scope and capture004_scope),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')
    if capture004_scope:return {**INPUT_PINS,capture004.namespace.PROBE:capture004.PROBE_PIN}
    return {**INPUT_PINS,capture003.namespace.PROBE:capture003.PROBE_PIN}if capture003_scope else dict(INPUT_PINS)


def require(ok,code):
    if not ok:raise ValueError('XREF_EXTERNAL_BATCH_'+code)


def artifact_directory(index):
    require(type(index)is int and 1<=index<=8,'FIXED_CASE')
    return f'implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c{index:02}-attempt01'


def absent_attempts(*,fixed_capture003=False,fixed_capture004=False):
    require(type(fixed_capture003)is bool,'EXACT_CAPTURE003_SCOPE_FLAG')
    require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')
    if fixed_capture004:return capture004.namespace.require_absent(r.c.ROOT)
    if fixed_capture003:return capture003.namespace.require_absent(r.c.ROOT)
    for index in range(1,9):
        path=r.c.ROOT/artifact_directory(index)
        require(not path.exists()and not path.is_symlink(),'EXISTING_CAPTURE_ATTEMPT_NO_REPLAY')


class Boundary:
    def __init__(self,guard,manifest,paths,label,shell_expected):
        self.label=label;self.closed=False;self.guard=guard
        self.source=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        self.native=r.a.AcceptanceReader(Path(installed.native.EXECUTABLE).parent,guard.check)
        self.shell=r.a.AcceptanceReader(Path(candidate.original.SHELL).parent,guard.check)
        self.runtime=r.a.AcceptanceReader(installed.fixed.PYTHON.parent,guard.check)
        fixed_pins={**fixed_input_pins(True),**fixed_input_pins(capture004_scope=True)}
        for path in sorted(paths):
            pin=self.source.pin(path)
            if path in fixed_pins:
                size,sha=fixed_pins[path];require((pin['bytes'],pin['sha256'])==(size,sha),'FIXED_PRODUCT_INPUT')
            else:require(path in manifest and pin==manifest[path],'CURRENT_SOURCE_MANIFEST')
        require(self.shell.pin(Path(candidate.original.SHELL).name)==shell_expected,'CURRENT_FIXED_SHELL')
        installed.runtime_pin_matches(self.runtime.pin(installed.fixed.PYTHON.name))
        native=self.native.pin(Path(installed.native.EXECUTABLE).name)
        require((native['bytes'],native['sha256'])==(installed.native.EXECUTABLE_BYTES,installed.native.EXECUTABLE_SHA),'CURRENT_FIXED_HANCOM_IMAGE')
        all_pins=[dict(root=root,**pin)for root,reader in self.readers()for pin in reader.snapshots.values()]
        self.fingerprint=hashlib.sha256(json.dumps(sorted(all_pins,key=lambda p:(p['root'],p['path'])),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def readers(self):return [('source',self.source),('native',self.native),('shell',self.shell),('runtime',self.runtime)]
    def native_pin(self):return self.native.fresh_pin(Path(installed.native.EXECUTABLE).name)
    def shell_pin(self):return self.shell.fresh_pin(Path(candidate.original.SHELL).name)
    def finish(self):
        require(not self.closed,'SOURCE_BOUNDARY_FINISH_ONCE')
        for root,reader in self.readers():reader.finish()
        self.guard.check(force=True);self.closed=True
    def summary(self):
        return dict(label=self.label,closed=self.closed,fingerprint=self.fingerprint,
            readers={root:dict(fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
                pins=list(reader.snapshots.values()))for root,reader in self.readers()})


class CaseInputs:
    def __init__(self,guard,manifest,shell_expected,*,fixed_capture003=False,fixed_capture004=False):
        require(type(fixed_capture003)is bool,'EXACT_CAPTURE003_SCOPE_FLAG')
        require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')
        self.guard,self.manifest,self.shell_expected=guard,manifest,shell_expected;self.current=None;self.rows=[]
        self.paths=CAPTURE004_CASE_PATHS if fixed_capture004 else CAPTURE003_CASE_PATHS if fixed_capture003 else CASE_PATHS
    def begin(self,index):
        require(self.current is None and index==len(self.rows)+1,'FIXED_CASE_SOURCE_ORDER')
        self.current=Boundary(self.guard,self.manifest,self.paths,'case'+str(index),self.shell_expected)
    def end(self,index):
        require(self.current is not None and self.current.label=='case'+str(index),'CURRENT_CASE_SOURCE_END')
        self.current.finish();self.rows.append(self.current.summary());self.current=None
    def native_pin(self):
        require(self.current is not None,'CASE_SOURCE_BEFORE_NATIVE');return self.current.native_pin()
    def shell_pin(self):
        # Ready handshake precedes the first product case; use a separate fresh
        # shell reader supplied by the enclosing batch boundary for that frame.
        require(self.current is not None,'CASE_SOURCE_BEFORE_WORKER_OBSERVATION');return self.current.shell_pin()


class SessionHandler:
    def __init__(self,qualifier):self.qualifier=qualifier
    def handle(self,line):return self.qualifier.respond(line)
    def current_native(self):return self.qualifier.current
    def close(self):self.qualifier.close()
    def summary(self):return self.qualifier.summary()


class BatchHandler:
    def __init__(self,host):self.host=host
    def handle(self,line):
        if not self.host.ready:return self.host.release_worker(line)
        return self.host.respond(line)
    def current_native(self):return self.host.scope.current
    def close(self):self.host.close()
    def summary(self):return self.host.summary()


def capture_artifacts(guard,host,*,fixed_capture003=False,fixed_capture004=False):
    require(type(fixed_capture003)is bool,'EXACT_CAPTURE003_SCOPE_FLAG')
    require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')
    require(host.protocol.protocol.case_index==9 and not host.protocol.protocol.stopped and len(host.scope.sessions)==16,'ALL_EIGHT_NATIVE_CALLBACKS_AND16_CLOSED_SESSIONS')
    q=r.a.AcceptanceReader(r.c.ROOT,guard.check);rows=[]
    for index in range(1,9):
        base=capture004.namespace.directory(index)if fixed_capture004 else capture003.namespace.directory(index)if fixed_capture003 else artifact_directory(index)
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


def execute(guard,manifest,all_paths,shell_expected,env,notify,record,*,fixed_capture003=False,fixed_capture004=False):
    require(type(fixed_capture003)is bool,'EXACT_CAPTURE003_SCOPE_FLAG')
    require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')
    if fixed_capture004:require(CAPTURE004_CASE_PATHS<=set(all_paths),'COMPLETE_CAPTURE004_INPUT_CLOSURE')
    if fixed_capture003:require(CAPTURE003_CASE_PATHS<=set(all_paths),'COMPLETE_CAPTURE003_INPUT_CLOSURE')
    check_attempts=(lambda:absent_attempts(fixed_capture004=True))if fixed_capture004 else (lambda:absent_attempts(fixed_capture003=True))if fixed_capture003 else absent_attempts
    check_attempts();before=installed.current_identity(guard.windows)
    qualification=Boundary(guard,manifest,all_paths,'current_session_qualification',shell_expected)
    record['qualification_boundary']=qualification.summary()
    worker=candidate.SessionWorker(guard);qualifier=session.SessionQualifier(guard,worker,qualification.native_pin,qualification.shell_pin)
    attempt={};record['qualification_worker']=attempt
    outcome=io.run(guard,worker,qualification.source,worker.start_session_worker,SessionHandler(qualifier),
        'hwpx-agent.private.crossref-session-worker-result/v1',env,notify,attempt)
    require(attempt['exit_code']==0,'CURRENT_SESSION_WORKER_FAILED_NO_BATCH')
    qualification.finish();record['qualification_boundary']=qualification.summary()
    after=installed.current_identity(guard.windows)
    handoff=batch.issue_handoff(guard,qualifier,outcome,qualification.closed,before,after,qualification.fingerprint)
    # Handoff fingerprint is for the complete, closed current qualification.
    # Fresh product-case boundaries recheck the active Native execution inputs.
    check_attempts();current=Boundary(guard,manifest,all_paths,'current_fixed_eight',shell_expected)
    cases=CaseInputs(guard,manifest,shell_expected,fixed_capture003=fixed_capture003,**({'fixed_capture004':True}if fixed_capture004 else{}))
    full=capture004.Fixed004Worker(guard)if fixed_capture004 else capture003.Fixed003Worker(guard)if fixed_capture003 else fixed.FixedWorker(guard)
    host=batch.FixedEightHost(guard,full,handoff,installed.current_identity(guard.windows),qualification.fingerprint,
        cases.native_pin,current.shell_pin,cases.begin,cases.end)
    attempt={};record['fixed_worker']=attempt
    try:
        result=io.run(guard,full,current.source,full.start_fixed_worker,BatchHandler(host),
            'hwpx-agent.private.crossref-fixed-worker-result/v1',env,notify,attempt)
        require(attempt['exit_code']==0 and result['state']=='fixed_eight_callbacks_returned_semantics_unqualified'
            and result['completed_callback_cases']==8 and result['host_messages']==152 and result['retained_live_or_uncertain_owners']==0
            and result['probe_lease_closed']is True and len(cases.rows)==8 and cases.current is None,'CURRENT_WHOLE_EIGHT_RETURNED_AND_ALL_CASE_SOURCE_BOUNDARIES_CLOSED')
        current.finish();require(installed.current_identity(guard.windows)==before,'SAME_LIVE_CREATOR_AFTER_BATCH')
        session.startup.parent_without_prompt_kill(guard.windows)
        record['artifacts']=capture_artifacts(guard,host,fixed_capture004=True)if fixed_capture004 else capture_artifacts(guard,host,fixed_capture003=True)if fixed_capture003 else capture_artifacts(guard,host)
    finally:
        record.update(fixed_boundary=current.summary(),case_source_boundaries=cases.rows,
            partial_case_source_boundary=None if cases.current is None else cases.current.summary(),
            same_invocation_handoff_consumed=handoff.consumed)
    return record['artifacts']
