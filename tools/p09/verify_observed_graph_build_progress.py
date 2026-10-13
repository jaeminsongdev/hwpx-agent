"""Sync current build + compiled249 ONLY, preserve whole previous documents."""
import hashlib
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF='tools/p09/verify_observed_graph_build_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-158-pre-progress-r39/document-pins.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-158-observed-graph-build.light-run01.v1.json',bytes=1043,sha256='9c6cb178f94d2dcface3421fb675af1955cce64564d18644a84332235c1925b8'),
    dict(path='implementation/p09/evidence/p09-158-observed-graph-build.actual-run01.v1.json',bytes=505469,sha256='25a6ad83c1c1383831e4e9b35a8b56210a81195b1bcfde88ba452070c28a811c'),
    dict(path='implementation/p09/evidence/p09-158-observed-graph-build.terminal-audit-run01.v1.json',bytes=354808,sha256='55060b3752a63fe7a8967d2a75ff8b0783606ded18ccbe4ce76b9199f253e3b3'),
    dict(path='implementation/p09/evidence/p09-158-current-graph-inventory.light-run01.v1.json',bytes=1387,sha256='91ef7a9d91a60d36847e1bc655290b584a2d44efa00962d02fc247a880f09e43'),
    dict(path='implementation/p09/evidence/p09-158-current-graph-inventory.actual-run01.v1.json',bytes=399156,sha256='88da824d33e37f80929c5be9da6f0a474a407ae4e8371b0ee0e3f674d8437e0f'),
    dict(path='implementation/p09/evidence/p09-158-current-graph-inventory.terminal-audit-run01.v1.json',bytes=352586,sha256='2ffa26b410bbd90e3d8364965f270bc20da39aeae7864f3d6b3806ede1d677c7'))


def require(ok,code):s.require(ok,'P158_SYNC_'+code)


def main():
    require(s.c.Path.cwd().resolve()==s.c.ROOT,'CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-158-observed-graph-build.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',goal_status='active',
        remaining_non_permission_work_units=76,PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_Cargo_SQL_native_or_test_EXE_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P158_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P158_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P158_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_EVIDENCE')
            light,build,audit,il,listing,ia=(q.json(p['path']) for p in PINS)
            require(light['contract_tests_passed']==46 and il['contract_tests_passed']==12,'LIGHT_CONTRACTS_ONLY')
            require(build['state']=='PASS_CURRENT_GRAPH_PRODUCT_OBSERVED_BUILD_ONLY_NOT_LISTING_FULL249_OR_GATE'
                and build['current_build_binding_accepted'] and build['source_freeze_exact_after']
                and build['protected_executables_exact_after'] and build['stop_reason'] is None and build['exit_code']==0
                and build['cleanup_confirmed'] and build['owned_tree_empty'] and build['job_final']['active_processes']==0
                and build['job_final']['owned_processes']==[],'ACTUAL_BUILD_ONLY')
            require(audit['state']=='PASS_CURRENT_OBSERVED_GRAPH_BUILD_CLOSING_ONLY_NOT_LISTING_FULL249_OR_GATE'
                and audit['source_closing_exact'] and audit['current_build_accepted'] and audit['contract_tests_passed']==46
                and audit['protected_executables_exact']==61 and audit['explicit_query_cleanup_confirmed']
                and audit['host_cpu_error_code'] is None,'BUILD_CLOSING_ONLY')
            require(listing['state']=='PASS_CURRENT_GRAPH_EXE_COMPILED249_LISTING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
                and listing['compiled_inventory_exact'] and listing['current_compiled249_qualified']
                and listing['fresh_EXE_list_only'] and listing['runtime_tests_executed'] is False
                and listing['expected_test_count']==249 and listing['stop_reason'] is None and listing['exit_code']==0
                and listing['cleanup_confirmed'] and listing['owned_tree_empty']
                and listing['job_final']['active_processes']==0 and listing['job_final']['owned_processes']==[],'ACTUAL_LISTING_NOT_TESTS')
            require(ia['state']=='PASS_CURRENT_GRAPH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
                and ia['source_closing_exact'] and ia['current_compiled249_qualified'] and ia['contract_tests_passed']==58
                and ia['compiled_test_count']==249 and ia['source_module_instance_count']==59
                and ia['protected_parent_EXE_inputs_exact']==62 and ia['runtime_test_bodies_executed'] is False,'LIST_CLOSING_ONLY')
            for row in (build,audit,listing,ia):
                require(row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
                    and row['product_complete'] is False and row['P09_gate']=='OPEN' and row['PC_freeze_resolved'] is False,'NO_FULL_PRODUCT_PROMOTION')
            for row in (audit,ia):require(row['resource_stop_reason'] is None and row['resource_watcher_cleanup_confirmed'],'AUDIT_CLEANUP')
            exe=build['executable_pin'];require(exe==audit['compiled_test_executable_pin']==listing['compiled_test_executable_pin']==ia['compiled_test_executable_pin']
                and exe['path']=='target/p09-149-conservative/debug/deps/form_stored_provider-p152-r03.exe'
                and q.pin(exe['path'])==exe,'CURRENT_R03_EXE')
            frozen=s.inputs.inventory(listing['source_freeze'])
            for n in ('crates/domain-ir/src/document_graph.rs','crates/domain-ir/tests/document_graph.rs',
                    'tools/p09/build_observed_graph_product.py','tools/p09/tests/test_observed_graph_product_build.py',
                    'tools/p09/run_observed_graph_inventory.py','tools/p09/tests/test_observed_graph_inventory.py'):
                require(q.pin(n)==frozen[n],'CURRENT_RELEVANT_SOURCE')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None
            require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'DOC_SCOPE')
            for name,pin in prior.items():
                current=q.text(name).encode();now=q.reader.snapshots[name]
                require(len(current)==now['bytes'] and hashlib.sha256(current).hexdigest()==now['sha256'],'DOC_BYTES')
                require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'WHOLE_PREVIOUS_DOC')
                this=current[:-pin['bytes']];require(prefix is None or prefix==this,'IDENTICAL_PREFIX');prefix=this
            require(prefix.startswith('> 2026-10-07 P158 current-graph-product-build-and-compiled249-r39:'.encode()),'PREFIX')
            header=prefix.decode()
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','원래full1200초','current_compiled249=true',
                '테스트 본문은 NOT_RUN','full249=false/signed16=false','프리즈 해결은 미입증','SQL fixed image 부재'):
                require(token in header,'DECLARED_BOUNDARY')
            for pin in PINS:require(pin['sha256'] in header,'DOC_EVIDENCE_PIN')
            q.finish();out.update(state='PASS_CURRENT_BUILD_AND_COMPILED249_PROGRESS_SYNC_ONLY_NOT_FULL_RUNTIME_OR_GATE',
                source_closing_exact=True,current_compiled249_qualified=True,previous_whole_document_bytes_preserved=True,
                current_evidence_pins=list(PINS),compiled_test_executable_pin=exe)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        code=str(e) if isinstance(e,ValueError) else 'P158_SYNC_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P158_SYNC_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','wall_seconds','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
