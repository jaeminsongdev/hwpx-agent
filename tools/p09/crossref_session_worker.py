"""Fixed candidate session worker transport, no external/native launch CLI.

The worker can only attach to a host-preassigned owner. The original native guard
and one-percent non-killing envelope are required before its fixed bootstrap GO.
"""
import ctypes,json,os,subprocess,sys
from ctypes import wintypes as w
import crossref_preassigned_preparation_drain as drain
import crossref_owned_host_process as original

TARGET='implementation/p09/tools/run-crossref-session-qualification-worker.ps1'
LIBRARIES=('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact','crossref-stage-probe',
    'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-dual-owner-identity',
    'crossref-preassigned-host-channel','crossref-preassigned-owner','crossref-session-qualification-channel')
SOURCES=(TARGET,)+tuple('implementation/p09/tools/'+n+'.ps1'for n in LIBRARIES)+(
    'implementation/p09/tools/crossref-existing-owner.cs','implementation/p09/tools/run-hancom-2020-sdk-baseline-capture.ps1',original.BOOTSTRAP)


def require(ok,code):
    if not ok:raise ValueError('XREF_SESSION_WORKER_'+code)


def command(reader):
    require(reader.root.resolve()==original.c.ROOT.resolve(),'FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    require(reader.snapshots[original.BOOTSTRAP]['sha256']==original.BOOTSTRAP_SHA,'ORIGINAL_FIXED_BOOTSTRAP')
    args=[original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(original.c.ROOT/TARGET),'-QualifySessionOnly']
    return [sys.executable,'-B',str(original.c.ROOT/original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]


class SessionWorker(drain.DrainedPreparationWorker):
    def __init__(self,guard):
        require(callable(getattr(guard,'check',None))and not hasattr(guard,'preparation_CPU')
            and type(getattr(guard,'windows',None))is original.c.Windows,'ORIGINAL_NATIVE_GUARD_REQUIRED')
        self.guard=guard;super().__init__(guard.windows,guard.check)

    def start_session_worker(self,reader,env=None):
        require(not self.closed and not self.start_attempted,'NO_WORKER_RESTART');self.start_attempted=True
        try:
            args=command(reader);self.checkpoint();self.readback()
            self.profile.update(role='private_session_qualification_candidate',qualification_target_pinned=True)
            self.process=subprocess.Popen(args,cwd=original.c.ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')if env is None else env,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='strict',
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            self.profile.update(bootstrap_created=True,bootstrap_pid=self.process.pid)
            memory=original.c.ProcessMemory();memory.size=ctypes.sizeof(memory)
            require(self.windows.k.K32GetProcessMemoryInfo(self.process._handle,ctypes.byref(memory),memory.size),'PRE_ASSIGNMENT_PRIVATE_MEMORY')
            original.native.combined_private_budget(self.plan['memory_limit'],int(memory.private),0,self.windows.total_ram)
            self.profile['pre_assignment_private_bytes']=int(memory.private)
            require(self.windows.k.AssignProcessToJobObject(self.job,self.process._handle),'ASSIGN_WAITING_WORKER')
            member=w.BOOL()
            require(self.windows.k.IsProcessInJob(self.process._handle,self.job,ctypes.byref(member))and member.value,'WAITING_WORKER_MEMBERSHIP')
            self.profile['bootstrap_assigned']=True
            allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
            require(self.windows.k.GetProcessAffinityMask(self.process._handle,ctypes.byref(allowed),ctypes.byref(system))
                and allowed.value==self.plan['affinity']and self.windows.k.GetPriorityClass(self.process._handle)==self.plan['priority'],'EFFECTIVE_WORKER_LIMITS')
            self.profile['bootstrap_limits_readback']=True;self.observe()
        except BaseException as error:error.owned_host_process=self;raise
