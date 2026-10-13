"""P160 strict stop-diagnostic progress synchronization, no runtime promotion."""
import hashlib
import json
import time
from unittest.mock import patch
import run_current_graph_cost as d

s=d.p.s
SELF='tools/p09/verify_current_graph_cost_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-160-pre-progress-r41/document-pins.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-160-current-graph-cost.light-run01.v1.json',bytes=1646,sha256='e9f52f43a74ae3736c38d3285c4f17e252c9321e9c6e58cdef502c6e68f25bd9'),
    dict(path='implementation/p09/evidence/p09-160-current-graph-cost.actual-run01.v1.json',bytes=1447049,sha256='8aa036c6b6343f0bdea76d78ac279f85312a056c177956b333dbfbaeb01e4abf'),
    dict(path='implementation/p09/evidence/p09-160-current-graph-cost.terminal-audit-run01.v1.json',bytes=298999,sha256='c2aaebe924f1e2c5da90b79c259594144dbe776c66310c4be241f104a2c216a5'))

def main():
    d.require(d.p.c.Path.cwd().resolve()==d.p.c.ROOT,'SYNC_CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-160-current-graph-cost.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',full249_current_qualified=False,signed16_current_qualified=False,
        current_compiled249_qualified=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        goal_status='active',remaining_non_permission_work_units=76,PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_audit_child_or_thread_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P160_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P160_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P160_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:d.require(q.pin(pin['path'])==pin,'SYNC_PIN')
            light,actual,audit=(q.json(pin['path']) for pin in PINS)
            d.require(light['contract_tests_passed']==80 and light['source_closing_exact'],'SYNC_LIGHT80')
            d.require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_DURATION_LIMIT'
                and actual['maximum_seconds']==360 and actual['original_full_qualification_seconds']==1200
                and actual['tests_passed'] is None and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[],'SYNC_STOP')
            d.require(audit['state']=='PASS_CURRENT_GRAPH_COST_TERMINAL_ACCOUNTED_ONLY_NOT_FULL249_OR_GATE'
                and audit['source_closing_exact'] and audit['contract_tests_passed']==80
                and audit['completed_case_observations']==47 and audit['protected_EXE_inputs_exact']==62
                and audit['resource_stop_reason'] is None and audit['resource_watcher_cleanup_confirmed'],'SYNC_AUDIT')
            for row in (actual,audit):d.require(row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete'] and row['P09_gate']=='OPEN'
                and not row['PC_freeze_resolved'],'SYNC_NO_PROMOTION')
            exe=actual['compiled_test_executable_pin'];d.require(exe==audit['compiled_test_executable_pin'] and q.pin(exe['path'])==exe,'SYNC_EXE')
            frozen=s.inputs.inventory(audit['bound_input_pins'])
            for n in (d.SELF,d.TEST,'tools/p09/audit_current_graph_cost.py','crates/domain-ir/src/document_graph.rs',
                    'crates/domain-ir/tests/document_graph.rs'):d.require(q.pin(n)==frozen[n],'SYNC_CURRENT_SOURCE')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None
            d.require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'SYNC_DOC_SCOPE')
            for n,pin in prior.items():
                b=q.text(n).encode();now=q.reader.snapshots[n]
                d.require(len(b)==now['bytes'] and hashlib.sha256(b).hexdigest()==now['sha256'],'SYNC_DOC_BYTES')
                d.require(len(b)>pin['bytes'] and hashlib.sha256(b[-pin['bytes']:]).hexdigest()==pin['sha256'],'SYNC_PRIOR_WHOLE')
                this=b[:-pin['bytes']];d.require(prefix is None or this==prefix,'SYNC_IDENTICAL_PREFIX');prefix=this
            header=prefix.decode();d.require(header.startswith('> 2026-10-07 P160 current-graph-per-case-cost-r41:'),'SYNC_PREFIX')
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','qualification1200초','360초 diagnostic-only',
                    'current_compiled249=true/full249=false/signed16=false/tests_passed=null','47개 완료 관측',
                    '프리즈 해결은 미입증','SQL fixed image 부재'):
                d.require(token in header,'SYNC_BOUNDARY')
            for pin in PINS:d.require(pin['sha256'] in header,'SYNC_DOC_EVIDENCE')
            q.finish();out.update(state='PASS_CURRENT_COST_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',source_closing_exact=True,
                previous_whole_document_bytes_preserved=True,current_compiled249_qualified=True,current_evidence_pins=list(PINS))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.full.s.original.closed_error(e)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
