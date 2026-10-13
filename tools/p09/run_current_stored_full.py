"""Current fresh EXE, ALL original249, same1200s/owned caps/captured terse.

과거 RAM-stop 증거나 compiled listing을 runtime PASS로 바꾸지 않는다.
원래 FullCapture의 complete249/zero-failed/ignored/filtered 조건을 그대로
재사용하며 현재 compiled249 closure와 fresh EXE hash를 실행 전후 결합한다.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import run_current_stored_inventory as inventory
import run_compression_full_stored as full

c=inventory.c
SELF='tools/p09/run_current_stored_full.py'
TEST='tools/p09/tests/test_current_stored_full.py'
TASK_ARGS=full.ARGS
MAXIMUM_SECONDS=full.MAXIMUM_SECONDS
PARENT=dict(path='implementation/p09/evidence/p09-152-current-stored-inventory.terminal-audit-run01.v1.json',
    bytes=332858,sha256='a8e3c4385af9dd05819ba85055cbfc84884fccf8b60b9918c107e8b445a65f46')
PASS='PASS_CURRENT_FRESH_UNFILTERED_FULL249_ONLY_NOT_SQL_NATIVE_OR_GATE'


def require(ok,code):c.require(ok,'P152_FULL_'+code)


def task_for(run):
    inventory.build.prepared.generation(run);return f'p152-current-stored-full-r{run:02}-tests'


def run_for(task):
    match=re.fullmatch(r'p152-current-stored-full-r([0-9]{2})-tests',task) if isinstance(task,str) else None
    require(match is not None,'TASK_SCOPE');run=int(match[1]);require(task_for(run)==task,'TASK_SCOPE');return run


def require_scope(seconds):
    require(type(seconds) is int and seconds==MAXIMUM_SECONDS==1200,'ORIGINAL1200_SCOPE')
    inventory.build.prepared.profile.config_contract(inventory.build.CONFIG)


def worker(task):
    run_for(task);require_scope(MAXIMUM_SECONDS);call=subprocess.call
    def selected(args,**kw):
        require(args[1:]==[*TASK_ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(c.TARGET),
            '--','--test-threads=1'] and kw.get('cwd')==c.ROOT and kw.get('stdin')==subprocess.DEVNULL,'NO_FILTER_EXACT_WORKER')
        env=kw['env'];require(all(env.get(k)==v for k,v in dict(CARGO_BUILD_JOBS='1',CARGO_PROFILE_TEST_OPT_LEVEL='0',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_CODEGEN_UNITS='16',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0').items()),'ORIGINAL_CHECKS_ENVIRONMENT')
        kw['env']=dict(env,RUST_TEST_NOCAPTURE='0')
        return call([str(c.ROOT/inventory.build.executable_name(1)),'--test-threads=1','--format=terse'],**kw)
    with patch.object(c,'TASKS',{task:TASK_ARGS}),patch.object(subprocess,'call',selected):return c.worker(task)


def load_binding():
    resources=inventory.build.prepared.SQLRuntimeResources();state={}
    try:
        resources.admit();q=inventory.build.prepared.LiveSQLReader(resources)
        require(q.pin(PARENT['path'])==PARENT,'IMMUTABLE_CURRENT_COMPILED249_CLOSING')
        parent=q.json(PARENT['path'])
        require(parent['state']=='PASS_CURRENT_FRESH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_TEST_RUNTIME_SQL_NATIVE_OR_GATE'
            and parent['source_closing_exact'] and parent['current_compiled249_qualified'] is True
            and parent['compiled_test_count']==249 and parent['source_module_instance_count']==59
            and parent['contract_tests_passed']==34 and parent['current_Rust_input_count']==785
            and parent['protected_parent_EXE_inputs_exact']==60 and parent['runtime_test_bodies_executed'] is False
            and parent['full249_current_qualified'] is False and parent['signed16_current_qualified'] is False
            and parent['resource_stop_reason'] is None and parent['resource_watcher_cleanup_confirmed'],'PARENT_SCOPE')
        expected=inventory.build.prepared.inputs.inventory(parent['bound_input_pins'],1203)
        for name,pin in expected.items():require(q.pin(name)==pin,'CURRENT_INPUT_DRIFT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and inventory.build.prepared.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        exe=parent['compiled_test_executable_pin']
        require(exe['path']==inventory.build.executable_name(1) and expected[exe['path']]==exe,'FRESH_CURRENT_EXE')
        def read(name):
            require(name in expected,'MODULE_SCOPE');value=q.text(name)
            require(q.reader.snapshots[name]==expected[name],'MODULE_FRESH');return value
        names,modules=inventory.PARENT.recursive_names(read,'stored-form-tests')
        full.cost.original.select_names(names)
        require(names==parent['source_test_names'] and modules==parent['source_module_instances'] and len(modules)==59,'EXACT_COMPILED249_59')
        helpers={SELF,TEST,PARENT['path'],'tools/p09/tests/test_compression_full_stored.py'}
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers):expected[name]=q.pin(name)
        q.finish();return expected,names,modules,exe
    finally:require(inventory.build.prepared.finish_watcher(resources,state),'WATCHER_CLEANUP')


def run_owned(run,destination,expected,names,modules,exe):
    require_scope(MAXIMUM_SECONDS);task=task_for(run);raw_pins=c.pins;dump=json.dump
    captures=[];accepted_final=False;revalidated=False
    class Capture(full.FullCapture):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);captures.append(self)
    def pins(checkpoint=None):
        nonlocal revalidated
        actual=raw_pins(checkpoint);seen={p['path']:p for p in actual}
        require(all(seen.get(n)==p for n,p in expected.items()),'FRESH_CURRENT_INPUTS')
        if not revalidated:
            resources=inventory.build.prepared.SQLRuntimeResources();state={}
            try:resources.admit();revalidated=True
            finally:require(inventory.build.prepared.finish_watcher(resources,state),'POST_HASH_WATCHER_CLEANUP')
        return actual
    def write(row,stream,**kw):
        nonlocal accepted_final
        capture=captures[-1] if captures else None
        accepted=row['state']=='PASS_SCOPED_NOT_GATE' and bool(capture and capture.accepted)
        accepted_final=accepted
        if row['state']=='PASS_SCOPED_NOT_GATE':
            row['state']=PASS if accepted else 'STOPPED_NOT_ACCEPTED'
            if not accepted:row['stop_reason']='FULL_COMPLETE_RESULT_MISSING'
        row.update(schema_version='hwpx-agent.p09-current-fresh-full249/v1',
            source_test_names=list(names),source_module_instances=list(modules),expected_test_count=249,
            selected_test_names=list(names),tests_passed=249 if accepted else None,
            full249_current_qualified=accepted,signed16_current_qualified=accepted,
            signed_original_test_name=full.cost.original.NAME,
            qualification_basis='exact_current_fresh_compiled249_unfiltered_all249_passed_zero_failed_ignored_filtered',
            current_Rust_input_count=785,current_compiled249_qualified=True,current_inventory_closing_pin=PARENT,
            compiled_test_executable_pin=exe,test_package_profile_config=list(inventory.build.CONFIG),
            capture_diagnostics=capture.diagnostics() if capture else None,
            post_hash_runtime_admission_revalidated=revalidated,runtime_admission_RAM_percent=10,
            test_body_execution_authorized=bool(row['writer_authorized']),actual_new_Cargo_compile_executed=False,
            native_or_SQL_run=False,original_test_bodies_or_product_sources_changed=False,
            original_owned_resource_policy_changed=False,raw_logs_printed_or_saved=False,PC_freeze_resolved=False,
            remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{task:TASK_ARGS}), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(full.bounded,'BoundedProcessCapture',Capture),patch.object(json,'dump',write):
        result=c.run(task,destination,MAXIMUM_SECONDS)
    return 0 if accepted_final else result


def light(run):
    resources=inventory.build.prepared.SQLRuntimeResources();q=None;out=dict(state='FAILED_NOT_ACCEPTED')
    destination=inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-full.light-run{run:02}.v1.json',fresh=True)
    try:
        resources.admit();q=inventory.build.prepared.LiveSQLReader(resources)
        for name in (SELF,TEST,full.SELF,full.TEST):q.pin(name)
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_current_stored_full','test_compression_full_stored'))
        with patch('subprocess.Popen',side_effect=AssertionError('P152_FULL_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P152_FULL_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P152_FULL_LIGHT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed=sorted({getattr(t,'test_case',t).id().split('.')[-1] for t,_ in checked.failures+checked.errors+checked.skipped})
        passed=checked.wasSuccessful() and checked.testsRun==25 and not checked.skipped
        q.finish();out.update(state='PASS_CURRENT_FULL249_CONTRACT_ONLY_NOT_RUNTIME_SQL_NATIVE_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            contract_tests_run=checked.testsRun,contract_tests_passed=checked.testsRun-len(failed),failed_tests=failed,
            source_closing_exact=True,actual_Cargo_EXE_SQL_native_executed=False,full249_current_qualified=False,
            signed16_current_qualified=False,product_complete=False,P09_gate='OPEN')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out['error_code']=closed_error(error)
    finally:
        inventory.build.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_run','contract_tests_passed','failed_tests','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


def closed_error(error):
    value=str(error) if isinstance(error,ValueError) else 'P152_FULL_REDACTED_FAILURE'
    return value if re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'P152_FULL_REDACTED_FAILURE'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--mode',choices=('light','actual'),required=True);args=parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD');require_scope(MAXIMUM_SECONDS)
    if args.mode=='light':return light(args.run)
    destination=inventory.build.prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-full.actual-run{args.run:02}.v1.json',fresh=True)
    return run_owned(args.run,destination,*load_binding())


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=closed_error(error))));raise SystemExit(2) from None
