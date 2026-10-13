"""P155 diagnostic/P156 immutable digest progress, never full-product/Gate PASS."""
import base64
import hashlib
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF='tools/p09/verify_immutable_graph_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-156-pre-progress-r37/document-pins.v1.json'
FAILED='implementation/p09/source-archive/p09-156-failed-closing-run01-r37/preimages.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-155-stored-cost.light-run01.v1.json',bytes=1671,sha256='cc387245468a77f3eaedf3a1b4f6740d90329566d7a8b0b7fc126ea0755a192f'),
    dict(path='implementation/p09/evidence/p09-155-stored-cost.actual-run01.v1.json',bytes=909271,sha256='81ff5364b9b05c5244c978e0c5624125ae4237a44b0d3af2a95b2d326cd5dc4d'),
    dict(path='implementation/p09/evidence/p09-155-stored-cost.terminal-audit-run01.v1.json',bytes=290757,sha256='dd0b446bc0bbb1ee190ecef339c7d85f3703798f46a9d002bec329f28d43b7b2'),
    dict(path='implementation/p09/evidence/p09-149-maintenance-run91.v1.json',bytes=46262,sha256='2bdba3900faaadf2a3224d499bb8f7538ed82bd80f602c605305e4d74ef40663'),
    dict(path='implementation/p09/evidence/p09-156-immutable-graph.units-run01.v1.json',bytes=264210,sha256='5b965db2b4f08cc55217530256b43e37ce26da9c7972ced4725acb1b40992e8d'),
    dict(path='implementation/p09/evidence/p09-156-immutable-graph.source-closing-run02.v1.json',bytes=252223,sha256='451472c39ead329c947e3efe623d39a647c6baf18ed1d8bd0863a669166f7407'))


def require(ok,code):s.require(ok,'P156_SYNC_'+code)


def main():
    require(s.c.Path.cwd().resolve()==s.c.ROOT,'CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-156-immutable-graph.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,full249_current_qualified=False,
        current_compiled249_qualified=False,signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',
        goal_status='active',remaining_non_permission_work_units=76,PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_Cargo_SQL_native_or_test_EXE_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P156_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P156_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P156_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_EVIDENCE')
            light,actual,audit,check,units,closing=(q.json(p['path']) for p in PINS)
            require(light['contract_tests_run']==light['contract_tests_passed']==75,'LIGHT75')
            require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_DURATION_LIMIT'
                and actual['maximum_seconds']==180 and actual['tests_passed'] is None
                and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[],'DIAGNOSTIC_NOT_PRODUCT')
            require(audit['state']=='PASS_UNFILTERED_COST_DIAGNOSTIC_TERMINAL_ACCOUNTED_NOT_FULL249_OR_GATE'
                and audit['source_closing_exact'] and audit['contract_tests_passed']==75
                and audit['protected_EXE_inputs_exact']==60,'HISTORICAL_DIAGNOSTIC_CLOSING')
            require(check['state']=='PASS_SCOPED_NOT_GATE' and check['task']=='domain-check'
                and check['stop_reason'] is None and check['cleanup_confirmed'] and check['owned_tree_empty'],'TYPECHECK_ONLY')
            require(units['state']=='PASS_CURRENT_IMMUTABLE_GRAPH_UNITS15_ONLY_NOT_FULL249_OR_GATE'
                and units['tests_passed']==15 and units['stop_reason'] is None
                and units['cleanup_confirmed'] and units['owned_tree_empty'],'UNITS15_ONLY')
            require(closing['state']=='PASS_CURRENT_IMMUTABLE_GRAPH_DELTA_AND_UNITS15_ONLY_NOT_FULL249_OR_GATE'
                and closing['source_closing_exact'] and closing['whole_original_core_inverse_exact']
                and closing['all_original_domain_tests_preserved'] and closing['actual_unit_tests_passed']==15
                and closing['protected_EXE_inputs_exact']==60 and closing['current_Rust_input_count']==785
                and closing['resource_stop_reason'] is None and closing['resource_watcher_cleanup_confirmed'],'DELTA_CLOSING')
            for pin in closing['declared_Rust_source_changes']:require(q.pin(pin['path'])==pin,'CURRENT_RUST_DELTA')
            for row in (actual,closing):
                require(row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
                    and row['product_complete'] is False and row['P09_gate']=='OPEN'
                    and row['PC_freeze_resolved'] is False,'NOT_GATE')
            require(closing['current_compiled249_qualified'] is False
                and closing['full_product_performance_improvement_measured'] is False,'NEW_FULL_BUILD_PENDING')
            failed=q.json(FAILED);fp=failed['preserved_failure_receipt_pin'];require(q.pin(fp['path'])==fp,'FAILED_RECEIPT_IMMUTABLE')
            failure=q.json(fp['path']);require(failure['state']=='FAILED_NOT_ACCEPTED'
                and failure['error_code']=='P152_PREP_P156_DELTA_ACTUAL15_NOT_PRODUCT','FAILED_RUN_PRESERVED')
            require(len(failed['files'])==1,'OLD_VERIFIER_WHOLE_SCOPE')
            old=failed['files'][0];raw=base64.b64decode(old['base64'],validate=True)
            require(old['path']=='tools/p09/verify_immutable_graph_delta.py'
                and len(raw)==old['bytes'] and hashlib.sha256(raw).hexdigest()==old['sha256'],'FAILED_VERIFIER_PREIMAGE')
            current=q.text(old['path'])
            restored=current.replace('source-closing-run02.v1.json','source-closing-run01.v1.json',1).replace(
                "and units['isolated_target']==str(s.c.Path('target/p09-156-immutable-graph'))\n            and units['policy']==s.c.POLICY,'ACTUAL15_NOT_PRODUCT')",
                "and units['isolated_target']=='target/p09-156-immutable-graph' and units['policy']==s.c.POLICY,'ACTUAL15_NOT_PRODUCT')",1)
            require(restored.encode()==raw,'NO_VERIFIER_CRITERIA_REMOVED')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None
            require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'DOC_SCOPE')
            for name,pin in prior.items():
                current=q.text(name).encode();now=q.reader.snapshots[name]
                require(len(current)==now['bytes'] and hashlib.sha256(current).hexdigest()==now['sha256'],'DOC_BYTES')
                require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'WHOLE_PRIOR_DOC')
                this=current[:-pin['bytes']];require(prefix is None or prefix==this,'IDENTICAL_PREFIX');prefix=this
            require(prefix.startswith('> 2026-10-07 P155/P156 immutable-digest-optimization-r37:'.encode()),'PREFIX')
            header=prefix.decode()
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','STOP_DURATION_LIMIT',
                '원래 전체 qualification1200초','full249=false','현재 full-product compiled249=false',
                '실제 units15/15 PASS','프리즈 해결은 미입증','SQL fixed image 부재','실패 receipt'):
                require(token in header,'DECLARED_BOUNDARY')
            for pin in PINS:require(pin['sha256'] in header,'DOC_EVIDENCE_PIN')
            q.finish();out.update(state='PASS_IMMUTABLE_GRAPH_UNITS15_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',
                source_closing_exact=True,previous_whole_document_bytes_preserved=True,
                failed_closing_receipt_and_whole_verifier_preserved=True,actual_unit_tests_passed=15,current_evidence_pins=list(PINS))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P156_SYNC_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P156_SYNC_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','wall_seconds','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
