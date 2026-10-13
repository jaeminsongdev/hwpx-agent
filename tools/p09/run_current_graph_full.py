"""P159 actual ALL original249 on current r03, same original1200/owned caps.

Reuse original complete249/zero failed/ignored/filtered parser and PDH limits.
No new Cargo/test filters/private originals/native document UI/SQL/settings.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import run_observed_stored_full as s
import run_observed_graph_inventory as v

p=v.p
SELF='tools/p09/run_current_graph_full.py'
TEST='tools/p09/tests/test_current_graph_full.py'
PARENT=dict(path='implementation/p09/evidence/p09-158-current-graph-inventory.terminal-audit-run01.v1.json',
    bytes=352586,sha256='2ffa26b410bbd90e3d8364965f270bc20da39aeae7864f3d6b3806ede1d677c7')
PASS='PASS_CURRENT_GRAPH_UNFILTERED_FULL249_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE'
RUN=3


def require(ok,code):v.require(ok,'FULL_'+code)


def worker(task):
    require(task==s.task_for(RUN),'CLOSED_FULL_TASK')
    real_name=p.b.executable_name
    def current_name(requested):
        require(type(requested) is int and requested==1,'ORIGINAL_WORKER_SINGLE_NAME_LOOKUP')
        return real_name(RUN)
    # Original workers still enforce GO/Job, exact full Cargo-contract argv,
    # original environment and unfiltered terse direct call. Only their fixed
    # historical EXE lookup is explicitly redirected to current r03.
    with patch.object(p.b,'executable_name',current_name):return s.worker(task)


def contracts():
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_current_stored_full','test_compression_full_stored','test_observed_stored_full','test_current_graph_full'))
    with patch('subprocess.Popen',side_effect=AssertionError('P159_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P159_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P159_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==48 and not result.skipped,'CONTRACT48')
    return dict(contract_tests_run=48,contract_tests_passed=48)


def parent_scope(row):
    require(row['state']=='PASS_CURRENT_GRAPH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
        and row['source_closing_exact'] and row['current_compiled249_qualified'] and row['contract_tests_passed']==58
        and row['compiled_test_count']==249 and row['source_module_instance_count']==59
        and row['current_Rust_input_count']==785 and row['protected_parent_EXE_inputs_exact']==62
        and row['runtime_test_bodies_executed'] is False and row['full249_current_qualified'] is False
        and row['signed16_current_qualified'] is False and row['product_complete'] is False and row['P09_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'CURRENT_COMPILED249_SCOPE')
    expected=p.s.inputs.inventory(row['bound_input_pins'],1262);exe=row['compiled_test_executable_pin']
    require(exe['path']==p.b.executable_name(RUN) and expected.get(exe['path'])==exe,'CURRENT_R03_IDENTITY')
    return expected,exe


def load_binding():
    resources=p.s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_COMPILED_CLOSING')
        row=q.json(PARENT['path']);expected,exe=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'CURRENT_WHOLE_COMPILED_INPUTS')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ALL249_59_CURRENT')
        contracts()
        for n in (*p.helpers(),SELF,TEST,PARENT['path'],'tools/p09/tests/test_current_stored_full.py',
                'tools/p09/tests/test_compression_full_stored.py','tools/p09/tests/test_observed_stored_full.py'):expected[n]=q.pin(n)
        q.finish();return expected,names,modules,exe
    finally:require(p.s.finish_watcher(resources,out),'BINDING_WATCHER_CLEANUP')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(f'implementation/p09/evidence/p09-159-current-graph-full.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='light':
        resources=p.s.SQLRuntimeResources();out={}
        try:
            resources.admit();q=p.s.LiveSQLReader(resources)
            for n in (SELF,TEST,s.SELF,s.TEST,s.original.SELF,s.original.TEST):q.pin(n)
            out.update(contracts());q.finish();out.update(state='PASS_CURRENT_GRAPH_FULL_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
                source_closing_exact=True,actual_Cargo_SQL_native_or_test_EXE_executed=False,product_complete=False,P09_gate='OPEN')
        finally:p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','resource_stop_reason')}));return 0 if out['state'].startswith('PASS_') else 2
    binding=load_binding();dump=json.dump
    def write(row,stream,**kw):
        row.update(schema_version='hwpx-agent.p09-current-immutable-graph-full249/v1',current_graph_inventory_closing_pin=PARENT,
            host_observed_target='stored-product-test-process',full_product_performance_improvement_measured=False,
            actual_Hangul_COM_or_SQL_run=False,previous_failed_full_or_CPU_stop_evidence_modified=False)
        return dump(row,stream,**kw)
    with patch.object(s,'SELF',SELF),patch.object(s,'TEST',TEST),patch.object(s,'PASS',PASS), \
            patch.object(s.original,'PARENT',PARENT),patch.object(json,'dump',write):return s.run_owned(RUN,destination,*binding)


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,p.b.subprocess.SubprocessError) as e:
        code=str(e) if isinstance(e,ValueError) else 'P159_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if s.re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P159_REDACTED_FAILURE')))
        raise SystemExit(2) from None
