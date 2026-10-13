"""P184 r58 terminal documents; retain full r57, product/Gate remain OPEN."""
import argparse
import base64
import hashlib
import json
import run_observed_r07_inventory as run
import audit_observed_r07_inventory as audit
import close_observed_r07_listing_output as post
b=run.b; s=run.s
SELF='tools/p09/sync_observed_r07_inventory_progress.py'
ARCHIVE='implementation/p09/source-archive/p09-184-pre-progress-r58/document-preimages.v1.json'
DEST='implementation/p09/evidence/p09-184-observed-r07-inventory.progress-sync-run01.v1.json'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('archive','verify'),required=True);mode=ap.parse_args().mode
    destination=s.scoped_path(ARCHIVE if mode=='archive' else DEST,fresh=True)
    resources=run.observation.OriginalResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        remaining_non_permission_work_units=76,whole_current_runtime_inputs_reaudited_by_doc_sync=False)
    try:
        resources.admit();q=run.observation.weighted.WeightedLiveReader(resources);q.pin(SELF)
        if mode=='archive':
            files=[]
            for name in b.parser.DOCS:
                raw=q.text(name).encode();pin=q.reader.snapshots[name]
                run.prior.require(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'R58_WHOLE_DOC_BYTES')
                files.append(dict(**pin,base64=base64.b64encode(raw).decode()))
            q.finish();out.update(state='WHOLE_P184_R58_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE',files=files)
        else:
            run.prior.require(q.pin(run.prior.CLOSING['path'])==run.prior.CLOSING,'R58_BUILD_CLOSING_PIN')
            parent=q.json(run.prior.CLOSING['path']);_,exe=run.prior.closing_scope(parent)
            prep=q.json(run.PREP);actual=q.json(run.ACTUAL);accepted=actual['state']==run.PASS
            qualified=accepted
            run.prior.require(prep['state']=='PASS_R07_LISTING_PREPARATION_ONLY_NOT_ACTUAL_OR_GATE'
                and prep['source_closing_exact'] and prep['contract_tests_passed']==33
                and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
                and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1434,
                'R58_WHOLE_PREPARATION')
            audit.extra_preparation_scope(q,prep)
            run.prior.require(actual['state'] in (run.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
                and actual['cleanup_confirmed'] and actual['owned_tree_empty']
                and actual['current_compiled249_qualified']==accepted
                and not actual['full249_current_qualified'] and not actual['signed16_current_qualified']
                and not actual['runtime_tests_executed'],'R58_LIST_TERMINAL_ONLY')
            if accepted:
                audit.actual_scope(actual);checked=q.json(audit.DEST)
                pins=s.inputs.inventory(checked['bound_input_pins'])
                run.prior.require(checked['state']==audit.PASS and checked['source_closing_exact']
                    and checked['current_compiled249_qualified'] and checked['compiled_test_count']==249
                    and checked['total_contract_tests_passed']==39 and checked['protected_parent_EXE_inputs_exact']==68
                    and checked['actual_inventory_receipt_pin']==q.pin(run.ACTUAL)
                    and checked['current_compile_closing_pin']==run.prior.CLOSING
                    and checked['compiled_test_executable_pin']==exe and checked['resource_stop_reason'] is None
                    and checked['resource_watcher_cleanup_confirmed'] and checked['IO']['finished']
                    and checked['IO']['bound_inputs']==checked['IO']['final_fresh_hashes']==len(pins)
                    and sum(n.endswith('.exe') for n in pins)==68,'R58_WHOLE_INDEPENDENT_LIST_CLOSING')
                out['independent_listing_closing_receipt_pin']=q.reader.snapshots[audit.DEST]
            else:
                run.prior.require(actual['stop_reason'] is not None,'R58_STOP_NOT_PASS')
                if (b.c.ROOT/post.DEST).exists():
                    checked=q.json(post.DEST)
                    if checked['state']==post.PASS:
                        post.metadata_scope(actual)
                        pins=s.inputs.inventory(checked['bound_input_pins'])
                        run.prior.require(checked['source_closing_exact'] and checked['current_compiled249_qualified']
                            and checked['separate_current_post_closing_exact'] and checked['current_build_accepted']
                            and checked['compiled_test_count']==249 and checked['total_contract_tests_passed']==82
                            and checked['listing_contract_tests_passed']==33 and checked['reader_contract_tests_passed']==43
                            and checked['post_closing_contract_tests_passed']==6
                            and checked['protected_parent_EXE_inputs_exact']==68
                            and checked['actual_inventory_receipt_pin']==post.ACTUAL==q.pin(run.ACTUAL)
                            and checked['preparation_receipt_pin']==post.PREP==q.pin(run.PREP)
                            and checked['current_compile_closing_pin']==run.prior.CLOSING
                            and checked['compiled_test_executable_pin']==exe
                            and checked['original_run_state']=='STOPPED_NOT_ACCEPTED'
                            and not checked['original_listing_run_accepted']
                            and checked['original_source_final_hash_not_retroactively_promoted']
                            and checked['original_incomplete_final_freeze_preserved']
                            and checked['validated_original_list_output_by_pinned_control_flow']
                            and checked['source_listing_replay_not_new_stdout']
                            and not checked['actual_new_list_Cargo_SQL_Hangul_child_or_test_body_executed']
                            and not checked['full249_current_qualified'] and not checked['signed16_current_qualified']
                            and not checked['product_complete'] and not checked['PC_freeze_resolved']
                            and checked['P09_gate']==checked['A12_gate']==checked['A13_gate']=='OPEN'
                            and checked['resource_stop_reason'] is None and checked['resource_watcher_cleanup_confirmed']
                            and checked['IO']['finished']
                            and checked['IO']['bound_inputs']==checked['IO']['final_fresh_hashes']==len(pins)
                            and sum(n.endswith('.exe') for n in pins)==68,
                            'R58_SEPARATE_CURRENT_LIST_POST_CLOSING_NOT_ORIGINAL_PASS')
                        qualified=True;out['separate_post_closing_receipt_pin']=q.reader.snapshots[post.DEST]
            run.prior.require(q.pin(exe['path'])==exe,'R58_CURRENT_R07')
            prepared=s.inputs.inventory(prep['bound_input_pins'])
            for n in (run.SELF,run.TEST,run.observation.SELF,run.observation.TEST):
                run.prior.require(q.pin(n)==prepared[n],'R58_CURRENT_BOUND_HELPERS')
            old=q.json(ARCHIVE);prefixes=[]
            run.prior.require(old['state']=='WHOLE_P184_R58_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','R58_ARCHIVE')
            for name in b.parser.DOCS:
                _,raw=b.parser.preimage(old,name);current=q.text(name).encode()
                run.prior.require(current.endswith(raw) and len(current)>len(raw),'R58_WHOLE_PRIOR_SUFFIX')
                prefixes.append(current[:-len(raw)])
            flag=b'compiled249=true/full249=false/signed16=false' if qualified else b'compiled249=false/full249=false/signed16=false'
            run.prior.require(prefixes[0]==prefixes[1] and b'P184' in prefixes[0] and b'TERMINAL' in prefixes[0]
                and b'R07_CURRENT_BUILD_ACCEPTED' in prefixes[0] and flag in prefixes[0],'R58_SAME_ACCURATE_PREFIX')
            q.finish();out.update(state='PASS_OBSERVED_R07_LIST_TERMINAL_DOCUMENT_SYNC_ONLY_NOT_RUNTIME_OR_GATE',
                current_build_accepted=True,current_compiled249_qualified=qualified,whole_prior_documents_preserved=True,
                current_build_closing_receipt_pin=run.prior.CLOSING,actual_listing_receipt_pin=q.reader.snapshots[run.ACTUAL],
                listing_preparation_receipt_pin=q.reader.snapshots[run.PREP],terminal_listing_accepted=accepted,
                compound_current_listing_qualified=qualified,
                original_P182_CPU_stop_receipt_preserved=True,compiled_test_executable_pin=exe)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:out['error_code']=run.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','current_build_accepted','current_compiled249_qualified',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith(('PASS_','WHOLE_')) else 2

if __name__=='__main__':raise SystemExit(main())
