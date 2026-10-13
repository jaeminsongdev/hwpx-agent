"""P157 CPU-stop/current-input closure + post-stop probe; never compile PASS."""
import base64
import hashlib
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF='tools/p09/verify_immutable_graph_build_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-157-pre-progress-r38/document-pins.v1.json'
SYNTAX='implementation/p09/source-archive/p09-157-pre-audit-syntax-repair-r38/source-preimages.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-157-immutable-graph-product-build.light-run01.v1.json',bytes=1660,sha256='5750737f82a5fb065378743413e52c00218ae1cd3f0fa35e2ff03b94bfb5c185'),
    dict(path='implementation/p09/evidence/p09-157-immutable-graph-product-build.actual-run01.v1.json',bytes=875277,sha256='fea41bd48e9f32efa2c03d6c881137e97ba576eb2c8f59281dcc14789ce227c4'),
    dict(path='implementation/p09/evidence/p09-157-immutable-graph-product-build.terminal-audit-run01.v1.json',bytes=356793,sha256='f3b990f6fd0842984e0e7a4baed4ae9ed04d89d9f9c04e8e3b88dee6a6562641'),
    dict(path='implementation/p09/evidence/p09-153-host-cpu-groups.actual-run02.v1.json',bytes=19050,sha256='60ba7337848b763f7dfd3d444334c6c461d11d96fd9d27be9e4f53fafed5927e'))


def require(ok,code):s.require(ok,'P157_SYNC_'+code)


def main():
    require(s.c.Path.cwd().resolve()==s.c.ROOT,'CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-157-immutable-graph-product-build.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_compiled249_qualified=False,
        current_build_accepted=False,full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',goal_status='active',remaining_non_permission_work_units=76,PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_Cargo_SQL_native_or_test_EXE_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P157_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P157_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P157_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_EVIDENCE')
            light,actual,audit,probe=(q.json(p['path']) for p in PINS)
            require(light['state']=='PASS_IMMUTABLE_GRAPH_BUILD_CONTRACTS_ONLY_NOT_PRODUCT_OR_GATE'
                and light['contract_tests_run']==light['contract_tests_passed']==36,'LIGHT36_ONLY')
            require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and actual['maximum_seconds']==600 and actual['build_result'] is None and actual['executable_pin'] is None
                and actual['exit_code'] is None and actual['source_freeze_exact_after'] is False
                and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[], 'CPU_STOP_NOT_BUILD')
            require(audit['state']=='PASS_CPU_STOP_ACCOUNTED_CURRENT_INPUTS_ONLY_NOT_PRODUCT_BUILD_OR_GATE'
                and audit['source_closing_exact'] and audit['contract_tests_passed']==36
                and audit['original_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and audit['original_source_final_hash_not_retroactively_promoted'] is True
                and audit['current_build_accepted'] is False and audit['protected_executables_exact']==61
                and audit['current_Rust_input_count']==785 and audit['resource_stop_reason'] is None
                and audit['resource_watcher_cleanup_confirmed'],'STOP_CLOSING_ONLY')
            frozen=s.inputs.inventory(actual['source_freeze'])
            require(len(frozen)==1249,'FROZEN1249')
            for n in ('tools/p09/build_immutable_graph_product.py','tools/p09/tests/test_immutable_graph_product_build.py',
                    'crates/domain-ir/src/document_graph.rs','crates/domain-ir/tests/document_graph.rs'):
                require(q.pin(n)==frozen[n],'CURRENT_RELEVANT_SOURCE')
            require(not (s.c.ROOT/actual['compile_recipe']['executable_path']).exists(),'NO_CURRENT_BUILD_EXE')
            require(probe['state']=='PASS_NATIVE_HOST_CPU_GROUP_DIAGNOSTIC_ONLY_NOT_FULL249_OR_GATE'
                and probe['observer_query_cleanup_confirmed'] is True and probe['causal_attribution'] is False
                and probe['raw_process_names_saved'] is False and probe['commands_paths_saved'] is False
                and probe['cleanup_confirmed'] and probe['owned_tree_empty']
                and probe['job_final']['active_processes']==0 and probe['job_final']['owned_processes']==[],'POST_STOP_DIAGNOSTIC_ONLY')
            for pin in probe['source_freeze']:require(q.pin(pin['path'])==pin,'PROBE_SOURCE_CURRENT')
            for row in (actual,audit,probe):
                require(row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
                    and row['product_complete'] is False and row['P09_gate']=='OPEN' and row['PC_freeze_resolved'] is False,'NO_PRODUCT_PROMOTION')
            saved=q.json(SYNTAX);require(saved['failure_code']=='PYTHON_SYNTAX_ERROR_LINE36_LEADING_AND'
                and saved['receipt_created'] is False and len(saved['files'])==1,'SYNTAX_FAILURE_PRESERVED')
            old=saved['files'][0];raw=base64.b64decode(old['base64'],validate=True)
            require(len(raw)==old['bytes'] and hashlib.sha256(raw).hexdigest()==old['sha256'],'WHOLE_FAILED_SOURCE')
            current=q.text(old['path']);oldline="        p.require(\n            and row['source249_generation_connected_to_actual_build'] is True and row['whole_workspace_Rust_input_count']==785"
            newline="        p.require(row['source249_generation_connected_to_actual_build'] is True and row['whole_workspace_Rust_input_count']==785"
            require(current.count(newline)==1 and current.replace(newline,oldline,1).encode()==raw,'EXACT_SINGLE_SYNTAX_REPAIR')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None
            require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'DOC_SCOPE')
            for name,pin in prior.items():
                current=q.text(name).encode();now=q.reader.snapshots[name]
                require(len(current)==now['bytes'] and hashlib.sha256(current).hexdigest()==now['sha256'],'DOC_BYTES')
                require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'WHOLE_PRIOR_DOC')
                this=current[:-pin['bytes']];require(prefix is None or prefix==this,'IDENTICAL_PREFIX');prefix=this
            require(prefix.startswith('> 2026-10-07 P157 current-product-build-CPU-stop-r38:'.encode()),'PREFIX')
            header=prefix.decode()
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','STOP_SUSTAINED_SYSTEM_CPU',
                '원래full qualification1200초','current full-product compiled249=false','프리즈 해결 증거가 아니며',
                '원래 source final hash를 사후 승격하지 않는다','SQL fixed image 부재','parser 실패'):
                require(token in header,'DECLARED_BOUNDARY')
            for pin in PINS:require(pin['sha256'] in header,'DOC_EVIDENCE_PIN')
            q.finish();out.update(state='PASS_CPU_STOP_CURRENT_INPUTS_AND_POST_STOP_PROBE_PROGRESS_ONLY_NOT_PRODUCT_OR_GATE',
                source_closing_exact=True,previous_whole_document_bytes_preserved=True,
                original_CPU_stop_not_retroactively_promoted=True,parser_failure_whole_source_preserved=True,current_evidence_pins=list(PINS))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        code=str(e) if isinstance(e,ValueError) else 'P157_SYNC_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P157_SYNC_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','wall_seconds','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
