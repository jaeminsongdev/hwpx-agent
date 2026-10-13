"""P174 current r06 case timings from existing pipes; no native query sampler."""
import argparse
import io
import json
import sys
import time
import unittest
from unittest.mock import patch
import run_writer_current_full as full
import audit_writer_current_full as audit
import stored_cost_observation as observation
d=full.d; c=full.c; s=full.s; original=full.original
SELF='tools/p09/run_writer_case_cost.py'
TEST='tools/p09/tests/test_writer_case_cost.py'
RUN=6
MAXIMUM_SECONDS=360
CONTRACT_COUNT=58
PARENT=dict(path='implementation/p09/evidence/p09-173-writer-current-full.terminal-audit-run01.v1.json',
    bytes=317364,sha256='5269b1822ee89fd72df324374e68e7b7d295264e420fe5b051030d7a1e933512')
BASE_CAPTURE=original.full.FullCapture
RAW_CALL=original.subprocess.call
RAW_RUN=c.run

def require(ok,code):full.require(ok,'CASE_COST_'+code)
def task_for(run):
    require(type(run) is int and run==RUN,'TASK_RUN')
    return 'p174-writer-case-cost-r06-diagnostic'
def present_call(args,**kw):
    require(args==[str(c.ROOT/full.executable_name()),'--test-threads=1','--format=terse']
        and kw.get('cwd')==c.ROOT and kw.get('stdin')==original.subprocess.DEVNULL
        and kw['env'].get('RUST_TEST_NOCAPTURE')=='0','EXACT_CURRENT_UNFILTERED_CALL')
    return RAW_CALL([*args[:-1],'--format=pretty','--color=never'],**kw)
def worker(task):
    require(task==task_for(RUN),'CLOSED_TASK')
    with patch.object(original.subprocess,'call',present_call):return full.worker(original.task_for(RUN))
def diagnostic_run(task,destination,seconds):
    require(task==task_for(RUN) and type(seconds) is int and seconds==1200,'ORIGINAL_QUALIFICATION1200')
    return RAW_RUN(task,destination,MAXIMUM_SECONDS)
class Capture(BASE_CAPTURE):
    def __init__(self,*a,names,**kw):
        self.trace=observation.CaseTrace(tuple(names));super().__init__(*a,**kw)
    def _accept(self,name,chunk):
        super()._accept(name,chunk)
        if name=='stdout':
            with self.lock:
                try:self.trace.feed(bytes(chunk),time.monotonic()-self.started)
                except (ValueError,TypeError,KeyError,AttributeError):self.error='live_progress_marker_scope'
    def diagnostics(self):
        row=super().diagnostics()
        with self.lock:row.update(case_progress=self.trace.snapshot(time.monotonic()-self.started),
            native_Process_query_started=False,additional_pipe_reader_threads=False,
            raw_case_or_process_output_saved=False)
        return row
def parent_scope(row):
    require(row['state']==audit.STOP_PASS and row['source_closing_exact']
        and row['current_compiled249_qualified'] and row['current_Rust_input_count']==785
        and row['protected_EXE_inputs_exact']==66 and row['contract_tests_passed']==32
        and row['actual_tests_passed'] is None and row['original_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and not row['full249_current_qualified'] and not row['signed16_current_qualified']
        and not row['product_complete'] and not row['PC_freeze_resolved']
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'STOP_NOT_RUNTIME_PASS')
    expected=s.inputs.inventory(row['bound_input_pins']);exe=row['compiled_test_executable_pin']
    require(exe['path']==full.executable_name() and expected.get(exe['path'])==exe
        and sum(n.endswith('.exe') for n in expected)==66
        and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==len(expected)
        and row['IO']['finished'],'WHOLE_CURRENT_R06_66')
    return expected,exe
def contracts():
    full.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_stored_cost_observation','test_writer_case_cost'))
    with patch('subprocess.Popen',side_effect=AssertionError('P174_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P174_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P174_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==26 and not result.skipped,'CONTRACT32_PLUS20_PLUS6')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)
def helpers():return sorted(set(full.helpers())|{SELF,TEST,PARENT['path'],'tools/p09/stored_cost_observation.py',
    'tools/p09/tests/test_stored_cost_observation.py'})
def load_binding():
    resources=s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=s.LiveSQLReader(resources);require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_STOP_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL249_59')
        contracts()
        for n in helpers():expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(s.finish_watcher(resources,out),'BINDING_CLEANUP')
def run_owned(destination,binding):
    names=binding[1];dump=json.dump
    class NamedCapture(Capture):
        def __init__(self,*a,**kw):super().__init__(*a,names=names,**kw)
    def write(row,stream,**kw):
        if row.get('state')==full.PASS:row['state']='DIAGNOSTIC_ALL249_FINISHED_NOT_FULL_QUALIFICATION_OR_GATE'
        row.update(schema_version='hwpx-agent.p09-current-writer-pipe-case-cost/v1',diagnostic_only=True,
            diagnostic_maximum_seconds=360,original_full_qualification_seconds=1200,
            full249_current_qualified=False,signed16_current_qualified=False,tests_passed=None,
            original_all249_unfiltered_single_thread_nocapture0=True,actual_test_format='pretty',
            immutable_full_stop_closing_pin=PARENT,native_Process_query_executed=False,
            timing_is_pipe_arrival_wall_not_CPU_profile=True,raw_logs_printed_or_saved=False)
        return dump(row,stream,**kw)
    with patch.object(full,'SELF',SELF),patch.object(original,'task_for',task_for), \
            patch.object(original.full,'FullCapture',NamedCapture),patch.object(c,'run',diagnostic_run),patch.object(json,'dump',write):
        return full.run_owned(destination,binding)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-174-writer-case-cost.{mode}-run01.v1.json',fresh=True)
    if mode=='actual':return run_owned(destination,load_binding())
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=s.LiveSQLReader(resources);out.update(contracts())
        for n in helpers():q.pin(n)
        q.finish();out.update(state='PASS_CURRENT_WRITER_PIPE_COST_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            actual_EXE_or_native_query_started=False,full249_current_qualified=False,signed16_current_qualified=False,
            product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=original.closed_error(e)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,d.b.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=original.closed_error(e))))
        raise SystemExit(2) from None
