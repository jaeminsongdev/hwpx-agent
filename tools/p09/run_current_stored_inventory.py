"""Execute ONLY fresh libtest --list, current whole source and original owned caps."""
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
import unittest
from unittest.mock import patch
import build_current_stored_generation as build

c=build.c
SELF='tools/p09/run_current_stored_inventory.py'
TEST='tools/p09/tests/test_current_stored_inventory.py'
ARCHIVE='implementation/p09/source-archive/p09-152-pre-inventory-exit-adapter-r34/source-preimages.v1.json'
CLOSING=dict(path='implementation/p09/evidence/p09-152-current-stored-build.terminal-audit-run01.v1.json',
    bytes=289819,sha256='edde914ab29feae0286ff03ea0005c12604e42f3b53ab60b49d972502d514d5a')
EXE_RUN=1
ARGS=build.ARGS
PARENT=build.prepared.profile.signed.previous.parent
PASS='PASS_CURRENT_FRESH_EXE_COMPILED249_LISTING_ONLY_NOT_TEST_RUNTIME_SQL_NATIVE_OR_GATE'


def require(ok,code):c.require(ok,'P152_INVENTORY_'+code)


def task_for(run):
    build.prepared.generation(run);return f'p152-current-stored-inventory-r{run:02}'


def run_for(task):
    require(isinstance(task,str) and re.fullmatch(r'p152-current-stored-inventory-r[0-9]{2}',task),'TASK_SCOPE')
    run=int(task[-2:]);require(task_for(run)==task,'TASK_SCOPE');return run


def validate_listing(output,names):
    PARENT.validate_listing(output,names,'stored-form-tests')


def worker(task):
    run_for(task);call=subprocess.call
    def selected(args,**kw):
        require(args[1:]==[*ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(c.TARGET)]
            and kw.get('cwd')==c.ROOT and kw.get('stdin')==subprocess.DEVNULL,'EXACT_WORKER_SCOPE')
        kw['env']=dict(kw['env'],RUST_TEST_NOCAPTURE='0')
        return call([str(c.ROOT/build.executable_name(EXE_RUN)),'--list','--format=terse'],**kw)
    with patch.object(c,'TASKS',{task:ARGS}),patch.object(subprocess,'call',selected):return c.worker(task)


def load_binding():
    resources=build.prepared.SQLRuntimeResources();state={}
    try:
        resources.admit();q=build.prepared.LiveSQLReader(resources)
        require(q.pin(CLOSING['path'])==CLOSING,'IMMUTABLE_CURRENT_COMPILE_CLOSING')
        closing=q.json(CLOSING['path'])
        require(closing['state']=='PASS_CURRENT_LIBTEST_BUILD_CLOSING_ONLY_NOT_COMPILED249_LISTING_RUNTIME_SQL_OR_GATE'
            and closing['source_closing_exact'] and closing['contract_tests_passed']==26
            and closing['current_Rust_input_count']==785 and closing['current_source_test_count']==249
            and closing['current_source_module_instance_count']==59 and closing['protected_executables_exact']==54
            and closing['parent_EXE_inputs_preserved']==59 and closing['current_compiled249_qualified'] is False
            and closing['full249_current_qualified'] is False and closing['resource_stop_reason'] is None
            and closing['resource_watcher_cleanup_confirmed'],'CLOSING_SCOPE')
        build.profile_scope(closing['actual_libtest_profile'])
        expected=build.prepared.inputs.inventory(closing['bound_input_pins'],1196)
        for name,pin in expected.items():require(q.pin(name)==pin,'CURRENT_INPUT_DRIFT')
        exe=closing['compiled_test_executable_pin']
        require(exe['path']==build.executable_name(EXE_RUN) and expected[exe['path']]==exe,'EXACT_CURRENT_EXE')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and build.prepared.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        def read(name):
            require(name in expected,'MODULE_SCOPE');value=q.text(name)
            require(q.reader.snapshots[name]==expected[name],'MODULE_FRESH');return value
        names,modules=PARENT.recursive_names(read,'stored-form-tests')
        build.prepared.profile.signed.previous.original.select_names(names);require(len(modules)==59,'WHOLE59_MODULES')
        archive=q.json(ARCHIVE);light=q.json(archive['light_receipt_pin']['path'])
        require(q.pin(archive['light_receipt_pin']['path'])==archive['light_receipt_pin']
            and light['state']=='PASS_CURRENT_EXE_INVENTORY_CONTRACT_ONLY_NOT_LISTING_RUNTIME_OR_GATE'
            and light['tests_run']==light['tests_passed']==8,'PRE_ADAPTER_LIGHT_SCOPE')
        require(len(archive['files'])==1,'PRE_ADAPTER_SOURCE_COUNT')
        item=archive['files'][0];raw=base64.b64decode(item['base64'],validate=True)
        require(item['path']==SELF and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
            and {k:item[k] for k in ('path','bytes','sha256')} in light['bound_input_pins'],'PRE_ADAPTER_WHOLE_SOURCE')
        helpers={SELF,TEST,ARCHIVE,archive['light_receipt_pin']['path'],CLOSING['path']}
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers):expected[name]=q.pin(name)
        q.finish();return expected,names,modules,exe
    finally:require(build.prepared.finish_watcher(resources,state),'WATCHER_CLEANUP')


def run_owned(run,destination,expected,names,modules,exe):
    task=task_for(run);raw_pins=c.pins;dump=json.dump;captures=[];accepted_final=False
    class Capture(build.legacy.original.capture.FullCapture):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);captures.append(self)
        def communicate(self,timeout):
            output,errors=build.legacy.RAW_CAPTURE.communicate(self,timeout)
            if self.process.returncode==0:
                validate_listing(output,names);require(errors=='','UNEXPECTED_STDERR');self.accepted=True
            return output,errors
    def pins(checkpoint=None):
        actual=raw_pins(checkpoint);seen={p['path']:p for p in actual}
        require(all(seen.get(n)==p for n,p in expected.items()),'FRESH_CURRENT_INPUTS');return actual
    def write(row,stream,**kw):
        nonlocal accepted_final
        accepted=row['state']=='PASS_SCOPED_NOT_GATE' and bool(captures and captures[-1].accepted)
        accepted_final=accepted
        if row['state']=='PASS_SCOPED_NOT_GATE':row['state']=PASS if accepted else 'STOPPED_NOT_ACCEPTED'
        row.update(schema_version='hwpx-agent.p09-current-fresh-libtest-inventory/v1',
            compiled_inventory_exact=accepted,current_compiled249_qualified=accepted,
            source_test_names=list(names),source_module_instances=list(modules),expected_test_count=249,
            current_Rust_input_count=785,compiled_test_executable_pin=exe,current_compile_closing_pin=CLOSING,
            test_package_profile_config=list(build.CONFIG),runtime_tests_executed=False,
            fresh_EXE_list_only=True,full249_current_qualified=False,signed16_current_qualified=False,
            capture_diagnostics=captures[-1].diagnostics() if captures else None,
            remaining_non_permission_work_units=76,PC_freeze_resolved=False)
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TASKS',{task:ARGS}), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',pins), \
            patch.object(build.legacy.original.capture.bounded,'BoundedProcessCapture',Capture),patch.object(json,'dump',write):
        result=c.run(task,destination,180)
    return 0 if accepted_final else result


def light(run):
    resources=build.prepared.SQLRuntimeResources();out={}
    try:
        resources.admit();q=build.prepared.LiveSQLReader(resources)
        for name in (SELF,TEST,ARCHIVE):q.pin(name)
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.defaultTestLoader.loadTestsFromName('test_current_stored_inventory')
        with patch('subprocess.Popen',side_effect=AssertionError('P152_INVENTORY_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P152_INVENTORY_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P152_INVENTORY_LIGHT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed=sorted({getattr(t,'test_case',t).id().split('.')[-1] for t,_ in checked.failures+checked.errors+checked.skipped})
        passed=checked.wasSuccessful() and checked.testsRun==8 and not checked.skipped
        q.finish();out.update(state='PASS_CURRENT_EXE_INVENTORY_CONTRACT_ONLY_NOT_LISTING_RUNTIME_OR_GATE' if passed else 'FAILED_NOT_ACCEPTED',
            tests_run=checked.testsRun,tests_passed=checked.testsRun-len(failed),failed_tests=failed,
            source_closing_exact=True,actual_EXE_executed=False,product_complete=False,P09_gate='OPEN')
    finally:build.prepared.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
    out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
    if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
    destination=build.prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-inventory.light-run{run:02}.v1.json',fresh=True)
    with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
    print(json.dumps({k:out.get(k) for k in ('state','tests_run','tests_passed','failed_tests','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--mode',choices=('light','actual'),required=True);args=parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD')
    if args.mode=='light':return light(args.run)
    destination=build.prepared.scoped_path(f'implementation/p09/evidence/p09-152-current-stored-inventory.actual-run{args.run:02}.v1.json',fresh=True)
    return run_owned(args.run,destination,*load_binding())


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) else 'P152_INVENTORY_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P152_INVENTORY_REDACTED_FAILURE')))
        raise SystemExit(2) from None
