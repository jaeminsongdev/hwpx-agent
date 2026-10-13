"""P172 r06 listing only, accepted fresh P171 build closure required."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_writer_xml_product_inventory as prior
import build_observed_writer_product_r2 as build
import audit_observed_writer_product as audit
d=prior.d; i=prior.i
SELF='tools/p09/run_observed_writer_inventory.py'
TEST='tools/p09/tests/test_observed_writer_inventory.py'
CLOSING=dict(path='implementation/p09/evidence/p09-171-observed-writer-product-build.terminal-audit-run02.v1.json',
    bytes=318206,sha256='742df1de8767b236b4d3dd9dc6db2e60a348f896683a17f56f803e956de3858c')
PASS='PASS_OBSERVED_WRITER_COMPILED249_LISTING_ONLY_NOT_RUNTIME_OR_GATE'

def require(ok,code):prior.require(ok,'OBSERVED_'+code)
def worker(task):
    require(task==i.task_for(6),'CLOSED_R06_LIST_TASK')
    with patch.object(i,'EXE_RUN',6),patch.object(d.c,'TARGET',d.TARGET):return i.worker(task)
def closing_scope(row):
    require(row['state']==audit.PASS and row['source_closing_exact'] and row['current_build_accepted']
        and row['contract_tests_passed']==205 and row['current_Rust_input_count']==785
        and row['current_source_test_count']==249 and row['current_source_module_instance_count']==59
        and row['protected_executables_exact']==65 and row['writer_xml_delta_closing_pin']==build.prior.WRITER_PARENT
        and row['previous_build_stop_closing_pin']==build.prior.PARENT
        and all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'BUILD_ONLY_SCOPE')
    build.prior.require_closed(row['validated_compiler_progress'])
    expected=d.s.inputs.inventory(row['bound_input_pins'])
    require(row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==len(expected)
        and row['IO']['finished'] and sum(n.endswith('.exe') for n in expected)==66,'WHOLE_FRESH66')
    exe=row['compiled_test_executable_pin']
    require(exe['path']==d.TARGET.relative_to(d.c.ROOT).as_posix()+'/debug/deps/form_stored_provider-p152-r06.exe'
        and expected.get(exe['path'])==exe,'FRESH_R06_EXE')
    return expected,exe
def contracts():
    prior.contracts();sys.path.insert(0,str(d.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_writer_inventory')
    with patch('subprocess.Popen',side_effect=AssertionError('P172_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P172_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P172_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==3 and not result.skipped,'CONTRACT3_PLUS12')
    return dict(contract_tests_run=15,contract_tests_passed=15)
def load_binding():
    raw_contracts=prior.contracts
    def qualified_contracts():
        with patch.object(prior,'contracts',raw_contracts):return contracts()
    with patch.object(prior,'CLOSING',CLOSING),patch.object(prior,'closing_scope',closing_scope), \
            patch.object(prior,'contracts',qualified_contracts),patch.object(prior,'SELF',SELF),patch.object(prior,'TEST',TEST):
        return prior.load_binding()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;require(d.c.Path.cwd().resolve()==d.c.ROOT,'CWD')
    destination=d.s.scoped_path(f'implementation/p09/evidence/p09-172-observed-writer-inventory.{mode}-run01.v1.json',fresh=True)
    if mode=='actual':
        binding=load_binding();dump=json.dump
        def write(row,stream,**kw):
            row.update(goal_status='active',A12_gate='OPEN',A13_gate='OPEN',native_Process_query_executed=False,
                full_product_performance_improvement_measured=False)
            return dump(row,stream,**kw)
        with patch.object(i,'SELF',SELF),patch.object(i,'CLOSING',CLOSING),patch.object(i,'PASS',PASS), \
                patch.object(d.c,'TARGET',d.TARGET),patch.object(json,'dump',write):
            return i.run_owned(6,destination,*binding)
    resources=d.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=d.s.LiveSQLReader(resources);out.update(contracts())
        for n in (SELF,TEST,prior.SELF,prior.TEST,i.SELF,i.TEST):q.pin(n)
        q.finish();out.update(state='PASS_R06_INVENTORY_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE',
            actual_EXE_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
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
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=d.writer.b.prior.d.original.closed_error(e))))
        raise SystemExit(2) from None
