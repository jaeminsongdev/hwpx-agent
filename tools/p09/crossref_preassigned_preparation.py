"""Fixed one-percent preparation worker and denial-only protocol, never a Native launcher.

Original non-killing owned worker envelope, waiting bootstrap and limits remain
unchanged. Native dispatch requires another explicitly qualified entry.
"""
import ctypes,json,os,subprocess,sys
from ctypes import wintypes as w
import crossref_owned_host_process as original
import crossref_preassigned_host_protocol as wire

c=original.c
TARGET='implementation/p09/tools/inspect-crossref-preassigned-worker.ps1'
LIBRARIES=('sdk-baseline-owned-session','crossref-owned-active-source','crossref-owned-artifact',
    'crossref-discovery-preflight-library','crossref-save-reopen','crossref-sdk-insertion','crossref-stage-probe',
    'crossref-case-flow','crossref-native-case-ports','crossref-host-channel','crossref-fixed-batch',
    'crossref-dual-owner-identity','crossref-canonical-runtime','crossref-preassigned-host-channel',
    'crossref-preassigned-owner','crossref-preassigned-case-ports','crossref-preassigned-controller','crossref-preassigned-preparation-gate')
SOURCE_FILES=(TARGET,)+tuple('implementation/p09/tools/'+name+'.ps1'for name in LIBRARIES)+(
    'implementation/p09/tools/crossref-existing-owner.cs','implementation/p09/tools/run-hancom-2020-sdk-baseline-capture.ps1',
    'implementation/p09/tools/inspect-crossref-worker-composition.ps1',original.BOOTSTRAP,
    'target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe',
    'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/prepared-sdk-batch.v1.json')


def require(ok,code):
    if not ok:raise ValueError('XREF_PREASSIGNED_PREPARATION_'+code)


def command(reader):
    require(reader.root.resolve()==c.ROOT.resolve(),'FIXED_ROOT')
    for path in SOURCE_FILES:reader.pin(path)
    require(reader.snapshots[original.BOOTSTRAP]['sha256']==original.BOOTSTRAP_SHA,'FROZEN_WAITING_BOOTSTRAP')
    target=[original.SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/TARGET),'-InspectPreparationOnly']
    return [sys.executable,'-B',str(c.ROOT/original.BOOTSTRAP),'--worker',json.dumps(target,ensure_ascii=False)]


class PreparationWorker(original.OwnedHostProcess):
    """One fixed no-native target. No arbitrary role/command, kill or Native mode."""
    def start_preparation(self,reader,env=None):
        require(not self.closed and not self.start_attempted,'NO_WORKER_RESTART')
        self.start_attempted=True
        try:
            args=command(reader);self.checkpoint();self.readback()
            self.profile['role']='closed_preassigned_preparation_not_native'
            self.process=subprocess.Popen(args,cwd=c.ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')if env is None else env,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='strict',
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            self.profile['bootstrap_created']=True
            memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
            require(self.windows.k.K32GetProcessMemoryInfo(self.process._handle,ctypes.byref(memory),memory.size),'PRE_ASSIGNMENT_PRIVATE_MEMORY')
            original.native.combined_private_budget(self.plan['memory_limit'],int(memory.private),0,self.windows.total_ram)
            self.profile['pre_assignment_private_bytes']=int(memory.private)
            require(self.windows.k.AssignProcessToJobObject(self.job,self.process._handle),'ASSIGN_WAITING_WORKER')
            member=w.BOOL()
            require(self.windows.k.IsProcessInJob(self.process._handle,self.job,ctypes.byref(member))and member.value,'WAITING_WORKER_MEMBERSHIP')
            self.profile['bootstrap_assigned']=True
            allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
            require(self.windows.k.GetProcessAffinityMask(self.process._handle,ctypes.byref(allowed),ctypes.byref(system))
                and allowed.value==self.plan['affinity']and self.windows.k.GetPriorityClass(self.process._handle)==self.plan['priority'],'WORKER_LIMIT_READBACK')
            self.profile['bootstrap_limits_readback']=True;self.observe()
        except BaseException as error:
            error.owned_host_process=self
            raise


class DenialProtocol:
    """Exactly prepare_slot denial -> failed finish. No Scope or Native callback."""
    def __init__(self):self.sequence=0;self.failed=False
    def respond(self,raw):
        require(not self.failed and self.sequence<2,'NO_RETRY_OR_THIRD_MESSAGE')
        try:
            request=wire.decode_request(raw)
            require(request['case_index']==1 and request['sequence']==self.sequence+1,'EXACT_FIRST_CASE_SEQUENCE')
            if self.sequence==0:require(request['operation']=='checkpoint'and request['step']=='prepare_slot','PREPARE_SLOT_ONLY')
            else:require(request['operation']=='finish'and request['case_status']=='failed','FAILED_FINISH_ONLY')
            self.sequence+=1;ack=self.sequence==2
            return json.dumps(dict(schema_version=wire.RESPONSE,sequence=self.sequence,case_index=1,acknowledged=ack,
                error_code=None if ack else'XREF_HOST_PREPARATION_NATIVE_DISPATCH_DENIED',owner_descriptor=None,
                native_execution_authorized=False,p09_complete=False),separators=(',',':'))
        except BaseException:
            self.failed=True;raise
