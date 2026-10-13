"""P178 r56 whole document archive and exact build-closing progress receipt."""
import argparse
import base64
import hashlib
import json
import build_xml_capacity_product as b
import build_xml_capacity_product_r3 as candidate
import audit_lower_pressure_xml_product as audit
SELF='tools/p09/verify_lower_pressure_product_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-178-pre-progress-r56/document-preimages.v1.json'
DEST='implementation/p09/evidence/p09-178-owned-hash-pressure.progress-sync-run02.v1.json'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True);mode=ap.parse_args().mode
    destination=b.s.scoped_path(ARCHIVE if mode=='archive' else DEST,fresh=True);resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF)
        if mode=='archive':
            files=[]
            for name in b.parser.DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                b.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'P178_WHOLE_DOC_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_P178_R56_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            actual=q.json(candidate.prior.ACTUAL);closing=q.json(audit.DEST);prep=q.json(candidate.prior.PREPARATION)
            b.require(actual['cleanup_confirmed'] and actual['owned_tree_empty'] and closing['resource_watcher_cleanup_confirmed'],
                'P178_TERMINAL')
            accepted=closing['state']==audit.PASS
            b.require(closing['state'] in (audit.PASS,'PASS_R07_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE','FAILED_NOT_ACCEPTED'),
                'P178_CLOSING_SCOPE')
            if accepted:
                b.require(actual['state']==b.PASS and actual['current_build_binding_accepted'] and actual['build_only_accepted']
                    and actual['source_freeze_exact_after'] and actual['protected_executables_exact_after']
                    and actual['exit_code']==0 and actual['stop_reason'] is None
                    and closing['source_closing_exact'] and closing['current_build_accepted']
                    and closing['contract_tests_passed']==262 and closing['current_Rust_input_count']==785
                    and closing['protected_executables_exact']==67 and closing['resource_stop_reason'] is None
                    and closing['actual_build_receipt_pin']==q.pin(candidate.prior.ACTUAL)
                    and closing['compiled_test_executable_pin']==actual['executable_pin'],'P178_FULL_BUILD_CLOSING')
                b.require(q.pin(actual['executable_pin']['path'])==actual['executable_pin'],'P178_FRESH_R07_EXE')
                pins=b.s.inputs.inventory(closing['bound_input_pins'])
                b.require(sum(n.endswith('.exe') for n in pins)==68 and closing['IO']['finished']
                    and closing['IO']['bound_inputs']==closing['IO']['final_fresh_hashes']==len(pins),'P178_FULL_FRESH68')
            b.require(prep['state']=='PASS_R07_CURRENT_SOURCE_PREPARATION_ONLY_NOT_BUILD_RUNTIME_OR_GATE'
                and prep['source_closing_exact'] and prep['contract_tests_passed']==262
                and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed'],'P178_PREPARATION')
            for row in (actual,closing):
                b.require(not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                    and not row['signed16_current_qualified'] and not row['product_complete']
                    and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','P178_NOT_PRODUCT_OR_GATE')
            archive=q.json(ARCHIVE);prefixes=[]
            b.require(archive['state']=='WHOLE_P178_R56_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','P178_ARCHIVE_SCOPE')
            for name in b.parser.DOCS:
                _,raw=b.parser.preimage(archive,name);current=q.text(name).encode()
                b.require(current.endswith(raw) and len(current)>len(raw),'P178_WHOLE_PRIOR_SUFFIX');prefixes.append(current[:-len(raw)])
            b.require(prefixes[0]==prefixes[1] and b'P178' in prefixes[0] and b'TERMINAL' in prefixes[0]
                and b'compiled249=false/full249=false/signed16=false' in prefixes[0],'P178_SAME_PREFIX')
            q.finish();out.update(state='PASS_P178_TERMINAL_BUILD_DOCUMENT_SYNC_ONLY_NOT_PRODUCT_OR_GATE',
                current_build_accepted=accepted,independent_build_closing_qualified=accepted,whole_prior_documents_preserved=True,
                actual_build_receipt_pin=q.reader.snapshots[candidate.prior.ACTUAL],closing_receipt_pin=q.reader.snapshots[audit.DEST])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','current_build_accepted','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_','WHOLE_')) else 2

if __name__=='__main__':raise SystemExit(main())
