"""P163 actual emergency-stop and post-stop-only observation docs sync.

No runtime retry, permission dialog, system mutation, child or new thread.
Immutable evidence/whole-document preimages only; docs use apply_patch.
"""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import run_source_xml_product_full as d
import probe_host_cpu_groups as native

p=d.p
SELF='tools/p09/sync_source_xml_full_stop_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-163-pre-progress-r44/document-preimages.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PINS=(
    dict(path='implementation/p09/evidence/p09-163-source-xml-product-full.light-run01.v1.json',bytes=2204,sha256='d9280a828183bde937620f3b407a1222aea5a305952c40ab77baa19bd45038fd'),
    dict(path='implementation/p09/evidence/p09-163-source-xml-product-full.actual-run01.v1.json',bytes=722862,sha256='090923b57aee1da25764952c377c7818051751aef56a2dfd4859410de5c9a0ab'),
    dict(path='implementation/p09/evidence/p09-163-source-xml-product-full.terminal-audit-run01.v1.json',bytes=367844,sha256='d98386dbde4fc75c1507f07893a303f9dac2b93b8b9c2dbec590a22098acbaba'),
    dict(path='implementation/p09/evidence/p09-153-host-cpu-groups.actual-run03.v1.json',bytes=20460,sha256='fd65875445f962d09a9a805850de2d6cbf3b09babd73194ae60bdc29ca85c877'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('archive','verify'),required=True);a=parser.parse_args()
    d.require(p.c.Path.cwd().resolve()==p.c.ROOT,'STOP_SYNC_CWD')
    destination=p.s.scoped_path(ARCHIVE if a.mode=='archive' else
        'implementation/p09/evidence/p09-163-source-xml-full-stop.progress-sync-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=True,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76,
        actual_audit_child_or_thread_started=False,causal_attribution=False)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P163_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P163_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P163_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:d.require(q.pin(pin['path'])==pin,'STOP_SYNC_IMMUTABLE_RECEIPTS')
            light,row,closing,post=(q.json(pin['path']) for pin in PINS)
            d.require(light['contract_tests_passed']==52,'STOP_SYNC_LIGHT52')
            d.require(row['state']=='STOPPED_NOT_ACCEPTED' and row['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and row['tests_passed'] is None and row['maximum_seconds']==1200 and row['policy']==p.c.POLICY
                and row['current_inventory_closing_pin']==d.PARENT and row['source_xml_inventory_closing_pin']==d.PARENT
                and row['cleanup_confirmed'] and row['owned_tree_empty']
                and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[]
                and row['owned_limits_readback']['verified']
                and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25,'STOP_SYNC_ORIGINAL_STOP')
            last=row['samples'][-4:]
            d.require(len(last)==4 and all(x['system_cpu_percent']>=98 for x in last)
                and all(0<=x['owned_job_cpu_machine_percent']<1 for x in last),'STOP_SYNC_LAST4_HOST_AND_OWNED')
            cap=row['capture_diagnostics'];d.require(cap['explicit_query_cleanup_confirmed'] is False
                and cap['host_cpu_error_code'] is None and sum(x['kind']=='sample' for x in cap['host_cpu_records'])==2
                and cap['raw_names_paths_commands_saved'] is False and cap['causal_attribution'] is False,'STOP_SYNC_PARTIAL_NATIVE_NOT_CAUSAL')
            d.require(closing['state']=='PASS_SOURCE_XML_CURRENT_FULL_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'
                and closing['source_closing_exact'] and closing['actual_tests_passed'] is None
                and closing['original_source_final_hash_not_retroactively_promoted']
                and closing['contract_tests_passed']==64 and closing['current_Rust_input_count']==785
                and closing['protected_EXE_inputs_exact']==64 and closing['resource_stop_reason'] is None
                and closing['resource_watcher_cleanup_confirmed'],'STOP_SYNC_CLOSING_ONLY')
            for item in (row,closing):d.require(not item['full249_current_qualified'] and not item['signed16_current_qualified']
                and not item['product_complete'] and item['P09_gate']=='OPEN' and not item['PC_freeze_resolved'],'STOP_SYNC_NO_PRODUCT_PROMOTION')
            frozen=p.s.inputs.inventory(closing['bound_input_pins'],1295)
            for n in (d.SELF,d.TEST,'tools/p09/audit_source_xml_product_full.py',
                    'crates/hwpx-package/src/document_import.rs','crates/domain-ir/src/document_graph.rs'):
                d.require(q.pin(n)==frozen[n],'STOP_SYNC_SELECTED_CURRENT_SOURCE')
            exe=closing['compiled_test_executable_pin'];d.require(q.pin(exe['path'])==exe==row['compiled_test_executable_pin'],'STOP_SYNC_CURRENT_R04')
            d.require(q.pin(d.PARENT['path'])==d.PARENT,'STOP_SYNC_ORIGINAL_LISTING_CLOSURE')
            d.require(post['state']==native.PASS and post['observer_query_cleanup_confirmed']
                and post['cleanup_confirmed'] and post['owned_tree_empty'] and post['job_final']['active_processes']==0
                and post['job_final']['owned_processes']==[] and post['causal_attribution'] is False
                and post['raw_process_names_saved'] is False and post['commands_paths_saved'] is False
                and not post['Rust_or_test_body_executed'],'STOP_SYNC_POST_STOP_ONLY_PROBE')
            native.validate_payload(post['observer_probe'])
            for n,pin in p.s.inputs.inventory(post['source_freeze'],10).items():
                d.require(q.pin(n)==pin,'STOP_SYNC_NATIVE_WHOLE_INPUTS')
            if a.mode=='archive':
                files=[]
                for n in DOCS:
                    raw=q.text(n).encode();pin=q.reader.snapshots[n]
                    d.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'STOP_SYNC_DOC_BYTES')
                    files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
                out.update(files=files,evidence_pins=list(PINS));q.finish()
                out['state']='PASS_P163_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE'
            else:
                archive=q.json(ARCHIVE);d.require(archive['evidence_pins']==list(PINS)
                    and len(archive['files'])==2 and archive['state']=='PASS_P163_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','STOP_SYNC_DOC_ARCHIVE')
                prefix=None
                for item in archive['files']:
                    old=base64.b64decode(item['base64'],validate=True)
                    d.require(item['path'] in DOCS and len(old)==item['bytes']
                        and hashlib.sha256(old).hexdigest()==item['sha256'],'STOP_SYNC_WHOLE_DOC_PREIMAGE')
                    current=q.text(item['path']).encode();d.require(current.endswith(old) and len(current)>len(old),'STOP_SYNC_PRIOR_WHOLE_DOC_PRESERVED')
                    added=current[:-len(old)];d.require(prefix is None or prefix==added,'STOP_SYNC_IDENTICAL_PREFIX');prefix=added
                header=prefix.decode()
                for token in ('P163 current-source-XML-full-CPU-stop-r44:','목표 active','잔여76','P10 새 구현 없음',
                        'compiled249=true/full249=false/signed16=false/tests_passed=null','STOP_SUSTAINED_SYSTEM_CPU',
                        '98.48/100/100/100','프리즈 해결·성능 개선 미입증','SQL fixed image 부재',
                        '중단 당시 원인 입증 아님','Git 명령 없음'):
                    d.require(token in header,'STOP_SYNC_DOC_BOUNDARIES')
                for pin in PINS:d.require(pin['sha256'] in header,'STOP_SYNC_DOC_PINS')
                q.finish();out.update(state='PASS_SOURCE_XML_FULL_CPU_STOP_PROGRESS_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
                    previous_whole_document_bytes_preserved=True,current_evidence_pins=list(PINS),
                    original_failed_full_not_promoted=True,post_stop_native_observation_not_causal=True)
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
