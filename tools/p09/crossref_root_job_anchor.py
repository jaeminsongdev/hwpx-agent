"""Closed readonly root-Job anchor qualification, not a native launcher.

Uses only an OS-permitted breakaway from the coordinator's external Job. Never
enables breakaway on an owned verification/native Job. A fixed isolated Python
child is born suspended, measured jobless, assigned a fresh original native-budget
Job and verified before its sole readonly resume. No Hwp/COM/CLI/native provider.
"""
import ctypes
from ctypes import wintypes as w
from pathlib import Path
import subprocess
import time

import crossref_native_host_limits as limits
import crossref_owned_host_process as host
import crossref_preassigned_readonly as fixed

BREAKAWAY=0x01000000
FLAGS=(fixed.CREATE_FLAGS & ~0x00080000) | BREAKAWAY
RUNTIME_BYTES=107312
RUNTIME_SHA='7d938c92a08d6495421f2f1076ccd7198aec0b288471abc0a55e90b1150d96a1'


def require(ok, code):
    if not ok:raise ValueError('XREF_ROOT_ANCHOR_'+code)


def permitted_external_parent(windows):
    value=host.read_parent_cpu(windows)
    require(value['job_present'] is False or (value['job_present'] is True
        and value['query_succeeded'] is True and value['flags'] & 0x800 != 0),
        'PARENT_BREAKAWAY_NOT_ALLOWED_NO_FALLBACK')
    # This is eligibility only, NOT proof that every ancestor permits breakaway.
    return value


class ReadonlyRootAnchor:
    """Retains exact handles/limits on uncertain creation or nonterminal cleanup."""
    def __init__(self, windows, checkpoint, fresh_runtime_pin):
        require(type(windows) is limits.c.Windows and callable(checkpoint)
            and callable(fresh_runtime_pin),'ORIGINAL_READONLY_DEPENDENCIES')
        self.windows,self.checkpoint,self.fresh_runtime_pin=windows,checkpoint,fresh_runtime_pin
        # This is a resource Job only. No native owner is admitted by this module.
        self.owner_job=limits.NativeOwnerJob(windows,checkpoint,
            lambda:(_ for _ in ()).throw(ValueError('XREF_ROOT_ANCHOR_NO_NATIVE_OWNER_PROVIDER')))
        self.process=None;self.thread=None;self.pid=None;self.birth=None
        self.created=False;self.assigned=False;self.resumed=False;self.closed=False
        self.start_attempted=False;self.resume_attempted=False
        self.resume_call_attempted=False
        self.start_failed=False
        self.parent=None;self.returncode=None
        self.profile=dict(role='closed_readonly_root_job_anchor',created=False,
            measured_jobless_before_assignment=False,root_established=False,
            pre_run_verified=False,resumed=False,cleanup_confirmed=False,
            owned_job_breakaway_enabled=False,parent_policy_changed=False,
            forced_termination_invoked=False,kill_on_close=False,actual_Hangul_or_COM=False,
            native_execution_authorized=False,native_startup_qualified=False,p09_complete=False)
        k=windows.k
        for name,args,result in (
            ('CreateProcessW',[w.LPCWSTR,w.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,w.BOOL,w.DWORD,
                ctypes.c_void_p,w.LPCWSTR,ctypes.POINTER(fixed.StartupInfoEx),ctypes.POINTER(fixed.ProcessInfo)],w.BOOL),
            ('GetProcessId',[w.HANDLE],w.DWORD),('ResumeThread',[w.HANDLE],w.DWORD),
            ('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD)):
            fn=getattr(k,name);fn.argtypes,fn.restype=args,result

    def _runtime_pin(self):
        pin=self.fresh_runtime_pin()
        require(type(pin) is dict and pin.get('path')==fixed.PYTHON.name
            and type(pin.get('bytes')) is int and pin['bytes']==RUNTIME_BYTES
            and pin.get('sha256')==RUNTIME_SHA,'FRESH_FIXED_RUNTIME_PIN')
        self.profile['runtime_pin']=dict(pin)

    def _handle(self, suspended):
        require(self.process is not None and self.pid is not None,'CREATED_HANDLE')
        k=self.windows.k;image,size=ctypes.create_unicode_buffer(32768),w.DWORD(32768)
        require(k.GetProcessId(self.process)==self.pid
            and k.QueryFullProcessImageNameW(self.process,0,image,ctypes.byref(size))
            and image.value.casefold()==str(fixed.PYTHON).casefold(),'EXACT_HANDLE_PID_IMAGE')
        times=[w.FILETIME() for _ in range(4)];code=w.DWORD()
        require(k.GetProcessTimes(self.process,*(ctypes.byref(t) for t in times))
            and k.GetExitCodeProcess(self.process,ctypes.byref(code)) and code.value==259,'LIVE_HANDLE_BIRTH')
        birth=times[0].dwLowDateTime | times[0].dwHighDateTime<<32
        require(birth>0 and (self.birth is None or birth==self.birth),'SAME_HANDLE_BIRTH')
        self.birth=birth
        allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
        require(k.GetProcessAffinityMask(self.process,ctypes.byref(allowed),ctypes.byref(system))
            and allowed.value==self.owner_job.plan['affinity']
            and k.GetPriorityClass(self.process)==self.owner_job.plan['priority'],'ONE_CPU_BELOW_NORMAL_BEFORE_BODY')
        if suspended:
            require(times[3].dwLowDateTime==times[3].dwHighDateTime==0,'NO_USER_CODE_BEFORE_LIMITS')
        return birth

    def create_suspended(self):
        require(not self.closed and not self.start_attempted,'NO_START_RETRY')
        self.start_attempted=True;k=self.windows.k
        try:
            self.checkpoint();self.parent=permitted_external_parent(self.windows)
            self._runtime_pin();self.owner_job.readback()
            require(self.windows.accounting(self.owner_job.job)['active_processes']==0,'FRESH_EMPTY_JOB')
            # The only command body is the frozen stdlib-only readonly self-check.
            args=fixed.fixed_command(self.owner_job.plan)
            startup=fixed.StartupInfoEx();startup.startup.cb=ctypes.sizeof(fixed.StartupInfo)
            command=ctypes.create_unicode_buffer(subprocess.list2cmdline(args));info=fixed.ProcessInfo()
            require(permitted_external_parent(self.windows)==self.parent,'PARENT_CHANGED_BEFORE_START')
            created=k.CreateProcessW(str(fixed.PYTHON),command,None,None,False,FLAGS,None,
                str(host.c.ROOT),ctypes.byref(startup),ctypes.byref(info))
            self.process,self.thread=info.process,info.thread;self.pid=int(info.pid) if info.pid else None
            require(created and self.process and self.thread and self.pid,'CREATE_FIXED_SUSPENDED_CHILD')
            self.created=True;self.profile.update(created=True,process_id=self.pid,creation_flags=FLAGS)
            self._handle(suspended=True)
            member=w.BOOL()
            require(k.IsProcessInJob(self.process,None,ctypes.byref(member)) and not member.value,
                'MEASURED_ALL_ANCESTOR_JOBS_REMOVED')
            self.profile['measured_jobless_before_assignment']=True
            before=self.owner_job._private_bytes(self.process)
            limits.combined_private_budget(self.owner_job.plan['memory_limit'],before,0,self.windows.total_ram)
            self.owner_job.profile['pre_assignment_private_bytes']=before
            self.profile['pre_assignment_private_bytes']=before
            # No thread has run, no native app exists and no caller Job is changed.
            require(k.AssignProcessToJobObject(self.owner_job.job,self.process),'ASSIGN_NEW_ROOT_JOB')
            self.assigned=True;self.verify_root()
        except BaseException as error:
            self.start_failed=True
            value=error.args[0] if error.args else None
            self.profile['start_error_code']=value if type(value) is str and value.startswith('XREF_ROOT_ANCHOR_') else 'XREF_ROOT_ANCHOR_START_FAILED_NO_RAW_VALUES'
            error.readonly_root_anchor=self
            raise

    def verify_root(self):
        require(not self.closed and self.assigned and not self.resumed
            and self.profile['measured_jobless_before_assignment'],'LIVE_SUSPENDED_ROOT_ANCHOR')
        self.checkpoint();self.owner_job.readback();self._handle(suspended=True)
        member=w.BOOL();k=self.windows.k
        require(k.IsProcessInJob(self.process,self.owner_job.job,ctypes.byref(member)) and member.value,
            'EXACT_ROOT_MEMBERSHIP')
        info=self.owner_job.observe()
        require(info['active_processes']==1 and len(info['owned_processes'])==1
            and info['owned_processes'][0]['pid']==self.pid,'SOLE_FRESH_ANCHOR_MEMBER')
        self.profile.update(root_established=True,pre_run_verified=True,process_birth_100ns=self.birth,
            pre_run_user_cpu_100ns=0,root_limits=self.owner_job.readback())
        return dict(self.profile['root_limits'])

    def resume_readonly(self):
        require(not self.closed and not self.resume_attempted,'NO_RESUME_RETRY')
        self.resume_attempted=True
        try:
            self._runtime_pin();self.verify_root()
            self.resume_call_attempted=True
            require(self.windows.k.ResumeThread(self.thread)==1,'EXACT_SINGLE_READONLY_RESUME')
            self.resumed=True;self.profile['resumed']=True
        except BaseException as error:
            self.start_failed=True
            error.readonly_root_anchor=self
            raise

    def wait_readonly(self):
        require(self.resumed and not self.closed,'READONLY_WAIT_PHASE')
        end=time.monotonic()+10
        while True:
            self.checkpoint();self.owner_job.observe()
            outcome=self.windows.k.WaitForSingleObject(self.process,50)
            if outcome==0:
                code=w.DWORD()
                require(self.windows.k.GetExitCodeProcess(self.process,ctypes.byref(code)),'READONLY_EXIT_CODE')
                self.returncode=int(code.value);self.profile['readonly_exit_code']=self.returncode
                return self.returncode
            require(outcome==258,'READONLY_WAIT_RESULT')
            require(time.monotonic()<end,'READONLY_OBSERVATION_TIMEOUT_RETAIN_HANDLES')

    def finish_failed_readonly(self):
        """Gracefully drain ONLY the known failed fixed self-check, not Native.

        A missing ancestor proof is preserved as failure. No qualification retry,
        assignment retry, arbitrary body, input or child process is allowed here.
        The fixed child merely queries limits and exits 0/65; it cannot open Hwp.
        """
        require(self.start_failed and self.created and not self.closed
            and not self.resume_call_attempted,'FAILED_FIXED_READONLY_CLEANUP_ONLY')
        self._handle(suspended=True)  # Exact image/birth, one CPU/BelowNormal, zero user code.
        private=self.owner_job._private_bytes(self.process)
        require(private < self.windows.memory_limit//8,'FAILED_READONLY_SMALL_SUSPENDED_IMAGE')
        self.resume_attempted=True
        self.resume_call_attempted=True
        require(self.windows.k.ResumeThread(self.thread)==1,'FAILED_READONLY_SINGLE_CLEANUP_RESUME')
        self.resumed=True;self.profile.update(resumed=True,failed_readonly_cleanup_only=True,
            root_established=False,native_startup_qualified=False)
        end=time.monotonic()+10
        while True:
            outcome=self.windows.k.WaitForSingleObject(self.process,50)
            if outcome==0:
                code=w.DWORD()
                require(self.windows.k.GetExitCodeProcess(self.process,ctypes.byref(code)),'FAILED_READONLY_EXIT_CODE')
                self.returncode=int(code.value);self.profile['readonly_cleanup_exit_code']=self.returncode
                return self.returncode
            require(outcome==258,'FAILED_READONLY_WAIT_RESULT')
            require(time.monotonic()<end,'FAILED_READONLY_OBSERVATION_TIMEOUT_RETAIN_HANDLES')

    def close(self):
        if self.closed:return
        k=self.windows.k
        # No pressure gate, automatic resume or kill to make cleanup appear complete.
        require(self.process is None or k.WaitForSingleObject(self.process,0)==0,'LIVE_READONLY_CHILD_RETAIN_HANDLES')
        require(self.windows.accounting(self.owner_job.job)['active_processes']==0,'LIVE_ROOT_JOB_RETAIN_LIMITS')
        for attribute in ('thread','process'):
            handle=getattr(self,attribute)
            if handle is not None:
                require(k.CloseHandle(handle),'CLOSE_OWNED_'+attribute.upper());setattr(self,attribute,None)
        self.owner_job.close();self.profile['root_job_profile']=dict(self.owner_job.profile)
        self.closed=True;self.profile['cleanup_confirmed']=True
