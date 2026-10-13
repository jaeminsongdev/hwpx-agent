"""P178/P179/P180 terminal doc sync, scoped stop accounting is not full closing."""
import json
import build_xml_capacity_product as b
import verify_lower_pressure_product_progress as archive
import account_lower_pressure_cpu_stop as accounting
import build_parent_observed_xml_product as candidate
SELF='tools/p09/verify_observed_cpu_stop_progress.py'
DEST='implementation/p09/evidence/p09-180-parent-observed-xml-product.progress-sync-run01.v1.json'

def main():
    destination=b.s.scoped_path(DEST,fresh=True);resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        current_build_accepted=False,independent_full_source_closing_qualified=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,PC_freeze_resolved=False,
        parent_observed_actual_build_executed=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF)
        stop=q.json(accounting.DEST);light=q.json(candidate.LIGHT)
        b.require(stop['state']==accounting.PASS and stop['terminal_accounting_qualified']
            and not stop['source_closing_exact'] and not stop['current_protected_EXE67_fresh_closing_after_stop']
            and stop['original_source_final_hash_not_retroactively_promoted'] and not stop['PC_freeze_cause_qualified']
            and stop['resource_stop_reason'] is None and stop['resource_watcher_cleanup_confirmed'],'STOP_NOT_FULL_CLOSING')
        b.require(light['state']=='PASS_PARENT_OBSERVED_R07_BUILD_CONTRACTS_ONLY_NOT_ACTUAL_OR_CAUSE'
            and light['contract_tests_passed']==271 and not light['parent_observed_actual_build_executed']
            and not light['actual_Cargo_native_SQL_Hangul_or_child_started']
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'],'CANDIDATE_ONLY')
        pins=b.s.inputs.inventory(light['bound_input_pins'])
        for name in (candidate.SELF,candidate.TEST,candidate.observer.SELF,candidate.observer.TEST,
                     'tools/p09/pre_go_parent_cpu_observer.py','tools/p09/owned_source_read_pressure.py'):
            b.require(q.pin(name)==pins[name],'CURRENT_CANDIDATE_BODY_EXACT')
        old=q.json(archive.ARCHIVE);prefixes=[]
        b.require(old['state']=='WHOLE_P178_R56_DOCUMENT_PREIMAGES_ONLY_NOT_RUNTIME_OR_GATE','DOC_ARCHIVE_SCOPE')
        for name in b.parser.DOCS:
            _,raw=b.parser.preimage(old,name);current=q.text(name).encode()
            b.require(current.endswith(raw) and len(current)>len(raw),'WHOLE_OLD_SUFFIX');prefixes.append(current[:-len(raw)])
        b.require(prefixes[0]==prefixes[1] and b'P178/P179/P180' in prefixes[0] and b'TERMINAL' in prefixes[0]
            and b'R07_NOT_BUILT' in prefixes[0] and b'compiled249=false/full249=false/signed16=false' in prefixes[0],
            'SAME_PREFIX_NOT_BUILD_SUCCESS')
        q.finish();out.update(state='PASS_LOWER_RATE_CPU_STOP_AND_PARENT_OBSERVER_DOCUMENT_SYNC_ONLY_NOT_PRODUCT_OR_GATE',
            whole_prior_documents_preserved=True,terminal_accounting_qualified=True,contract_tests_passed=271,
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
