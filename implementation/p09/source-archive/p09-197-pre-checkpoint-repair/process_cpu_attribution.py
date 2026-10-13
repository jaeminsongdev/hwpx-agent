"""Bounded, read-only CPU attribution. No stress workload or privileged retry.

원 보호 표본은 그대로 두고 1초 이상 간격의 프로세스 시간 차이를 덧붙인다.
명령줄/경로/환경/파일 내용/모듈/스레드 목록은 조회하지 않는다.
허용 목록 밖 실행파일 이름은 즉시 OTHER로 바꾼다. 원인 판정 도구가 아니다.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import io
import json
import sys
import time
import unittest
from unittest.mock import patch

import observe_shared_metadata_recheck as observation

c=observation.c
SELF='tools/p09/process_cpu_attribution.py'
TEST='tools/p09/tests/test_process_cpu_attribution.py'
MAX_PROCESSES=1024
MAX_SCAN_SECONDS=0.25
INTERVAL_SECONDS=1.0
TOP=8
LABELS={n.lower():n for n in ('git.exe','MsMpEng.exe','MsSense.exe','Codex.exe',
    'Code.exe','node.exe','python.exe','pythonw.exe','cargo.exe','rustc.exe',
    'vmmem','vmmemWSL','SearchIndexer.exe','powershell.exe','pwsh.exe','System')}
LABEL_VALUES=frozenset(LABELS.values())|{'OTHER'}
REFERENCES=[
    'https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot',
    'https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/ns-tlhelp32-processentry32w',
    'https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes']


def require(ok,code):c.require(ok,'CPU_ATTRIBUTION_'+code)


def label(name):return LABELS.get(name.lower(),'OTHER')


class Entry(ctypes.Structure):
    _fields_=[('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',ctypes.c_size_t),
        ('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),
        ('flags',w.DWORD),('name',w.WCHAR*260)]


class ProcessCPU:
    def __init__(self,k,times,clock=time.monotonic):
        self.k=k;self.times=times;self.clock=clock
        for name,args,result in (
            ('CreateToolhelp32Snapshot',[w.DWORD,w.DWORD],w.HANDLE),
            ('Process32FirstW',[w.HANDLE,ctypes.POINTER(Entry)],w.BOOL),
            ('Process32NextW',[w.HANDLE,ctypes.POINTER(Entry)],w.BOOL),
            ('GetProcessTimes',[w.HANDLE]+[ctypes.c_void_p]*4,w.BOOL)):
            fn=getattr(k,name);fn.argtypes=args;fn.restype=result

    def snapshot(self):
        started=self.clock();system=self.times();rows={};counts={};inaccessible=0
        handle=self.k.CreateToolhelp32Snapshot(2,0)  # PROCESS only, never SNAPALL.
        require(handle not in (None,0,ctypes.c_void_p(-1).value),'SNAPSHOT_FAILED')
        seen=0
        try:
            entry=Entry();entry.size=ctypes.sizeof(entry)
            ok=self.k.Process32FirstW(handle,ctypes.byref(entry))
            require(ok or ctypes.get_last_error()==18,'ENUM_FIRST_FAILED')
            while ok:
                seen+=1;require(seen<=MAX_PROCESSES,'PROCESS_LIMIT')
                require(self.clock()-started<=MAX_SCAN_SECONDS,'SCAN_TIME_LIMIT')
                name=label(entry.name);counts[name]=counts.get(name,0)+1
                process=self.k.OpenProcess(0x1000,False,entry.pid)  # QUERY_LIMITED only.
                if process:
                    try:
                        values=[ctypes.c_uint64() for _ in range(4)]
                        if self.k.GetProcessTimes(process,*(ctypes.byref(v) for v in values)):
                            rows[entry.pid]=(values[0].value,values[2].value+values[3].value,name)
                        else:inaccessible+=1
                    finally:require(self.k.CloseHandle(process),'PROCESS_HANDLE_CLOSE_FAILED')
                else:inaccessible+=1
                ok=self.k.Process32NextW(handle,ctypes.byref(entry))
            require(ctypes.get_last_error()==18,'ENUM_NEXT_FAILED')
        finally:require(self.k.CloseHandle(handle),'SNAPSHOT_HANDLE_CLOSE_FAILED')
        elapsed=self.clock()-started
        require(elapsed<=MAX_SCAN_SECONDS,'SCAN_TIME_LIMIT')
        return dict(system=system,rows=rows,counts=counts,inaccessible=inaccessible,
            scan_seconds=elapsed,time=self.clock())


def compare(before,after):
    delta=[b-a for a,b in zip(before['system'],after['system'])]
    require(len(delta)==3 and all(type(n) is int and n>=0 for n in delta)
        and delta[1]+delta[2]>0 and delta[0]<=delta[1]+delta[2],'SYSTEM_DELTA')
    denominator=delta[1]+delta[2];groups={};new_or_reused=0;reset=0
    for pid,(created,cpu,name) in after['rows'].items():
        require(name in LABEL_VALUES,'CLOSED_LABEL')
        old=before['rows'].get(pid)
        if old is None or old[0]!=created or old[2]!=name:
            new_or_reused+=1;continue
        if cpu<old[1]:reset+=1;continue
        item=groups.setdefault(name,dict(label=name,cpu_delta_100ns=0,matched_processes=0))
        item['cpu_delta_100ns']+=cpu-old[1];item['matched_processes']+=1
    for item in groups.values():
        item['machine_cpu_percent']=round(100*item['cpu_delta_100ns']/denominator,6)
    top=sorted(groups.values(),key=lambda x:(-x['cpu_delta_100ns'],x['label']))[:TOP]
    return dict(system_cpu_percent=round(100*(denominator-delta[0])/denominator,6),
        total_system_delta_100ns=denominator,top_cpu_groups=top,
        process_counts=after['counts'],inaccessible_processes=after['inaccessible'],
        newly_seen_or_reused_PIDs=new_or_reused,counter_reset_processes=reset,
        no_longer_readable_PIDs=len(set(before['rows'])-set(after['rows'])),
        scan_seconds=round(after['scan_seconds'],6),
        snapshot_interval_seconds=round(after['time']-before['time'],6),
        CPU_samples_not_atomic=True,all_system_CPU_attributed=False,
        exited_short_lived_protected_processes_and_kernel_work_may_be_missing=True,
        CPU_cause_or_PC_freeze_resolution_established=False)


class AttributionWindows(observation.ObservedWindows):
    def __init__(self,context):
        super().__init__(context);self.attribution=[];self.attribution_error=None
        self.process_cpu=ProcessCPU(self.k,self.times);self.previous=None;self.due=0

    def sample(self):
        row=super().sample()  # 원 .5초 CPU/RAM 표본과 stop 계산은 바꾸지 않는다.
        now=time.monotonic()
        if self.attribution_error is None and now>=self.due:
            try:
                current=self.process_cpu.snapshot()
                if self.previous is not None:
                    require(len(self.attribution)<600,'SAMPLE_LIMIT')
                    result=compare(self.previous,current);result['time_utc']=row['time_utc']
                    self.attribution.append(result)
                self.previous=current;self.due=time.monotonic()+INTERVAL_SECONDS
            except (ValueError,OSError,AttributeError) as error:
                # 관측 실패를 CPU=0으로 쓰거나 원 보호 검사를 무효화하지 않는다.
                self.attribution_error=str(error) if isinstance(error,ValueError) else 'CPU_ATTRIBUTION_NATIVE_FAILURE'
        return row


class Resources(observation.RAW_RESOURCES):
    def __init__(self,context):super().__init__(windows=AttributionWindows(context))


def summary(owner):
    windows=owner.windows
    return dict(samples=windows.attribution,error_code=windows.attribution_error,
        completed_intervals=len(windows.attribution),foreign_PID_CPU_query_executed=True,
        access_mask=0x1000,privilege_elevation_or_retry=False,
        command_line_path_environment_modules_threads_or_file_contents_queried=False,
        names_outside_allowlist_persisted=False,external_process_state_changed=False,
        maximum_processes_per_snapshot=MAX_PROCESSES,maximum_snapshot_seconds=MAX_SCAN_SECONDS,
        minimum_snapshot_interval_seconds=INTERVAL_SECONDS,maximum_intervals=600,
        new_sampler_thread_started=False,original_resource_policy_unchanged=True,
        CPU_cause_or_PC_freeze_resolution_established=False,official_references=REFERENCES)


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_process_cpu_attribution')
    with patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    require(result.wasSuccessful() and result.testsRun==10 and not result.skipped,'CONTRACT10')
    return 10


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','baseline'),required=True)
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=observation.old.s.scoped_path(
        f'implementation/p09/evidence/p09-197-process-cpu-{args.mode}-run{args.run:02}.v1.json',fresh=True)
    owner=None;q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',product_complete=False,P09_gate='OPEN',PC_freeze_resolved=False,
        product_child_or_stress_reproduction_executed=False)
    try:
        out['contract_tests_passed']=contracts()
        context=observation.Context()
        owner=Resources(context) if args.mode=='baseline' else observation.Resources(context)
        owner.admit();q=observation.RAW_READER(owner)
        for name in (SELF,TEST,observation.SELF):q.pin(name)
        if args.mode=='baseline':
            for _ in range(8):
                time.sleep(c.POLICY['sample_seconds']);owner.checkpoint()
        q.finish();out['state']='PASS_BOUNDED_CPU_ATTRIBUTION_'+args.mode.upper()+'_NOT_CAUSE_OR_GATE'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=observation.old.run.original.closed_error(error)
    finally:
        if owner is not None:
            observation.old.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
            if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
            out['own_and_system_observation']=observation.summary(owner)
            if args.mode=='baseline':
                out['process_cpu_attribution']=summary(owner)
                if owner.windows.attribution_error or not owner.windows.attribution:
                    out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':
    sys.modules.setdefault('process_cpu_attribution',sys.modules[__name__])
    raise SystemExit(main())
