"""P169 current Writer source -> fresh r05 product, original full Cargo guards."""
import argparse
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import build_immutable_graph_product as p
import audit_writer_xml_reuse as writer

c=p.c
s=p.s
b=p.b
SELF='tools/p09/build_writer_xml_product.py'
TEST='tools/p09/tests/test_writer_xml_product_build.py'
RUN=5
TARGET=c.ROOT/'target/p09-168-writer-xml-reuse'
PARENT=dict(path='implementation/p09/evidence/p09-168-writer-xml-reuse.source-closing-run01.v1.json',
    bytes=310132,sha256='c6a675eda17ce1450721ce31f4c6b702191138cbd0eb53ffc5fcef90ce3e3709')
PASS='PASS_WRITER_XML_CURRENT_PRODUCT_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
CONTRACT_COUNT=178

def require(ok,code):p.require(ok,'WRITER_BUILD_'+code)

def executable_name():return (TARGET/'debug/deps/form_stored_provider-p152-r05.exe').relative_to(c.ROOT).as_posix()

def recipe():
    with patch.object(c,'TARGET',TARGET):return s.recipe(RUN)

def parent_scope(row):
    require(row['state']=='PASS_WRITER_XML_REUSE_DELTA_AND_ALL71_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
        and row['source_closing_exact'] and row['actual_unit_tests_passed']==71 and row['contract_tests_passed']==136
        and row['whole_original_core_inverse_exact'] and row['all_original_package_lib_tests_preserved']
        and row['test_oracle_whole_original_body_exact_after_declared_formatting'] and row['typecheck_accepted']
        and row['current_Rust_input_count']==785 and len(row['source_test_names'])==249
        and len(row['source_module_instances'])==59 and len(row['declared_Rust_source_changes'])==1
        and row['protected_parent_EXE_inputs_exact']==64 and row['old_product_EXE_not_current_qualified']
        and all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
            'signed16_current_qualified','product_complete','PC_freeze_resolved'))
        and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'PARENT_SCOPE')
    expected=s.inputs.inventory(row['bound_input_pins'],1328)
    protected={n:pin for n,pin in expected.items() if n.endswith('.exe')}
    require(len(protected)==65 and expected.get(row['declared_Rust_source_changes'][0]['path'])
        ==row['declared_Rust_source_changes'][0] and protected.get(row['fresh_package_lib_executable_pin']['path'])
        ==row['fresh_package_lib_executable_pin'],'ALL64_OLD_PLUS1_FRESH_LIB')
    return expected,protected

def fresh_scope(protected):
    name=executable_name();require(name not in protected,'FRESH_R05_NOT_HISTORY')
    s.scoped_path(name,fresh=True)
    require(TARGET.is_dir() and not TARGET.is_symlink() and not TARGET.is_junction()
        and TARGET.resolve()==TARGET,'EXISTING_ISOLATED_TARGET_NO_LINK')
    require(not list((TARGET/'debug/deps').glob('form_stored_provider*.exe')),'NO_PRIOR_PRODUCT_IN_TARGET')
    return name

def worker(task):
    require(task==b.task_for(RUN),'CLOSED_WORKER_TASK')
    with patch.object(b,'TARGET',TARGET),patch.object(c,'TARGET',TARGET):return b.worker(task)

def contracts():
    writer.units.contracts();p.contracts();sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_writer_xml_product_build')
    with patch('subprocess.Popen',side_effect=AssertionError('P169_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P169_LIGHT_CHILD_FORBIDDEN')), \
            patch('threading.Thread.start',side_effect=AssertionError('P169_LIGHT_THREAD_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'CONTRACT6_PLUS136_PLUS36')
    return dict(contract_tests_run=CONTRACT_COUNT,contract_tests_passed=CONTRACT_COUNT)

def helpers():
    result={SELF,TEST,PARENT['path'],writer.SELF,writer.b.SELF,writer.units.SELF,writer.units.TEST}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            path=c.Path(file).resolve()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':result.add(path.relative_to(c.ROOT).as_posix())
    return sorted(result)

def load_binding():
    resources=s.SQLRuntimeResources();out={}
    try:
        resources.admit();q=s.LiveSQLReader(resources);require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_WRITER_CLOSING')
        row=q.json(PARENT['path']);expected,protected=parent_scope(row)
        for n,pin in expected.items():require(q.pin(n)==pin,'WHOLE_CURRENT_PARENT')
        archive=q.json(writer.b.ARCHIVE);_,old=writer.b.preimage(archive,writer.b.SOURCE)
        current=q.text(writer.b.SOURCE);writer.b.inverse(current,old.decode());writer.verify_original_oracle(current,old.decode())
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=p.source_scope(q,expected)
        require(names==row['source_test_names'] and modules==row['source_module_instances'],'ORIGINAL249_59')
        fresh_scope(protected);contracts();local=helpers()
        for n in local:expected[n]=q.pin(n)
        q.finish();return expected,list(protected.values()),local
    finally:require(s.finish_watcher(resources,out),'BINDING_CLEANUP')

def run_owned(destination,binding):
    dump=json.dump
    def write(row,stream,**kw):
        if row.get('state')==p.PASS:row['state']=PASS
        row.pop('current_graph_delta_closing_pin',None)
        row.update(schema_version='hwpx-agent.p09-writer-xml-product-build/v1',goal_status='active',
            writer_xml_delta_closing_pin=PARENT,protected_executables_expected=65,previous_parent_EXE_inputs_preserved=65,
            isolated_target=TARGET.relative_to(c.ROOT).as_posix(),cache_reuse_planned=True,
            actual_cache_hit_or_speedup_proven=False,native_Process_query_executed=False,
            writer_xml_lib71_accepted=True,old_product_EXE_not_current_qualified=True,
            A12_gate='OPEN',A13_gate='OPEN',full_product_performance_improvement_measured=False)
        return dump(row,stream,**kw)
    with patch.object(p,'RUN',RUN),patch.object(p,'SELF',SELF),patch.object(p,'PARENT',PARENT), \
            patch.object(b,'TARGET',TARGET),patch.object(json,'dump',write):
        return p.run_owned(destination,*binding)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True)
    mode=parser.parse_args().mode;require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-169-writer-xml-product-build.{mode}-run01.v1.json',fresh=True)
    if mode=='actual':return run_owned(destination,load_binding())
    resources=s.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        for n in (SELF,TEST,writer.SELF,writer.b.SELF,writer.units.SELF,writer.units.TEST):q.pin(n)
        out.update(contracts());q.finish()
        out.update(state='PASS_WRITER_XML_PRODUCT_BUILD_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
            actual_Cargo_SQL_native_executed=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=writer.b.prior.d.original.closed_error(e)
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
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=writer.b.prior.d.original.closed_error(e))))
        raise SystemExit(2) from None
