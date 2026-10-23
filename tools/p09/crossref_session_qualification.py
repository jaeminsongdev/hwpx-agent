"""Private exact session qualification protocol, no CLI or acceptance permit.

Ready worker -> original jobless preassigned startup -> exact owner/window bind
-> verified worker Close/Quit -> original kernel/empty-tree close. Input data
cannot replace the original guard, worker Job, executable pin or native backend.
"""
import ctypes,json,re,time
from ctypes import wintypes as w
from pathlib import Path
import crossref_native_startup as startup
import crossref_preassigned_host_protocol as descriptor
import crossref_owned_host_process as owned

REQUEST='hwpx-agent.private.crossref-session-qualification-request/v1'
RESPONSE='hwpx-agent.private.crossref-session-qualification-response/v1'
WORKER_KEYS={'process_id','session_id','created_at_utc','executable_sha256'}
CLEANUP_KEYS={'close_without_dirty_prompt_returned','quit_invoked','reference_release_returned','remaining_owned_process_count'}


def require(ok,code):
    if not ok:raise ValueError('XREF_SESSION_QUALIFICATION_'+code)


def decode(raw):
    require(type(raw)is str and 0<len(raw.encode('utf-8'))<=4096 and '\n'not in raw and '\r'not in raw,'WIRE_BOUNDARY')
    try:value=json.loads(raw,object_pairs_hook=descriptor.original.unique_pairs)
    except(json.JSONDecodeError,RecursionError):raise ValueError('XREF_SESSION_QUALIFICATION_INVALID_JSON')from None
    require(type(value)is dict and value.get('schema_version')==REQUEST,'REQUEST_SCHEMA')
    operation=value.get('operation');require(type(operation)is str and operation in('ready','admit_owner','closed','failed'),'FIXED_OPERATION')
    extras={'ready':{'worker_identity'},'admit_owner':{'identity','window_handle'},'closed':{'cleanup'},'failed':{'error_code','cleanup'}}[operation]
    require(value.keys()=={'schema_version','sequence','operation'}|extras and type(value['sequence'])is int and 1<=value['sequence']<=4,'EXACT_KEYS_AND_SEQUENCE')
    if operation=='ready':
        item=value['worker_identity'];require(type(item)is dict and item.keys()==WORKER_KEYS,'WORKER_IDENTITY_SCHEMA')
        require(type(item['process_id'])is int and 0<item['process_id']<=0x7fffffff and type(item['session_id'])is int and 0<=item['session_id']<=0x7fffffff
            and type(item['executable_sha256'])is str and re.fullmatch('[0-9a-f]{64}',item['executable_sha256'])is not None,'WORKER_IDENTITY_VALUES')
        startup.limits.creation_ticks(item['created_at_utc'])
    elif operation=='admit_owner':startup.limits.validate_identity(value['identity'],value['window_handle'])
    else:
        item=value['cleanup'];require(type(item)is dict and item.keys()==CLEANUP_KEYS,'CLEANUP_SCHEMA')
        require(all(type(item[k])is bool for k in CLEANUP_KEYS-{'remaining_owned_process_count'})
            and type(item['remaining_owned_process_count'])is int and -1<=item['remaining_owned_process_count']<=16,'CLEANUP_TYPES')
        if operation=='closed':require(all(item[k]is True for k in CLEANUP_KEYS-{'remaining_owned_process_count'})and item['remaining_owned_process_count']==0,'CLOSED_REQUIRES_COMPLETE_CLEANUP')
        else:require(type(value['error_code'])is str and re.fullmatch(r'P09_XREF_BIND_[A-Z0-9_]{1,120}',value['error_code'])is not None,'CLOSED_FAILURE_CODE')
    return value


class WorkerKernelLease:
    """Same live held worker handle in the original one-percent Job, not a PID lookup permit."""
    def __init__(self,worker,identity,fresh_shell_pin,expected_role='private_session_qualification_candidate'):
        require(type(expected_role)is str and expected_role in('private_session_qualification_candidate','private_fixed_eight_worker'),'CLOSED_EXPECTED_WORKER_ROLE')
        require(isinstance(worker,owned.OwnedHostProcess)and not worker.closed and worker.process is not None
            and worker.profile.get('role')==expected_role and worker.profile.get('qualification_target_pinned')is True
            and worker.profile['host_worker_one_percent_installed']and worker.profile['bootstrap_assigned']
            and worker.profile['bootstrap_limits_readback']and worker.profile['readonly_signal_written'],'CURRENT_SIGNALED_ONE_PERCENT_WORKER')
        require(callable(fresh_shell_pin),'FRESH_SHELL_CALLBACK');self.worker,self.identity,self.pin=worker,dict(identity),fresh_shell_pin
        self.handle=None;self.closed=False;k=worker.windows.k
        k.GetCurrentProcessId.argtypes,k.GetCurrentProcessId.restype=[],w.DWORD
        k.GetProcessId.argtypes,k.GetProcessId.restype=[w.HANDLE],w.DWORD
        k.WaitForSingleObject.argtypes,k.WaitForSingleObject.restype=[w.HANDLE,w.DWORD],w.DWORD
        k.GetProcessTimes.argtypes,k.GetProcessTimes.restype=[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4,w.BOOL
        k.GetExitCodeProcess.argtypes,k.GetExitCodeProcess.restype=[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL
        k.ProcessIdToSessionId.argtypes,k.ProcessIdToSessionId.restype=[w.DWORD,ctypes.POINTER(w.DWORD)],w.BOOL
        self.handle=k.OpenProcess(0x00101000,False,identity['process_id'])
        require(bool(self.handle),'OPEN_WORKER_QUERY_SYNCHRONIZE_ONLY')
        try:self.observe()
        except BaseException as error:
            if k.CloseHandle(self.handle):self.handle=None;self.closed=True
            else:error.worker_kernel_lease=self
            raise

    def observe(self,refresh_image=True):
        require(type(refresh_image)is bool,'EXACT_REFRESH_IMAGE_FLAG')
        require(not self.closed and self.handle is not None,'WORKER_LEASE_OPEN')
        worker=self.worker;k=worker.windows.k;worker.observe();worker.readback()
        identity=self.identity;member=w.BOOL();session,own_session,code=w.DWORD(),w.DWORD(),w.DWORD();times=[w.FILETIME()for _ in range(4)]
        image,size=ctypes.create_unicode_buffer(32768),w.DWORD(32768)
        require(k.GetProcessId(self.handle)==identity['process_id']and k.WaitForSingleObject(self.handle,0)==258
            and k.GetProcessTimes(self.handle,*(ctypes.byref(v)for v in times))and k.GetExitCodeProcess(self.handle,ctypes.byref(code))and code.value==259
            and k.ProcessIdToSessionId(identity['process_id'],ctypes.byref(session))and k.ProcessIdToSessionId(k.GetCurrentProcessId(),ctypes.byref(own_session))
            and k.IsProcessInJob(self.handle,worker.job,ctypes.byref(member))and member.value
            and k.QueryFullProcessImageNameW(self.handle,0,image,ctypes.byref(size)),'SAME_LIVE_EXACT_JOB_WORKER_HANDLE')
        birth=times[0].dwLowDateTime | times[0].dwHighDateTime<<32
        require(birth==startup.limits.creation_ticks(identity['created_at_utc'])and session.value==identity['session_id']==own_session.value
            and image.value.casefold()==owned.SHELL.casefold(),'FIXED_CURRENT_X86_WORKER_BIRTH_SESSION_IMAGE')
        allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
        require(k.GetProcessAffinityMask(self.handle,ctypes.byref(allowed),ctypes.byref(system))and allowed.value==worker.plan['affinity']
            and k.GetPriorityClass(self.handle)==worker.plan['priority'],'CURRENT_EFFECTIVE_WORKER_LIMITS')
        if refresh_image:
            pin=self.pin();require(type(pin)is dict and pin.get('path')==Path(owned.SHELL).name
                and pin.get('sha256')==identity['executable_sha256']and type(pin.get('bytes'))is int and pin['bytes']>0,'FRESH_EXACT_WORKER_IMAGE')
        require(k.WaitForSingleObject(self.handle,0)==258,'WORKER_STILL_SAME_LIVE_HANDLE')
        return dict(exact_live_worker_observed=True,original_one_percent_job_member=True,native_execution_authorized=False)

    def close(self):
        if self.closed:return
        require(self.worker.process.poll()is not None,'LIVE_WORKER_LEASE_RETAINED')
        require(self.worker.windows.k.CloseHandle(self.handle),'WORKER_QUERY_HANDLE_CLOSE');self.handle=None;self.closed=True


class SessionQualifier:
    """One native lifetime, one resume/bind/finish. Successful lifecycle is only a candidate.

    Full source/image/runtime final closure and independent acceptance are required
    before any fixed-eight execution. No serialized field grants that authority.
    """
    def __init__(self,guard,worker,fresh_native_pin,fresh_shell_pin):
        require(callable(getattr(guard,'check',None))and not hasattr(guard,'preparation_CPU')
            and type(guard.windows)is startup.limits.c.Windows and callable(fresh_native_pin)and callable(fresh_shell_pin),'ORIGINAL_NATIVE_GUARD_AND_PINS')
        require(isinstance(worker,owned.OwnedHostProcess)and worker.windows is guard.windows,'SAME_GUARD_OWNED_WORKER')
        self.guard,self.worker,self.native_pin,self.shell_pin=guard,worker,fresh_native_pin,fresh_shell_pin
        self.sequence=0;self.phase='ready';self.current=None;self.worker_lease=None;self.stopped=False;self.primary_error=None
        self.finished=False;self.lifecycle_candidate=False;self.close_observations=0

    def _retire(self):
        if self.current is None or self.current.closed:return True
        current=self.current;k=self.guard.windows.k
        # Unguarded cleanup: preserve the original refusal for a live native.
        # Once its held handle is signaled, wait for the SAME Job, never another
        # process or a forced close. No live observe() on an exited process.
        if current.process is not None and k.WaitForSingleObject(current.process,0)!=0:return False
        while True:
            info=self.guard.windows.accounting(current.owner_job.job);self.close_observations+=1
            if info['active_processes']==0:break
            time.sleep(.05)
        current.close();return current.closed and current.profile['cleanup_confirmed']is True

    def respond(self,raw):
        request=None;ack=False;error=None;owner=None
        try:
            request=decode(raw);require(not self.finished and request['sequence']==self.sequence+1,'EXACT_SEQUENCE_ONE_LIFETIME')
            self.sequence=request['sequence'];op=request['operation']
            if op=='failed':
                self.stopped=True;self.primary_error=self.primary_error or request['error_code']
                self._retire();self.finished=True;self.phase='finished_failed';ack=True
            else:
                require(not self.stopped and op==self.phase,'STOPPED_OR_WRONG_PHASE')
                if op=='ready':
                    try:self.worker_lease=WorkerKernelLease(self.worker,request['worker_identity'],self.shell_pin)
                    except BaseException as failure:
                        self.worker_lease=getattr(failure,'worker_kernel_lease',None);raise
                    startup.parent_without_prompt_kill(self.guard.windows)
                    self.current=startup.PreassignedNativeStartup(self.guard,self.native_pin)
                    self.current.create_suspended();self.current.resume()
                    owner=descriptor.validate_descriptor(dict(profile=descriptor.sessions.PROFILE,case_index=1,session_label='save',
                        process_id=self.current.pid,session_id=self.current.session,created_at_utc=startup.utc_identity(self.current.birth),
                        executable_sha256=startup.limits.EXECUTABLE_SHA,source='current_exact_preassigned_process_handle',COM_owner_bound=False,
                        native_execution_authorized=False,native_startup_qualified=False,P09_complete=False),1,'save')
                    self.phase='admit_owner'
                elif op=='admit_owner':
                    self.worker_lease.observe();self.current.bind_owner(request['identity'],request['window_handle']);self.phase='closed'
                else:
                    self.worker_lease.observe();require(self._retire(),'LIVE_NATIVE_RETAINED_AFTER_WORKER_CLOSED')
                    require(self.current.profile['assigned_before_initial_thread']and self.current.profile['pre_run_verified']
                        and self.current.profile['resumed']and self.current.profile['owner_bound'],'ORIGINAL_PREASSIGN_RESUME_BIND_AND_CLOSE')
                    self.lifecycle_candidate=True;self.finished=True;self.phase='finished_candidate'
                ack=True
        except(ValueError,OSError,KeyError,TypeError,AttributeError)as failure:
            value=failure.args[0]if failure.args else None
            error=value if type(value)is str and re.fullmatch(r'(XREF_[A-Z0-9_]+|STOP_[A-Z0-9_]+|[A-Z_]+_RESOURCE_STOP)',value)else'XREF_SESSION_QUALIFICATION_FAILURE_NO_RAW_VALUES'
            self.stopped=True;self.primary_error=self.primary_error or error;owner=None
        return json.dumps(dict(schema_version=RESPONSE,sequence=0 if request is None else request['sequence'],acknowledged=ack,error_code=error,
            owner_descriptor=owner,native_execution_authorized=False,native_startup_qualified=False,p09_complete=False),separators=(',',':'))

    def close(self):
        require(self._retire(),'LIVE_NATIVE_RETAIN_HANDLES_AND_JOB')
        if self.worker_lease is not None:self.worker_lease.close()

    def summary(self):
        return dict(phase=self.phase,sequence=self.sequence,stopped=self.stopped,primary_error=self.primary_error,
            lifecycle_candidate_observed=self.lifecycle_candidate,finished=self.finished,close_observations=self.close_observations,
            native_backend_profile=None if self.current is None else dict(self.current.profile),
            worker_lease_closed=self.worker_lease is None or self.worker_lease.closed,
            native_execution_authorized=False,native_startup_qualified=False,fixed_eight_executed=False,accepted_count_delta=0,P09_complete=False)
