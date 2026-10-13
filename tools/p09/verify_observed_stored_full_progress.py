"""Sync original full duration-stop + owned diagnostic evidence, NOT product PASS."""
import hashlib
import json
import re
import time
from unittest.mock import patch
import prepare_current_stored_generation as s

SELF='tools/p09/verify_observed_stored_full_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-154-pre-progress-r36/document-pins.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-154-observed-full.light-run02.v1.json',bytes=2893,
        sha256='aaef1e3aee1910bebd21232a9a82290d8e488ad603568f8668d4bfa0dcd8e822'),
    dict(path='implementation/p09/evidence/p09-154-observed-full.actual-run01.v1.json',bytes=3917483,
        sha256='c81b34d53215da2bee70709358963db5f1de5db6fbd17caa629673011c67754a'),
    dict(path='implementation/p09/evidence/p09-154-observed-full.terminal-audit-run01.v1.json',bytes=350671,
        sha256='edbd9c643c30c1d2cf965fabbb4df4b0b0729a5b85f1f5778f15236602075964'))


def require(ok,code):s.require(ok,'P154_SYNC_'+code)


def main():
    require(s.c.Path.cwd().resolve()==s.c.ROOT,'CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-154-observed-full.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,full249_current_qualified=False,
        signed16_current_qualified=False,PC_freeze_resolved=False,product_complete=False,P09_gate='OPEN',
        goal_status='active',remaining_non_permission_work_units=76,actual_Cargo_SQL_native_or_test_EXE_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P154_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P154_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P154_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_EVIDENCE')
            light,actual,audit=(q.json(pin['path']) for pin in PINS)
            require(light['contract_tests_run']==light['contract_tests_passed']==55
                and light['state']=='PASS_OBSERVED_FULL249_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE','LIGHT55')
            require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_DURATION_LIMIT'
                and actual['maximum_seconds']==1200 and actual['tests_passed'] is None
                and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[],'DURATION_STOP_CLEANUP')
            require(audit['state']=='PASS_OBSERVED_FULL249_STOP_ACCOUNTED_NOT_RUNTIME_SQL_NATIVE_OR_GATE'
                and audit['source_closing_exact'] and audit['contract_tests_passed']==55
                and audit['original_stop_reason']=='STOP_DURATION_LIMIT'
                and audit['original_source_final_hash_not_retroactively_promoted'] is True
                and audit['protected_EXE_inputs_exact']==60 and audit['current_Rust_input_count']==785,'CLOSING_NOT_RUNTIME')
            for row in (actual,audit):require(row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
                and row['product_complete'] is False and row['P09_gate']=='OPEN' and row['PC_freeze_resolved'] is False,'NOT_GATE')
            cap=actual['capture_diagnostics'];frames=cap['host_cpu_records']
            require(cap['explicit_query_cleanup_confirmed'] is False and cap['host_cpu_error_code'] is None
                and cap['received_bytes']==dict(stdout=89,stderr=6137)
                and [r['kind'] for r in frames]==['ready','sample','sample','sample'],'PARTIAL_DIAGNOSTICS_PRESERVED')
            hot=frames[-1]
            require(hot['system_cpu_percent']==89.04 and hot['observation']['unstable_instances']==51
                and hot['observation']['causal_attribution'] is False,'CANDIDATES_NOT_CAUSE')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None
            require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'DOC_SCOPE')
            for name,pin in prior.items():
                current=q.text(name).encode();now=q.reader.snapshots[name]
                require(len(current)==now['bytes'] and hashlib.sha256(current).hexdigest()==now['sha256'],'DOC_BYTES')
                require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'WHOLE_PRIOR_DOC')
                this=current[:-pin['bytes']];require(prefix is None or prefix==this,'IDENTICAL_PREFIX');prefix=this
            require(prefix.startswith('> 2026-10-07 P154 observed-full-duration-stop-r36:'.encode()),'PREFIX')
            header=prefix.decode()
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','STOP_DURATION_LIMIT',
                '원래1200초','full249=false','불안정51','프리즈 해결은 미입증','SQL fixed image 부재'):
                require(token in header,'DECLARED_BOUNDARY')
            for pin in PINS:require(pin['sha256'] in header,'DOC_EVIDENCE_PIN')
            q.finish();out.update(state='PASS_OBSERVED_FULL_DURATION_STOP_PROGRESS_SYNC_ONLY_NOT_GATE',
                source_closing_exact=True,previous_whole_document_bytes_preserved=True,original_duration_stop_preserved=True,
                current_compiled249_qualified=True,current_Rust_input_count=785,current_evidence_pins=list(PINS))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P154_SYNC_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P154_SYNC_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','wall_seconds','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
