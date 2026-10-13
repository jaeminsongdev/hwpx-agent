"""ALL original249 + qualified PDH group observations in the SAME owned Job.

No SQL/native/Git/builds/settings. Existing parent .5s guards, original1200s,
32768 per stream, source closure, exact EXE and original full result unchanged.
Diagnostic snapshots are bounded/explicitly partial; never individual attribution
for duplicate groups, never retroactive promotion of original stopped receipts.
"""
import argparse
import copy
from datetime import datetime,timezone,timedelta
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
import run_current_stored_full as original
import host_cpu_group_observer as group
import probe_host_cpu_groups as probe

c=original.c
SELF='tools/p09/run_observed_stored_full.py'
TEST='tools/p09/tests/test_observed_stored_full.py'
MARKER=b'P154_HOST_CPU:'
MAX_FRAME=2800
FRAME_BOUNDS=dict(ready=256,sample=MAX_FRAME,budget=128,closed=512)
MAX_SAVED=10
OBSERVATION_SECONDS=1.0
HOT_DIAGNOSTIC_PERCENT=80
BASE_CAPTURE=original.full.FullCapture
PARENT=dict(path='implementation/p09/evidence/p09-153-host-cpu-groups.closing-run02.v1.json',bytes=6501,
    sha256='0a56faecdfcc8351c5c6e2f7e54ad6fffeb974d085e0e979dfb2200f3afe25a9')
PASS='PASS_CURRENT_UNFILTERED_FULL249_WITH_BOUNDED_HOST_DIAGNOSTICS_NOT_SQL_NATIVE_OR_GATE'


def require(ok,code):c.require(ok,'P154_'+code)


def task_for(run):
    original.inventory.build.prepared.generation(run);return f'p154-observed-full-r{run:02}-tests'


def run_for(task):
    match=re.fullmatch(r'p154-observed-full-r([0-9]{2})-tests',task) if isinstance(task,str) else None
    require(match is not None,'TASK');run=int(match[1]);require(task_for(run)==task,'TASK');return run


def valid_record(row,worker_pid=None):
    require(type(row) is dict and row.get('kind') in ('ready','sample','budget','closed'),'RECORD_KIND')
    keys=dict(ready={'kind','worker_pid','test_pid','processor_count'},
        sample={'kind','worker_pid','test_pid','sequence','observed_at','collect_seconds','system_cpu_percent','observation'},
        budget={'kind','saved_samples','diagnostic_budget_limited'},
        closed={'kind','query_cleanup_confirmed','total_samples','saved_samples','high_samples','unsaved_high_samples','diagnostic_budget_limited'})
    require(set(row)==keys[row['kind']],'RECORD_KEYS')
    if row['kind'] in ('ready','sample'):
        for key in ('worker_pid','test_pid'):require(type(row[key]) is int and 1<=row[key]<=0xffffffff,'RECORD_PID')
        require(row['worker_pid']!=row['test_pid'] and (worker_pid is None or row['worker_pid']==worker_pid),'RECORD_OWNER')
    if row['kind']=='ready':require(type(row['processor_count']) is int and 1<=row['processor_count']<=64,'RECORD_PROCESSORS')
    if row['kind']=='sample':
        require(type(row['sequence']) is int and 1<=row['sequence']<=MAX_SAVED,'RECORD_SEQUENCE')
        value=row['system_cpu_percent'];require(type(value) in (float,int) and math.isfinite(value) and 0<=value<=100,'RECORD_HOST_CPU')
        require(type(row['observed_at']) is str and len(row['observed_at'])<=40,'RECORD_TIME')
        stamp=datetime.fromisoformat(row['observed_at']);require(stamp.tzinfo==timezone.utc,'RECORD_TIME')
        # Pure schema adapter ONLY; artificial duplicate is NOT evidence and is
        # never persisted. Reuse qualified group's exact field/number/PID checks.
        samples=[dict(sequence=i+1,observed_at=(stamp+timedelta(microseconds=i)).isoformat(),
            collect_seconds=row['collect_seconds'],observation=row['observation']) for i in range(2)]
        probe.validate_payload(dict(schema_version='hwpx-agent.p09-host-cpu-observer-probe/v1',
            state='PASS_TWO_NATIVE_SAMPLES_ONLY',worker_pid=row['worker_pid'],query_cleanup_confirmed=True,
            query_count=1,samples=samples,causal_attribution=False,raw_process_names_saved=False,commands_paths_saved=False))
    if row['kind']=='budget':
        require(type(row['saved_samples']) is int and row['saved_samples']==MAX_SAVED and row['diagnostic_budget_limited'] is True,'RECORD_BUDGET')
    if row['kind']=='closed':
        for key in ('total_samples','saved_samples','high_samples','unsaved_high_samples'):
            require(type(row[key]) is int and 0<=row[key]<=1201,'RECORD_COUNTS')
        require(row['query_cleanup_confirmed'] is True and 1<=row['saved_samples']<=MAX_SAVED
            and row['saved_samples']<=row['total_samples'] and row['unsaved_high_samples']<=row['high_samples']<=row['total_samples']
            and row['diagnostic_budget_limited']==(row['unsaved_high_samples']>0)
            and type(row['diagnostic_budget_limited']) is bool,'RECORD_CLOSING')
    return row


def emit(row):
    valid_record(row);raw=MARKER+json.dumps(row,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n'
    require(len(raw)<=FRAME_BOUNDS[row['kind']],'FRAME_BOUND');sys.stderr.write(raw.decode('ascii'));sys.stderr.flush()


def observed_call(args,**kw):
    require(args==[str(c.ROOT/original.inventory.build.executable_name(1)),'--test-threads=1','--format=terse']
        and kw.get('cwd')==c.ROOT and kw.get('stdin')==subprocess.DEVNULL and kw['env'].get('RUST_TEST_NOCAPTURE')=='0','EXACT_EXE_UNFILTERED')
    windows=c.Windows();member=c.w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(),None,c.ctypes.byref(member)) and member.value,'OWNED_BEFORE_QUERY')
    observer=group.Observer(windows.processors);process=None;total=saved=high=unsaved=0;budget=False
    try:
        require(observer.collect() is None,'QUERY_WARM')
        process=subprocess.Popen(args,**kw)
        emit(dict(kind='ready',worker_pid=os.getpid(),test_pid=process.pid,processor_count=windows.processors))
        while True:
            # Provider calls stay inside Job; parent guards remain responsive.
            time.sleep(OBSERVATION_SECONDS);started=time.monotonic()
            snapshot=observer.collect((os.getpid(),));elapsed=time.monotonic()-started
            require(snapshot is not None and snapshot['stable_candidate_count']>0,'QUERY_SAMPLE')
            host=windows.sample()['system_cpu_percent'];total+=1;hot=host>=HOT_DIAGNOSTIC_PERCENT;high+=int(hot)
            if saved<2 or (hot and saved<MAX_SAVED):
                saved+=1;emit(dict(kind='sample',worker_pid=os.getpid(),test_pid=process.pid,sequence=saved,
                    observed_at=datetime.now(timezone.utc).isoformat(),collect_seconds=elapsed,
                    system_cpu_percent=host,observation=snapshot))
            elif hot:
                unsaved+=1
                if not budget:emit(dict(kind='budget',saved_samples=saved,diagnostic_budget_limited=True));budget=True
            result=process.poll()
            if result is not None:break
    finally:observer.close()
    emit(dict(kind='closed',query_cleanup_confirmed=True,total_samples=total,saved_samples=saved,
        high_samples=high,unsaved_high_samples=unsaved,diagnostic_budget_limited=bool(unsaved)))
    return result


def worker(task):
    run=run_for(task)
    # Immutable old worker checks GO/Job, full Cargo-contract argv and original
    # env before delegating ONLY its direct fresh EXE call to observed_call.
    with patch.object(subprocess,'call',observed_call):return original.worker(original.task_for(run))


class Capture(BASE_CAPTURE):
    def __init__(self,*args,**kw):
        self.records=[];self.observer_pending=bytearray();self.observer_error=None;self.observer_closed=False
        super().__init__(*args,**kw)

    def _accept(self,name,chunk):
        super()._accept(name,chunk)
        if name!='stderr':return
        with self.lock:
            if self.observer_error:return
            self.observer_pending.extend(chunk)
            try:
                while b'\n' in self.observer_pending:
                    raw,_,tail=self.observer_pending.partition(b'\n');self.observer_pending=bytearray(tail)
                    if not raw.startswith(MARKER):continue  # Do not save raw test/panic text.
                    require(len(raw)+1<=MAX_FRAME and len(self.records)<MAX_SAVED+3,'FRAME_BOUND')
                    row=valid_record(json.loads(raw[len(MARKER):]),self.process.pid)
                    kind=row['kind'];require(len(raw)+1<=FRAME_BOUNDS[kind],'FRAME_KIND_BOUND')
                    require(not self.observer_closed,'AFTER_CLOSED')
                    if kind=='ready':require(not self.records,'READY_FIRST')
                    else:require(self.records and self.records[0]['kind']=='ready','READY_MISSING')
                    if kind=='sample':
                        ready=self.records[0];samples=[r for r in self.records if r['kind']=='sample']
                        require(row['test_pid']==ready['test_pid'] and row['observation']['processor_count']==ready['processor_count']
                            and row['sequence']==len(samples)+1 and (not samples or row['observed_at']>samples[-1]['observed_at']),'SAMPLE_BINDING')
                    if kind=='budget':require(not any(r['kind']=='budget' for r in self.records),'DUPLICATE_BUDGET')
                    if kind=='closed':
                        require(row['saved_samples']==sum(r['kind']=='sample' for r in self.records)
                            and row['diagnostic_budget_limited']==any(r['kind']=='budget' for r in self.records),'CLOSING_MATCH')
                        self.observer_closed=True
                    self.records.append(row)
                require(len(self.observer_pending)<=MAX_FRAME,'FRAME_PENDING_BOUND')
            except (ValueError,KeyError,TypeError,AttributeError,OverflowError):
                self.observer_error='P154_CLOSED_DIAGNOSTIC_REJECTED';self.error='live_progress_marker_scope'

    def communicate(self,timeout):
        output,errors=super().communicate(timeout)
        if self.process.returncode==0:
            require(self.observer_closed and not self.observer_error and not self.observer_pending,'QUERY_CLOSING_REQUIRED')
            require(1<=sum(r['kind']=='sample' for r in self.records)<=MAX_SAVED,'ACTUAL_SAMPLE_REQUIRED')
        return output,errors

    def diagnostics(self):
        out=super().diagnostics()
        with self.lock:
            out.update(host_cpu_records=copy.deepcopy(self.records),host_cpu_error_code=self.observer_error,
                explicit_query_cleanup_confirmed=self.observer_closed,diagnostic_snapshots_max=MAX_SAVED,
                diagnostic_frame_limit=MAX_FRAME,raw_names_paths_commands_saved=False,causal_attribution=False)
        return out


def load_binding():
    binding=original.load_binding();expected=binding[0]
    resources=original.inventory.build.prepared.SQLRuntimeResources();out={}
    try:
        resources.admit();q=original.inventory.build.prepared.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_QUALIFIED_OBSERVER')
        parent=q.json(PARENT['path']);require(parent['state']=='PASS_NATIVE_GROUP_OBSERVER_CLOSING_ONLY_NOT_FULL249_OR_GATE'
            and parent['source_closing_exact'] and parent['contract_tests_passed']==65 and parent['accepted_observer_only']
            and parent['PC_freeze_resolved'] is False and parent['full249_current_qualified'] is False,'PARENT_SCOPE')
        for pin in parent['bound_input_pins']:
            require(q.pin(pin['path'])==pin,'CURRENT_OBSERVER_SOURCE_DRIFT');expected[pin['path']]=pin
        for name in (SELF,TEST,PARENT['path']):expected[name]=q.pin(name)
        q.finish();return binding
    finally:require(original.inventory.build.prepared.finish_watcher(resources,out),'BINDING_WATCHER_CLEANUP')


def run_owned(run,destination,*binding):
    dump=json.dump
    def write(row,stream,**kw):
        if row['state']==original.PASS:row['state']=PASS
        row.update(schema_version='hwpx-agent.p09-observed-current-full249/v1',host_observer_closing_pin=PARENT,
            observed_same_owned_job=True,observer_collection_seconds=OBSERVATION_SECONDS,
            diagnostic_only_hot_threshold=HOT_DIAGNOSTIC_PERCENT,original_emergency_cpu_guard_unchanged=True,
            observer_calls_outside_parent_guard=False,diagnostic_snapshots_max=MAX_SAVED,
            diagnostic_snapshots_are_not_complete_host_process_history=True,individual_duplicated_PID_attribution=False)
        return dump(row,stream,**kw)
    with patch.object(original,'SELF',SELF),patch.object(original,'TEST',TEST),patch.object(original,'task_for',task_for), \
            patch.object(original.full,'FullCapture',Capture),patch.object(json,'dump',write):
        return original.run_owned(run,destination,*binding)


def light(run):
    destination=original.inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-154-observed-full.light-run{run:02}.v1.json',fresh=True)
    resources=original.inventory.build.prepared.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=original.inventory.build.prepared.LiveSQLReader(resources)
        for name in (SELF,TEST,*probe.FILES):q.pin(name)
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_observed_stored_full','test_current_stored_full','test_compression_full_stored','test_host_cpu_groups'))
        with patch('subprocess.Popen',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('LIGHT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed=sorted({getattr(t,'test_case',t).id().split('.')[-1] for t,_ in checked.failures+checked.errors+checked.skipped})
        passed=checked.wasSuccessful() and checked.testsRun==55 and not checked.skipped
        q.finish();out.update(state='PASS_OBSERVED_FULL249_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            contract_tests_run=checked.testsRun,contract_tests_passed=checked.testsRun-len(failed),failed_tests=failed,
            source_closing_exact=True,actual_EXE_SQL_native_executed=False,full249_current_qualified=False,
            signed16_current_qualified=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:out['error_code']=original.closed_error(error)
    finally:
        original.inventory.build.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_run','contract_tests_passed','failed_tests','error_code')}))
    return 0 if out['state'].startswith('PASS_') else 2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--mode',choices=('light','actual'),required=True);args=parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD');original.require_scope(1200);task_for(args.run)
    if args.mode=='light':return light(args.run)
    destination=original.inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-154-observed-full.actual-run{args.run:02}.v1.json',fresh=True)
    return run_owned(args.run,destination,*load_binding())


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        print('P154_CLOSED_WORKER_FAILURE' if '--owned-worker' in sys.argv else original.closed_error(error));raise SystemExit(2) from None
