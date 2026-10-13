"""P161 progress: units68 only; original failures/docs preserved, no Gate."""
import base64
import hashlib
import json
from unittest.mock import patch
import source_xml_reuse_binding as b

SELF='tools/p09/verify_source_xml_reuse_progress.py'
DOC_ARCHIVE='implementation/p09/source-archive/p09-161-pre-progress-r42/document-pins.v1.json'
FAIL_ARCHIVE='implementation/p09/source-archive/p09-161-initial-failures-r42/preimages.v1.json'
PINS=(
    dict(path='implementation/p09/evidence/p09-161-source-xml-reuse.units-run01.v1.json',bytes=657719,sha256='3aa53c03793d1ba491713d2a9fef6a9c27a8282892ed0c058668dabfcf794163'),
    dict(path='implementation/p09/evidence/p09-161-source-xml-reuse.source-closing-run01.v1.json',bytes=257924,sha256='e872d0a00264f270545c9fe95db76a5275aea07c8b85742a84ef1ef1ef3c955f'),
    dict(path='implementation/p09/evidence/p09-161-source-xml-reuse.source-closing-run02.v1.json',bytes=299662,sha256='b639dd28fcf2d35a1d6495c33276c8b822edc3b2b629d87c7a33c92a4eb35461'),
    dict(path='implementation/p09/evidence/p09-161-source-xml-reuse.units-run02.v1.json',bytes=697853,sha256='b96cf3dd695ccf3076071dbd7c73ca6ca8053330465f5adf7ed5129e4a8cf547'),
    dict(path='implementation/p09/evidence/p09-161-source-xml-reuse.source-closing-run03.v1.json',bytes=300097,sha256='06064c635b123d3665369374a3c342a254b0451e4ceb44e8f5c09d7cb5aa23b1'))

def main():
    b.require(b.p.c.Path.cwd().resolve()==b.p.c.ROOT,'SYNC_CWD')
    destination=b.s.scoped_path('implementation/p09/evidence/p09-161-source-xml-reuse.progress-sync-run01.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',current_compiled249_qualified=False,full249_current_qualified=False,
        signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        goal_status='active',remaining_non_permission_work_units=76,PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_audit_child_or_thread_started=False)
    try:
        resources.admit();q=b.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P161_SYNC_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P161_SYNC_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P161_SYNC_THREAD_FORBIDDEN')):
            for pin in PINS:b.require(q.pin(pin['path'])==pin,'SYNC_EVIDENCE')
            failed,bad,account,units,audit=(q.json(pin['path']) for pin in PINS)
            b.require(failed['state']=='STOPPED_NOT_ACCEPTED' and failed['compiler_error_codes']==['E0061']
                and bad['state']=='FAILED_NOT_ACCEPTED' and bad['error_code']=='sql_io_already_finished'
                and account['actual_unit_tests_passed'] is None and not account['typecheck_accepted'],'SYNC_FAILURES_NOT_PROMOTED')
            b.require(units['state']=='PASS_SOURCE_XML_REUSE_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
                and units['tests_passed']==68 and units['exit_code']==0 and units['stop_reason'] is None
                and units['job_final']['active_processes']==0 and units['job_final']['owned_processes']==[]
                and units['cleanup_confirmed'] and units['owned_tree_empty'],'SYNC_UNIT68')
            b.require(audit['state']=='PASS_SOURCE_XML_REUSE_DELTA_AND_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
                and audit['source_closing_exact'] and audit['actual_unit_tests_passed']==68 and audit['typecheck_accepted']
                and audit['whole_original_core_inverse_exact'] and audit['all_original_package_lib_tests_preserved']
                and audit['protected_parent_EXE_inputs_exact']==62 and audit['current_Rust_input_count']==785
                and audit['resource_stop_reason'] is None and audit['resource_watcher_cleanup_confirmed'],'SYNC_CLOSING')
            for row in (units,audit):b.require(not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete'] and row['P09_gate']=='OPEN','SYNC_NO_PRODUCT')
            frozen=b.s.inputs.inventory(audit['bound_input_pins'])
            for n in (b.SOURCE,b.SELF,'tools/p09/run_source_xml_reuse_units.py','tools/p09/audit_source_xml_reuse.py'):
                b.require(q.pin(n)==frozen[n],'SYNC_CURRENT_SOURCE')
            exe=audit['fresh_package_lib_executable_pin'];b.require(q.pin(exe['path'])==exe,'SYNC_LIB_EXE')
            archive=q.json(FAIL_ARCHIVE);b.require(archive['failed_receipt_pins']==list(PINS[:2]),'SYNC_FAILED_RECEIPT_PINS')
            for item in archive['files']:
                raw=base64.b64decode(item['base64'],validate=True)
                b.require(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'SYNC_FAILED_WHOLE_PREIMAGE')
            prior=b.s.inputs.inventory(q.json(DOC_ARCHIVE)['files'],2);prefix=None
            b.require(set(prior)=={'CURRENT_STATE.md','implementation/p09/P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md'},'SYNC_DOC_SCOPE')
            for n,pin in prior.items():
                current=q.text(n).encode();now=q.reader.snapshots[n]
                b.require(len(current)==now['bytes'] and hashlib.sha256(current).hexdigest()==now['sha256'],'SYNC_DOC_BYTES')
                b.require(len(current)>pin['bytes'] and hashlib.sha256(current[-pin['bytes']:]).hexdigest()==pin['sha256'],'SYNC_WHOLE_PRIOR_DOC')
                this=current[:-pin['bytes']];b.require(prefix is None or this==prefix,'SYNC_IDENTICAL_PREFIX');prefix=this
            header=prefix.decode();b.require(header.startswith('> 2026-10-08 P161 source-import-call-local-XML-reuse-r42:'),'SYNC_PREFIX')
            for token in ('목표 active','product=false','P10 새 구현 없음','잔여76','current_compiled249=false/full249=false/signed16=false',
                    '원래64+추가4','프리즈 해결은 미입증','SQL fixed image 부재','Git blob batch 단일 프로세스'):
                b.require(token in header,'SYNC_BOUNDARY')
            for pin in PINS:b.require(pin['sha256'] in header,'SYNC_DOC_PIN')
            q.finish();out.update(state='PASS_SOURCE_XML_REUSE_UNIT68_PROGRESS_SYNC_ONLY_NOT_FULL249_OR_GATE',
                source_closing_exact=True,previous_whole_document_bytes_preserved=True,previous_failure_receipts_preserved=True,
                actual_unit_tests_passed=68,current_evidence_pins=list(PINS))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=b.prior.full.s.original.closed_error(e)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_unit_tests_passed','previous_whole_document_bytes_preserved','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
