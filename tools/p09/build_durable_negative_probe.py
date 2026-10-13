"""P151 non-test runtime: reuse cache, preserve all 53 prior EXEs; NOT SQL/Gate.

과거 P150 실행기/stream/supervisor는 수정하지 않는다. 현재 P151 whole-source
closing을 새 입력으로 결합하고 run-specific rustc suffix에만 결과를 만든다.
"""
import argparse
import base64
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import unittest
from unittest.mock import patch
import build_signed_durable_probe as legacy
import run_durable_negative_example_tests as parent

c=legacy.c
SELF='tools/p09/build_durable_negative_probe.py'
TEST='tools/p09/tests/test_build_durable_negative_probe.py'
TARGET=parent.TARGET
ARGS=legacy.ARGS
DEV_CONFIG=legacy.DEV_CONFIG
AUDIT_PIN=dict(path='implementation/p09/evidence/p09-151-durable-negative.terminal-audit-run02.v1.json',
    bytes=296406,sha256='d3006b6b871b390d32593c81079aef04d01e0404dcbf04b25b39c9a9bdb5c307')
PASS='PASS_CURRENT_DS06_NON_TEST_RUNTIME_BUILD_ONLY_NOT_SQL_NATIVE_OR_GATE'
RAW_PARSE=legacy.parse_build


def require(ok,code):c.require(ok,'P151_BUILD_'+code)


def task_for(run):
    require(type(run) is int and 1<=run<=99,'RUN_SCOPE')
    return f'p151-durable-negative-probe-build-r{run:02}'


def run_for(task):
    require(isinstance(task,str) and re.fullmatch(r'p151-durable-negative-probe-build-r[0-9]{2}',task),'TASK_SCOPE')
    run=int(task[-2:]);require(task_for(run)==task,'TASK_SCOPE');return run


def executable_name(run):
    task_for(run)
    return (TARGET/'debug/examples'/f'formula_issuer_product_postgres_probe-p151-r{run:02}.exe').relative_to(c.ROOT).as_posix()


def parse_build(output,run,*,require_stream=False):
    task_for(run)
    with patch.object(legacy,'TARGET',TARGET),patch.object(legacy,'executable_name',executable_name):
        return RAW_PARSE(output,run,require_stream=require_stream)


def worker(task):
    run=run_for(task)
    def selected(args,**kw):
        require(args[1:]==[*ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(TARGET)],'WORKER_ARGUMENT_SCOPE')
        env=dict(kw['env'])
        require(all(not env.get(k) for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER',
            'RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')),'AMBIENT_COMPILER_OVERRIDE')
        for name in ('P150_BLOB_ROOT','P150_BLOB_RUN_ID','P150_BLOB_MODE'):env.pop(name,None)
        env.update(CARGO_PROFILE_DEV_OPT_LEVEL='0',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_INCREMENTAL='0')
        actual=[args[0],*[v for entry in DEV_CONFIG for v in ('--config',entry)],*args[1:],
            '--message-format=json','--','-C',f'extra-filename=-p151-r{run:02}']
        kw['env']=env
        return legacy.stream.run_command(actual,kw,lambda output:parse_build(output,run,require_stream=True))
    with patch.object(c,'TARGET',TARGET),patch.object(c,'TASKS',{task:ARGS}),patch.object(subprocess,'call',selected):
        return c.worker(task)


def load_binding():
    resources=parent.SQLRuntimeResources();state={}
    try:
        resources.admit();q=parent.LiveSQLReader(resources)
        require(q.pin(AUDIT_PIN['path'])==AUDIT_PIN,'IMMUTABLE_PARENT_AUDIT')
        prior=q.json(AUDIT_PIN['path'])
        require(prior['state']=='PASS_CURRENT_SERVICE_OWNED_DISK_NEGATIVE_UNITS27_ONLY_NOT_SQL_NATIVE_OR_GATE'
            and prior['source_closing_exact'] and prior['actual_example_tests_passed']==27
            and prior['contract_tests_passed']==10 and prior['current_Rust_input_count']==785
            and prior['protected_executables_exact']==52
            and prior['actual_SQL_metadata_or_signed_consumer_controls_qualified'] is False,'PARENT_SCOPE')
        expected={p['path']:p for p in prior['bound_input_pins']}
        require(len(expected)==len(prior['bound_input_pins']),'PARENT_UNIQUE')
        for name,pin in expected.items():require(q.pin(name)==pin,'UNCHANGED_PARENT_INPUT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and parent.original.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        for item in q.json(parent.ARCHIVE)['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            require(parent.recovered(raw,parent.restore_previous(item['path'],q.text(item['path'])))==raw,'WHOLE_PRIOR_BODY')
        for item in q.json(parent.original.ARCHIVE)['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            previous=parent.restore_previous(item['path'],q.text(item['path']))
            require(parent.recovered(raw,parent.original.restore_original(item['path'],previous))==raw,'WHOLE_ORIGINAL_BODY')
        actual=q.json(prior['actual_receipt_pin']['path'])
        require(q.pin(prior['actual_receipt_pin']['path'])==prior['actual_receipt_pin'],'PARENT_ACTUAL_PIN')
        protected=[*actual['protected_executables'],prior['compiled_test_artifact']]
        require(len(protected)==len({p['path'] for p in protected})==53,'PROTECTED53')
        for pin in protected:
            require(q.pin(pin['path'])==pin and pin['path'] in expected and expected[pin['path']]==pin,'OLD_EXE_EXACT')
            require(not re.fullmatch(r'formula_issuer_product_postgres_probe-p151-r[0-9]{2}\.exe',c.Path(pin['path']).name),'NEW_SUFFIX_NOT_HISTORY')
        helpers={SELF,TEST,AUDIT_PIN['path']}
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers):expected[name]=q.pin(name)
        q.finish();return expected,protected,sorted(helpers)
    finally:require(parent.finish_watcher(resources,state),'WATCHER_CLEANUP')


def run_owned(run,destination,expected,protected,helpers):
    dump=json.dump
    def write(row,stream,**kw):
        accepted=row.get('current_build_binding_accepted') is True
        if row.get('state')==legacy.PASS:row['state']=PASS
        row.update(schema_version='hwpx-agent.p09-current-ds06-runtime-build/v1',
            provided_driver_generation='P151_R31_CURRENT_DS06_NON_TEST',whole_workspace_Rust_input_count=785,
            parent_example_audit_pin=AUDIT_PIN,protected_executables_expected=53,
            whole_prior_R29_and_preP150_bodies_restored_exact=True,cache_target_reused=True,
            distinct_output_suffix_preserves_prior_unit_executable=True,prior_unit27_not_reexecuted=True,
            runtime_only_build_accepted=accepted,actual_SQL_metadata_or_signed_consumer_qualified=False,
            full_durable_DS01_DS09_qualified=False,independent_restart_or_key_custody_qualified=False,
            remaining_non_permission_work_units=76)
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for name,value in (('SELF',SELF),('TARGET',TARGET),('task_for',task_for),('run_for',run_for),
                ('executable_name',executable_name),('parse_build',parse_build),('AUDIT_PIN',AUDIT_PIN)):
            stack.enter_context(patch.object(legacy,name,value))
        stack.enter_context(patch.object(json,'dump',write))
        return legacy.run_owned(run,destination,expected,protected,helpers)


def light(run):
    resources=parent.SQLRuntimeResources();out={}
    try:
        resources.admit();q=parent.LiveSQLReader(resources)
        pins=[q.pin(n) for n in (SELF,TEST,'tools/p09/build_signed_durable_probe.py',
            'tools/p09/signed_durable_build_stream.py','tools/p09/tests/test_signed_durable_build_stream.py')]
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in
            ('test_build_durable_negative_probe','test_signed_durable_build_stream'))
        with patch('subprocess.Popen',side_effect=AssertionError('P151_BUILD_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_BUILD_LIGHT_CHILD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed={getattr(t,'test_case',t).id() for t,_ in checked.errors+checked.failures+checked.skipped}
        out.update(state='PASS_P151_BUILD_CONTRACT_ONLY_NOT_COMPILED_SQL_OR_GATE' if checked.wasSuccessful()
            and checked.testsRun==22 and not checked.skipped else 'FAILED_NOT_ACCEPTED',tests_run=checked.testsRun,
            tests_passed=checked.testsRun-len(failed),failed_tests=sorted(n.split('.')[-1] for n in failed),source_freeze=pins)
        q.finish();out.update(source_closing_exact=True,IO=q.summary(),raw_logs_included=False,
            actual_compile_SQL_native_executed=False,P09_gate='OPEN',product_complete=False)
    finally:parent.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
    destination=parent.scoped_path(f'implementation/p09/evidence/p09-151-runtime-build.light-run{run:02}.v1.json',fresh=True)
    with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
    print(json.dumps({k:out.get(k) for k in ('state','tests_run','tests_passed','failed_tests','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out.get('resource_watcher_cleanup_confirmed') and not resources.reason else 2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--mode',choices=('light','actual'),required=True);args=parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD')
    if args.mode=='light':return light(args.run)
    destination=parent.scoped_path(f'implementation/p09/evidence/p09-151-runtime-build.actual-run{args.run:02}.v1.json',fresh=True)
    parent.scoped_path(executable_name(args.run),fresh=True)
    expected,protected,helpers=load_binding()
    return run_owned(args.run,destination,expected,protected,helpers)


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,TypeError,KeyError,subprocess.SubprocessError) as error:
        value=str(error) if isinstance(error,ValueError) else 'P151_BUILD_REDACTED_FAILURE'
        code=value if len(value)<=160 and re.fullmatch('[A-Z_]+',value) else 'P151_BUILD_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code)));raise SystemExit(2) from None
