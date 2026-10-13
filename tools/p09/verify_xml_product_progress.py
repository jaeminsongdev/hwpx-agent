"""P177 bounded whole-document archive/sync proof, build is not product acceptance."""
import argparse
import base64
import hashlib
import json
import build_xml_capacity_product as b
import audit_xml_capacity_product as audit
SELF='tools/p09/verify_xml_product_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-177-pre-progress-r55/document-preimages.v1.json'
DEST='implementation/p09/evidence/p09-177-xml-capacity-product-build.progress-sync-run01.v1.json'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True);mode=ap.parse_args().mode
    destination=b.s.scoped_path(ARCHIVE if mode=='archive' else DEST,fresh=True)
    resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,PC_freeze_resolved=False)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF)
        if mode=='archive':
            files=[]
            for name in b.parser.DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                b.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'WHOLE_DOCUMENT_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_P177_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            actual=q.json(b.ACTUAL);closing=q.json(audit.DEST);preparation=q.json(b.PREPARATION)
            accepted=closing['state']==audit.PASS
            b.require(actual['cleanup_confirmed'] and actual['owned_tree_empty'] and closing['resource_watcher_cleanup_confirmed'],
                'TERMINAL_CLEANUP')
            b.require(closing['state'] in (audit.PASS,'PASS_R07_BUILD_STOP_ACCOUNTED_ONLY_NOT_BUILD_OR_GATE','FAILED_NOT_ACCEPTED')
                and preparation['source_closing_exact'] and preparation['contract_tests_passed']==254,'BOUND_STATES')
            if accepted:
                b.require(actual['state']==b.PASS and actual['current_build_binding_accepted'] and actual['source_freeze_exact_after']
                    and actual['protected_executables_exact_after'] and actual['exit_code']==0 and actual['stop_reason'] is None
                    and closing['current_build_accepted'] and closing['source_closing_exact'] and closing['contract_tests_passed']==254
                    and closing['current_Rust_input_count']==785 and closing['protected_executables_exact']==67
                    and closing['compiled_test_executable_pin']==actual['executable_pin']
                    and closing['actual_build_receipt_pin']==q.pin(b.ACTUAL)
                    and closing['resource_stop_reason'] is None,'WHOLE_BUILD_CLOSING')
                b.require(q.pin(actual['executable_pin']['path'])==actual['executable_pin'],'CURRENT_R07_EXE')
            for row in (actual,closing):
                b.require(not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                    and not row['signed16_current_qualified'] and not row['product_complete']
                    and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN','BUILD_NOT_RUNTIME_OR_GATE')
            old=q.json(ARCHIVE);prefixes=[]
            b.require(old['state']=='WHOLE_P177_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','DOCUMENT_ARCHIVE')
            for name in b.parser.DOCS:
                _,raw=b.parser.preimage(old,name);current=q.text(name).encode()
                b.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX');prefixes.append(current[:-len(raw)])
            b.require(prefixes[0]==prefixes[1] and b'P177' in prefixes[0] and b'TERMINAL' in prefixes[0]
                and b'compiled249=false/full249=false/signed16=false' in prefixes[0],'SAME_TERMINAL_PREFIX')
            q.finish();out.update(state='PASS_R07_TERMINAL_DOCUMENT_SYNC_ONLY_NOT_PRODUCT_OR_GATE',
                independent_build_closing_qualified=accepted,whole_prior_documents_preserved=True,
                actual_build_receipt_pin=q.reader.snapshots[b.ACTUAL],closing_receipt_pin=q.reader.snapshots[audit.DEST])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','independent_build_closing_qualified','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_','WHOLE_')) else 2

if __name__=='__main__':raise SystemExit(main())
