"""P169 r05 --list only; complete original249 and current-source binding."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_writer_xml_product as d
import audit_writer_xml_product_build as audit
import run_current_stored_inventory as i

SELF='tools/p09/run_writer_xml_product_inventory.py'
TEST='tools/p09/tests/test_writer_xml_product_inventory.py'
CLOSING=None  # Set to the fresh accepted build receipt before any listing.
PASS='PASS_WRITER_XML_CURRENT_EXE_COMPILED249_LISTING_ONLY_NOT_FULL_RUNTIME_OR_GATE'

def require(ok,code):d.require(ok,'INVENTORY_'+code)

def worker(task):
    require(task==i.task_for(d.RUN),'CLOSED_R05_LIST_TASK')
    with patch.object(i,'EXE_RUN',d.RUN),patch.object(d.c,'TARGET',d.TARGET):return i.worker(task)

def contracts():
    sys.path.insert(0,str(d.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_current_stored_inventory','test_writer_xml_product_inventory'))
    with patch('subprocess.Popen',side_effect=AssertionError('P169_LIST_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P169_LIST_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P169_LIST_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==12 and not result.skipped,'CONTRACT12')
    return dict(contract_tests_run=12,contract_tests_passed=12)

def closing_scope(row):
    require(row['state']==audit.PASS and row['source_closing_exact'] and row['current_build_accepted']
        and row['contract_tests_passed']==178 and row['current_Rust_input_count']==785
        and row['current_source_test_count']==249 and row['current_source_module_instance_count']==59
        and row['protected_executables_exact']==65 and row['writer_xml_delta_closing_pin']==d.PARENT
        and all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'BUILD_CLOSING_ONLY')
    d.b.profile_scope(row['actual_libtest_profile']);expected=d.s.inputs.inventory(row['bound_input_pins'])
    require(row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==len(expected)
        and row['IO']['finished'] and sum(n.endswith('.exe') for n in expected)==66,'WHOLE_CLOSING66')
    exe=row['compiled_test_executable_pin']
    require(exe['path']==d.executable_name() and expected.get(exe['path'])==exe,'FRESH_R05_IDENTITY')
    return expected,exe

def load_binding():
    resources=d.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=d.s.LiveSQLReader(resources);require(isinstance(CLOSING,dict),'CLOSING_BOUND')
        require(q.pin(CLOSING['path'])==CLOSING,'IMMUTABLE_CURRENT_BUILD_CLOSING')
        row=q.json(CLOSING['path']);expected,exe=closing_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_BUILD')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and d.s.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ORIGINAL249_59')
        contracts()
        for n in (*d.helpers(),SELF,TEST,i.SELF,i.TEST,CLOSING['path']):expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(d.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;require(d.c.Path.cwd().resolve()==d.c.ROOT,'CWD')
    destination=d.s.scoped_path(f'implementation/p09/evidence/p09-169-writer-xml-product-inventory.{mode}-run01.v1.json',fresh=True)
    if mode=='actual':
        binding=load_binding();dump=json.dump
        def write(row,stream,**kw):
            row.update(goal_status='active',A12_gate='OPEN',A13_gate='OPEN',native_Process_query_executed=False,
                full_product_performance_improvement_measured=False)
            return dump(row,stream,**kw)
        with patch.object(i,'SELF',SELF),patch.object(i,'CLOSING',CLOSING),patch.object(i,'PASS',PASS), \
                patch.object(d.c,'TARGET',d.TARGET),patch.object(json,'dump',write):
            return i.run_owned(d.RUN,destination,*binding)
    resources=d.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=d.s.LiveSQLReader(resources)
        for n in (SELF,TEST,i.SELF,i.TEST):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_WRITER_XML_INVENTORY_CONTRACTS_ONLY_NOT_EXE_OR_GATE',
            actual_EXE_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
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
