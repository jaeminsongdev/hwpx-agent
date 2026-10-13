"""Fresh current stored-product build after P156 delta; no old EXE restamp.

Reuse the original P152 compiler/whole Cargo stream/GO/Job/resource protocol.
The next fresh suffix in that compiler family is p152-r02, not the old r01.
"""
import argparse
import contextlib
import io
import json
import re
import sys
import time
import unittest
from unittest.mock import patch
import build_current_stored_generation as b

s=b.prepared
c=s.c
SELF='tools/p09/build_immutable_graph_product.py'
TEST='tools/p09/tests/test_immutable_graph_product_build.py'
RUN=2
PARENT=dict(path='implementation/p09/evidence/p09-156-immutable-graph.source-closing-run02.v1.json',
    bytes=252223,sha256='451472c39ead329c947e3efe623d39a647c6baf18ed1d8bd0863a669166f7407')
PASS='PASS_CURRENT_IMMUTABLE_GRAPH_PRODUCT_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
CONTRACT_COUNT=36


def require(ok,code):s.require(ok,'P157_BUILD_'+code)


def parent_scope(row):
    require(isinstance(row,dict) and row.get('state')=='PASS_CURRENT_IMMUTABLE_GRAPH_DELTA_AND_UNITS15_ONLY_NOT_FULL249_OR_GATE'
        and row.get('source_closing_exact') is True and row.get('whole_original_core_inverse_exact') is True
        and row.get('all_original_domain_tests_preserved') is True and row.get('actual_unit_tests_passed')==15
        and row.get('typecheck_accepted') is True and row.get('protected_EXE_inputs_exact')==60
        and row.get('current_Rust_input_count')==785 and row.get('resource_stop_reason') is None
        and row.get('resource_watcher_cleanup_confirmed') is True,'PARENT_SCOPE')
    for key in ('current_compiled249_qualified','full249_current_qualified','signed16_current_qualified',
            'product_complete','PC_freeze_resolved','full_product_performance_improvement_measured'):
        require(row.get(key) is False,'NO_PRIOR_PRODUCT_PROMOTION')
    require(row.get('P09_gate')=='OPEN','PARENT_GATE')
    expected=s.inputs.inventory(row['bound_input_pins'],1246)
    protected={n:p for n,p in expected.items() if n.endswith('.exe')}
    require(len(protected)==61 and expected.get(row['fresh_domain_unit_executable_pin']['path'])==row['fresh_domain_unit_executable_pin'],
        'ALL60_OLD_PLUS1_DOMAIN_EXE')
    changes=s.inputs.inventory(row['declared_Rust_source_changes'],2)
    require(set(changes)=={'crates/domain-ir/src/document_graph.rs','crates/domain-ir/tests/document_graph.rs'}
        and all(expected.get(n)==p for n,p in changes.items()),'DECLARED_DELTA_EXACT')
    return expected,protected


def fresh_scope(protected):
    name=b.executable_name(RUN)
    require(name=='target/p09-149-conservative/debug/deps/form_stored_provider-p152-r02.exe'
        and name not in protected,'NEW_FAMILY_SUFFIX_NOT_HISTORY')
    s.scoped_path(name,fresh=True)
    return name


def source_scope(q,expected):
    def read(n):
        require(n in expected,'MODULE_SCOPE');text=q.text(n)
        require(q.reader.snapshots[n]==expected[n],'MODULE_BYTES_EXACT');return text
    names,modules=s.profile.signed.previous.parent.recursive_names(read,'stored-form-tests')
    s.profile.signed.previous.original.select_names(names)
    old=q.json(s.HISTORICAL_INVENTORY)
    require(len(names)==249 and len(modules)==59 and old['source_test_names']==list(names)
        and old['source_module_instances']==list(modules)
        and old['test_package_profile_config']==list(b.CONFIG),'ALL_ORIGINAL249_59_PROFILE81')
    require(len(b.CONFIG)==81,'PROFILE81')
    return list(names),list(modules)


def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
        ('test_build_current_stored_generation','test_signed_durable_build_stream','test_immutable_graph_product_build'))
    # Original stream cases use in-memory fake pipes; no real OS child permitted.
    with patch('subprocess.Popen',side_effect=AssertionError('P157_LIGHT_CHILD_FORBIDDEN')), \
            patch('subprocess.run',side_effect=AssertionError('P157_LIGHT_CHILD_FORBIDDEN')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    failures=sorted({getattr(t,'test_case',t).id().split('.')[-1] for t,_ in checked.failures+checked.errors+checked.skipped})
    require(checked.wasSuccessful() and checked.testsRun==CONTRACT_COUNT and not checked.skipped,'CONTRACT36')
    return dict(contract_tests_run=checked.testsRun,contract_tests_passed=checked.testsRun,failed_tests=failures)


def helpers():
    result={SELF,TEST,b.TEST,'tools/p09/tests/test_signed_durable_build_stream.py',PARENT['path']}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            path=c.Path(file).absolute()
            if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':result.add(path.relative_to(c.ROOT).as_posix())
    return sorted(result)


def load_binding():
    resources=s.SQLRuntimeResources();state={}
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_P156_CLOSING')
        expected,protected=parent_scope(q.json(PARENT['path']))
        for n,p in expected.items():require(q.pin(n)==p,'WHOLE_PARENT_INPUTS_CURRENT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        fresh_scope(protected);source_scope(q,expected);contracts();local=helpers()
        for n in local:expected[n]=q.pin(n)
        q.finish();return expected,list(protected.values()),local
    finally:require(s.finish_watcher(resources,state),'LOAD_WATCHER_CLEANUP')


def run_owned(destination,expected,protected,local):
    dump=json.dump
    def write(row,stream,**kw):
        accepted=row.get('current_build_binding_accepted') is True
        if row.get('state')==b.legacy.PASS:row['state']=PASS
        row.pop('current_dev_package_profile_config',None)
        row.pop('parent_example_audit_pin',None)
        row.update(schema_version='hwpx-agent.p09-immutable-graph-product-build/v1',
            whole_workspace_Rust_input_count=785,current_test_package_profile_config=list(b.CONFIG),
            current_graph_delta_closing_pin=PARENT,protected_executables_expected=61,
            previous_parent_EXE_inputs_preserved=61,source249_generation_connected_to_actual_build=True,
            build_only_accepted=accepted,compile_recipe=s.recipe(RUN),
            current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
            compiled249_listing_required_before_runtime=True,runtime_tests_executed=False,
            full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for name,value in (('SELF',SELF),('TARGET',b.TARGET),('ARGS',b.ARGS),('DEV_CONFIG',b.CONFIG),
                ('task_for',b.task_for),('run_for',b.run_for),('executable_name',b.executable_name),
                ('parse_build',b.parse_build),('AUDIT_PIN',PARENT)):
            stack.enter_context(patch.object(b.legacy,name,value))
        stack.enter_context(patch.object(json,'dump',write))
        return b.legacy.run_owned(RUN,destination,expected,protected,local)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('light','actual'),required=True);a=parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD')
    destination=s.scoped_path(f'implementation/p09/evidence/p09-157-immutable-graph-product-build.{a.mode}-run01.v1.json',fresh=True)
    if a.mode=='actual':return run_owned(destination,*load_binding())
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',product_complete=False,P09_gate='OPEN',actual_Cargo_SQL_native_executed=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources)
        for n in (SELF,TEST,b.SELF,b.TEST,'tools/p09/tests/test_signed_durable_build_stream.py'):q.pin(n)
        out.update(contracts());q.finish();out.update(state='PASS_IMMUTABLE_GRAPH_BUILD_CONTRACTS_ONLY_NOT_PRODUCT_OR_GATE',source_closing_exact=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:out['error_code']=str(e) if isinstance(e,ValueError) else 'P157_LIGHT_REDACTED'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:
            require(sys.argv[3]==b.task_for(RUN),'CLOSED_WORKER_TASK');raise SystemExit(b.worker(sys.argv[3]))
        raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,b.subprocess.SubprocessError) as e:
        code=str(e) if isinstance(e,ValueError) else 'P157_BUILD_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P157_BUILD_REDACTED_FAILURE')))
        raise SystemExit(2) from None
