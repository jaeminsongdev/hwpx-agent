"""P163 ALL original249 on current r04; original1200 and guards unchanged."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_current_graph_full as prior
import run_source_xml_product_inventory as v

p=v.p
s=prior.s
SELF='tools/p09/run_source_xml_product_full.py'
TEST='tools/p09/tests/test_source_xml_product_full.py'
PARENT=dict(path='implementation/p09/evidence/p09-162-source-xml-product-inventory.terminal-audit-run01.v1.json',
    bytes=358557,sha256='7fd9777c4c1f1574f2a6e84ed2c0a4ad06b6c4de2a45cef7f6a4ac258045dc3d')
PASS='PASS_SOURCE_XML_CURRENT_UNFILTERED_FULL249_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
RUN=4

def require(ok,code):v.require(ok,'FULL_'+code)

def worker(task):
    require(task==s.task_for(RUN),'CLOSED_CURRENT_FULL_TASK')
    with patch.object(prior,'RUN',RUN):return prior.worker(task)

def contracts():
    prior.contracts();sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_source_xml_product_full')
    with patch('subprocess.Popen',side_effect=AssertionError('P163_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P163_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P163_LIGHT_THREAD_FORBIDDEN')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==4 and not checked.skipped,'CONTRACT4_PLUS48')
    return dict(contract_tests_run=52,contract_tests_passed=52)

def parent_scope(row):
    require(row['state']=='PASS_SOURCE_XML_CURRENT_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
        and row['source_closing_exact'] and row['current_compiled249_qualified'] and row['contract_tests_passed']==66
        and row['compiled_test_count']==249 and row['source_module_instance_count']==59
        and row['current_Rust_input_count']==785 and row['protected_parent_EXE_inputs_exact']==64
        and row['runtime_test_bodies_executed'] is False and row['full249_current_qualified'] is False
        and row['signed16_current_qualified'] is False and row['product_complete'] is False
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['current_compile_closing_pin']==v.CLOSING
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'CURRENT_COMPILED249_SCOPE')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1290);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(RUN) and expected.get(exe['path'])==exe,'CURRENT_R04_IDENTITY')
    return expected,exe

def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_CURRENT_COMPILED_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_COMPILED_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL249_59_CURRENT')
        contracts()
        for n in (*p.helpers(),SELF,TEST,PARENT['path'],'tools/p09/tests/test_current_stored_full.py',
                'tools/p09/tests/test_compression_full_stored.py','tools/p09/tests/test_observed_stored_full.py',prior.TEST):
            expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_CLEANUP')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD');s.original.require_scope(1200)
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-163-source-xml-product-full.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':
        binding=load_binding();dump=json.dump
        def write(row,stream,**kw):
            row.update(schema_version='hwpx-agent.p09-source-xml-current-full249/v1',
                current_graph_inventory_closing_pin=PARENT,source_xml_inventory_closing_pin=PARENT,
                host_observed_target='stored-product-test-process',full_product_performance_improvement_measured=False,
                actual_Hangul_COM_or_SQL_run=False,previous_failed_full_or_CPU_stop_evidence_modified=False,
                source_xml_delta_already_accepted_not_modified_during_run=True)
            return dump(row,stream,**kw)
        with patch.object(s,'SELF',SELF),patch.object(s,'TEST',TEST),patch.object(s,'PASS',PASS), \
                patch.object(s.original,'PARENT',PARENT),patch.object(json,'dump',write):
            return s.run_owned(RUN,destination,*binding)
    resources=p.s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        for n in (SELF,TEST,s.SELF,s.TEST,s.original.SELF,s.original.TEST,prior.SELF,prior.TEST):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_SOURCE_XML_CURRENT_FULL_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            source_closing_exact=True,actual_Cargo_SQL_native_or_test_EXE_executed=False,
            full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:out['error_code']=s.original.closed_error(e)
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
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=s.original.closed_error(e))))
        raise SystemExit(2) from None
