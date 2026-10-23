"""Private live one-use handoff and fixed-eight host composition, no saved permit.

The original v2 protocol/scope/guards remain authoritative. Source callbacks are
trusted program dependencies, never request-supplied commands or authority flags.
"""
import json,re,time
import crossref_session_qualification as sessions
import crossref_preassigned_host_protocol as original

READY='hwpx-agent.private.crossref-fixed-worker-ready/v1'
READY_REPLY='hwpx-agent.private.crossref-fixed-worker-release/v1'
_ISSUER=object()


def require(ok,code):
    if not ok:raise ValueError('XREF_HOST_QUALIFIED_BATCH_'+code)


class LiveHandoff:
    def __init__(self,issuer,guard,creator,source_fingerprint):
        require(issuer is _ISSUER,'INTERNAL_ISSUER_REQUIRED')
        self.guard=guard;self.creator=dict(creator);self.source_fingerprint=source_fingerprint;self.consumed=False
    def consume(self,guard,creator,source_fingerprint):
        require(not self.consumed and self.guard is guard and self.creator==creator
            and self.source_fingerprint==source_fingerprint,'SAME_LIVE_INVOCATION_ONE_USE_ONLY')
        self.consumed=True


def issue_handoff(guard,qualifier,worker_result,source_closed,before,after,fingerprint):
    require(type(qualifier)is sessions.SessionQualifier and qualifier.guard is guard and qualifier.finished and not qualifier.stopped
        and qualifier.lifecycle_candidate and qualifier.current is not None and qualifier.current.closed
        and qualifier.current.profile['cleanup_confirmed']is True and qualifier.worker.closed
        and qualifier.worker_lease is not None and qualifier.worker_lease.closed,'CURRENT_COMPLETED_LIFECYCLE_AND_WORKER')
    require(worker_result['state']=='session_worker_lifecycle_returned_source_and_native_qualification_pending'
        and worker_result['COM_owner_observed']is True and type(worker_result['cleanup'])is dict
        and worker_result['cleanup'].keys()==sessions.CLEANUP_KEYS
        and all(worker_result['cleanup'][k]is True for k in sessions.CLEANUP_KEYS-{'remaining_owned_process_count'})
        and type(worker_result['cleanup']['remaining_owned_process_count'])is int and worker_result['cleanup']['remaining_owned_process_count']==0
        and worker_result['document_opened_or_saved']is False and worker_result['fixed_eight_executed']is False,'EXACT_CURRENT_WORKER_CLEANUP_RESULT')
    require(type(source_closed)is bool and source_closed and type(before)is dict and before==after
        and before.get('kernel_handle_observation')is True and type(fingerprint)is str and re.fullmatch('[0-9a-f]{64}',fingerprint)is not None,'FRESH_SOURCE_CLOSURE_SAME_KERNEL_CREATOR')
    sessions.startup.parent_without_prompt_kill(guard.windows)
    return LiveHandoff(_ISSUER,guard,before,fingerprint)


def wait_exited_tree(current,windows):
    if current is None or current.closed:return
    if current.process is not None and windows.k.WaitForSingleObject(current.process,0)!=0:return
    # A verified-owner close has returned. Wait only for the already-signaled
    # exact process's same Job counter, then let ORIGINAL close verify it again.
    while windows.accounting(current.owner_job.job)['active_processes']:
        time.sleep(.05)


class FixedEightHost:
    def __init__(self,guard,worker,handoff,creator,fingerprint,fresh_native_pin,fresh_shell_pin,begin_case,end_case):
        require(type(handoff)is LiveHandoff and callable(begin_case)and callable(end_case),'LIVE_HANDOFF_AND_PROGRAM_SOURCE_CALLBACKS')
        handoff.consume(guard,creator,fingerprint)
        self.guard,self.worker,self.shell_pin=guard,worker,fresh_shell_pin
        self.begin_case,self.end_case=begin_case,end_case
        self.scope=original.sessions.PreassignedSessionScope(guard,fresh_native_pin)
        self.protocol=original.PreassignedHostProtocol(self.scope)
        self.worker_lease=None;self.ready=False;self.source_case=None;self.source_error=None;self.source_primary_error=None
    def release_worker(self,raw):
        require(not self.ready and self.worker_lease is None,'WORKER_RELEASE_ONCE')
        require(type(raw)is str and 0<len(raw.encode())<=4096 and '\n'not in raw and '\r'not in raw,'READY_WIRE_BOUNDARY')
        value=json.loads(raw,object_pairs_hook=original.original.unique_pairs)
        require(type(value)is dict and value.keys()=={'schema_version','worker_identity'}and value['schema_version']==READY,'FIXED_READY_SCHEMA')
        sessions.decode(json.dumps(dict(schema_version=sessions.REQUEST,sequence=1,operation='ready',worker_identity=value['worker_identity']),separators=(',',':')))
        try:self.worker_lease=sessions.WorkerKernelLease(self.worker,value['worker_identity'],self.shell_pin,expected_role='private_fixed_eight_worker')
        except BaseException as failure:self.worker_lease=getattr(failure,'worker_kernel_lease',None);raise
        sessions.startup.parent_without_prompt_kill(self.guard.windows);self.ready=True
        return json.dumps(dict(schema_version=READY_REPLY,acknowledged=True,error_code=None,native_execution_authorized=False,p09_complete=False),separators=(',',':'))
    def respond(self,raw):
        require(self.ready and self.worker_lease is not None,'CURRENT_EXACT_WORKER_BEFORE_CASE_IO')
        # This NEW batch composes explicit complete executable/source boundaries
        # at each case start/end. Kernel/Job identity is still checked on EVERY
        # frame; avoid rehashing the same loaded PowerShell image152 times.
        request=original.decode_request(raw);self.worker_lease.observe(refresh_image=False)
        exact=(request['sequence']==self.protocol.protocol.sequence+1 and request['case_index']==self.scope.case_index)
        try:
            if exact and request['operation']=='checkpoint'and not self.protocol.protocol.stopped:
                step=request['step'];index=request['case_index']
                if step=='prepare_slot'and self.scope.cursor==0:
                    require(self.source_case is None,'NO_OVERLAPPING_CASE_SOURCE_SCOPE');self.begin_case(index);self.source_case=index
                if step in('create_reopen_session','final_source_check'):
                    wait_exited_tree(self.scope.current,self.guard.windows)
            response=self.protocol.respond(raw);reply=json.loads(response)
            if exact and reply['acknowledged']and request['operation']=='checkpoint'and request['step']=='final_source_check':
                require(self.source_case==request['case_index'],'EXACT_CASE_SOURCE_END');self.end_case(self.source_case);self.source_case=None
            return response
        except(ValueError,OSError,KeyError,TypeError,AttributeError)as failure:
            self.protocol.protocol.stopped=True;self.scope.stopped=True
            value=failure.args[0]if failure.args else None
            self.source_primary_error=self.source_primary_error or(value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'XREF_HOST_QUALIFIED_BATCH_FAILURE_NO_RAW_VALUES')
            self.source_error=self.source_error or'XREF_HOST_QUALIFIED_BATCH_CURRENT_SOURCE_OR_CLEANUP_FAILED'
            return json.dumps(dict(schema_version=original.RESPONSE,sequence=request['sequence'],case_index=request['case_index'],acknowledged=False,
                error_code=self.source_error,owner_descriptor=None,native_execution_authorized=False,p09_complete=False),separators=(',',':'))
    def close(self):
        wait_exited_tree(self.scope.current,self.guard.windows);self.scope.close()
        if self.worker_lease is not None:self.worker_lease.close()
    def summary(self):
        return dict(ready=self.ready,source_case=self.source_case,source_error=self.source_error,source_primary_error=self.source_primary_error,protocol=self.protocol.summary(),
            worker_lease_closed=self.worker_lease is None or self.worker_lease.closed,native_execution_authorized=False,p09_complete=False)
