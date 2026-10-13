"""P177 terminal stop accounting ONLY; no full protected/source closing promoted."""
import json
import build_xml_capacity_product as b
import weighted_audit_io as w
SELF='tools/p09/account_xml_product_pre_go_stop.py'
LIGHT='implementation/p09/evidence/p09-178-owned-hash-pressure.light-r3-run01.v1.json'
DEST='implementation/p09/evidence/p09-177-xml-capacity-product-build.pre-go-stop-accounting-run01.v1.json'
PASS='PASS_PRE_GO_CPU_STOP_ACCOUNTING_ONLY_NOT_BUILD_WHOLE_SOURCE_CLOSING_OR_GATE'

def main():
    destination=b.s.scoped_path(DEST,fresh=True);resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        current_build_accepted=False,current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        current_protected_EXE67_fresh_closing_after_stop=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        PC_freeze_resolved=False,PC_freeze_cause_qualified=False,actual_Cargo_or_native_or_child_started=False,
        original_source_final_hash_not_retroactively_promoted=True,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=w.WeightedLiveReader(resources);q.pin(SELF)
        row=q.json(b.ACTUAL);preparation=q.json(b.PREPARATION);light=q.json(LIGHT)
        b.require(row['state']=='DEFERRED_NOT_STARTED' and row['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and row['operation_phase']=='source_freeze' and row['cleanup_confirmed'] and row['owned_tree_empty']
            and not row['heavy_work_started'] and not row['worker_created'] and not row['job_assigned']
            and not row['writer_authorized'] and not row['current_build_binding_accepted']
            and not row['source_freeze_exact_after'] and row['executable_pin'] is None and row['source_freeze']==[],
            'PRE_GO_STOP_NOT_BUILD')
        b.require(preparation['state']=='PASS_R07_CURRENT_SOURCE_PREPARATION_ONLY_NOT_BUILD_RUNTIME_OR_GATE'
            and preparation['source_closing_exact'] and preparation['contract_tests_passed']==254
            and preparation['protected_executables_exact']==67 and preparation['resource_stop_reason'] is None
            and preparation['IO']['finished'] and preparation['IO']['bound_inputs']==preparation['IO']['final_fresh_hashes']==1398,
            'PREPARATION_NOT_FINAL_AFTER_STOP')
        b.require(light['state']=='PASS_LOWER_OWNED_HASH_PRESSURE_CONTRACTS_ONLY_NOT_ACTUAL_OR_GATE'
            and light['contract_tests_passed']==262 and not light['actual_lower_rate_build_executed']
            and light['owned_hash_read_rates']=={'binary':1048576,'other':2097152}
            and light['independent_live_reader_rates']=={'binary':2621440,'other':4194304}
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'],'CANDIDATE_ONLY')
        samples=row['samples'];b.require(len(samples)>=4 and all(s['system_cpu_percent']>=98 for s in samples[-4:]),'ORIGINAL_CPU_GUARD')
        b.require(all('job_cpu_seconds' not in s for s in samples),'NO_CREATED_COMPILER_JOB')
        for source in (row,preparation):
            b.require(not source['product_complete'] and not source['current_compiled249_qualified']
                and not source['full249_current_qualified'] and not source['signed16_current_qualified'],'NO_PASS_PROMOTION')
        q.finish();out.update(state=PASS,terminal_accounting_qualified=True,original_stop_reason=row['stop_reason'],
            original_host_CPU_max_percent=max(s['system_cpu_percent'] for s in samples),
            original_available_RAM_min_percent=min(s['available_ram_percent'] for s in samples),
            original_elapsed_seconds=row['elapsed_seconds'],actual_build_receipt_pin=q.reader.snapshots[b.ACTUAL],
            preparation_receipt_pin=q.reader.snapshots[b.PREPARATION],lower_rate_contract_receipt_pin=q.reader.snapshots[LIGHT],
            new_actual_build_retry_started=False,full_independent_build_audit_executed=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','terminal_accounting_qualified','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
