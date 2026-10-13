"""P162 evidence/docs sync with exclusive whole-preimage archive.

Does not build/list/test, change settings, or execute any OS child/thread.
Only immutable evidence JSON is written here; document edits use apply_patch.
"""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import build_source_xml_product as d

p=d.p
SELF='tools/p09/sync_source_xml_product_progress_r2.py'
ARCHIVE='implementation/p09/source-archive/p09-162-pre-progress-r43/document-preimages-run02.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PINS=(
    dict(path='implementation/p09/evidence/p09-162-source-xml-product-build.light-run01.v1.json',bytes=1439,sha256='ee11d737ae81384a87874f2326b10be53941a4ad703d4a7c8638074839a50d47'),
    dict(path='implementation/p09/evidence/p09-162-source-xml-product-build.actual-run01.v1.json',bytes=887310,sha256='351d1aeafbbcd8ca43f6965a4299c8a905cb268f30a1530a6a093fcc2859e2b9'),
    dict(path='implementation/p09/evidence/p09-162-source-xml-product-build.terminal-audit-run01.v1.json',bytes=364919,sha256='45bc28afba022dd36e3f81be2947b838702b6c74a73ec5714991d5cc5e49ef69'),
    dict(path='implementation/p09/evidence/p09-162-source-xml-product-inventory.light-run01.v1.json',bytes=1762,sha256='820e714183754fa1dc044f9a3bd40c1482e997bb9d33ee249cc69b0f336a892d'),
    dict(path='implementation/p09/evidence/p09-162-source-xml-product-inventory.actual-run01.v1.json',bytes=414840,sha256='fc8e8f43b664201fca760eca43eb4ca0d757dca054c273c0bf87d61d2c6233c1'),
    dict(path='implementation/p09/evidence/p09-162-source-xml-product-inventory.terminal-audit-run01.v1.json',bytes=358557,sha256='7fd9777c4c1f1574f2a6e84ed2c0a4ad06b6c4de2a45cef7f6a4ac258045dc3d'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('archive','verify'),required=True);a=parser.parse_args()
    d.require(p.c.Path.cwd().resolve()==p.c.ROOT,'SYNC_CWD')
    destination=p.s.scoped_path(ARCHIVE if a.mode=='archive' else
        'implementation/p09/evidence/p09-162-source-xml-product.progress-sync-run02.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=True,
        compiled249_qualification_is_listing_only=True,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76,
        actual_audit_child_or_thread_started=False)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P162_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P162_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P162_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:d.require(q.pin(pin['path'])==pin,'SYNC_IMMUTABLE_RECEIPTS')
            light,build,closing,listlight,listing,listclosing=(q.json(pin['path']) for pin in PINS)
            d.require(light['contract_tests_passed']==50 and listlight['contract_tests_passed']==16,'SYNC_CONTRACTS')
            d.require(build['state']==d.PASS and build['exit_code']==0 and build['stop_reason'] is None
                and closing['current_build_accepted'] and closing['contract_tests_passed']==50,'SYNC_BUILD_ONLY')
            d.require(listclosing['state']=='PASS_SOURCE_XML_CURRENT_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'
                and listclosing['source_closing_exact'] and listclosing['current_compiled249_qualified']
                and listclosing['compiled_test_count']==249 and listclosing['source_module_instance_count']==59
                and listclosing['current_Rust_input_count']==785 and listclosing['contract_tests_passed']==66
                and listclosing['protected_parent_EXE_inputs_exact']==64
                and listclosing['resource_stop_reason'] is None and listclosing['resource_watcher_cleanup_confirmed'],'SYNC_LIST_CLOSING')
            for row in (build,listing):
                d.require(row['cleanup_confirmed'] and row['owned_tree_empty'] and row['job_final']['active_processes']==0
                    and row['job_final']['owned_processes']==[] and not row['runtime_tests_executed'],'SYNC_NO_BODIES_CLEAN')
            for row in (build,closing,listing,listclosing):
                d.require(not row['full249_current_qualified'] and not row['signed16_current_qualified']
                    and not row['product_complete'] and row['P09_gate']=='OPEN' and not row['PC_freeze_resolved'],'SYNC_NO_GATE_OR_FREEZE_PROMOTION')
            frozen=p.s.inputs.inventory(listclosing['bound_input_pins'],1290)
            for n in ('crates/hwpx-package/src/document_import.rs','crates/domain-ir/src/document_graph.rs',
                    d.SELF,d.TEST,'tools/p09/audit_source_xml_product_build.py',
                    'tools/p09/run_source_xml_product_inventory.py','tools/p09/tests/test_source_xml_product_inventory.py'):
                d.require(q.pin(n)==frozen[n],'SYNC_SELECTED_CURRENT_SOURCE')
            exe=listclosing['compiled_test_executable_pin'];d.require(q.pin(exe['path'])==exe==build['executable_pin'],'SYNC_CURRENT_R04')
            d.require(q.pin(d.PARENT['path'])==d.PARENT,'SYNC_FAILED_UNIT_HISTORY_CLOSURE_PRESERVED')
            if a.mode=='archive':
                files=[]
                for n in DOCS:
                    raw=q.text(n).encode('utf-8');pin=q.reader.snapshots[n]
                    d.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'SYNC_DOC_RAW_BYTES')
                    files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
                out.update(files=files,evidence_pins=list(PINS));q.finish()
                out.update(state='PASS_P162_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_PRODUCT_OR_GATE')
            else:
                archive=q.json(ARCHIVE);d.require(archive['evidence_pins']==list(PINS)
                    and archive['state']=='PASS_P162_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_PRODUCT_OR_GATE'
                    and len(archive['files'])==2,'SYNC_DOC_ARCHIVE')
                prefix=None
                for item in archive['files']:
                    old=base64.b64decode(item['base64'],validate=True)
                    d.require(item['path'] in DOCS and len(old)==item['bytes']
                        and hashlib.sha256(old).hexdigest()==item['sha256'],'SYNC_ARCHIVE_WHOLE_BYTES')
                    current=q.text(item['path']).encode('utf-8')
                    d.require(current.endswith(old) and len(current)>len(old),'SYNC_WHOLE_PRIOR_DOC_PRESERVED')
                    added=current[:-len(old)];d.require(prefix is None or prefix==added,'SYNC_IDENTICAL_PREFIX');prefix=added
                header=prefix.decode('utf-8')
                for token in ('P162 source-XML-current-product-build-and-list-r43:','목표 active','잔여76',
                        'compiled249=true(listing ONLY)/full249=false/signed16=false','P10 새 구현 없음',
                        '프리즈 해결·성능 개선 미입증','hostCPU max100%','SQL fixed image 부재','Git 명령 없음'):
                    d.require(token in header,'SYNC_DOC_BOUNDARIES')
                for pin in PINS:d.require(pin['sha256'] in header,'SYNC_DOC_EXACT_RECEIPTS')
                q.finish();out.update(state='PASS_SOURCE_XML_PRODUCT_BUILD_AND_LIST_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',
                    previous_whole_document_bytes_preserved=True,current_evidence_pins=list(PINS))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=str(e) if isinstance(e,ValueError) else 'P162_SYNC_REDACTED_FAILURE'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
