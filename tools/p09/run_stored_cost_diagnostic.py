"""Unfiltered current249, PRETTY pipe case cost/churn diagnostic, max180s.

Does NOT replace original1200s full qualification; always full249/signed16false.
No test body/source/check changes, no fresh Cargo, no external settings/native UI.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import run_observed_stored_full as s
import stored_cost_observation as observation

c=s.c
SELF='tools/p09/run_stored_cost_diagnostic.py'
TEST='tools/p09/tests/test_stored_cost_observation.py'
PARENT=dict(path='implementation/p09/evidence/p09-154-observed-full.terminal-audit-run01.v1.json',bytes=350671,
    sha256='edbd9c643c30c1d2cf965fabbb4df4b0b0729a5b85f1f5778f15236602075964')
MAXIMUM_SECONDS=180
SAVED=6
CHURN=b'P155_CHURN:'
CHURN_FRAME=1400


def require(ok,code):c.require(ok,'P155_'+code)


def task_for(run):
    s.original.inventory.build.prepared.generation(run);return f'p155-stored-cost-r{run:02}-diagnostic'


def run_for(task):
    match=re.fullmatch(r'p155-stored-cost-r([0-9]{2})-diagnostic',task) if isinstance(task,str) else None
    require(match is not None,'TASK');run=int(match[1]);require(task_for(run)==task,'TASK');return run


def worker(task):
    run=run_for(task);popen=subprocess.Popen;emit=s.emit;observers=[]
    class Observer(observation.ChurnObserver):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);observers.append(self)
    def selected(args,**kw):
        expected=[str(c.ROOT/s.original.inventory.build.executable_name(1)),'--test-threads=1','--format=terse']
        require(args==expected and kw.get('cwd')==c.ROOT and kw.get('stdin')==subprocess.DEVNULL,'EXACT_EXISTING_EXE')
        return popen([*args[:-1],'--format=pretty','--color=never'],**kw)
    def observed_emit(row):
        emit(row)
        if row['kind']=='sample':
            require(len(observers)==1 and observers[0].last_churn is not None,'CHURN_QUERY_BINDING')
            extra=dict(worker_pid=row['worker_pid'],test_pid=row['test_pid'],sequence=row['sequence'],
                observed_at=row['observed_at'],churn=observation.valid_churn(observers[0].last_churn))
            raw=CHURN+json.dumps(extra,separators=(',',':'),ensure_ascii=True).encode('ascii')+b'\n'
            require(len(raw)<=CHURN_FRAME,'CHURN_FRAME_BOUND');sys.stderr.write(raw.decode('ascii'));sys.stderr.flush()
    with patch.object(s,'MAX_SAVED',SAVED),patch.object(s.group,'Observer',Observer), \
            patch.object(s,'emit',observed_emit),patch.object(subprocess,'Popen',selected):return s.worker(s.task_for(run))


def load_binding():
    resources=s.original.inventory.build.prepared.SQLRuntimeResources();state={}
    try:
        resources.admit();q=s.original.inventory.build.prepared.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_FULL_STOP_CLOSING');parent=q.json(PARENT['path'])
        require(parent['state']=='PASS_OBSERVED_FULL249_STOP_ACCOUNTED_NOT_RUNTIME_SQL_NATIVE_OR_GATE'
            and parent['source_closing_exact'] and parent['contract_tests_passed']==55
            and parent['original_stop_reason']=='STOP_DURATION_LIMIT' and parent['protected_EXE_inputs_exact']==60
            and parent['full249_current_qualified'] is False and parent['signed16_current_qualified'] is False,'PARENT_NOT_GATE')
        expected=s.original.inventory.build.prepared.inputs.inventory(parent['bound_input_pins'],1233)
        for name,pin in expected.items():require(q.pin(name)==pin,'WHOLE_CURRENT_PARENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.original.inventory.build.prepared.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        def read(name):require(name in expected,'MODULE_SCOPE');return q.text(name)
        names,modules=s.original.inventory.PARENT.recursive_names(read,'stored-form-tests');s.original.full.cost.original.select_names(names)
        require(list(names)==parent['source_test_names'] and list(modules)==parent['source_module_instances'] and len(modules)==59,'ALL249_59')
        exe=parent['compiled_test_executable_pin'];require(q.pin(exe['path'])==exe
            and exe['path']==s.original.inventory.build.executable_name(1),'EXACT_EXE')
        for name in (SELF,TEST,'tools/p09/stored_cost_observation.py',PARENT['path']):expected[name]=q.pin(name)
        q.finish();return expected,names,modules,exe
    finally:require(s.original.inventory.build.prepared.finish_watcher(resources,state),'BINDING_WATCHER_CLEANUP')


def run_owned(run,destination,expected,names,modules,exe):
    task=task_for(run);raw_pins=c.pins;dump=json.dump;captures=[];admitted=False
    class Capture(s.Capture):
        def __init__(self,*a,**kw):
            self.trace=observation.CaseTrace(tuple(names));self.churn_pending=bytearray();self.churn_records=[]
            super().__init__(*a,**kw);captures.append(self)
        def _accept(self,name,chunk):
            super()._accept(name,chunk)
            with self.lock:
                try:
                    if name=='stdout':self.trace.feed(bytes(chunk),time.monotonic()-self.started)
                    else:
                        self.churn_pending.extend(chunk)
                        while b'\n' in self.churn_pending:
                            raw,_,tail=self.churn_pending.partition(b'\n');self.churn_pending=bytearray(tail)
                            if not raw.startswith(CHURN):continue
                            require(len(raw)+1<=CHURN_FRAME and len(self.churn_records)<SAVED,'CHURN_BOUND')
                            row=json.loads(raw[len(CHURN):]);require(set(row)=={'worker_pid','test_pid','sequence','observed_at','churn'},'CHURN_KEYS')
                            observation.valid_churn(row['churn'])
                            snapshots=[r for r in self.records if r['kind']=='sample'];index=len(self.churn_records)
                            require(len(snapshots)>index and row['worker_pid']==self.process.pid
                                and row['sequence']==index+1 and all(row[k]==snapshots[index][k] for k in ('worker_pid','test_pid','sequence','observed_at')),'CHURN_SAMPLE_BINDING')
                            self.churn_records.append(row)
                        require(len(self.churn_pending)<=s.MAX_FRAME,'CHURN_PENDING_BOUND')
                except (ValueError,KeyError,TypeError,AttributeError):
                    self.observer_error='P155_CLOSED_CASE_OR_CHURN_REJECTED';self.error='live_progress_marker_scope'
        def diagnostics(self):
            row=super().diagnostics()
            with self.lock:row.update(case_progress=self.trace.snapshot(time.monotonic()-self.started),
                churn_identity_records=list(self.churn_records),raw_case_or_process_output_saved=False)
            return row
    def pins(checkpoint=None):
        nonlocal admitted
        value=raw_pins(checkpoint);seen={p['path']:p for p in value}
        require(all(seen.get(n)==p for n,p in expected.items()),'FRESH_WHOLE_CURRENT_INPUT')
        if not admitted:
            resources=s.original.inventory.build.prepared.SQLRuntimeResources();state={}
            try:resources.admit();admitted=True
            finally:require(s.original.inventory.build.prepared.finish_watcher(resources,state),'POST_HASH_WATCHER_CLEANUP')
        return value
    def write(row,stream,**kw):
        if row['state']=='PASS_SCOPED_NOT_GATE':row['state']='DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE'
        row.update(schema_version='hwpx-agent.p09-unfiltered-stored-case-cost-diagnostic/v1',diagnostic_only=True,
            original_full_qualification_seconds=1200,full249_current_qualified=False,signed16_current_qualified=False,tests_passed=None,
            current_Rust_input_count=785,source_test_names=list(names),selected_test_names=list(names),source_module_instances=list(modules),
            compiled_test_executable_pin=exe,immutable_full_stop_closing_pin=PARENT,current_compiled249_qualified=True,
            actual_test_format='pretty',original_all249_unfiltered_single_thread_nocapture0=True,
            actual_new_Cargo_compile_executed=False,native_or_SQL_run=False,original_test_bodies_or_product_sources_changed=False,
            post_hash_runtime_admission_revalidated=admitted,diagnostic_frame_max=SAVED,churn_frame_limit=CHURN_FRAME,
            capture_diagnostics=captures[-1].diagnostics() if captures else None,raw_logs_printed_or_saved=False,
            PC_freeze_resolved=False,remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{task:[]}), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(s.original.full.bounded,'BoundedProcessCapture',Capture),patch.object(s,'MAX_SAVED',SAVED),patch.object(json,'dump',write):
        return c.run(task,destination,MAXIMUM_SECONDS)


def light(run):
    resources=s.original.inventory.build.prepared.SQLRuntimeResources();q=None;row=dict(state='FAILED_NOT_ACCEPTED')
    destination=s.original.inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-155-stored-cost.light-run{run:02}.v1.json',fresh=True)
    try:
        resources.admit();q=s.original.inventory.build.prepared.LiveSQLReader(resources)
        for name in (SELF,TEST,'tools/p09/stored_cost_observation.py',s.SELF,s.TEST):q.pin(name)
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_stored_cost_observation','test_observed_stored_full','test_current_stored_full','test_compression_full_stored','test_host_cpu_groups'))
        with patch('subprocess.Popen',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('LIGHT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed=sorted({getattr(t,'test_case',t).id().split('.')[-1] for t,_ in checked.failures+checked.errors+checked.skipped})
        passed=checked.wasSuccessful() and checked.testsRun==75 and not checked.skipped;q.finish()
        row.update(state='PASS_UNFILTERED_CASE_COST_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            contract_tests_run=checked.testsRun,contract_tests_passed=checked.testsRun-len(failed),failed_tests=failed,
            source_closing_exact=True,actual_EXE_or_native_counter_run=False,full249_current_qualified=False,
            signed16_current_qualified=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:row['error_code']=s.original.closed_error(error)
    finally:
        s.original.inventory.build.prepared.finish_watcher(resources,row);row['resource_stop_reason']=resources.reason
        if resources.reason or not row.get('resource_watcher_cleanup_confirmed'):row['state']='FAILED_NOT_ACCEPTED'
        if q is not None:row.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
        print(json.dumps({k:row.get(k) for k in ('state','contract_tests_run','contract_tests_passed','failed_tests','error_code')}))
    return 0 if row['state'].startswith('PASS_') else 2


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=int,choices=range(1,100),required=True);p.add_argument('--mode',choices=('light','actual'),required=True);args=p.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD');task_for(args.run)
    if args.mode=='light':return light(args.run)
    dest=s.original.inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-155-stored-cost.actual-run{args.run:02}.v1.json',fresh=True)
    return run_owned(args.run,dest,*load_binding())


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        print('P155_CLOSED_WORKER_FAILURE' if '--owned-worker' in sys.argv else s.original.closed_error(error));raise SystemExit(2) from None
