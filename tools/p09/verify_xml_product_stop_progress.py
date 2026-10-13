"""P177/P178 terminal stop/candidate document proof, no full closing assertion."""
import json
import build_xml_capacity_product as b
import verify_xml_product_progress as docs
import account_xml_product_pre_go_stop as accounting
import build_xml_capacity_product_r3 as candidate
SELF='tools/p09/verify_xml_product_stop_progress.py'
DEST='implementation/p09/evidence/p09-178-owned-hash-pressure.progress-sync-run01.v1.json'

def main():
    destination=b.s.scoped_path(DEST,fresh=True);resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        current_build_accepted=False,independent_full_source_closing_qualified=False,PC_freeze_resolved=False,
        actual_lower_rate_build_executed=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF)
        stop=q.json(accounting.DEST);actual=q.json(b.ACTUAL);light=q.json(candidate.LIGHT)
        b.require(stop['state']==accounting.PASS and stop['terminal_accounting_qualified'] and not stop['source_closing_exact']
            and not stop['current_protected_EXE67_fresh_closing_after_stop']
            and stop['original_source_final_hash_not_retroactively_promoted']
            and stop['resource_stop_reason'] is None and stop['resource_watcher_cleanup_confirmed'],'SCOPED_STOP_NOT_FULL_CLOSING')
        b.require(actual['state']=='DEFERRED_NOT_STARTED' and actual['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and actual['cleanup_confirmed'] and actual['owned_tree_empty'] and not actual['worker_created']
            and not actual['heavy_work_started'] and actual['executable_pin'] is None
            and stop['actual_build_receipt_pin']==q.pin(b.ACTUAL),'ACTUAL_TERMINAL')
        b.require(light['state']=='PASS_LOWER_OWNED_HASH_PRESSURE_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE'
            and light['contract_tests_passed']==262 and not light['actual_lower_rate_build_executed']
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'],'CANDIDATE262_ONLY')
        pins=b.s.inputs.inventory(light['bound_input_pins'])
        for name in (candidate.SELF,candidate.TEST,candidate.prior.SELF,candidate.prior.pressure.SELF,
                     b.SELF,b.TEST):b.require(q.pin(name)==pins[name],'EXACT_CURRENT_CANDIDATE_HELPERS')
        old=q.json(docs.ARCHIVE);prefixes=[]
        b.require(old['state']=='WHOLE_P177_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','WHOLE_ARCHIVE')
        for name in b.parser.DOCS:
            _,raw=b.parser.preimage(old,name);current=q.text(name).encode()
            b.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_PRIOR_SUFFIX');prefixes.append(current[:-len(raw)])
        b.require(prefixes[0]==prefixes[1] and b'P177/P178' in prefixes[0] and b'TERMINAL' in prefixes[0]
            and b'R07_NOT_BUILT' in prefixes[0] and b'compiled249=false/full249=false/signed16=false' in prefixes[0],
            'SAME_STOP_PREFIX_NOT_SUCCESS')
        q.finish();out.update(state='PASS_PRE_GO_STOP_AND_LOWER_RATE_CANDIDATE_DOCUMENT_SYNC_ONLY_NOT_PRODUCT_OR_GATE',
            whole_prior_documents_preserved=True,terminal_accounting_qualified=True,contract_tests_passed=262,
            stop_receipt_pin=q.reader.snapshots[accounting.DEST],candidate_receipt_pin=q.reader.snapshots[candidate.LIGHT])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','terminal_accounting_qualified','error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
