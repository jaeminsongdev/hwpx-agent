"""P181/P182 r57 whole document preservation and terminal scope accounting."""
import argparse
import base64
import hashlib
import json
import close_r07_compiler_output as build
import run_r07_postclosed_inventory as listing
import audit_r07_postclosed_inventory as audit
b=build.b
SELF='tools/p09/sync_r07_postclosed_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-181-pre-progress-r57/document-preimages.v1.json'
DEST='implementation/p09/evidence/p09-182-r07-postclosed-inventory.progress-sync-run01.v1.json'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True);mode=ap.parse_args().mode
    destination=b.s.scoped_path(ARCHIVE if mode=='archive' else DEST,fresh=True)
    resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        remaining_non_permission_work_units=76,whole_current_runtime_inputs_reaudited_by_doc_sync=False)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF)
        if mode=='archive':
            files=[]
            for name in b.parser.DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                b.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'R57_WHOLE_DOC_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_P181_P182_R57_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            b.require(q.pin(listing.CLOSING['path'])==listing.CLOSING,'R57_BUILD_PIN')
            closing=q.json(listing.CLOSING['path']);_,exe=listing.closing_scope(closing)
            original=q.json(build.ACTUAL['path']);b.require(q.pin(build.ACTUAL['path'])==build.ACTUAL,'R57_ORIGINAL_STOP_PIN')
            build.metadata_scope(original)
            prep=q.json(listing.PREP);actual=None;accepted=False
            if (b.c.ROOT/listing.ACTUAL).exists():
                actual=q.json(listing.ACTUAL);accepted=actual['state']==listing.PASS
                b.require(actual['cleanup_confirmed'] and actual['owned_tree_empty']
                    and actual['state'] in (listing.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED'), 'R57_LIST_TERMINAL')
            else:
                b.require(prep['state']=='FAILED_NOT_ACCEPTED' and not prep['source_closing_exact']
                    and prep['error_code']==prep['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
                    and prep['resource_watcher_cleanup_confirmed'] and not prep['actual_EXE_executed']
                    and prep['IO']['finished'] is False
                    and prep['IO']['final_fresh_hashes']<prep['IO']['bound_inputs'],'R57_PREPARATION_STOP_NOT_RUN')
            if accepted:
                audit.actual_scope(actual);checked=q.json(audit.DEST)
                pins=b.s.inputs.inventory(checked['bound_input_pins'])
                b.require(checked['state']==audit.PASS and checked['source_closing_exact']
                    and checked['current_compiled249_qualified'] and checked['compiled_test_count']==249
                    and checked['total_contract_tests_passed']==22 and checked['protected_parent_EXE_inputs_exact']==68
                    and checked['current_compile_closing_pin']==listing.CLOSING
                    and checked['actual_inventory_receipt_pin']==q.pin(listing.ACTUAL)
                    and checked['compiled_test_executable_pin']==exe and checked['resource_stop_reason'] is None
                    and checked['resource_watcher_cleanup_confirmed'] and checked['IO']['finished']
                    and checked['IO']['bound_inputs']==checked['IO']['final_fresh_hashes']==len(pins)
                    and pins.get(exe['path'])==exe and sum(n.endswith('.exe') for n in pins)==68,'R57_WHOLE_LIST_CLOSING')
                out['independent_listing_closing_receipt_pin']=q.reader.snapshots[audit.DEST]
            else:
                if actual is not None:
                    b.require(not actual['current_compiled249_qualified'] and actual['stop_reason'] is not None,'R57_STOP_NOT_LIST')
            b.require(q.pin(exe['path'])==exe,'R57_FRESH_R07')
            old=q.json(ARCHIVE);prefixes=[]
            b.require(old['state']=='WHOLE_P181_P182_R57_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','R57_DOC_ARCHIVE')
            for name in b.parser.DOCS:
                _,raw=b.parser.preimage(old,name);current=q.text(name).encode()
                b.require(current.endswith(raw) and len(current)>len(raw),'R57_WHOLE_PRIOR_SUFFIX')
                prefixes.append(current[:-len(raw)])
            expected_flag=b'compiled249=true/full249=false/signed16=false' if accepted else b'compiled249=false/full249=false/signed16=false'
            b.require(prefixes[0]==prefixes[1] and b'P180/P181/P182' in prefixes[0]
                and b'TERMINAL' in prefixes[0] and b'R07_CURRENT_BUILD_ACCEPTED' in prefixes[0]
                and expected_flag in prefixes[0],'R57_SAME_ACCURATE_PREFIX')
            q.finish();out.update(state='PASS_R07_SEPARATE_POST_CLOSING_AND_LIST_TERMINAL_DOCUMENT_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
                current_build_accepted=True,current_compiled249_qualified=accepted,whole_prior_documents_preserved=True,
                original_compile_STOP_preserved=True,current_build_closing_receipt_pin=listing.CLOSING,
                actual_listing_receipt_pin=q.reader.snapshots.get(listing.ACTUAL),
                listing_preparation_receipt_pin=q.reader.snapshots[listing.PREP],compiled_test_executable_pin=exe,
                actual_listing_executed=actual is not None,terminal_listing_accepted=accepted)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','current_build_accepted','current_compiled249_qualified',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_','WHOLE_')) else 2

if __name__=='__main__':raise SystemExit(main())
