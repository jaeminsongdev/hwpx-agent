"""Preserve whole prior docs; synchronize actual P165 terminal state, not Gate."""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import audit_adaptive_source_xml_full as audit

d=audit.d
p=d.p
SELF='tools/p09/sync_adaptive_full_terminal_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-165-pre-progress-r46/document-preimages.v1.json'
CLOSING='implementation/p09/evidence/p09-165-adaptive-source-xml-full.terminal-audit-run01.v1.json'
LIGHT='implementation/p09/evidence/p09-165-adaptive-source-xml-full.light-run01.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')

def require(ok,code):d.require(ok,'SYNC_'+code)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('archive','verify'),required=True)
    mode=parser.parse_args().mode
    require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(ARCHIVE if mode=='archive' else
        'implementation/p09/evidence/p09-165-adaptive-full-terminal.progress-sync-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_or_thread_started=False)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        with patch('subprocess.Popen',side_effect=AssertionError('P165_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P165_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P165_SYNC_THREAD_FORBIDDEN')):
            q.pin(SELF)
            evidence=[q.pin(n) for n in (audit.ACTUAL,CLOSING,LIGHT,d.PARENT['path'])]
            actual,closing,light,parent=(q.json(pin['path']) for pin in evidence)
            passed=actual['state']==d.PASS
            require(closing['state']==(audit.PASS if passed else audit.STOP_PASS)
                and closing['actual_full_receipt_pin']==evidence[0]
                and closing['source_closing_exact'] and closing['contract_tests_passed']==97
                and closing['current_Rust_input_count']==785 and closing['protected_EXE_inputs_exact']==64
                and closing['original_run_state']==actual['state']
                and closing['original_stop_reason']==actual['stop_reason']
                and closing['resource_stop_reason'] is None and closing['resource_watcher_cleanup_confirmed'],
                'INDEPENDENT_TERMINAL')
            require(actual['state'] in (d.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
                and actual['tests_passed']==(249 if passed else None)
                and actual['maximum_seconds']==1200 and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['policy']==p.c.POLICY and not actual['actual_new_Cargo_compile_executed']
                and not actual['actual_Hangul_COM_or_SQL_run'],'ORIGINAL_FULL_OR_STOP')
            if actual['heavy_work_started']:
                require(actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[]
                    and actual['owned_limits_readback']['verified'],'OWNED_CLEANUP')
            for row in (actual,closing):
                require(row['full249_current_qualified'] is passed and row['signed16_current_qualified'] is passed
                    and row['product_complete'] is False and row['P09_gate']=='OPEN'
                    and row['PC_freeze_resolved'] is False,'NO_GATE_OR_FREEZE_PROMOTION')
            require(closing['A12_gate']==closing['A13_gate']=='OPEN'
                and closing['original_source_final_hash_not_retroactively_promoted'] is (not passed)
                and closing['actual_tests_passed']==(249 if passed else None),'DISTINCT_CLOSING')
            require(evidence[3]==d.PARENT,'PARENT_PIN')
            expected,exe=d.parent_scope(parent)
            require(light['contract_tests_passed']==85 and light['actual_product_test_body_executed'] is False
                and light['state']=='PASS_ADAPTIVE_SOURCE_XML_FULL_CONNECTION_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE',
                'LIGHT_IS_NOT_RUNTIME')
            for n in ('crates/hwpx-package/src/document_import.rs','crates/domain-ir/src/document_graph.rs',
                    d.SELF,d.TEST,d.adaptive.SELF):
                pin=actual['source_freeze'] if actual['source_freeze'] else list(expected.values())
                bound=p.s.inputs.inventory(pin)
                require(q.pin(n)==bound[n],'SELECTED_CURRENT_SOURCE')
            require(q.pin(exe['path'])==exe,'CURRENT_R04')
            q.pin(audit.SELF)
            if mode=='archive':
                files=[]
                for n in DOCS:
                    raw=q.text(n).encode();pin=q.reader.snapshots[n]
                    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'DOC_BYTES')
                    files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
                q.finish()
                out.update(state='PASS_P165_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',
                    files=files,evidence_pins=evidence)
            else:
                archive=q.json(ARCHIVE)
                require(archive['evidence_pins']==evidence and len(archive['files'])==2,'ARCHIVE')
                prefix=None
                for item in archive['files']:
                    old=base64.b64decode(item['base64'],validate=True)
                    require(item['path'] in DOCS and len(old)==item['bytes']
                        and hashlib.sha256(old).hexdigest()==item['sha256'],'WHOLE_PREIMAGE')
                    current=q.text(item['path']).encode()
                    require(current.endswith(old) and len(current)>len(old),'WHOLE_PRIOR_DOCUMENT')
                    added=current[:-len(old)];require(prefix is None or prefix==added,'IDENTICAL_PREFIX');prefix=added
                header=prefix.decode()
                tokens=('P165 adaptive-source-XML-full-terminal-r46:','목표 active','잔여76','P10 새 구현 없음',
                    f'compiled249=true/full249={str(passed).lower()}/signed16={str(passed).lower()}',
                    actual['state'],closing['state'],'프리즈 해결·전체 성능 개선 미입증',
                    'SQL fixed image 부재','Git 명령 없음')
                for token in tokens:require(token in header,'DOC_BOUNDARIES')
                for pin in evidence[:3]:require(pin['sha256'] in header,'DOC_RECEIPTS')
                if not passed:require(actual['stop_reason'] in header,'STOP_RETAINED')
                q.finish()
                out.update(state='PASS_ADAPTIVE_FULL_TERMINAL_PROGRESS_SYNC_ONLY_NOT_SQL_NATIVE_PRODUCT_OR_GATE',
                    previous_whole_document_bytes_preserved=True,current_evidence_pins=evidence)
            out.update(current_compiled249_qualified=True,full249_current_qualified=passed,
                signed16_current_qualified=passed,actual_tests_passed=249 if passed else None,
                original_run_state=actual['state'],original_stop_reason=actual['stop_reason'])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.s.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_tests_passed','original_stop_reason',
            'previous_whole_document_bytes_preserved','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
