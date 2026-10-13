"""P173 current r06 ALL249: original1200, guards and full-result parser."""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_current_stored_full as original
import run_observed_writer_inventory as inventory
import audit_observed_writer_inventory as inventory_audit
d=inventory.d; c=d.c; s=d.s; b=d.b
SELF='tools/p09/run_writer_current_full.py'
TEST='tools/p09/tests/test_writer_current_full.py'
RUN=6
PARENT=dict(path='implementation/p09/evidence/p09-172-observed-writer-inventory.terminal-audit-run01.v1.json',
    bytes=316641,sha256='1ab0ec59c63c6751f39069de1fb35b4936ce0434bda5e13275ae2309bb4f0da7')
PASS='PASS_WRITER_CURRENT_UNFILTERED_ALL249_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
CONTRACT_COUNT=32

def require(ok,code):d.require(ok,'WRITER_FULL_'+code)
def executable_name():
    return (d.TARGET/'debug/deps/form_stored_provider-p152-r06.exe').relative_to(c.ROOT).as_posix()
def worker(task):
    require(task==original.task_for(RUN),'CLOSED_R06_TASK')
    def current_name(requested):
        require(type(requested) is int and requested==1,'ORIGINAL_SINGLE_LOOKUP')
        return executable_name()
    with patch.object(c,'TARGET',d.TARGET),patch.object(b,'executable_name',current_name):
        return original.worker(task)
def parent_scope(row):
    require(row['state']==inventory_audit.PASS and row['source_closing_exact']
        and row['current_compiled249_qualified'] and row['compiled_test_count']==249
        and row['source_module_instance_count']==59 and row['contract_tests_passed']==193
        and row['current_Rust_input_count']==785 and row['protected_parent_EXE_inputs_exact']==66
        and row['current_compile_closing_pin']==inventory.CLOSING
        and not row['runtime_test_bodies_executed'] and not row['full249_current_qualified']
        and not row['signed16_current_qualified'] and not row['product_complete'] and not row['PC_freeze_resolved']
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'COMPILED_ONLY_PARENT')
    expected=s.inputs.inventory(row['bound_input_pins']);exe=row['compiled_test_executable_pin']
    require(exe['path']==executable_name() and expected.get(exe['path'])==exe
        and sum(n.endswith('.exe') for n in expected)==66
        and row['IO']['bound_inputs']==row['IO']['final_fresh_hashes']==len(expected)
        and row['IO']['finished'],'EXACT_CURRENT66')
    return expected,exe
def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_current_stored_full','test_compression_full_stored','test_writer_current_full'))
    with patch('subprocess.Popen',side_effect=AssertionError('P173_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P173_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P173_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==CONTRACT_COUNT and not result.skipped,'CONTRACT25_PLUS7')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)
def helpers():
    result={SELF,TEST,PARENT['path'],original.SELF,original.TEST,original.full.SELF,original.full.TEST}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            path=c.Path(file).resolve()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':result.add(path.relative_to(c.ROOT).as_posix())
    return sorted(result)
def load_binding():
    resources=s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_CURRENT_LIST_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_COMPILED')
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
    dump=json.dump
    def write(row,stream,**kw):
        row.update(schema_version='hwpx-agent.p09-current-writer-unfiltered-full249/v1',goal_status='active',
            A12_gate='OPEN',A13_gate='OPEN',current_writer_inventory_closing_pin=PARENT,
            native_Process_query_executed=False,additional_native_Process_diagnostic_required=False,
            full_product_performance_improvement_measured=False,actual_Hangul_COM_or_SQL_run=False,
            previous_failed_full_or_CPU_stop_evidence_modified=False)
        return dump(row,stream,**kw)
    with patch.object(original,'SELF',SELF),patch.object(original,'TEST',TEST),patch.object(original,'PARENT',PARENT), \
            patch.object(original,'PASS',PASS),patch.object(c,'TARGET',d.TARGET),patch.object(json,'dump',write):
        return original.run_owned(RUN,destination,*binding)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;require(c.Path.cwd().resolve()==c.ROOT,'CWD');original.require_scope(1200)
    destination=s.scoped_path(f'implementation/p09/evidence/p09-173-writer-current-full.{mode}-run01.v1.json',fresh=True)
    if mode=='actual':return run_owned(destination,load_binding())
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        out.update(contracts())
        for n in helpers():q.pin(n)
        q.finish();out.update(state='PASS_CURRENT_WRITER_FULL_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            actual_Cargo_SQL_native_or_test_EXE_executed=False,product_complete=False,P09_gate='OPEN')
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
    except (ValueError,OSError,KeyError,TypeError,AttributeError,b.subprocess.SubprocessError) as e:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=original.closed_error(e))))
        raise SystemExit(2) from None
