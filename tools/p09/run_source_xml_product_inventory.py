"""Fresh P162 r04 --list only, never executes a test body."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_observed_graph_inventory as prior
import build_source_xml_product as d

p=d.p
i=prior.i
SELF='tools/p09/run_source_xml_product_inventory.py'
TEST='tools/p09/tests/test_source_xml_product_inventory.py'
CLOSING=dict(path='implementation/p09/evidence/p09-162-source-xml-product-build.terminal-audit-run01.v1.json',
    bytes=364919,sha256='45bc28afba022dd36e3f81be2947b838702b6c74a73ec5714991d5cc5e49ef69')
PASS='PASS_SOURCE_XML_CURRENT_EXE_COMPILED249_LISTING_ONLY_NOT_FULL_RUNTIME_OR_GATE'

def require(ok,code):d.require(ok,'INVENTORY_'+code)

def worker(task):
    require(task==i.task_for(d.RUN),'CLOSED_CURRENT_TASK')
    with patch.object(i,'EXE_RUN',d.RUN):return i.worker(task)

def contracts():
    prior.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_source_xml_product_inventory')
    with patch('subprocess.Popen',side_effect=AssertionError('P162_LIST_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P162_LIST_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P162_LIST_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==4 and not result.skipped,'CONTRACT4_PLUS12')
    return dict(contract_tests_run=16,contract_tests_passed=16)

def closing_scope(row):
    require(row['state']=='PASS_SOURCE_XML_PRODUCT_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'
        and row['source_closing_exact'] and row['current_build_accepted'] and row['contract_tests_passed']==50
        and row['current_Rust_input_count']==785 and row['current_source_test_count']==249
        and row['current_source_module_instance_count']==59 and row['protected_executables_exact']==63
        and row['source_xml_delta_closing_pin']==d.PARENT
        and row['explicit_query_cleanup_confirmed'] and row['host_cpu_error_code'] is None
        and all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete'))
        and row['P09_gate']=='OPEN' and row['resource_stop_reason'] is None
        and row['resource_watcher_cleanup_confirmed'],'BUILD_CLOSING_ONLY')
    p.b.profile_scope(row['actual_libtest_profile'])
    expected=p.s.inputs.inventory(row['bound_input_pins'],1285)
    require(row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==len(expected)
        and row['IO']['finished'] and sum(n.endswith('.exe') for n in expected)==64,'WHOLE_CLOSING_INVENTORY')
    exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(d.RUN) and expected.get(exe['path'])==exe,'EXACT_CURRENT_R04')
    return expected,exe

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(CLOSING['path'])==CLOSING,'IMMUTABLE_P162_BUILD_CLOSING')
        row=q.json(CLOSING['path']);expected,exe=closing_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_COMPILE_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ORIGINAL249_59')
        contracts()
        for n in (*d.helpers(),SELF,TEST,i.SELF,i.TEST,prior.SELF,prior.TEST,CLOSING['path']):expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-162-source-xml-product-inventory.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':
        binding=load_binding()
        with patch.object(i,'SELF',SELF),patch.object(i,'CLOSING',CLOSING),patch.object(i,'PASS',PASS):
            return i.run_owned(d.RUN,destination,*binding)
    resources=p.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,i.SELF,i.TEST,prior.SELF,prior.TEST):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_SOURCE_XML_INVENTORY_CONTRACTS_ONLY_NOT_EXE_OR_GATE',
            source_closing_exact=True,actual_EXE_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        out['error_code']=str(e) if isinstance(e,ValueError) else 'P162_LIST_LIGHT_REDACTED'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,p.b.subprocess.SubprocessError) as e:
        code=str(e) if isinstance(e,ValueError) else 'P162_LIST_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if d.d.observed.re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P162_LIST_REDACTED_FAILURE')))
        raise SystemExit(2) from None
