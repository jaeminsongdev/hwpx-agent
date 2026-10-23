"""Private preassigned Hancom startup backend; no CLI or authority provider.

Only the pinned Hwp.exe with its fixed -Automation argument can be created.
The native seven-percent Job is installed at creation, not after COM activation.
Original native guards/admission, running-object binding and product qualification
are still required by the future controller. This module never activates COM,
opens documents, writes evidence, retries a launch or kills a process.
"""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import re
import subprocess
import winreg

import crossref_native_host_limits as limits
import crossref_owned_host_process as host
import crossref_startup_input_idle as input_idle
from crossref_preassigned_readonly import StartupInfoEx, ProcessInfo, JOB_LIST, CREATE_FLAGS

CLSID='{2291CF00-64A1-4877-A9B4-68CFE89612D6}'
PROGID='HWPFrame.HwpObject.2'
UNSAFE_PARENT_FLAGS=0x2000 | 0x1800 | 0x0002 | 0x0004


def require(ok, code):
    if not ok:raise ValueError('XREF_NATIVE_STARTUP_'+code)


def registered_command(value):
    """Validate registration; never execute the registry text as a command."""
    require(type(value) is str and 0<len(value)<=1024,'REGISTRATION_BOUNDARY')
    image=re.escape(limits.EXECUTABLE)
    require(re.fullmatch(r'\s*(?:"'+image+r'"|'+image+r')\s+-Automation\s*',value,re.IGNORECASE)
        is not None,'FIXED_REGISTERED_SERVER')
    return [limits.EXECUTABLE,'-Automation']


def read_registered_command():
    access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,PROGID+r'\CLSID',0,access) as key:
        clsid,kind=winreg.QueryValueEx(key,'')
    require(kind==winreg.REG_SZ and type(clsid) is str and clsid.upper()==CLSID,'FIXED_PROGID_CLSID')
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,'CLSID\\'+CLSID+r'\LocalServer32',0,access) as key:
        text,kind=winreg.QueryValueEx(key,'')
    require(kind==winreg.REG_SZ,'SERVER_REGISTRY_VALUE_TYPE')
    return registered_command(text)


def parent_without_prompt_kill(windows):
    observed=host.read_parent_cpu(windows)
    # NULL Job queries expose only the immediate Job, not every ancestor.
    # Even an apparently safe immediate Job may hide a kill/time policy above it.
    # Without qualified whole-chain provenance, permit only a genuinely jobless caller.
    require(observed['job_present'] is False,'PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
    return observed


class ProcessEntry(ctypes.Structure):
    _fields_=[('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',ctypes.c_size_t),
        ('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),
        ('flags',w.DWORD),('name',w.WCHAR*260)]


def hwp_pids(windows, checkpoint):
    """One bounded PROCESS snapshot, not WMI/PDH/a sampler or command-line scan."""
    k=windows.k
    for name,args,result in (
        ('CreateToolhelp32Snapshot',[w.DWORD,w.DWORD],w.HANDLE),
        ('Process32FirstW',[w.HANDLE,ctypes.POINTER(ProcessEntry)],w.BOOL),
        ('Process32NextW',[w.HANDLE,ctypes.POINTER(ProcessEntry)],w.BOOL)):
        fn=getattr(k,name);fn.argtypes,fn.restype=args,result
    checkpoint();snapshot=k.CreateToolhelp32Snapshot(2,0)
    require(snapshot not in (None,0,ctypes.c_void_p(-1).value),'PROCESS_SNAPSHOT')
    result=set();entry=ProcessEntry();entry.size=ctypes.sizeof(entry);count=0
    try:
        ctypes.set_last_error(0);more=k.Process32FirstW(snapshot,ctypes.byref(entry))
        while more:
            count+=1;require(count<=4096,'PROCESS_SNAPSHOT_BOUND')
            if count%32==0:checkpoint()
            if entry.name.casefold()=='hwp.exe':result.add(int(entry.pid))
            ctypes.set_last_error(0);more=k.Process32NextW(snapshot,ctypes.byref(entry))
        require(ctypes.get_last_error()==18,'COMPLETE_PROCESS_SNAPSHOT')
    finally:require(k.CloseHandle(snapshot),'SNAPSHOT_CLOSE')
    return result


def utc_identity(ticks):
    require(type(ticks) is int and ticks>0,'EXACT_CREATION_TICKS')
    seconds,fraction=divmod(ticks,10000000)
    point=datetime(1601,1,1,tzinfo=timezone.utc)+timedelta(seconds=seconds)
    return point.strftime('%Y-%m-%dT%H:%M:%S')+'.'+f'{fraction:07d}'+'Z'


class PreassignedNativeStartup:
    """Owned exact process handle, retained across uncertain start/binding.

    The controller must supply the original native guard and a fresh executable
    byte-pin callback. Neither this object nor serialized identity is authority.
    No one-percent worker Job, apartment/ROT binding or product attempt is installed.
    """
    def __init__(self, guard, fresh_executable_pin):
        require(callable(getattr(guard,'check',None)) and callable(fresh_executable_pin)
            and not hasattr(guard,'preparation_CPU') and type(guard.windows) is limits.c.Windows,
            'ORIGINAL_NATIVE_GUARD_REQUIRED')
        self.guard,self.windows,self.fresh_executable_pin=guard,guard.windows,fresh_executable_pin
        self.owner_job=limits.NativeOwnerJob(self.windows,guard.check,fresh_executable_pin)
        self.process=None;self.thread=None;self.pid=None;self.birth=None;self.session=None
        self.closed=False;self.start_attempted=False;self.resume_attempted=False;self.bind_attempted=False
        self.parent=None
        self.profile=dict(state='unstarted',created=False,assigned_before_initial_thread=False,
            pre_run_verified=False,resumed=False,owner_bound=False,cleanup_confirmed=False,
            atomic_job_list=True,kill_on_close=False,forced_termination_invoked=False,
            native_execution_authorized=False,native_startup_qualified=False,p09_complete=False)
        k=self.windows.k
        for name,args,result in (
            ('InitializeProcThreadAttributeList',[ctypes.c_void_p,w.DWORD,w.DWORD,ctypes.POINTER(ctypes.c_size_t)],w.BOOL),
            ('UpdateProcThreadAttribute',[ctypes.c_void_p,w.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p],w.BOOL),
            ('DeleteProcThreadAttributeList',[ctypes.c_void_p],None),
            ('CreateProcessW',[w.LPCWSTR,w.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,w.BOOL,w.DWORD,ctypes.c_void_p,w.LPCWSTR,ctypes.POINTER(StartupInfoEx),ctypes.POINTER(ProcessInfo)],w.BOOL),
            ('ResumeThread',[w.HANDLE],w.DWORD),('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD),
            ('GetProcessId',[w.HANDLE],w.DWORD)):
            fn=getattr(k,name);fn.argtypes,fn.restype=args,result

    def _fresh_image(self):
        pin=self.fresh_executable_pin()
        require(type(pin) is dict and pin.get('bytes')==limits.EXECUTABLE_BYTES
            and type(pin['bytes']) is int and pin.get('sha256')==limits.EXECUTABLE_SHA,'FRESH_PINNED_IMAGE')

    def _parent_unchanged(self):
        current=parent_without_prompt_kill(self.windows)
        if self.parent is not None:require(current==self.parent,'PARENT_POLICY_CHANGED')
        return current

    def create_suspended(self):
        require(not self.closed and not self.start_attempted,'NO_START_RETRY')
        self.start_attempted=True;k=self.windows.k;attributes=None;initialized=False
        try:
            self.guard.check();self.parent=self._parent_unchanged()
            require(hwp_pids(self.windows,self.guard.check)==set(),'EXISTING_HWP_NO_START')
            args=read_registered_command()  # Closed argv, never the raw registry string.
            self._fresh_image();self.owner_job.readback()
            require(self.windows.accounting(self.owner_job.job)['active_processes']==0,'EMPTY_JOB_BEFORE_START')
            size=ctypes.c_size_t();ctypes.set_last_error(0)
            first=k.InitializeProcThreadAttributeList(None,1,0,ctypes.byref(size))
            require(not first and ctypes.get_last_error()==122 and 0<size.value<=65536,'ATTRIBUTE_SIZE')
            attributes=ctypes.create_string_buffer(size.value)
            require(k.InitializeProcThreadAttributeList(attributes,1,0,ctypes.byref(size)),'ATTRIBUTE_INITIALIZE')
            initialized=True;jobs=(w.HANDLE*1)(self.owner_job.job)
            require(k.UpdateProcThreadAttribute(attributes,0,JOB_LIST,jobs,ctypes.sizeof(jobs),None,None),'ATOMIC_JOB_ATTRIBUTE')
            startup=StartupInfoEx();startup.startup.cb=ctypes.sizeof(startup)
            startup.attributes=ctypes.cast(attributes,ctypes.c_void_p)
            command=ctypes.create_unicode_buffer(subprocess.list2cmdline(args));info=ProcessInfo()
            self.guard.check();self._parent_unchanged();self.owner_job.readback()
            require(hwp_pids(self.windows,self.guard.check)==set(),'HWP_APPEARED_BEFORE_START')
            self.profile['state']='create_attempted_effect_unknown'
            created=k.CreateProcessW(limits.EXECUTABLE,command,None,None,False,CREATE_FLAGS,None,
                str(Path(limits.EXECUTABLE).parent),ctypes.byref(startup),ctypes.byref(info))
            # Retain any supplied handles even if an API outcome is contradictory.
            self.process,self.thread=info.process,info.thread
            self.pid=int(info.pid) if info.pid else None
            require(created and self.process and self.thread and self.pid,'CREATE_PINNED_NATIVE_SUSPENDED')
            self.profile.update(created=True,state='suspended_unbound',process_id=self.pid)
            self.verify_suspended()
        except BaseException as error:
            self.profile['state']='start_failed_or_uncertain_no_retry'
            error.preassigned_native_startup=self
            raise
        finally:
            if initialized:k.DeleteProcThreadAttributeList(attributes)

    def _handle_identity(self):
        require(self.process is not None and self.pid is not None,'OWNED_PROCESS_HANDLE')
        k=self.windows.k;image,size=ctypes.create_unicode_buffer(32768),w.DWORD(32768)
        require(k.GetProcessId(self.process)==self.pid,'EXACT_HANDLE_PID')
        require(k.QueryFullProcessImageNameW(self.process,0,image,ctypes.byref(size))
            and image.value.casefold()==limits.EXECUTABLE.casefold(),'EXACT_HANDLE_IMAGE')
        times=[w.FILETIME() for _ in range(4)];session,code=w.DWORD(),w.DWORD()
        require(k.GetProcessTimes(self.process,*(ctypes.byref(v) for v in times))
            and k.ProcessIdToSessionId(self.pid,ctypes.byref(session))
            and k.GetExitCodeProcess(self.process,ctypes.byref(code)) and code.value==259,'LIVE_HANDLE_IDENTITY')
        own_session=w.DWORD()
        require(k.ProcessIdToSessionId(os.getpid(),ctypes.byref(own_session))
            and own_session.value==session.value,'CURRENT_SESSION_ONLY')
        birth=times[0].dwLowDateTime | times[0].dwHighDateTime<<32
        require(birth>0 and (self.birth is None or (birth==self.birth and int(session.value)==self.session)),
            'EXACT_SAME_BIRTH_SESSION')
        self.birth,self.session=birth,int(session.value)
        member=w.BOOL();allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
        require(k.IsProcessInJob(self.process,self.owner_job.job,ctypes.byref(member)) and member.value,
            'ATOMIC_MEMBERSHIP')
        require(k.GetProcessAffinityMask(self.process,ctypes.byref(allowed),ctypes.byref(system))
            and allowed.value==self.owner_job.plan['affinity']
            and k.GetPriorityClass(self.process)==self.owner_job.plan['priority'],'EFFECTIVE_PROCESS_LIMITS')
        require(hwp_pids(self.windows,self.guard.check)=={self.pid},'ONLY_THE_PREASSIGNED_HWP')
        return times

    def verify_suspended(self):
        require(not self.closed and not self.resume_attempted,'SUSPENDED_PHASE_ONLY')
        self.guard.check();self._parent_unchanged();self.owner_job.readback()
        times=self._handle_identity()
        require(times[3].dwLowDateTime==times[3].dwHighDateTime==0,'NO_INITIAL_USER_THREAD_EXECUTION')
        self.owner_job.observe()
        self.owner_job.profile.update(native_process_assigned=True,preassigned_at_creation=True,
            pre_assignment_private_bytes=0)
        self.profile.update(assigned_before_initial_thread=True,pre_run_verified=True,
            process_birth_100ns=self.birth,session_id=self.session,pre_run_user_cpu_100ns=0)

    def resume(self):
        require(not self.closed and self.profile['pre_run_verified'] and not self.resume_attempted,'NO_RESUME_RETRY')
        # Re-read actual installed bytes and identity immediately before the sole resume.
        try:
            self._fresh_image();self.verify_suspended();self.resume_attempted=True
            require(self.windows.k.ResumeThread(self.thread)==1,'EXACT_SINGLE_RESUME')
            self.profile.update(resumed=True,state='running_unbound')
            input_idle.wait(self)
        except BaseException as error:
            self.resume_attempted=True
            self.profile['state']='resume_uncertain_no_retry';error.preassigned_native_startup=self;raise

    def bind_owner(self, identity, window_handle):
        require(not self.closed and self.profile['resumed'] and not self.bind_attempted,'NO_BIND_RETRY')
        self.bind_attempted=True
        try:
            ticks=limits.validate_identity(identity,window_handle)
            require(identity['process_id']==self.pid and ticks==self.birth
                and identity['session_id']==self.session,'BIND_PREASSIGNED_IDENTITY_ONLY')
            self.guard.check();self._parent_unchanged();self._fresh_image();self._handle_identity()
            self.owner_job._observe_identity(self.process,identity,window_handle,ticks)
            self.owner_job.identity=dict(identity)
            self.owner_job.profile.update(native_process_assigned=True,preassigned_at_creation=True,
                pre_assignment_private_bytes=0)
            self.owner_job.observe()
            self.profile.update(owner_bound=True,state='owner_bound_unqualified')
            return dict(self.owner_job.profile['limits_readback'])
        except BaseException as error:
            self.profile['state']='binding_failed_or_uncertain_no_retry'
            error.preassigned_native_startup=self;raise

    def observe(self):
        self.guard.check();self._parent_unchanged();self._handle_identity()
        return self.owner_job.observe()

    def close(self):
        if self.closed:return
        # No sampler/deadline here. Original verified-owner Close/Quit belongs
        # to the controller; an unbound live child is retained, never blanket-Quit.
        k=self.windows.k
        require(self.process is None or k.WaitForSingleObject(self.process,0)==0,'LIVE_NATIVE_RETAIN_HANDLES_AND_JOB')
        require(self.windows.accounting(self.owner_job.job)['active_processes']==0,'LIVE_NATIVE_TREE_RETAIN_JOB')
        for attribute in ('thread','process'):
            handle=getattr(self,attribute)
            if handle is not None:
                require(k.CloseHandle(handle),'CLOSE_OWNED_'+attribute.upper());setattr(self,attribute,None)
        self.owner_job.close();self.profile['native_job_profile']=dict(self.owner_job.profile)
        self.closed=True;self.profile.update(cleanup_confirmed=True,state='closed_not_qualified')
