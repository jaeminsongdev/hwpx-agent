"""One-percent owned readonly host qualification; no native launch route.

Reuses the frozen waiting bootstrap. Limits and membership are read back before
signalling a fixed readonly target. Nonempty close never kills or
abandons its Job. Coordinator RAM remains under the original separate guard;
the one-percent partition here covers the waiting bootstrap and its children.
"""
import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import subprocess
import sys

import crossref_native_host_limits as native

c = native.c
BOOTSTRAP = 'tools/p09/owned_sql_job.py'
BOOTSTRAP_SHA = '30b08c4d779494bbdb7579b9bb28782b4f4588fc69b931cc9d18af326d46b7a0'
DRIVER = 'implementation/p09/tools/test-crossref-host-channel.ps1'
DRIVER_SHA = '19aa109313305b10e04430995ff1b1bcff161546751d94695f5f8e68adb8031e'
PREFIX = 'implementation/p09/tools/inspect-crossref-pre-com-prefix.ps1'
PREFIX_SHA = '36f86459b6f59ee979cb9a04c06f0ac03e30a416ed1d77e05b917c7845738441'
CONNECTION = 'implementation/p09/tools/inspect-crossref-runtime-connection.ps1'
CONNECTION_SHA = 'afcb2052a2b152d323bc42f0a32da16e676eda9df730dd0b720be0d06a9099d1'
CONNECTION_SOURCES = 'implementation/p09/evidence/p09-361-crossref-fixed-batch-final-sync052.v1.json'
CONNECTION_SOURCES_SHA = 'da42092904c1152873a092b043c63bfe9f23fb514fe618c8ea5acc20ae2c6688'
SOURCE_RECEIPT = 'implementation/p09/evidence/p09-361-crossref-host-channel-final-sync042.v1.json'
SOURCE_RECEIPT_SHA = '2e3f06ebcfd6af3cc1692102cbc60dd0049824d3983a3093e675013933d8ebb9'
SHELL = r'C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe'
TOKEN = 'P149_SQL_JOB_GO\n'


def require(ok, code):
    if not ok:
        raise ValueError('XREF_HOST_PROCESS_' + code)


def host_plan(windows):
    # Validate the shared CPU/priority/eight-percent base without mutating it.
    original = native.validate_plan(windows)
    original['memory_limit'] = windows.memory_limit // 8 // 65536 * 65536
    require(original['memory_limit'] > 0, 'ONE_PERCENT_MEMORY')
    return original


def read_parent_cpu(windows):
    member=w.BOOL();k=windows.k
    require(k.IsProcessInJob(k.GetCurrentProcess(),None,ctypes.byref(member)), 'CURRENT_JOB_MEMBERSHIP')
    result=dict(job_present=bool(member.value),query_succeeded=False,flags=0,affinity=0,priority=0,
        rate_flags=0,rate=0)
    if not member.value:return result
    limits,rate=c.ExtendedLimit(),c.CpuRate()
    if not (k.QueryInformationJobObject(None,9,ctypes.byref(limits),ctypes.sizeof(limits),None)
        and k.QueryInformationJobObject(None,15,ctypes.byref(rate),ctypes.sizeof(rate),None)):
        return result  # Unknown parent keeps the original restrictive child quota.
    result.update(query_succeeded=True,flags=int(limits.basic.flags),affinity=int(limits.basic.affinity),
        priority=int(limits.basic.priority),rate_flags=int(rate.flags),rate=int(rate.rate))
    return result


def cpu_budget(windows, parent):
    verified=(parent.get('job_present') is True and parent.get('query_succeeded') is True
        and all(type(parent.get(k)) is int for k in ('flags','affinity','priority','rate_flags','rate'))
        and parent['flags'] & 0x30 == 0x30 and parent['flags'] & 0x1800 == 0
        and parent['affinity']==windows.mask and parent['priority']==0x4000
        and parent['rate_flags']==5 and 0 < parent['rate'] <= windows.cpu_rate)
    # Nested rates are relative to the immediate parent, not the whole machine.
    # 100% of an observed <=one-core parent is NOT 100% of the PC.
    return dict(verified_parent_budget=verified,configured_rate=10000 if verified else windows.cpu_rate,
        machine_percent_upper_bound=(parent['rate'] if verified else windows.cpu_rate)/100,
        scope='verified_parent_budget' if verified else 'original_restrictive_fallback')


def readonly_command(reader, role='wrapper_denial'):
    require(type(role) is str and role in ('wrapper_denial','pre_com_prefix','runtime_connection'), 'FIXED_READONLY_ROLE')
    require(reader.root.resolve() == c.ROOT.resolve(), 'SOURCE_ROOT')
    receipt = reader.json(SOURCE_RECEIPT)
    require(reader.snapshots[SOURCE_RECEIPT]['sha256'] == SOURCE_RECEIPT_SHA
        and receipt['cleanup'] is True, 'FROZEN_READONLY_SOURCE_RECEIPT')
    selected = [pin for pin in receipt['source_pins'] if pin['path'].startswith('implementation/p09/tools/')
        and pin['path'].endswith('.ps1')]
    require(8 <= len(selected) <= 20 and any(p['path'] == DRIVER for p in selected), 'READONLY_SOURCE_INVENTORY')
    for pin in selected:
        require(reader.pin(pin['path']) == pin, 'READONLY_SOURCE_CHANGED')
    require(reader.pin(DRIVER)['sha256'] == DRIVER_SHA and reader.pin(BOOTSTRAP)['sha256'] == BOOTSTRAP_SHA,
        'FROZEN_TARGET_AND_BOOTSTRAP')
    for path in (Path(sys.executable), Path(SHELL)):
        require(path.is_absolute() and path.is_file() and not path.is_symlink() and not path.is_junction(),
            'REGULAR_FIXED_EXECUTABLE')
    target = [SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/DRIVER),'-WrapperOnly']
    if role == 'pre_com_prefix':
        require(reader.pin(PREFIX)['sha256'] == PREFIX_SHA, 'FIXED_PREFIX_SHA')
        target = [SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/PREFIX),'-InspectOnly']
    if role == 'runtime_connection':
        connected = reader.json(CONNECTION_SOURCES)
        require(reader.snapshots[CONNECTION_SOURCES]['sha256'] == CONNECTION_SOURCES_SHA
            and connected['cleanup'] is True, 'FIXED_CONNECTION_SOURCE_RECEIPT')
        for source in connected['source_pins']:
            if source['path'].startswith('implementation/p09/tools/') and source['path'].endswith('.ps1'):
                require(reader.pin(source['path']) == source, 'CONNECTION_SOURCE_CHANGED')
        require(reader.pin(CONNECTION)['sha256'] == CONNECTION_SHA, 'FIXED_CONNECTION_SHA')
        target = [SHELL,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/CONNECTION),'-InspectConnectionOnly']
    return [sys.executable,'-B',str(c.ROOT/BOOTSTRAP),'--worker',json.dumps(target,ensure_ascii=False)]


class OwnedHostProcess:
    """Waiting-worker ownership and one-percent limits, without a kill method.

    A running target/uncertain signal is not restarted. The caller drains bounded
    pipes and waits for this exact handle; close refuses a live worker/tree.
    Only closed readonly targets are implemented here. There is no native mode.
    """
    def __init__(self, windows, checkpoint):
        require(type(windows) is c.Windows and callable(checkpoint), 'ORIGINAL_HOST_DEPENDENCIES')
        self.windows,self.checkpoint = windows,checkpoint
        self.plan = host_plan(windows)
        self.parent_cpu=read_parent_cpu(windows)
        self.cpu_budget=cpu_budget(windows,self.parent_cpu)
        self.plan['cpu_rate']=self.cpu_budget['configured_rate']
        self.job=None;self.process=None;self.closed=False;self.start_attempted=False;self.signal_attempted=False
        self.profile=dict(role='fixed_readonly_wrapper_qualification',host_worker_one_percent_installed=False,
            coordinator_in_this_job=False,original_coordinator_guard_required=True,bootstrap_created=False,
            parent_cpu_readback=self.parent_cpu,cpu_budget=self.cpu_budget,
            bootstrap_assigned=False,limits_readback=None,bootstrap_limits_readback=False,
            readonly_signal_written=False,pre_assignment_private_bytes=0,
            input_eof_sent=False,owned_tree_empty=False,cleanup_confirmed=False,job_handle_closed=False,
            kill_on_close=False,forced_termination_invoked=False,native_execution_authorized=False,
            complete_native_guard_integration_qualified=False,p09_complete=False)
        checkpoint()
        self.job=windows.k.CreateJobObjectW(None,None)
        require(bool(self.job), 'CREATE_JOB')
        try:
            limits=c.ExtendedLimit();limits.basic.flags=self.plan['flags']
            limits.basic.affinity,limits.basic.priority=self.plan['affinity'],self.plan['priority']
            limits.basic.active_limit,limits.job_memory=self.plan['active_limit'],self.plan['memory_limit']
            require(windows.k.SetInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits)), 'SET_LIMITS')
            rate=c.CpuRate(5,self.plan['cpu_rate'])
            require(windows.k.SetInformationJobObject(self.job,15,ctypes.byref(rate),ctypes.sizeof(rate)), 'SET_CPU_RATE')
            self.profile['limits_readback']=self.readback()
            self.profile['host_worker_one_percent_installed']=True
        except BaseException:
            self.close()
            raise

    def readback(self):
        require(self.job is not None and not self.closed, 'JOB_CLOSED')
        self._verify_parent_cpu()
        limits,rate=c.ExtendedLimit(),c.CpuRate();k=self.windows.k
        require(k.QueryInformationJobObject(self.job,9,ctypes.byref(limits),ctypes.sizeof(limits),None)
            and k.QueryInformationJobObject(self.job,15,ctypes.byref(rate),ctypes.sizeof(rate),None), 'READBACK')
        require(limits.basic.flags == self.plan['flags'] and limits.job_memory == self.plan['memory_limit']
            and limits.basic.affinity == self.plan['affinity'] and limits.basic.priority == self.plan['priority']
            and limits.basic.active_limit == self.plan['active_limit'] and rate.flags == 5
            and rate.rate == self.plan['cpu_rate'], 'READBACK_MISMATCH')
        return dict(verified=True,job_private_limit_mib=limits.job_memory/1048576,
            cpu_hard_cap_machine_percent=self.cpu_budget['machine_percent_upper_bound'],
            configured_cpu_rate_percent=rate.rate/100,cpu_rate_scope=self.cpu_budget['scope'],cpu_machine_cap_is_upper_bound=True,
            affinity_mask=limits.basic.affinity,
            priority_class=limits.basic.priority,active_process_limit=limits.basic.active_limit,
            kill_on_close=False,breakaway_disabled=True,time_limit_installed=False)

    def _verify_parent_cpu(self):
        if self.cpu_budget['verified_parent_budget']:
            require(read_parent_cpu(self.windows)==self.parent_cpu, 'PARENT_CPU_BUDGET_CHANGED')

    def start_waiting(self, reader, role='wrapper_denial'):
        require(not self.closed and not self.start_attempted, 'NO_WORKER_RESTART')
        self.start_attempted=True
        try:
            args=readonly_command(reader, role=role)
            self.profile['role']='pre_com_prefix_qualification' if role == 'pre_com_prefix' else self.profile['role']
            if role == 'runtime_connection':self.profile['role']='closed_runtime_connection_inspection'
            self.checkpoint();self.readback()
            self.process=subprocess.Popen(args,cwd=c.ROOT,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='strict',
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            self.profile['bootstrap_created']=True
            memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
            require(self.windows.k.K32GetProcessMemoryInfo(self.process._handle,ctypes.byref(memory),memory.size),
                'PRE_ASSIGNMENT_PRIVATE_MEMORY')
            native.combined_private_budget(self.plan['memory_limit'],int(memory.private),0,self.windows.total_ram)
            self.profile['pre_assignment_private_bytes']=int(memory.private)
            require(self.windows.k.AssignProcessToJobObject(self.job,self.process._handle), 'ASSIGN_WAITING_WORKER')
            member=w.BOOL()
            require(self.windows.k.IsProcessInJob(self.process._handle,self.job,ctypes.byref(member)) and member.value,
                'WAITING_WORKER_MEMBERSHIP')
            self.profile['bootstrap_assigned']=True
            allowed,system=ctypes.c_size_t(),ctypes.c_size_t()
            require(self.windows.k.GetProcessAffinityMask(self.process._handle,ctypes.byref(allowed),ctypes.byref(system))
                and allowed.value == self.plan['affinity']
                and self.windows.k.GetPriorityClass(self.process._handle)==self.plan['priority'], 'WORKER_LIMIT_READBACK')
            self.profile['bootstrap_limits_readback']=True
            self.observe()
        except BaseException as error:
            # Preserve this object's handles on any partial start, never force-kill it.
            error.owned_host_process=self
            raise

    def signal_readonly_target(self):
        require(not self.closed and self.process is not None and self.profile['bootstrap_assigned']
            and not self.signal_attempted and not self.profile['input_eof_sent'], 'NO_TARGET_SIGNAL_RETRY')
        self.signal_attempted=True
        self.checkpoint();self.readback();self.observe()
        require(self.process.poll() is None, 'WAITING_WORKER_ALREADY_TERMINAL')
        require(self.process.stdin.write(TOKEN)==len(TOKEN), 'READONLY_SIGNAL_WRITE')
        self.process.stdin.flush();self.profile['readonly_signal_written']=True

    def cancel_before_signal(self):
        require(self.process is not None and not self.signal_attempted, 'CANCEL_WAITING_ONLY')
        if not self.process.stdin.closed:self.process.stdin.close()
        self.profile['input_eof_sent']=True

    @property
    def stdin(self):return self.process.stdin
    @property
    def stdout(self):return self.process.stdout
    @property
    def stderr(self):return self.process.stderr
    @property
    def returncode(self):return self.process.returncode
    def poll(self):return self.process.poll()
    def wait(self,timeout=None):return self.process.wait(timeout=timeout)

    def observe(self):
        require(not self.closed and self.job is not None, 'JOB_CLOSED')
        self.checkpoint()
        self._verify_parent_cpu()
        info=self.windows.accounting(self.job);self.profile['last_job_accounting']=info
        native.combined_private_budget(self.plan['memory_limit'],self.profile['pre_assignment_private_bytes'],
            info['peak_job_private_percent'],self.windows.total_ram)
        return info

    def close(self):
        if self.closed:
            require(self.profile['cleanup_confirmed'], 'PREVIOUS_CLEANUP_FAILED')
            return
        # No sampler/deadline/pressure check: cleanup remains available after a stop.
        require(self.process is None or self.process.poll() is not None, 'LIVE_WORKER_NO_FORCE_CLOSE')
        if self.job is not None:
            info=self.windows.accounting(self.job);self.profile['last_job_accounting']=info
            require(info['active_processes']==0, 'LIVE_TREE_NO_FORCE_CLOSE')
            self.profile['owned_tree_empty']=True
        if self.process is not None:
            self.process.wait(timeout=0)
            for stream in (self.process.stdin,self.process.stdout,self.process.stderr):stream.close()
        if self.job is not None:
            require(self.windows.k.CloseHandle(self.job), 'JOB_HANDLE_CLOSE')
            self.job=None;self.profile['job_handle_closed']=True
        self.closed=True;self.profile['cleanup_confirmed']=True
