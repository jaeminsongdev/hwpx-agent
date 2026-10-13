"""Current graph product compile, same owned Job + bounded qualified PDH.

No stale EXE/listing promotion. Preserve P157 stopped receipt; fresh suffix r03.
"""
import argparse
import io
import json
import os
import sys
import time
import unittest
from unittest.mock import patch
import build_immutable_graph_product as p
import run_observed_stored_full as observed

SELF='tools/p09/build_observed_graph_product.py'
TEST='tools/p09/tests/test_observed_graph_product_build.py'
RUN=3
STOP_PIN=dict(path='implementation/p09/evidence/p09-157-immutable-graph-product-build.terminal-audit-run01.v1.json',
    bytes=356793,sha256='f3b990f6fd0842984e0e7a4baed4ae9ed04d89d9f9c04e8e3b88dee6a6562641')
PASS='PASS_CURRENT_GRAPH_PRODUCT_OBSERVED_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
RAW_STREAM=p.b.legacy.stream.run_command
RAW_CAPTURE=p.b.legacy.RAW_CAPTURE
CONTRACT_COUNT=46


def require(ok,code):p.require(ok,'OBSERVED_'+code)


class Pump:
    """No thread/child; poll-time sampling stays inside the guarded worker Job."""
    def __init__(self,process,observer,windows,worker_pid,clock=time.monotonic,emit=observed.emit):
        self.process,self.observer,self.windows=process,observer,windows
        self.worker_pid,self.clock,self.emit=worker_pid,clock,emit
        self.last=clock();self.total=self.saved=self.high=self.unsaved=0;self.budget=False
        emit(dict(kind='ready',worker_pid=worker_pid,test_pid=process.pid,processor_count=windows.processors))

    def __getattr__(self,name):return getattr(self.process,name)

    def poll(self):
        result=self.process.poll();now=self.clock()
        if now-self.last>=observed.OBSERVATION_SECONDS or (result is not None and self.total==0):
            started=self.clock();snap=self.observer.collect((self.worker_pid,));elapsed=self.clock()-started
            require(snap is not None and snap['stable_candidate_count']>0,'NATIVE_SAMPLE')
            host=self.windows.sample()['system_cpu_percent'];self.total+=1;hot=host>=observed.HOT_DIAGNOSTIC_PERCENT;self.high+=int(hot)
            if self.saved<2 or (hot and self.saved<observed.MAX_SAVED):
                self.saved+=1;self.emit(dict(kind='sample',worker_pid=self.worker_pid,test_pid=self.process.pid,sequence=self.saved,
                    observed_at=observed.datetime.now(observed.timezone.utc).isoformat(),collect_seconds=elapsed,
                    system_cpu_percent=host,observation=snap))
            elif hot:
                self.unsaved+=1
                if not self.budget:self.emit(dict(kind='budget',saved_samples=self.saved,diagnostic_budget_limited=True));self.budget=True
            self.last=self.clock()
        return result

    def closing(self):
        self.emit(dict(kind='closed',query_cleanup_confirmed=True,total_samples=self.total,saved_samples=self.saved,
            high_samples=self.high,unsaved_high_samples=self.unsaved,diagnostic_budget_limited=bool(self.unsaved)))


def observed_stream(args,kwargs,validator):
    require(args[1:]==p.s.recipe(RUN)['argv_without_cargo'] and kwargs.get('cwd')==p.c.ROOT
        and kwargs.get('stdin')==p.b.subprocess.DEVNULL,'EXACT_COMPILER_SCOPE')
    windows=p.c.Windows();member=p.c.w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(),None,p.c.ctypes.byref(member)) and member.value,'JOB_BEFORE_COUNTER')
    observer=observed.group.Observer(windows.processors);pump=None
    try:
        require(observer.collect() is None,'QUERY_WARM')
        def factory(*a,**kw):
            nonlocal pump
            require(pump is None,'ONE_CARGO_PROCESS')
            pump=Pump(p.b.subprocess.Popen(*a,**kw),observer,windows,os.getpid());return pump
        return RAW_STREAM(args,kwargs,validator,process_factory=factory)
    finally:
        observer.close()
        if pump is not None and pump.saved:pump.closing()


class DiagnosticCapture(observed.Capture):
    def communicate(self,timeout):
        # Do not invoke the inherited full249 result parser on Cargo JSON.
        # Same bounded pipe reader/marker parser, original build parser follows.
        output,errors=RAW_CAPTURE.communicate(self,timeout)
        if self.process.returncode==0:
            require(self.observer_closed and not self.observer_error and not self.observer_pending
                and 1<=sum(r['kind']=='sample' for r in self.records)<=observed.MAX_SAVED,'QUERY_CLOSING_REQUIRED')
        return output,errors


def worker(task):
    require(task==p.b.task_for(RUN),'CLOSED_WORKER_TASK')
    with patch.object(p.b.legacy.stream,'run_command',observed_stream):return p.b.worker(task)


def contracts():
    p.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_graph_product_build')
    with patch('subprocess.Popen',side_effect=AssertionError('P158_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P158_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P158_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==10 and not result.skipped,'CONTRACT10_PLUS36')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)


def fresh_scope(protected):
    name=p.b.executable_name(RUN);require(name.endswith('form_stored_provider-p152-r03.exe') and name not in protected,'FRESH_R03')
    p.s.scoped_path(name,fresh=True);return name


def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(STOP_PIN['path'])==STOP_PIN,'IMMUTABLE_STOP_CLOSING');row=q.json(STOP_PIN['path'])
        require(row['state']=='PASS_CPU_STOP_ACCOUNTED_CURRENT_INPUTS_ONLY_NOT_PRODUCT_BUILD_OR_GATE'
            and row['source_closing_exact'] and row['contract_tests_passed']==36 and row['current_build_accepted'] is False
            and row['original_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and row['original_source_final_hash_not_retroactively_promoted'] is True
            and row['current_Rust_input_count']==785 and row['protected_executables_exact']==61
            and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'STOP_SCOPE')
        expected=p.s.inputs.inventory(row['bound_input_pins'],1251)
        for n,pin in expected.items():require(q.pin(n)==pin,'CURRENT_WHOLE_STOP_INPUTS')
        require(q.pin(p.PARENT['path'])==p.PARENT,'GRAPH_DELTA_PIN');old,protected=p.parent_scope(q.json(p.PARENT['path']))
        require(all(expected.get(n)==pin for n,pin in old.items()),'WHOLE_GRAPH_DELTA_PARENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        fresh_scope(protected);p.source_scope(q,expected);contracts();local=p.helpers()
        for n in (SELF,TEST,STOP_PIN['path'],*local):expected[n]=q.pin(n)
        q.finish();return expected,list(protected.values()),sorted(set(local)|{SELF,TEST,STOP_PIN['path']})
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-158-observed-graph-build.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='light':
        resources=p.s.SQLRuntimeResources();out={}
        try:
            resources.admit();q=p.s.LiveSQLReader(resources)
            for n in (SELF,TEST):q.pin(n)
            out.update(contracts());q.finish();out.update(state='PASS_OBSERVED_GRAPH_BUILD_CONTRACTS_ONLY_NOT_NATIVE_PRODUCT_OR_GATE',
                source_closing_exact=True,actual_Cargo_SQL_native_executed=False,product_complete=False,P09_gate='OPEN')
        finally:p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','resource_stop_reason')}));return 0 if out['state'].startswith('PASS_') else 2
    binding=load_binding();dump=json.dump
    def write(row,stream,**kw):
        if row['state']==p.PASS:row['state']=PASS
        row.update(schema_version='hwpx-agent.p09-observed-graph-product-build/v1',previous_CPU_stop_closing_pin=STOP_PIN,
            observed_same_owned_job=True,host_observed_target='cargo-launcher-process',observer_collection_seconds=1.0,
            diagnostic_snapshots_max=observed.MAX_SAVED,diagnostic_snapshots_are_not_complete_host_process_history=True,
            original_emergency_cpu_guard_unchanged=True,individual_duplicated_PID_attribution=False)
        return dump(row,stream,**kw)
    with patch.object(p,'RUN',RUN),patch.object(p,'SELF',SELF),patch.object(p.b.legacy.original.capture,'FullCapture',DiagnosticCapture), \
            patch.object(p.b.legacy,'RAW_CAPTURE',DiagnosticCapture),patch.object(json,'dump',write):return p.run_owned(destination,*binding)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,p.b.subprocess.SubprocessError) as e:
        code=str(e) if isinstance(e,ValueError) else 'P158_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if observed.re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P158_REDACTED_FAILURE')))
        raise SystemExit(2) from None
