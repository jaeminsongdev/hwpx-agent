"""P164 diagnostic optimization and P165 connection only; no full/Gate PASS."""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import run_adaptive_source_xml_full as d
import probe_adaptive_host_cpu_sampler_r2 as probe

p=d.p
SELF='tools/p09/sync_adaptive_sampling_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-164-pre-progress-r45/document-preimages.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PINS=(
    dict(path='implementation/p09/evidence/p09-164-adaptive-native-query.light-run01.v1.json',bytes=3091,sha256='a12be6786ad2bde9223d879d62f9b70d961455208e485ce0ea6617e97a45d45a'),
    dict(path='implementation/p09/evidence/p09-164-adaptive-native-query.actual-run01.v1.json',bytes=29155,sha256='80c116b1cd17ae20d1ab9f26de6c987778f1616876130bc4dc3888a717463b9e'),
    dict(path='implementation/p09/evidence/p09-164-adaptive-native-query.light-run02.v1.json',bytes=12831,sha256='745b2751d44e950ca1587015baa6d2359b3b2e58168570dc9bf4aa8d9c36fe6b'),
    dict(path='implementation/p09/evidence/p09-164-adaptive-native-query.actual-run02.v1.json',bytes=37564,sha256='94b451a4b0b71b789b8ff66be8097d13143602957385918b8ebd26f18ae0108f'),
    d.PARENT,
    dict(path='implementation/p09/evidence/p09-165-adaptive-source-xml-full.light-run01.v1.json',bytes=1981,sha256='52eb8a0192c819deea8f48659386597689892a0c605a9a9a2a6a43b222d60f72'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('archive','verify'),required=True);mode=parser.parse_args().mode
    d.require(p.c.Path.cwd().resolve()==p.c.ROOT,'SYNC_CWD')
    destination=p.s.scoped_path(ARCHIVE if mode=='archive' else
        'implementation/p09/evidence/p09-164-adaptive-sampling.progress-sync-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=True,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_or_thread_started=False,hot_resume_native_actual_verified=False)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P164_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P164_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P164_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:d.require(q.pin(pin['path'])==pin,'SYNC_RECEIPT_PINS')
            oldlight,old,light,actual,closing,prepared=(q.json(pin['path']) for pin in PINS)
            expected,exe=d.parent_scope(closing)
            d.require(closing['prior_run01_startup_helper_binding_complete'] is False
                and closing['prior_run01_product_or_full_qualification'] is False
                and len(old['source_freeze'])==13 and oldlight['contract_tests_passed']==81,'SYNC_RUN01_PARTIAL_PRESERVED')
            d.require(actual['state']==probe.PASS and actual['exit_code']==0 and actual['stop_reason'] is None
                and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[]
                and len(actual['source_freeze'])==67 and actual['observer_query_cleanup_confirmed'],'SYNC_REAL_NATIVE_ONLY')
            probe.validate_payload(actual['observer_probe'])
            d.require(actual['observer_probe']['schedule']==closing['actual_four_host_poll_schedule']
                and closing['actual_native_query_calls']==3 and closing['cold_native_queries_avoided']==2
                and closing['equivalent_old_per_poll_recipe_query_calls']==5
                and closing['old_per_poll_recipe_not_actually_rerun'] is True
                and closing['hot_resume_native_actual_verified'] is False,'SYNC_COUNTER_REDUCTION_NOT_CAUSE')
            d.require(light['contract_tests_passed']==81 and prepared['contract_tests_passed']==85
                and prepared['state']=='PASS_ADAPTIVE_SOURCE_XML_FULL_CONNECTION_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
                and prepared['actual_product_test_body_executed'] is False,'SYNC_PREP_ONLY85')
            for row in (actual,closing,prepared):d.require(not row['full249_current_qualified'] and not row['signed16_current_qualified']
                and not row['product_complete'] and not row['PC_freeze_resolved'],'SYNC_NO_FULL_OR_FREEZE_PROMOTION')
            for n in ('crates/hwpx-package/src/document_import.rs','crates/domain-ir/src/document_graph.rs',
                    d.adaptive.SELF,probe.SELF,probe.TEST,'tools/p09/audit_adaptive_native_query.py'):
                d.require(q.pin(n)==expected[n],'SYNC_CURRENT_SELECTED_SOURCE')
            for pin in prepared['bound_input_pins']:d.require(q.pin(pin['path'])==pin,'SYNC_PREPARED_CONNECTION_FRESH')
            d.require(q.pin(exe['path'])==exe,'SYNC_CURRENT_R04')
            if mode=='archive':
                files=[]
                for n in DOCS:
                    raw=q.text(n).encode();pin=q.reader.snapshots[n]
                    d.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'SYNC_DOC_BYTES')
                    files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
                out.update(files=files,evidence_pins=list(PINS));q.finish()
                out['state']='PASS_P164_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE'
            else:
                archive=q.json(ARCHIVE);d.require(archive['evidence_pins']==list(PINS) and len(archive['files'])==2,'SYNC_ARCHIVE')
                prefix=None
                for item in archive['files']:
                    oldbytes=base64.b64decode(item['base64'],validate=True)
                    d.require(item['path'] in DOCS and len(oldbytes)==item['bytes']
                        and hashlib.sha256(oldbytes).hexdigest()==item['sha256'],'SYNC_WHOLE_PREIMAGE')
                    current=q.text(item['path']).encode();d.require(current.endswith(oldbytes) and len(current)>len(oldbytes),'SYNC_WHOLE_PRIOR_DOC')
                    added=current[:-len(oldbytes)];d.require(prefix is None or prefix==added,'SYNC_IDENTICAL_PREFIX');prefix=added
                header=prefix.decode()
                for token in ('P164 adaptive-native-query-schedule-r45:','목표 active','잔여76','P10 새 구현 없음',
                        'compiled249=true/full249=false/signed16=false','hot resume 실제 검증 미실행',
                        '프리즈 해결·전체 성능 개선 미입증','SQL fixed image 부재','Git 명령 없음','P165 actual 미실행'):
                    d.require(token in header,'SYNC_DOC_BOUNDARIES')
                for pin in PINS:d.require(pin['sha256'] in header,'SYNC_DOC_RECEIPTS')
                q.finish();out.update(state='PASS_ADAPTIVE_SAMPLING_AND_CONNECTION_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',
                    previous_whole_document_bytes_preserved=True,current_evidence_pins=list(PINS),
                    actual_counter_queries=3,actual_cold_queries_avoided=2,prepared_full_connection_contracts_passed=85)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=d.s.original.closed_error(e)
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
