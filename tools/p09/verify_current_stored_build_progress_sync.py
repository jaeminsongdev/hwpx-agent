"""P152 current compile/listing progress only; no full249 runtime/Gate promotion."""
import hashlib
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF='tools/p09/verify_current_stored_build_progress_sync.py'
ARCHIVE='implementation/p09/source-archive/p09-152-pre-progress-r34/document-pins.v1.json'
PINS=[
    dict(path='implementation/p09/evidence/p09-152-current-stored-build.actual-run01.v1.json',bytes=950954,
        sha256='6cea7575cb9eb6cb76706e715f9c82afb5a067a993c406341053a1d0dc3fe9fc'),
    dict(path='implementation/p09/evidence/p09-152-current-stored-build.terminal-audit-run01.v1.json',bytes=289819,
        sha256='edde914ab29feae0286ff03ea0005c12604e42f3b53ab60b49d972502d514d5a'),
    dict(path='implementation/p09/evidence/p09-152-current-stored-inventory.actual-run01.v1.json',bytes=380076,
        sha256='8b8dddd171cdbc92a7fd27909fa429123d66744cbc090499194f304f49965c82'),
    dict(path='implementation/p09/evidence/p09-152-current-stored-inventory.terminal-audit-run01.v1.json',bytes=332858,
        sha256='a8e3c4385af9dd05819ba85055cbfc84884fccf8b60b9918c107e8b445a65f46')]


def main():
    s.require(s.c.Path.cwd().resolve()==s.c.ROOT,'SYNC_REPOSITORY_CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-152-current-stored-build.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(schema_version='hwpx-agent.p09-current-stored-build-listing-progress-sync/v1',state='FAILED_NOT_ACCEPTED',
        source_closing_exact=False,actual_Cargo_Rustc_SQL_Docker_native_or_EXE_executed=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        runtime_test_bodies_executed=False,raw_logs_included=False,PC_freeze_resolved=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',goal_status='active',remaining_non_permission_work_units=76)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P152_BUILD_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P152_BUILD_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P152_BUILD_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:s.require(q.pin(pin['path'])==pin,'SYNC_IMMUTABLE_EVIDENCE')
            actual=q.json(PINS[0]['path']);built=q.json(PINS[1]['path']);inventory=q.json(PINS[2]['path']);closed=q.json(PINS[3]['path'])
            s.require(actual['state']=='PASS_CURRENT_STORED_LIBTEST_BUILD_ONLY_NOT_LISTING_RUNTIME_SQL_NATIVE_OR_GATE'
                and actual['build_only_accepted'] is True and actual['build_result']['catalog_profile']['test'] is True
                and actual['runtime_tests_executed'] is False and actual['cleanup_confirmed'] is True
                and actual['job_final']['active_processes']==0,'SYNC_ACTUAL_COMPILE_ONLY')
            s.require(built['state']=='PASS_CURRENT_LIBTEST_BUILD_CLOSING_ONLY_NOT_COMPILED249_LISTING_RUNTIME_SQL_OR_GATE'
                and built['source_closing_exact'] and built['contract_tests_passed']==26
                and built['current_Rust_input_count']==785,'SYNC_COMPILE_CLOSING')
            s.require(inventory['state']=='PASS_CURRENT_FRESH_EXE_COMPILED249_LISTING_ONLY_NOT_TEST_RUNTIME_SQL_NATIVE_OR_GATE'
                and inventory['compiled_inventory_exact'] is True and inventory['runtime_tests_executed'] is False
                and inventory['job_final']['active_processes']==0 and inventory['cleanup_confirmed'],'SYNC_ACTUAL_LISTING_ONLY')
            s.require(closed['state']=='PASS_CURRENT_FRESH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_TEST_RUNTIME_SQL_NATIVE_OR_GATE'
                and closed['source_closing_exact'] and closed['contract_tests_passed']==34
                and closed['current_compiled249_qualified'] is True and closed['compiled_test_count']==249
                and closed['source_module_instance_count']==59 and closed['protected_parent_EXE_inputs_exact']==60
                and closed['runtime_test_bodies_executed'] is False,'SYNC_FRESH_COMPILED249_ONLY')
            for row in (actual,built,inventory,closed):
                s.require(row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
                    and row['product_complete'] is False and row['P09_gate']=='OPEN','SYNC_NOT_RUNTIME_OR_GATE')
            exe=actual['executable_pin']
            s.require(exe==built['compiled_test_executable_pin']==inventory['compiled_test_executable_pin']==closed['compiled_test_executable_pin']
                and q.pin(exe['path'])==exe,'SYNC_CURRENT_FRESH_EXE_IDENTITY')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None;docs=[]
            s.require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'SYNC_DOCUMENT_SCOPE')
            for name,pin in prior.items():
                current=q.text(name).encode();actual_pin=q.reader.snapshots[name]
                s.require(len(current)==actual_pin['bytes'] and hashlib.sha256(current).hexdigest()==actual_pin['sha256'],'SYNC_CURRENT_DOCUMENT_BYTES')
                s.require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'SYNC_WHOLE_PRIOR_DOCUMENT_EXACT')
                this_prefix=current[:-pin['bytes']];s.require(prefix is None or prefix==this_prefix,'SYNC_IDENTICAL_PREFIX')
                prefix=this_prefix;docs.append(actual_pin)
            s.require(prefix.startswith('> 2026-10-07 P152 fresh-libtest build/inventory-r34:'.encode()),'SYNC_CURRENT_GENERATION')
            header=prefix.decode()
            for literal in ('목표 active','잔여76','product=false','P10 새 구현 없음','compiled249=true',
                    'runtime=false/NOT_RUN','test bodies 실행은0회','PC freeze 해결 증명이 아니다','원래1200초','SQL fixed image 부재'):
                s.require(literal in header,'SYNC_DECLARED_BOUNDARY')
            for pin in PINS:s.require(pin['sha256'] in header,'SYNC_EVIDENCE_LINK')
            q.finish();out.update(state='PASS_COMPILE_LISTING_PROGRESS_SYNC_ONLY_NOT_TEST_RUNTIME_SQL_NATIVE_OR_GATE',
                source_closing_exact=True,current_compiled249_qualified=True,previous_whole_document_bytes_preserved=True,
                current_Rust_input_count=785,compiled_test_count=249,source_module_instance_count=59,
                current_executable_pin=exe,current_document_pins=docs,current_evidence_pins=PINS,
                prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest())
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P152_BUILD_SYNC_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P152_BUILD_SYNC_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out['IO']=q.summary();out['bound_input_pins']=list(q.reader.snapshots.values())
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','current_compiled249_qualified','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') and out['source_closing_exact'] else 2


if __name__=='__main__':raise SystemExit(main())
