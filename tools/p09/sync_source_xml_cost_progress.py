"""P166 bounded diagnostic evidence and preserved failed audit, not Gate."""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import audit_source_xml_stored_cost_r2 as a

d=a.d
p=d.p
SELF='tools/p09/sync_source_xml_cost_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-166-pre-progress-r47/document-preimages.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PINS=(
    dict(path='implementation/p09/evidence/p09-166-source-xml-stored-cost.light-run01.v1.json',bytes=2577,
        sha256='75dbb743b27a396a2667feaec94a86b3a506ca55a0bc73a1883434639163b8d5'),
    dict(path=a.ACTUAL,bytes=1469770,sha256='5a1aad29eccdbf7bd7842fc2fc170ef07778a706b756dc295107a03f728ed0f6'),
    dict(path='implementation/p09/evidence/p09-166-source-xml-stored-cost.terminal-audit-run01.v1.json',bytes=265293,
        sha256='96d9f5abae47714d0f4f356e11fc0ab334d6c20ee588c5f71731aeae6ee7b808'),
    dict(path='implementation/p09/evidence/p09-166-source-xml-stored-cost.terminal-audit-run02.v1.json',bytes=311754,
        sha256='86ccba87fe8f12bc9d4b5abefa300a5d5cdf6f81c1f88e62fe442d1feaa9a3ea'),
    d.PARENT)

def require(ok,code):d.require(ok,'SYNC_'+code)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('archive','verify'),required=True)
    mode=parser.parse_args().mode;require(p.c.Path.cwd().resolve()==p.c.ROOT,'CWD')
    destination=p.s.scoped_path(ARCHIVE if mode=='archive' else
        'implementation/p09/evidence/p09-166-source-xml-cost.progress-sync-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=True,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_or_thread_started=False)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources)
        with patch('subprocess.Popen',side_effect=AssertionError('P166_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P166_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P166_SYNC_THREAD_FORBIDDEN')):
            q.pin(SELF)
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_RECEIPT')
            light,actual,failed,closing,parent=(q.json(pin['path']) for pin in PINS)
            expected,exe=d.parent_scope(parent)
            require(light['contract_tests_passed']==112 and not light['actual_EXE_SQL_native_or_child_started']
                and light['state']=='PASS_CURRENT_SOURCE_XML_ADAPTIVE_COST_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE','LIGHT_NOT_ACTUAL')
            require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_DURATION_LIMIT'
                and actual['maximum_seconds']==360 and actual['original_full_qualification_seconds']==1200
                and actual['policy']==p.c.POLICY and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[],'ACTUAL_STOP_CLEANUP')
            require(failed['state']=='FAILED_NOT_ACCEPTED' and failed['error_code'].endswith(
                'CONTRACT80_test_diagnostic360_does_not_change_qualification1200_or_original180'),
                'FAILED_AUDIT_RETAINED')
            require(failed['state']=='FAILED_NOT_ACCEPTED' and failed.get('contract_tests_passed') is None,
                'FAILED_NOT_PROMOTED')
            require(closing['state']==a.PASS and closing['contract_tests_passed']==112 and closing['source_closing_exact']
                and closing['current_Rust_input_count']==785 and closing['protected_EXE_inputs_exact']==64
                and closing['actual_diagnostic_receipt_pin']==PINS[1] and closing['completed_case_observations']==50
                and closing['resource_stop_reason'] is None and closing['resource_watcher_cleanup_confirmed'],
                'INDEPENDENT_CLOSING')
            trace=actual['capture_diagnostics']['case_progress']
            require(a.prior.check_trace(trace,actual['source_test_names'])==50 and trace==closing['case_progress']
                and trace['active']['case']==d.full.s.original.full.cost.original.NAME,'CURRENT_SLOW_CASE')
            require(closing['adaptive_schedule'] is None and not closing['adaptive_schedule_complete']
                and not closing['query_reduction_actual_verified'] and not closing['hot_resume_native_actual_verified']
                and actual['capture_diagnostics']['explicit_query_cleanup_confirmed'] is False,'PARTIAL_NATIVE_NOT_PROMOTED')
            for row in (actual,closing):
                require(row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
                    and row['product_complete'] is False and row['P09_gate']=='OPEN' and row['PC_freeze_resolved'] is False,
                    'NO_FULL_OR_FREEZE_PROMOTION')
            for n in ('crates/hwpx-package/src/document_import.rs','crates/domain-ir/src/document_graph.rs',
                    d.SELF,d.TEST,d.adaptive.SELF):
                bound=p.s.inputs.inventory(actual['source_freeze']);require(q.pin(n)==bound[n],'CURRENT_SELECTED_SOURCE')
            require(q.pin(exe['path'])==exe,'CURRENT_R04')
            for n in (a.SELF,'tools/p09/audit_source_xml_stored_cost.py'):q.pin(n)
            if mode=='archive':
                files=[]
                for n in DOCS:
                    raw=q.text(n).encode();pin=q.reader.snapshots[n]
                    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'DOC_BYTES')
                    files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
                q.finish();out.update(state='PASS_P166_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',
                    files=files,evidence_pins=list(PINS))
            else:
                archive=q.json(ARCHIVE);require(archive['evidence_pins']==list(PINS) and len(archive['files'])==2,'ARCHIVE')
                prefix=None
                for item in archive['files']:
                    old=base64.b64decode(item['base64'],validate=True)
                    require(item['path'] in DOCS and len(old)==item['bytes']
                        and hashlib.sha256(old).hexdigest()==item['sha256'],'WHOLE_PREIMAGE')
                    current=q.text(item['path']).encode();require(current.endswith(old) and len(current)>len(old),'WHOLE_PRIOR_DOC')
                    added=current[:-len(old)];require(prefix is None or prefix==added,'IDENTICAL_PREFIX');prefix=added
                header=prefix.decode()
                for token in ('P166 current-source-XML-case-cost-r47:','목표 active','잔여76','P10 새 구현 없음',
                        'compiled249=true/full249=false/signed16=false','STOP_DURATION_LIMIT','50개 완료 관찰',
                        'FAILED_NOT_ACCEPTED','프리즈 해결·전체 성능 개선 미입증','SQL fixed image 부재','Git 명령 없음'):
                    require(token in header,'DOC_BOUNDARIES')
                for pin in PINS[:4]:require(pin['sha256'] in header,'DOC_RECEIPTS')
                q.finish();out.update(state='PASS_CURRENT_SOURCE_XML_COST_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',
                    previous_whole_document_bytes_preserved=True,current_evidence_pins=list(PINS),
                    completed_case_observations=50,active_case_is_not_complete=True,failed_audit_preserved=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.full.s.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
