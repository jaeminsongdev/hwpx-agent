"""Closed first-instruction Job qualification, never a native/COM launcher.

PROC_THREAD_ATTRIBUTE_JOB_LIST assigns the already-limited Job during creation.
CREATE_SUSPENDED additionally permits handle/limit inspection before the sole
resume. Only the fixed isolated Python self-check below is executable here.
No generic command, Hwp path, product authority or force-termination interface.
"""
import ctypes
from ctypes import wintypes as w
from pathlib import Path
import subprocess
import sys
import time

import crossref_owned_host_process as host

PYTHON = Path(r'C:\Users\thdqu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
JOB_LIST = 0x0002000d
CREATE_FLAGS = 0x00080000 | 0x08000000 | 0x00004000 | 0x00000004

# Isolated stdlib-only child; no repository import, source file, IO or COM.
# A zero exit means the child's own immediate Job and effective process limits
# matched all expected values. It is not a native product/causality result.
CHILD = '''import ctypes,sys
from ctypes import wintypes as w
class Basic(ctypes.Structure):
 _fields_=[('pt',ctypes.c_int64),('jt',ctypes.c_int64),('flags',w.DWORD),('min',ctypes.c_size_t),('max',ctypes.c_size_t),('active',w.DWORD),('affinity',ctypes.c_size_t),('priority',w.DWORD),('scheduling',w.DWORD)]
class IO(ctypes.Structure):
 _fields_=[(n,ctypes.c_uint64) for n in ('ro','wo','oo','r','w','o')]
class Limits(ctypes.Structure):
 _fields_=[('basic',Basic),('io',IO),('pm',ctypes.c_size_t),('jm',ctypes.c_size_t),('pp',ctypes.c_size_t),('pj',ctypes.c_size_t)]
class Rate(ctypes.Structure):
 _fields_=[('flags',w.DWORD),('rate',w.DWORD)]
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.GetCurrentProcess.restype=w.HANDLE
k.QueryInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p]
k.QueryInformationJobObject.restype=w.BOOL
k.GetProcessAffinityMask.argtypes=[w.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
k.GetProcessAffinityMask.restype=w.BOOL
k.GetPriorityClass.argtypes=[w.HANDLE];k.GetPriorityClass.restype=w.DWORD
limits,rate=Limits(),Rate();allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
memory,mask,flags,quota,priority,active=map(int,sys.argv[1:])
ok=(k.QueryInformationJobObject(None,9,ctypes.byref(limits),ctypes.sizeof(limits),None)
 and k.QueryInformationJobObject(None,15,ctypes.byref(rate),ctypes.sizeof(rate),None)
 and k.GetProcessAffinityMask(k.GetCurrentProcess(),ctypes.byref(allowed),ctypes.byref(system))
 and limits.jm==memory and limits.basic.affinity==mask and allowed.value==mask
 and limits.basic.flags==flags and limits.basic.priority==priority and limits.basic.active==active
 and k.GetPriorityClass(k.GetCurrentProcess())==priority and rate.flags==5 and rate.rate==quota)
sys.exit(0 if ok else 65)
'''


def require(ok, code):
    if not ok:raise ValueError('XREF_PREASSIGNED_' + code)


class StartupInfo(ctypes.Structure):
    _fields_=[('cb',w.DWORD),('reserved',w.LPWSTR),('desktop',w.LPWSTR),('title',w.LPWSTR),
        ('x',w.DWORD),('y',w.DWORD),('width',w.DWORD),('height',w.DWORD),
        ('xc',w.DWORD),('yc',w.DWORD),('fill',w.DWORD),('flags',w.DWORD),
        ('show',w.WORD),('reserved_size',w.WORD),('reserved_pointer',ctypes.c_void_p),
        ('stdin',w.HANDLE),('stdout',w.HANDLE),('stderr',w.HANDLE)]


class StartupInfoEx(ctypes.Structure):
    _fields_=[('startup',StartupInfo),('attributes',ctypes.c_void_p)]


class ProcessInfo(ctypes.Structure):
    _fields_=[('process',w.HANDLE),('thread',w.HANDLE),('pid',w.DWORD),('tid',w.DWORD)]


def fixed_command(plan, role='limit_selfcheck'):
    require(type(role) is str and role=='limit_selfcheck','FIXED_READONLY_ROLE')
    require(Path(sys.executable)==PYTHON and PYTHON.is_file()
        and not PYTHON.is_symlink() and not PYTHON.is_junction(),'FIXED_RUNTIME')
    keys=('memory_limit','affinity','flags','cpu_rate','priority','active_limit')
    require(all(type(plan.get(k)) is int and plan[k]>0 for k in keys),'INTEGER_LIMIT_VALUES')
    return [str(PYTHON),'-I','-S','-B','-c',CHILD]+[str(plan[k]) for k in keys]


class PreassignedReadonlyProcess:
    """Atomically preassigned fixed child; live/uncertain handles stay owned."""
    def __init__(self, windows, checkpoint):
        self.envelope=host.OwnedHostProcess(windows,checkpoint)
        self.windows,self.checkpoint=windows,checkpoint
        self.process=None;self.thread=None;self.closed=False
        self.creation_attempted=False;self.resume_attempted=False
        self.profile=dict(role='fixed_readonly_job_at_creation',created=False,
            assigned_before_initial_thread=False,suspended_handle_verified=False,
            resumed=False,child_selfcheck_exit_code=None,cleanup_confirmed=False,
            atomic_job_list=True,force_termination_invoked=False,kill_on_close=False,
            native_execution_authorized=False,native_startup_qualified=False,p09_complete=False)
        k=self.windows.k
        for name,args,result in (
            ('InitializeProcThreadAttributeList',[ctypes.c_void_p,w.DWORD,w.DWORD,ctypes.POINTER(ctypes.c_size_t)],w.BOOL),
            ('UpdateProcThreadAttribute',[ctypes.c_void_p,w.DWORD,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_void_p,ctypes.c_void_p],w.BOOL),
            ('DeleteProcThreadAttributeList',[ctypes.c_void_p],None),
            ('CreateProcessW',[w.LPCWSTR,w.LPWSTR,ctypes.c_void_p,ctypes.c_void_p,w.BOOL,w.DWORD,ctypes.c_void_p,w.LPCWSTR,ctypes.POINTER(StartupInfoEx),ctypes.POINTER(ProcessInfo)],w.BOOL),
            ('ResumeThread',[w.HANDLE],w.DWORD),
            ('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD),
            ('GetExitCodeProcess',[w.HANDLE,ctypes.POINTER(w.DWORD)],w.BOOL),
            ('GetProcessTimes',[w.HANDLE]+[ctypes.POINTER(w.FILETIME)]*4,w.BOOL)):
            fn=getattr(k,name);fn.argtypes,fn.restype=args,result

    def create_suspended(self, role='limit_selfcheck'):
        require(not self.closed and not self.creation_attempted,'NO_CREATION_RETRY')
        self.creation_attempted=True
        attributes=None;initialized=False;info=ProcessInfo();k=self.windows.k
        try:
            args=fixed_command(self.envelope.plan,role)
            self.checkpoint();self.envelope.readback()
            size=ctypes.c_size_t()
            ctypes.set_last_error(0)
            first=k.InitializeProcThreadAttributeList(None,1,0,ctypes.byref(size))
            require(not first and ctypes.get_last_error()==122 and 0<size.value<=65536,'ATTRIBUTE_SIZE')
            attributes=ctypes.create_string_buffer(size.value)
            require(k.InitializeProcThreadAttributeList(attributes,1,0,ctypes.byref(size)),'ATTRIBUTE_INITIALIZE')
            initialized=True
            jobs=(w.HANDLE*1)(self.envelope.job)
            require(k.UpdateProcThreadAttribute(attributes,0,JOB_LIST,jobs,ctypes.sizeof(jobs),None,None),'JOB_LIST_ATTRIBUTE')
            startup=StartupInfoEx();startup.startup.cb=ctypes.sizeof(startup)
            startup.attributes=ctypes.cast(attributes,ctypes.c_void_p)
            command=ctypes.create_unicode_buffer(subprocess.list2cmdline(args))
            require(k.CreateProcessW(str(PYTHON),command,None,None,False,CREATE_FLAGS,
                None,str(host.c.ROOT),ctypes.byref(startup),ctypes.byref(info)),'CREATE_FIXED_CHILD')
            self.process,self.thread=info.process,info.thread
            self.profile.update(created=True,process_id=int(info.pid),creation_flags=CREATE_FLAGS,
                handles_inherited=False,external_stdio=False)
            self.verify_suspended()
        except BaseException as error:
            # No fallback CreateProcess/COM/restart; retain even a suspended child.
            error.preassigned_readonly_process=self
            raise
        finally:
            if initialized:k.DeleteProcThreadAttributeList(attributes)

    def verify_suspended(self):
        require(self.process is not None and not self.resume_attempted,'SUSPENDED_PHASE')
        self.envelope.readback();k=self.windows.k;member=w.BOOL()
        require(k.IsProcessInJob(self.process,self.envelope.job,ctypes.byref(member)) and member.value,
            'PRE_RUN_JOB_MEMBERSHIP')
        image,size=ctypes.create_unicode_buffer(32768),w.DWORD(32768)
        require(k.QueryFullProcessImageNameW(self.process,0,image,ctypes.byref(size))
            and image.value.casefold()==str(PYTHON).casefold(),'PRE_RUN_IMAGE')
        allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
        require(k.GetProcessAffinityMask(self.process,ctypes.byref(allowed),ctypes.byref(system))
            and allowed.value==self.envelope.plan['affinity']
            and k.GetPriorityClass(self.process)==self.envelope.plan['priority'],'PRE_RUN_EFFECTIVE_LIMITS')
        times=[w.FILETIME() for _ in range(4)]
        require(k.GetProcessTimes(self.process,*(ctypes.byref(v) for v in times)),'PRE_RUN_TIMES')
        birth=times[0].dwLowDateTime | times[0].dwHighDateTime<<32
        require(birth>0 and times[3].dwLowDateTime==times[3].dwHighDateTime==0,'NO_PRE_RUN_USER_CPU')
        self.profile.update(assigned_before_initial_thread=True,suspended_handle_verified=True,
            process_birth_100ns=birth,pre_run_user_cpu_100ns=0,
            pre_run_limits=self.envelope.readback())

    def resume_readonly(self):
        require(not self.closed and self.profile['suspended_handle_verified']
            and not self.resume_attempted,'NO_RESUME_RETRY')
        # Failed pre-resume checks leave the sole attempt unused and handles retained;
        # only explicit observation of the same suspended readonly child can continue.
        self.checkpoint();self.verify_suspended()
        self.resume_attempted=True
        try:
            require(self.windows.k.ResumeThread(self.thread)==1,'RESUME_EXACTLY_ONE_SUSPENSION')
            self.profile['resumed']=True
        except BaseException as error:
            error.preassigned_readonly_process=self
            raise

    def wait_readonly(self, maximum_seconds=15):
        require(type(maximum_seconds) in (int,float) and 0<maximum_seconds<=30
            and self.profile['resumed'] and not self.closed,'READONLY_WAIT_SCOPE')
        end=time.monotonic()+maximum_seconds
        while True:
            self.checkpoint();self.envelope.observe()
            result=self.windows.k.WaitForSingleObject(self.process,50)
            if result==0:
                code=w.DWORD()
                require(self.windows.k.GetExitCodeProcess(self.process,ctypes.byref(code)),'TERMINAL_EXIT_CODE')
                self.profile['child_selfcheck_exit_code']=int(code.value)
                return int(code.value)
            require(result==258,'WAIT_RESULT')
            require(time.monotonic()<end,'READONLY_OBSERVATION_DEADLINE_NO_KILL')

    def close(self):
        if self.closed:return
        k=self.windows.k
        # Cleanup is unguarded: no CPU admission or deadline may prevent it.
        require(self.process is None or k.WaitForSingleObject(self.process,0)==0,'LIVE_CHILD_RETAIN_HANDLES')
        require(self.windows.accounting(self.envelope.job)['active_processes']==0,'LIVE_TREE_RETAIN_JOB')
        for attribute in ('thread','process'):
            value=getattr(self,attribute)
            if value is not None:
                require(k.CloseHandle(value),'CLOSE_OWNED_'+attribute.upper())
                setattr(self,attribute,None)
        self.envelope.close();self.profile['envelope_profile']=dict(self.envelope.profile)
        self.closed=True;self.profile['cleanup_confirmed']=True
