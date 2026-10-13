"""Current r03 all249 per-case diagnostic, 360s ONLY, not full qualification.

Reuse original owned Job, guard, bounded CaseTrace and native/churn collector.
Only pretty/color presentation and diagnostic timeout differ from full1200.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_stored_cost_diagnostic as old
import run_current_graph_full as full

p=full.p
SELF='tools/p09/run_current_graph_cost.py'
TEST='tools/p09/tests/test_current_graph_cost.py'
PARENT=dict(path='implementation/p09/evidence/p09-159-current-graph-full.terminal-audit-run01.v1.json',
    bytes=376506,sha256='22db5cfe44272f9eb9e76a8194f557c3c41beff993b3fe3bd2acc25d0b496ade')
RUN=3
MAXIMUM_SECONDS=360

def require(ok,code):full.require(ok,'COST_'+code)

def worker(task):
    require(task==old.task_for(RUN),'TASK')
    real=p.b.executable_name
    def current(requested):
        require(type(requested) is int and requested==1,'SINGLE_HISTORICAL_NAME_LOOKUP')
        return real(RUN)
    with patch.object(p.b,'executable_name',current):return old.worker(task)

def parent_scope(row):
    require(row['state']=='PASS_CURRENT_GRAPH_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'
        and row['source_closing_exact'] and row['contract_tests_passed']==60
        and row['current_compiled249_qualified'] and row['current_Rust_input_count']==785
        and row['protected_EXE_inputs_exact']==62 and row['actual_tests_passed'] is None
        and row['original_stop_reason']=='STOP_DURATION_LIMIT' and row['original_run_state']=='STOPPED_NOT_ACCEPTED'
        and not row['full249_current_qualified'] and not row['signed16_current_qualified']
        and not row['product_complete'] and row['P09_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'CURRENT_STOP_NOT_PASS')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1267);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(RUN) and expected.get(exe['path'])==exe,'CURRENT_R03')
    return expected,exe

def contracts():
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_stored_cost_observation','test_observed_stored_full','test_current_stored_full',
         'test_compression_full_stored','test_host_cpu_groups','test_current_graph_cost'))
    with patch('subprocess.Popen',side_effect=AssertionError('P160_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P160_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P160_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failed=sorted({getattr(t,'test_case',t).id().split('.')[-1] for t,_ in result.errors+result.failures+result.skipped})
    require(result.wasSuccessful() and result.testsRun==80 and not result.skipped,'CONTRACT80_'+'_'.join(failed))
    return dict(contract_tests_run=80,contract_tests_passed=80)

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_STOP_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_PARENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL249_59')
        contracts()
        for n in (SELF,TEST,old.SELF,old.TEST,'tools/p09/stored_cost_observation.py',PARENT['path']):expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run_owned(destination,binding):
    dump=json.dump
    def write(row,stream,**kw):
        row.update(current_graph_stop_closing_pin=PARENT,current_cost_diagnostic_seconds=MAXIMUM_SECONDS,
            full_product_performance_improvement_measured=False,previous_failed_evidence_modified=False,
            actual_Hangul_COM_or_SQL_run=False)
        return dump(row,stream,**kw)
    # Existing callback still fixes qualification1200, tests_passed=null, all
    # promotion flags false and current compiled identity. No source/test edit.
    with patch.object(old,'SELF',SELF),patch.object(old,'PARENT',PARENT), \
            patch.object(old,'MAXIMUM_SECONDS',MAXIMUM_SECONDS),patch.object(json,'dump',write):
        return old.run_owned(RUN,destination,*binding)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-160-current-graph-cost.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':return run_owned(destination,load_binding())
    resources=p.s.SQLRuntimeResources();out={};q=None
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,old.SELF,old.TEST,'tools/p09/stored_cost_observation.py'):q.pin(n)
        out.update(contracts());q.finish();out.update(state='PASS_CURRENT_GRAPH_COST_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            source_closing_exact=True,full249_current_qualified=False,signed16_current_qualified=False,
            product_complete=False,P09_gate='OPEN',actual_EXE_SQL_native_or_child_started=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:out.update(state='FAILED_NOT_ACCEPTED',error_code=full.s.original.closed_error(e))
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
    except (ValueError,OSError,KeyError,TypeError,AttributeError,old.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=full.s.original.closed_error(e))))
        raise SystemExit(2) from None
