"""Two native PDH samples in the existing owned Job; not full249 or product QA."""
import argparse
import ctypes
from ctypes import wintypes as w
from datetime import datetime,timezone
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import conservative_maintenance as c
import bounded_process_progress as bounded
import host_cpu_observer as observer

SELF='tools/p09/probe_host_cpu_observer.py'
FILES=(SELF,'tools/p09/host_cpu_observer.py','tools/p09/tests/test_host_cpu_observer.py',
    'tools/p09/tests/test_probe_host_cpu_observer.py','tools/p09/conservative_maintenance.py',
    'tools/p09/bounded_process_progress.py','tools/p09/audit_evidence_io.py')
PASS='PASS_NATIVE_HOST_CPU_OBSERVER_TWO_SAMPLES_ONLY_NOT_FULL249_OR_GATE'


def require(ok,code):observer.require(ok,'PROBE_'+code)


def task_for(run):
    require(type(run) is int and 1<=run<=99,'RUN');return f'p153-host-cpu-observer-r{run:02}'


def fresh_pins(checkpoint=None):
    pins=[]
    for name in FILES:
        digest=hashlib.sha256();size=0
        with (c.ROOT/name).open('rb') as stream:
            while chunk:=stream.read(65536):
                started=time.monotonic();digest.update(chunk);size+=len(chunk)
                if checkpoint:checkpoint()
                time.sleep(max(0,len(chunk)/(8*1048576)-(time.monotonic()-started)))
        require(size<=131072,'HELPER_FILE_BOUND');pins.append(dict(path=name,bytes=size,sha256=digest.hexdigest()))
    return pins


def worker(task):
    match=re.fullmatch(r'p153-host-cpu-observer-r([0-9]{2})',task)
    require(match is not None and task_for(int(match[1]))==task,'TASK')
    require(sys.stdin.readline()=='P149_GO\n','GO')
    windows=c.Windows();member=w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(),None,ctypes.byref(member)) and member.value,'OWNED_JOB')
    o=observer.Observer(windows.processors);snapshots=[];closed=False
    try:
        require(o.collect() is None,'WARM_BASELINE')
        for number in range(2):
            time.sleep(1);started=time.monotonic();sample=o.collect((os.getpid(),))
            require(sample is not None and sample['stable_candidate_count']>0,'NATIVE_SAMPLE')
            snapshots.append(dict(sequence=number+1,observed_at=datetime.now(timezone.utc).isoformat(),
                collect_seconds=time.monotonic()-started,observation=sample))
    finally:
        o.close();closed=True
    row=dict(schema_version='hwpx-agent.p09-host-cpu-observer-probe/v1',state='PASS_TWO_NATIVE_SAMPLES_ONLY',
        worker_pid=os.getpid(),query_cleanup_confirmed=closed,query_count=1,samples=snapshots,
        causal_attribution=False,raw_process_names_saved=False,commands_paths_saved=False)
    validate_payload(row);print(json.dumps(row,separators=(',',':')));return 0


def exact_keys(row,names):require(type(row) is dict and set(row)==set(names),'OUTPUT_KEYS')


def validate_payload(row):
    exact_keys(row,('schema_version','state','worker_pid','query_cleanup_confirmed','query_count','samples',
        'causal_attribution','raw_process_names_saved','commands_paths_saved'))
    require(row['schema_version']=='hwpx-agent.p09-host-cpu-observer-probe/v1' and row['state']=='PASS_TWO_NATIVE_SAMPLES_ONLY'
        and type(row['worker_pid']) is int and 1<=row['worker_pid']<=0xffffffff and row['query_cleanup_confirmed'] is True
        and type(row['query_count']) is int and row['query_count']==1
        and row['causal_attribution'] is False and row['raw_process_names_saved'] is False and row['commands_paths_saved'] is False,'OUTPUT_SCOPE')
    require(type(row['samples']) is list and len(row['samples'])==2,'OUTPUT_SAMPLES')
    previous=None
    for index,sample in enumerate(row['samples']):
        exact_keys(sample,('sequence','observed_at','collect_seconds','observation'))
        require(type(sample['sequence']) is int and sample['sequence']==index+1,'SEQUENCE')
        require(isinstance(sample['observed_at'],str) and len(sample['observed_at'])<=40,'TIMESTAMP')
        stamp=datetime.fromisoformat(sample['observed_at']);require(stamp.tzinfo==timezone.utc and (previous is None or stamp>previous),'TIMESTAMP')
        previous=stamp
        elapsed=sample['collect_seconds'];require(type(elapsed) in (float,int) and math.isfinite(elapsed) and 0<=elapsed<30,'COLLECT_SECONDS')
        snap=sample['observation']
        exact_keys(snap,('processor_count','cpu_instance_count','pid_instance_count','stable_candidate_count',
            'unavailable_instances','unstable_instances','top','causal_attribution'))
        require(type(snap['processor_count']) is int and 1<=snap['processor_count']<=64 and snap['causal_attribution'] is False,'PROCESSOR_SCOPE')
        for name in ('cpu_instance_count','pid_instance_count','stable_candidate_count','unavailable_instances','unstable_instances'):
            require(type(snap[name]) is int and 0<=snap[name]<=observer.MAX_ITEMS,'INSTANCE_SCOPE')
        require(snap['stable_candidate_count']>0 and snap['cpu_instance_count']>=snap['stable_candidate_count']
            +snap['unavailable_instances']+snap['unstable_instances'] and snap['pid_instance_count']>=snap['stable_candidate_count'],'INSTANCE_ACCOUNTING')
        require(type(snap['top']) is list and len(snap['top'])==min(observer.TOP,snap['stable_candidate_count']),'TOP_BOUND')
        seen=set();sortkeys=[]
        for item in snap['top']:
            exact_keys(item,('pid','role','owned','processor_time_raw_percent','machine_cpu_percent'))
            require(type(item['pid']) is int and 1<=item['pid']<=0xffffffff and item['pid'] not in seen,'PID_SCOPE');seen.add(item['pid'])
            require(item['role'] in observer.ROLES and type(item['owned']) is bool and item['owned']==(item['pid']==row['worker_pid']),'ROLE_SCOPE')
            for name in ('processor_time_raw_percent','machine_cpu_percent'):
                require(type(item[name]) in (float,int) and math.isfinite(item[name]) and item[name]>=0,'CPU_SCOPE')
            require(math.isclose(item['machine_cpu_percent'],item['processor_time_raw_percent']/snap['processor_count'],rel_tol=1e-12,abs_tol=1e-12),'NORMALIZATION')
            sortkeys.append((-item['machine_cpu_percent'],item['pid']))
        require(sortkeys==sorted(sortkeys),'TOP_ORDER')
    return row


def actual(run,destination):
    task=task_for(run);dump=json.dump;captures=[];accepted_final=False
    class Capture(bounded.BoundedProcessCapture):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.payload=None;self.failure_code=None;captures.append(self)
        def communicate(self,timeout):
            output,errors=super().communicate(timeout)
            require(errors=='' and len(output.encode('utf-8'))<=16384,'BOUNDED_CLOSED_OUTPUT')
            if self.process.returncode==0:self.payload=validate_payload(json.loads(output))
            else:
                require(re.fullmatch(r'P153_[A-Z_]{1,120}\s*',output) is not None,'CLOSED_FAILURE_CODE')
                self.failure_code=output.strip()
            return output,errors
    def write(row,stream,**kw):
        nonlocal accepted_final
        payload=captures[-1].payload if captures else None
        accepted_final=row['state']=='PASS_SCOPED_NOT_GATE' and payload is not None and row['owned_tree_empty'] and row['cleanup_confirmed']
        if row['state']=='PASS_SCOPED_NOT_GATE':row['state']=PASS if accepted_final else 'STOPPED_NOT_ACCEPTED'
        row.update(schema_version='hwpx-agent.p09-native-host-cpu-observer/v1',observer_probe=payload,
            observer_query_cleanup_confirmed=bool(payload and payload['query_cleanup_confirmed']),
            observer_failure_code=captures[-1].failure_code if captures else None,
            raw_process_names_saved=False,commands_paths_saved=False,causal_attribution=False,
            full249_current_qualified=False,signed16_current_qualified=False,PC_freeze_resolved=False,
            Rust_or_test_body_executed=False,remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{task:[]}), \
            patch.object(c,'pins',fresh_pins),patch.object(bounded,'BoundedProcessCapture',Capture),patch.object(json,'dump',write):
        code=c.run(task,destination,30)
    return 0 if accepted_final else code


def light(destination):
    c.Windows();before=fresh_pins();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name)
        for name in ('test_host_cpu_observer','test_probe_host_cpu_observer'))
    with patch('subprocess.Popen',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failed=sorted({test.id().split('.')[-1] for test,_ in result.failures+result.errors+result.skipped})
    after=fresh_pins();accepted=result.wasSuccessful() and result.testsRun==28 and not result.skipped and before==after
    row=dict(state='PASS_HOST_CPU_OBSERVER_CONTRACTS_ONLY_NOT_NATIVE_OR_GATE' if accepted else 'FAILED_NOT_ACCEPTED',
        tests_run=result.testsRun,tests_passed=result.testsRun-len(failed),failed_tests=failed,source_closing_exact=before==after,
        bound_input_pins=after,actual_native_counter_run=False,product_complete=False,P09_gate='OPEN')
    with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row[k] for k in ('state','tests_run','tests_passed','failed_tests')}));return 0 if accepted else 2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    parser.add_argument('--run',type=int,choices=range(1,100),required=True);args=parser.parse_args();task_for(args.run)
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD')
    destination=c.ROOT/f'implementation/p09/evidence/p09-153-host-cpu-observer.{args.mode}-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_RECEIPT')
    return light(destination) if args.mode=='light' else actual(args.run,destination)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) else ''
        print(code if re.fullmatch(r'P153_[A-Z_]{1,120}',code) else 'P153_REDACTED_NOT_ACCEPTED');raise SystemExit(2) from None
