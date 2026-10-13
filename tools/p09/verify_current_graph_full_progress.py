"""P159 stop-only progress sync; whole prior docs and evidence immutable."""
import hashlib
import json
import time
from unittest.mock import patch
import run_current_graph_full as f

s=f.p.s
SELF='tools/p09/verify_current_graph_full_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-159-pre-progress-r40/document-pins.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-159-current-graph-full.light-run01.v1.json',bytes=1752,sha256='3c45795e3f3b778c499097afedb8a57a5721701e15c258bdbbb987803d4bea64'),
    dict(path='implementation/p09/evidence/p09-159-current-graph-full.actual-run01.v1.json',bytes=3959557,sha256='70d755fb99fa2ae5f2776d613d52123cdc9fed4e63860e5ed71d593ba6b9784e'),
    dict(path='implementation/p09/evidence/p09-159-current-graph-full.terminal-audit-run01.v1.json',bytes=376506,sha256='22db5cfe44272f9eb9e76a8194f557c3c41beff993b3fe3bd2acc25d0b496ade'))

def require(ok,code):f.require(ok,'SYNC_'+code)

def main():
    require(f.p.c.Path.cwd().resolve()==f.p.c.ROOT,'CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-159-current-graph-full.progress-sync-run01.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        goal_status='active',remaining_non_permission_work_units=76,full249_current_qualified=False,
        signed16_current_qualified=False,current_compiled249_qualified=False,PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_test_EXE_SQL_native_or_child_started=False)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P159_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P159_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P159_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_EVIDENCE')
            light,actual,audit=(q.json(pin['path']) for pin in PINS)
            require(light['contract_tests_passed']==48 and light['source_closing_exact'],'LIGHT48')
            require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_DURATION_LIMIT'
                and actual['maximum_seconds']==1200 and actual['tests_passed'] is None
                and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[],'ACTUAL_STOP_NOT_PASS')
            require(audit['state']=='PASS_CURRENT_GRAPH_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'
                and audit['source_closing_exact'] and audit['contract_tests_passed']==60
                and audit['actual_tests_passed'] is None and audit['original_stop_reason']=='STOP_DURATION_LIMIT'
                and audit['protected_EXE_inputs_exact']==62 and audit['current_Rust_input_count']==785
                and audit['resource_stop_reason'] is None and audit['resource_watcher_cleanup_confirmed'],'AUDIT60_ONLY')
            for row in (actual,audit):
                require(row['current_compiled249_qualified'] and not row['full249_current_qualified']
                    and not row['signed16_current_qualified'] and not row['product_complete']
                    and row['P09_gate']=='OPEN' and not row['PC_freeze_resolved'],'NO_PROMOTION')
            exe=actual['compiled_test_executable_pin']
            require(exe==audit['compiled_test_executable_pin'] and q.pin(exe['path'])==exe
                and exe['path']==f.p.b.executable_name(3),'CURRENT_EXE')
            frozen=s.inputs.inventory(audit['bound_input_pins'])
            for n in ('crates/domain-ir/src/document_graph.rs','crates/domain-ir/tests/document_graph.rs',f.SELF,f.TEST,
                    'tools/p09/audit_current_graph_full.py'):
                require(q.pin(n)==frozen[n],'CURRENT_SOURCE')
            prior=s.inputs.inventory(q.json(ARCHIVE)['files'],2);prefix=None
            require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'DOC_SCOPE')
            for name,pin in prior.items():
                current=q.text(name).encode();now=q.reader.snapshots[name]
                require(len(current)==now['bytes'] and hashlib.sha256(current).hexdigest()==now['sha256'],'DOC_BYTES')
                require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'WHOLE_PRIOR_DOC')
                this=current[:-pin['bytes']];require(prefix is None or this==prefix,'IDENTICAL_PREFIX');prefix=this
            header=prefix.decode();require(header.startswith('> 2026-10-07 P159 current-graph-full-stop-accounting-r40:'),'PREFIX')
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','원래full1200초','STOP_DURATION_LIMIT',
                    'current_compiled249=true/full249=false/signed16=false/tests_passed=null','프리즈 해결은 미입증','SQL fixed image 부재'):
                require(token in header,'BOUNDARY')
            for pin in PINS:require(pin['sha256'] in header,'DOC_EVIDENCE')
            q.finish();out.update(state='PASS_CURRENT_FULL_STOP_PROGRESS_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
                source_closing_exact=True,current_compiled249_qualified=True,previous_whole_document_bytes_preserved=True,
                current_evidence_pins=list(PINS),compiled_test_executable_pin=exe)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=f.s.original.closed_error(e)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','wall_seconds','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
