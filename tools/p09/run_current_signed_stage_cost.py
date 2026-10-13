"""P167 current-r04 existing signed-case timing, original180s diagnostic only.

The selected test and its assertions are unchanged. No native Process query,
new compilation, service/authorization cache, full249 or Gate promotion.
"""
import argparse
import io
import json
import re
import sys
import unittest
from unittest.mock import patch
import bounded_process_progress as bounded
import run_source_xml_stored_cost as prior
import run_signed_stage_cost as stage

p=prior.p
c=p.c
original=prior.full.s.original
SELF='tools/p09/run_current_signed_stage_cost.py'
TEST='tools/p09/tests/test_current_signed_stage_cost.py'
PARENT=dict(path='implementation/p09/evidence/p09-166-source-xml-stored-cost.terminal-audit-run02.v1.json',
    bytes=311754,sha256='86ccba87fe8f12bc9d4b5abefa300a5d5cdf6f81c1f88e62fe442d1feaa9a3ea')
TASK='p167-current-signed-stage-diagnostic'
RUN=4
MAXIMUM_SECONDS=180
NAME=original.full.cost.original.NAME
FINISHED='DIAGNOSTIC_SIGNED_CHANGED16_STAGE_FINISHED_NOT_FULL249_SQL_NATIVE_OR_GATE'

def require(ok,code):prior.require(ok,'STAGE_'+code)

def profile_argv(exe):
    return [str(exe),NAME,'--exact','--test-threads=1','--nocapture','--format=terse']

def worker(task):
    require(task==TASK,'CLOSED_TASK')
    real_call=original.subprocess.call;real_name=p.b.executable_name
    def current(requested):
        require(type(requested) is int and requested==1,'ONE_HISTORICAL_LOOKUP')
        return real_name(RUN)
    def selected(args,**kw):
        exe=c.ROOT/real_name(RUN)
        require(args==[str(exe),'--test-threads=1','--format=terse'] and kw.get('cwd')==c.ROOT
            and kw.get('stdin')==original.subprocess.DEVNULL and kw['env'].get('RUST_TEST_NOCAPTURE')=='0',
            'ORIGINAL_EXACT_CALL_BEFORE_DIAGNOSTIC_FILTER')
        return real_call(profile_argv(exe),**kw)
    # Original worker still checks GO, real Job membership, full original Cargo
    # argv/profile81/env and then invokes its direct fixed EXE call. Only this
    # declared timing diagnostic changes filter/presentation; never full proof.
    with patch.object(p.b,'executable_name',current),patch.object(original.subprocess,'call',selected):
        return original.worker(original.task_for(RUN))

class StageCapture(bounded.BoundedProcessCapture):
    def cost(self):
        with self.lock:text=bytes(self.buffers['stderr']).decode('utf-8',errors='replace')
        return stage.observe_cost(text)

    def progress(self):
        result=super().progress();self.cost();return result

    def diagnostic(self):
        cost=self.cost()
        with self.lock:
            return dict(signed_stage_cost=cost,buffered_bytes={k:len(v) for k,v in self.buffers.items()},
                error_code=self.error,per_stream_limit_bytes=self.output_limit,raw_log_content_included=False,
                native_Process_query_started=False)

    def selected_finished(self):
        cost=self.cost()
        with self.lock:text=bytes(self.buffers['stdout']).decode('utf-8',errors='replace')
        summaries=re.findall(r'test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 248 filtered out;',text)
        return len(summaries)==1 and cost['fully_observed_case_sequences']==16 and self.error is None

def parent_scope(row):
    require(row['state']=='PASS_CURRENT_SOURCE_XML_ADAPTIVE_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE'
        and row['source_closing_exact'] and row['contract_tests_passed']==112 and row['current_compiled249_qualified']
        and row['current_Rust_input_count']==785 and row['protected_EXE_inputs_exact']==64
        and row['completed_case_observations']==50 and row['case_progress']['active']['case']==NAME
        and row['original_stop_reason']=='STOP_DURATION_LIMIT' and row['original_run_state']=='STOPPED_NOT_ACCEPTED'
        and not row['full249_current_qualified'] and not row['signed16_current_qualified'] and not row['product_complete']
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'CURRENT_CASE_NOT_PASSED')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1314);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(RUN) and expected.get(exe['path'])==exe,'CURRENT_R04')
    return expected,exe

def contracts():
    prior.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_signed_stage_cost','test_current_signed_stage_cost'))
    with patch('subprocess.Popen',side_effect=AssertionError('P167_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P167_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P167_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==18 and not result.skipped,'CONTRACT18_PLUS112')
    return dict(contract_tests_run=130,contract_tests_passed=130)

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_CURRENT_CASE_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_PARENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(len(names)==249 and len(modules)==59 and names.count(NAME)==1,'ORIGINAL_BODY_AND_EXACT_ONE_NAME')
        contracts()
        for n in (SELF,TEST,PARENT['path'],stage.SOURCE,stage.CONSUMER,stage.NEW):expected[n]=q.pin(n)
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).resolve()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':
                    n=path.relative_to(c.ROOT).as_posix();expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run_owned(destination,binding):
    expected,names,modules,exe=binding;raw_pins=c.pins;dump=json.dump;captures=[];admitted=False
    class Capture(StageCapture):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);captures.append(self)
    def pins(checkpoint=None):
        nonlocal admitted
        actual=raw_pins(checkpoint);seen={pin['path']:pin for pin in actual}
        require(all(seen.get(n)==pin for n,pin in expected.items()),'WHOLE_FRESH_INPUT')
        if not admitted:
            resources=p.s.SQLRuntimeResources();out={}
            try:resources.admit();admitted=True
            finally:require(p.s.finish_watcher(resources,out),'POST_HASH_CLEANUP')
        return actual
    def write(row,stream,**kw):
        cap=captures[-1] if captures else None;diagnostic=None;cost_error=None
        if cap:
            try:diagnostic=cap.diagnostic()
            except ValueError:cost_error='P167_CLOSED_STAGE_RECORD_REJECTED'
        completed=bool(row.get('state')=='PASS_SCOPED_NOT_GATE' and cap and not cost_error and cap.selected_finished())
        if row.get('state')=='PASS_SCOPED_NOT_GATE':
            row['state']=FINISHED if completed else 'STOPPED_NOT_ACCEPTED'
            if not completed:row['stop_reason']='P167_EXACT_SELECTED_BODY_AND16_STAGES_REQUIRED'
        row.update(schema_version='hwpx-agent.p09-current-signed-stage-cost/v1',diagnostic_only=True,
            current_case_closing_pin=PARENT,current_Rust_input_count=785,current_compiled249_qualified=True,
            source_test_names=names,source_module_instances=modules,selected_test_names=[NAME],
            compiled_test_executable_pin=exe,test_package_profile_config=list(p.b.CONFIG),
            original_full_qualification_seconds=1200,tests_passed=None,selected_body_finished=completed,
            full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
            P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
            full_product_performance_improvement_measured=False,exact_CPU_profiler=False,
            capture_diagnostics=diagnostic,stage_record_error_code=cost_error,
            original_test_bodies_or_product_sources_changed=False,actual_new_Cargo_compile_executed=False,
            actual_Hangul_COM_SQL_or_Process_query_run=False,post_hash_runtime_admission_revalidated=admitted,
            raw_logs_printed_or_saved=False,remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{TASK:[]}), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(bounded,'BoundedProcessCapture',Capture),patch.object(json,'dump',write):
        return c.run(TASK,destination,MAXIMUM_SECONDS)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    a=parser.parse_args();require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-167-current-signed-stage-cost.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':return run_owned(destination,load_binding())
    resources=p.s.SQLRuntimeResources();out={};q=None
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,stage.SELF,stage.TEST,stage.SOURCE,stage.CONSUMER,stage.NEW):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_CURRENT_SIGNED_STAGE_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            actual_EXE_SQL_native_or_child_started=False,product_complete=False,P09_gate='OPEN',
            full249_current_qualified=False,signed16_current_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out.update(state='FAILED_NOT_ACCEPTED',error_code=original.closed_error(e))
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,original.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=original.closed_error(e))))
        raise SystemExit(2) from None
