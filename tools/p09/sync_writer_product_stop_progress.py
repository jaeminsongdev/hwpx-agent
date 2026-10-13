"""P169 build CPU stop/P170 diagnostic-only progress with whole old docs."""
import argparse
import base64
import hashlib
import json
from unittest.mock import patch
import audit_writer_xml_product_build as a
import validated_compiler_progress_r2 as progress

d=a.d
SELF='tools/p09/sync_writer_product_stop_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-169-pre-progress-r49/document-preimages.v1.json'
DOCS=('CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md')
PINS=[
    {
        "path": "implementation/p09/evidence/p09-169-writer-xml-product-build.light-run01.v1.json",
        "bytes": 1718,
        "sha256": "772523b540284204bf05b3b388021665947efe696306ffc2f9296e570708bda7"
    },
    {
        "path": "implementation/p09/evidence/p09-169-writer-xml-product-build.actual-run01.v1.json",
        "bytes": 688481,
        "sha256": "147c344fbe515885ec476667e73099c4736fd2680cd6c4e3c945927c46a345e5"
    },
    {
        "path": "implementation/p09/evidence/p09-169-writer-xml-product-build.terminal-audit-run01.v1.json",
        "bytes": 310589,
        "sha256": "ff7e1d9dc16d9e26e138bdf58b5e73df7ddf89ac2722588e02c217e5619a28a6"
    },
    {
        "path": "implementation/p09/evidence/p09-169-writer-xml-product-inventory.light-run01.v1.json",
        "bytes": 1359,
        "sha256": "b43c588a2e931ee6b5d32489cdc957aa3d00fb841149f77f5dd11d0c5c36b1cf"
    },
    {
        "path": "implementation/p09/evidence/p09-170-validated-compiler-progress.light-run01.v1.json",
        "bytes": 1486,
        "sha256": "8d9a3181f6ce1c6ad855020becd82660657511588b38fb9eb2fee13cd2878066"
    },
    {
        "path": "implementation/p09/evidence/p09-170-validated-compiler-progress.light-run02.v1.json",
        "bytes": 1863,
        "sha256": "c90ee9d44bb80ef1eab3230f8976ff0bfaaec217b25a25668deb0a831dc4b8e0"
    }
]

def require(ok,code):d.require(ok,'SYNC_'+code)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('archive','verify'),required=True)
    mode=parser.parse_args().mode;require(d.c.Path.cwd().resolve()==d.c.ROOT,'CWD')
    destination=d.s.scoped_path(ARCHIVE if mode=='archive' else
        'implementation/p09/evidence/p09-169-writer-product-stop.progress-sync-run01.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',remaining_non_permission_work_units=76,
        PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_child_or_new_thread_started=False)
    try:
        resources.admit();q=d.s.LiveSQLReader(resources)
        with patch('subprocess.Popen',side_effect=AssertionError('P169_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P169_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P169_SYNC_THREAD_FORBIDDEN')):
            q.pin(SELF)
            for pin in PINS:require(q.pin(pin['path'])==pin,'IMMUTABLE_RECEIPTS')
            light,actual,closing,listing_light,first_diag,diag=(q.json(pin['path']) for pin in PINS)
            require(light['state']=='PASS_WRITER_XML_PRODUCT_BUILD_CONTRACTS_ONLY_NOT_RUNTIME_OR_GATE'
                and light['contract_tests_passed']==178 and not light['actual_Cargo_SQL_native_executed'],'BUILD_LIGHT_ONLY')
            require(actual['state']=='STOPPED_NOT_ACCEPTED' and actual['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                and actual['maximum_seconds']==600 and actual['policy']==d.c.POLICY
                and actual['cleanup_confirmed'] and actual['owned_tree_empty'] and actual['heavy_work_started']
                and actual['job_final']['active_processes']==0 and actual['job_final']['owned_processes']==[]
                and actual['writer_xml_delta_closing_pin']==d.PARENT
                and not actual['current_build_binding_accepted'] and actual['build_result'] is None
                and actual['executable_pin'] is None and not actual['native_Process_query_executed'],'BUILD_STOP_CLEANUP')
            require(closing['state']=='PASS_WRITER_XML_PRODUCT_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE'
                and closing['source_closing_exact'] and not closing['current_build_accepted']
                and closing['contract_tests_passed']==178 and closing['current_Rust_input_count']==785
                and closing['protected_executables_exact']==65 and closing['actual_build_receipt_pin']==PINS[1]
                and closing['resource_stop_reason'] is None and closing['resource_watcher_cleanup_confirmed']
                and closing['original_source_final_hash_not_retroactively_promoted'],'CLOSING_NOT_SUCCESS')
            for row in (actual,closing):
                require(all(row[k] is False for k in ('current_compiled249_qualified','full249_current_qualified',
                    'signed16_current_qualified','product_complete','PC_freeze_resolved','full_product_performance_improvement_measured'))
                    and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','NO_PROMOTION')
            require(listing_light['state']=='PASS_WRITER_XML_INVENTORY_CONTRACTS_ONLY_NOT_EXE_OR_GATE'
                and listing_light['contract_tests_passed']==12 and not listing_light['actual_EXE_executed'],'LISTING_NOT_RUN')
            require(first_diag['state']=='PASS_VALIDATED_COMPILER_PROGRESS_CONTRACTS_ONLY_NOT_ACTUAL_BUILD_OR_GATE'
                and first_diag['contract_tests_passed']==10 and not first_diag['actual_compiler_progress_observed']
                and diag['state']=='PASS_RESERVED_COMPILER_PROGRESS_CONTRACTS_ONLY_NOT_ACTUAL_BUILD_OR_GATE'
                and diag['contract_tests_passed']==16 and not diag['actual_compiler_progress_observed']
                and not diag['actual_child_or_new_thread_started'],'DIAGNOSTICS_NOT_ACTUAL')
            for row in (first_diag,diag):
                for pin in row['bound_input_pins']:require(q.pin(pin['path'])==pin,'DIAGNOSTIC_HELPERS_IMMUTABLE')
            progress.contracts()
            frozen=d.s.inputs.inventory(actual['source_freeze'])
            require(q.pin(d.writer.b.SOURCE)==frozen[d.writer.b.SOURCE],'CURRENT_WRITER')
            checked={**frozen,**d.s.inputs.inventory(closing['bound_input_pins'],1333)}
            for n in (d.SELF,d.TEST,a.SELF):require(n in checked and q.pin(n)==checked[n],'BUILD_HELPERS')
            require(not list((d.TARGET/'debug/deps').glob('form_stored_provider*.exe')),'NO_CURRENT_PRODUCT_EXE')
            if mode=='archive':
                files=[]
                for n in DOCS:
                    raw=q.text(n).encode();pin=q.reader.snapshots[n]
                    require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'WHOLE_DOC_BYTES')
                    files.append(dict(**pin,base64=base64.b64encode(raw).decode('ascii')))
                q.finish();out.update(state='PASS_P169_WHOLE_DOCUMENT_PREIMAGES_ONLY_NOT_BUILD_OR_GATE',
                    files=files,evidence_pins=PINS)
            else:
                archive=q.json(ARCHIVE);require(archive['evidence_pins']==PINS and len(archive['files'])==2,'DOC_ARCHIVE')
                prefix=None
                for item in archive['files']:
                    old=base64.b64decode(item['base64'],validate=True)
                    require(item['path'] in DOCS and len(old)==item['bytes']
                        and hashlib.sha256(old).hexdigest()==item['sha256'],'EXACT_WHOLE_PREIMAGE')
                    current=q.text(item['path']).encode();require(current.endswith(old) and len(current)>len(old),'WHOLE_PRIOR_SUFFIX')
                    added=current[:-len(old)];require(prefix is None or added==prefix,'IDENTICAL_DOC_PREFIX');prefix=added
                header=prefix.decode()
                for token in ('P169/P170 current-Writer-build-CPU-stop-r49:','목표 active','잔여76','P10 새 구현 없음',
                        'compiled249=false/full249=false/signed16=false','STOP_SUSTAINED_SYSTEM_CPU',
                        '178 contracts','16 contracts','실제 compiler progress 미관찰','프리즈 해결·전체 성능 개선 미입증',
                        'SQL fixed image 부재','접근허용 없음','Git 명령 없음'):
                    require(token in header,'DOC_BOUNDARIES')
                for pin in PINS:require(pin['sha256'] in header,'DOC_RECEIPTS')
                q.finish();out.update(state='PASS_CURRENT_WRITER_BUILD_STOP_PROGRESS_SYNC_ONLY_NOT_BUILD_OR_GATE',
                    previous_whole_document_bytes_preserved=True,current_evidence_pins=PINS,
                    product_build_accepted=False,compiled_listing_actual_not_started=True,
                    compiler_progress_component_only=True)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','previous_whole_document_bytes_preserved','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
