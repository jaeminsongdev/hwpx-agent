"""Fixed eight worker in the original non-killing one-percent envelope; no CLI."""
import ctypes,json,os,subprocess,sys
from ctypes import wintypes as w
import crossref_session_worker as prior
import crossref_preassigned_preparation as prep

TARGET='implementation/p09/tools/run-crossref-qualified-fixed-worker.ps1'
SOURCES=(TARGET,)+tuple(p for p in prep.SOURCE_FILES if p not in(prep.TARGET,'implementation/p09/tools/crossref-preassigned-preparation-gate.ps1'))


def command(reader):
    prior.require(reader.root.resolve()==prior.original.c.ROOT.resolve(),'FIXED_SOURCE_ROOT')
    for path in SOURCES:reader.pin(path)
    prior.require(reader.snapshots[prior.original.BOOTSTRAP]['sha256']==prior.original.BOOTSTRAP_SHA,'ORIGINAL_FIXED_BOOTSTRAP')
    args=[prior.original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(prior.original.c.ROOT/TARGET),'-FixedEightAfterSession']
    return [sys.executable,'-B',str(prior.original.c.ROOT/prior.original.BOOTSTRAP),'--worker',json.dumps(args,ensure_ascii=False)]


class FixedWorker(prior.SessionWorker):
    def _fixed_command(self,reader):return command(reader)

    def start_fixed_worker(self,reader,env=None):
        prior.require(not self.closed and not self.start_attempted,'NO_WORKER_RESTART');self.start_attempted=True
        try:
            args=self._fixed_command(reader);self.checkpoint();self.readback()
            self.profile.update(role='private_fixed_eight_worker',qualification_target_pinned=True)
            self.process=subprocess.Popen(args,cwd=prior.original.c.ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')if env is None else env,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='strict',
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            self.profile.update(bootstrap_created=True,bootstrap_pid=self.process.pid)
            memory=prior.original.c.ProcessMemory();memory.size=ctypes.sizeof(memory)
            prior.require(self.windows.k.K32GetProcessMemoryInfo(self.process._handle,ctypes.byref(memory),memory.size),'PRE_ASSIGNMENT_PRIVATE_MEMORY')
            prior.original.native.combined_private_budget(self.plan['memory_limit'],int(memory.private),0,self.windows.total_ram)
            self.profile['pre_assignment_private_bytes']=int(memory.private)
            prior.require(self.windows.k.AssignProcessToJobObject(self.job,self.process._handle),'ASSIGN_WAITING_WORKER')
            member=w.BOOL()
            prior.require(self.windows.k.IsProcessInJob(self.process._handle,self.job,ctypes.byref(member))and member.value,'WAITING_WORKER_MEMBERSHIP')
            self.profile['bootstrap_assigned']=True
            allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
            prior.require(self.windows.k.GetProcessAffinityMask(self.process._handle,ctypes.byref(allowed),ctypes.byref(system))
                and allowed.value==self.plan['affinity']and self.windows.k.GetPriorityClass(self.process._handle)==self.plan['priority'],'EFFECTIVE_WORKER_LIMITS')
            self.profile['bootstrap_limits_readback']=True;self.observe()
        except BaseException as error:error.owned_host_process=self;raise
