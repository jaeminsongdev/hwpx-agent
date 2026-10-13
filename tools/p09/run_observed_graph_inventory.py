"""ONLY current P158 fresh EXE --list; exact original249, no test body run."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_current_stored_inventory as i
import build_observed_graph_product as d

p=d.p
SELF='tools/p09/run_observed_graph_inventory.py'
TEST='tools/p09/tests/test_observed_graph_inventory.py'
CLOSING=dict(path='implementation/p09/evidence/p09-158-observed-graph-build.terminal-audit-run01.v1.json',
    bytes=354808,sha256='55060b3752a63fe7a8967d2a75ff8b0783606ded18ccbe4ce76b9199f253e3b3')
PASS='PASS_CURRENT_GRAPH_EXE_COMPILED249_LISTING_ONLY_NOT_FULL_RUNTIME_OR_GATE'


def require(ok,code):d.require(ok,'INVENTORY_'+code)


def worker(task):
    require(task==i.task_for(d.RUN),'CLOSED_CURRENT_TASK')
    with patch.object(i,'EXE_RUN',d.RUN):return i.worker(task)


def contracts():
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_current_stored_inventory','test_observed_graph_inventory'))
    with patch('subprocess.Popen',side_effect=AssertionError('P158_INVENTORY_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P158_INVENTORY_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P158_INVENTORY_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'CONTRACT12')
    return dict(contract_tests_run=12,contract_tests_passed=12)


def closing_scope(row):
    require(row['state']=='PASS_CURRENT_OBSERVED_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'
        and row['source_closing_exact'] and row['current_build_accepted'] and row['contract_tests_passed']==46
        and row['current_Rust_input_count']==785 and row['current_source_test_count']==249
        and row['current_source_module_instance_count']==59 and row['protected_executables_exact']==61
        and row['explicit_query_cleanup_confirmed'] and row['host_cpu_error_code'] is None
        and row['current_compiled249_qualified'] is False and row['full249_current_qualified'] is False
        and row['signed16_current_qualified'] is False and row['product_complete'] is False
        and row['P09_gate']=='OPEN' and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'BUILD_CLOSING_ONLY')
    p.b.profile_scope(row['actual_libtest_profile'])
    expected=p.s.inputs.inventory(row['bound_input_pins'],1257);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(d.RUN) and expected.get(exe['path'])==exe,'EXACT_CURRENT_EXE')
    return expected,exe


def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(CLOSING['path'])==CLOSING,'IMMUTABLE_CURRENT_BUILD_CLOSING')
        row=q.json(CLOSING['path']);expected,exe=closing_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_COMPILE_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'CURRENT249_NAMES')
        contracts()
        for n in (*p.helpers(),SELF,TEST,i.TEST,CLOSING['path']):expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_WATCHER_CLEANUP')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-158-current-graph-inventory.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='light':
        resources=p.s.SQLRuntimeResources();out={}
        try:
            resources.admit();q=p.s.LiveSQLReader(resources)
            for n in (SELF,TEST,i.SELF,i.TEST):q.pin(n)
            out.update(contracts());q.finish();out.update(state='PASS_CURRENT_GRAPH_INVENTORY_CONTRACTS_ONLY_NOT_EXE_OR_GATE',
                source_closing_exact=True,actual_EXE_executed=False,product_complete=False,P09_gate='OPEN')
        finally:p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','resource_stop_reason')}));return 0 if out['state'].startswith('PASS_') else 2
    binding=load_binding()
    with patch.object(i,'SELF',SELF),patch.object(i,'CLOSING',CLOSING),patch.object(i,'PASS',PASS):
        return i.run_owned(d.RUN,destination,*binding)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,p.b.subprocess.SubprocessError) as e:
        code=str(e) if isinstance(e,ValueError) else 'P158_INVENTORY_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if d.observed.re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P158_INVENTORY_REDACTED_FAILURE')))
        raise SystemExit(2) from None
