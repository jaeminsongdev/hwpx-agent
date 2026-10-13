"""P151 current generation, old19+new8 real-service unit controls; NOT SQL/Gate.

새 target에서만 compile-no-run→reported unit EXE를 실행한다. r29 whole preimages
inverse와 모든 unchanged prior inputs/protected52를 결합하며 과거 EXE를 덮어쓰지 않는다.
"""
import argparse
import base64
import hashlib
import io
import json
import re
import os
import subprocess
import sys
import unittest
from unittest.mock import patch
import run_signed_durable_example_tests as original
from live_sql_evidence_reader import LiveSQLReader
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher
from sql_owned_execution import scoped_path

c=original.c
SELF='tools/p09/run_durable_negative_example_tests.py'
TEST='tools/p09/tests/test_durable_negative_example_tests.py'
SOURCE='crates/product-cli/examples/formula_issuer_product_postgres_probe/durable_negative.rs'
ARCHIVE='implementation/p09/source-archive/p09-151-pre-durable-negative-r30/Rust-preimages.v1.json'
PARENT_PIN=dict(path='implementation/p09/evidence/p09-150-durable-SQL-connection.terminal-audit-run01.v1.json',
    bytes=360847,sha256='b81df3bc862520361523c0f1643c3090221a90086db735e47d4d3375b733f4cf')
BUILD_PIN=dict(path='implementation/p09/evidence/p09-150-durable-probe-build.actual-run05.v1.json',
    bytes=370635,sha256='fb766c4981569a0f6d8140c10e066d23a01dc5e5da004616a602d2a684280ce2')
TARGET=c.ROOT/'target/p09-151-durable-negative/build'
TASK='p151-durable-negative-example-tests'
NEGATIVE_TESTS=('actual_service_local_disk_all_eight_controls_exact','memory_mode_cannot_claim_durable_negative_qualification',
    'head_change_never_becomes_negative_controls_pass','already_present_control_is_not_reingested_or_restamped',
    'synthetic_scanner_rejects_arbitrary_plaintext_or_kind','caller_without_write_scope_is_denied_before_control_ingest',
    'already_tampered_disk_is_not_rewritten_again','quarantined_record_cannot_be_selected_for_available_disk_tamper')
CONTROL_CHECKS=(
    'durable_negative_new_fixture_whole_AEAD_disk_read','durable_negative_wrong_key_denied',
    'durable_negative_ACL_grant_fresh_whole_read','durable_negative_ACL_revoke_deny_restore_fresh_read',
    'durable_negative_disk_tag_one_byte_tamper_exact','durable_negative_tampered_disk_ciphertext_denied',
    'durable_negative_quarantine_disk_relocation_and_read_denied','durable_negative_no_head_or_additional_ingest_change')
TOTAL=27


def require(ok,code):c.require(ok,'P151_'+code)


def restore_previous(name,text):
    if name==original.ROOT_SOURCE:
        marker='// P151 negative-controls module: private synthetic fixture only.\n'
        block=marker+'#[path = "formula_issuer_product_postgres_probe/durable_negative.rs"]\nmod durable_negative;\n// End P151 negative-controls module.\n'
        require(text.count(block)==1,'ROOT_MODULE_DELTA');return text.replace(block,'')
    if name==original.BACKEND_SOURCE:
        pattern=r'(?m)^    // P151 controlled-negative extension: never accepts a user artifact or raw path\.\n.*?^    // End P151 controlled-negative extension\.\n\n'
        result,count=re.subn(pattern,'',text,flags=re.DOTALL);require(count==1,'BACKEND_DELTA');return result
    require(name==original.PROVIDER_SOURCE,'SOURCE_DELTA_SCOPE')
    block='''    // P151 negative-controls extension: all original live negatives execute first.
    verify_live_approval(probe, p, provider, &prepared, &raw, &wanted, binding)?;
    if p.blobs.is_durable() {
        super::durable_negative::exercise(probe, metadata, p.blobs, p.context, || {
            Ok(revisions.head(&ctx, p.project, branch()?)? == head)
        })?;
    }
    Ok(())
    // End P151 negative-controls extension.
'''
    require(text.count(block)==1,'CONSUMER_DELTA');return text.replace(block,
        '    verify_live_approval(probe, p, provider, &prepared, &raw, &wanted, binding)\n')


def recovered(raw,text):
    return text.replace('\n','\r\n').encode() if b'\r\n' in raw else text.encode()


def load_binding():
    resources=SQLRuntimeResources();state={}
    try:
        resources.admit();q=LiveSQLReader(resources)
        require(q.pin(PARENT_PIN['path'])==PARENT_PIN,'IMMUTABLE_R29_AUDIT')
        parent=q.json(PARENT_PIN['path'])
        require(parent['state']=='PASS_CURRENT_BUILD_AND_FAILED_PREFLIGHT_CLOSING_ONLY_NOT_SQL_DURABLE_OR_GATE'
            and parent['source_closing_exact'] and parent['tests_passed']==40 and parent['current_Rust_inputs']==784
            and parent['original_SQL_run_promoted_to_success'] is False,'PARENT_SCOPE')
        expected={p['path']:p for p in parent['bound_input_pins']}
        require(len(expected)==len(parent['bound_input_pins']),'PARENT_UNIQUE')
        archive=q.json(ARCHIVE);seen=set()
        for item in archive['files']:
            raw=base64.b64decode(item['base64'],validate=True);name=item['path'];pin={k:item[k] for k in ('path','bytes','sha256')}
            require(name in (original.ROOT_SOURCE,original.PROVIDER_SOURCE,original.BACKEND_SOURCE) and name not in seen
                and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'] and expected[name]==pin,'R29_WHOLE_PREIMAGES')
            current=q.text(name);require(recovered(raw,restore_previous(name,current))==raw,'WHOLE_PREVIOUS_BODY')
            expected[name]=q.pin(name);seen.add(name)
        require(len(seen)==3,'EXACT_THREE_DELTAS')
        for item in q.json(original.ARCHIVE)['files']:
            raw=base64.b64decode(item['base64'],validate=True)
            text=restore_previous(item['path'],q.text(item['path']))
            require(recovered(raw,original.restore_original(item['path'],text))==raw,'WHOLE_PRE_P150_ORIGINAL')
        for name,pin in expected.items():require(q.pin(name)==pin,'UNCHANGED_PRIOR_INPUT_DRIFT')
        source=q.text(SOURCE)
        require(tuple(re.findall(r'#\[test\]\s+fn ([a-z_]+)\(',source))==NEGATIVE_TESTS
            and len(re.findall(r'#\[test\]',source))==8,'EIGHT_NEGATIVE_TESTS')
        checks=re.search(r'pub\(super\) const CHECKS: \[&str; 8\] = \[(.*?)\];',source,re.DOTALL)
        require(checks is not None and tuple(re.findall(r'"([a-zA-Z0-9_]+)"',checks.group(1)))==CONTROL_CHECKS,'EXACT_EIGHT_CHECKS')
        require(len(re.findall(r'#\[test\]',q.text(original.BACKEND_SOURCE)))==8
            and len(re.findall(r'#\[test\]',q.text(original.PROVIDER_SOURCE)))==11,'ORIGINAL19_RETAINED')
        expected[SOURCE]=q.pin(SOURCE)
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and original.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        require(q.pin(BUILD_PIN['path'])==BUILD_PIN,'OLD_BUILD_IMMUTABLE')
        build=q.json(BUILD_PIN['path']);protected=[*build['protected_executables'],build['executable_pin']]
        require(len(protected)==len({p['path'] for p in protected})==52,'PROTECTED52')
        for pin in protected:
            require(not (c.ROOT/pin['path']).is_relative_to(TARGET) and q.pin(pin['path'])==pin,'OLD_EXE_PRESERVED')
            expected[pin['path']]=pin
        helpers={SELF,TEST,ARCHIVE,PARENT_PIN['path'],BUILD_PIN['path']}
        for module in tuple(sys.modules.values()):
            file=getattr(module,'__file__',None)
            if file:
                path=c.Path(file).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':helpers.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(helpers):expected[name]=q.pin(name)
        q.finish();return expected,protected,sorted(helpers)
    finally:require(finish_watcher(resources,state),'WATCHER_CLEANUP')


def variant():
    return (patch.object(original,'TARGET',TARGET),patch.object(original,'TASK',TASK),
        patch.object(original,'SELF',SELF),patch.object(original,'TOTAL_TEST_COUNT',TOTAL),
        patch.object(original,'TEST_NAMES',original.TEST_NAMES+NEGATIVE_TESTS))


def worker(task):
    require(task==TASK,'WORKER_TASK')
    require(all(not os.environ.get(n) for n in ('RUSTC','CARGO_BUILD_TARGET')),'AMBIENT_TARGET_OR_COMPILER_OVERRIDE')
    import contextlib
    with contextlib.ExitStack() as stack:
        for p in variant():stack.enter_context(p)
        return original.worker(task)


def run_owned(destination,expected,protected,helpers):
    import contextlib
    dump=json.dump
    def write(row,stream,**kw):
        accepted=row.get('example_backend_tests_qualified') is True and row.get('tests_passed')==27
        row.update(whole_workspace_Rust_input_count=785,original_backend_tests_retained=8,new_service_negative_tests=8,
            original_source_tests_retained=11,expected_example_test_count=27,provided_driver_generation='P151_R30_DS06',
            three_prior_source_bodies_restored_exact=True,whole_preP150_root_and_provider_restored_exact=True,
            historical_preP151_build_admission_is_current=False,actual_service_and_owned_disk_controls_qualified=accepted,
            actual_SQL_metadata_or_signed_consumer_controls_qualified=False,production_scanner_qualified=False,
            original_build_and_runtime_sources_modified=False,imported_helper_inventory=helpers,
            declared_control_check_names=list(CONTROL_CHECKS),full_durable_DS01_DS09_qualified=False,
            source_variant='P151_current_DS06_private_new_synthetic_artifact_original19_preserved')
        return dump(row,stream,**kw)
    with contextlib.ExitStack() as stack:
        for p in variant():stack.enter_context(p)
        stack.enter_context(patch.object(json,'dump',write))
        return original.run_owned(destination,expected,protected,task=TASK)


def light(run):
    resources=SQLRuntimeResources();row={}
    try:
        resources.admit();q=LiveSQLReader(resources)
        pins=[q.pin(n) for n in (SELF,TEST,SOURCE,ARCHIVE,original.ROOT_SOURCE,original.PROVIDER_SOURCE,original.BACKEND_SOURCE)]
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        suite=unittest.defaultTestLoader.loadTestsFromName('test_durable_negative_example_tests')
        with patch('subprocess.Popen',side_effect=AssertionError('P151_LIGHT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P151_LIGHT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P151_LIGHT_THREAD_FORBIDDEN')):
            checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
        failed={getattr(test,'test_case',test).id() for test,_ in checked.errors+checked.failures+checked.skipped}
        row.update(state='PASS_P151_SOURCE_CONTRACT_ONLY_NOT_COMPILED_SQL_OR_GATE' if checked.wasSuccessful() and not checked.skipped
            and checked.testsRun==10 else 'FAILED_NOT_ACCEPTED',tests_run=checked.testsRun,tests_passed=checked.testsRun-len(failed),
            failed_tests=sorted(n.split('.')[-1] for n in failed),source_freeze=pins)
        q.finish();row.update(source_closing_exact=True,IO=q.summary(),actual_compile_SQL_native_executed=False,
            P09_gate='OPEN',product_complete=False,remaining_non_permission_work_units=76,raw_logs_included=False)
    finally:
        finish_watcher(resources,row);row['resource_stop_reason']=resources.reason
    name=scoped_path(f'implementation/p09/evidence/p09-151-durable-negative.light-run{run:02}.v1.json',fresh=True)
    with name.open('x',encoding='utf-8') as stream:json.dump(row,stream,indent=2)
    print(json.dumps({k:row.get(k) for k in ('state','tests_run','tests_passed','failed_tests','resource_stop_reason')}))
    return 0 if row['state'].startswith('PASS_') and row.get('resource_watcher_cleanup_confirmed') and not resources.reason else 2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--mode',choices=('light','actual'),required=True);args=parser.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'REPOSITORY_CWD')
    if args.mode=='light':return light(args.run)
    destination=scoped_path(f'implementation/p09/evidence/p09-151-durable-negative.actual-run{args.run:02}.v1.json',fresh=True)
    expected,protected,helpers=load_binding();scoped_path(TARGET.relative_to(c.ROOT).as_posix()).mkdir(parents=True,exist_ok=True)
    return run_owned(destination,expected,protected,helpers)


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]+',str(error)) else 'P151_REDACTED_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED',error_code=code)));raise SystemExit(2) from None
