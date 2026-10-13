"""P178 stop and P179/P180 observation candidates, metadata scope only."""
import json
import build_xml_capacity_product as b
import build_xml_capacity_product_r3 as prior
import build_parent_observed_xml_product as next_build
SELF='tools/p09/account_lower_pressure_cpu_stop.py'
DEST='implementation/p09/evidence/p09-178-owned-hash-pressure.pre-go-stop-accounting-run01.v1.json'
PASS='PASS_LOWER_RATE_PRE_GO_CPU_STOP_AND_OBSERVER_ACCOUNTING_ONLY_NOT_BUILD_OR_CAUSE'
BASELINE='implementation/p09/evidence/p09-179-parent-cpu-observer.observe-r2-run01.v1.json'

def main():
    destination=b.s.scoped_path(DEST,fresh=True);resources=b.s.SQLRuntimeResources();q=None
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        current_protected_EXE67_fresh_closing_after_stop=False,current_build_accepted=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        PC_freeze_cause_qualified=False,original_source_final_hash_not_retroactively_promoted=True,
        new_actual_build_retry_started=False,full_independent_build_audit_executed=False)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF)
        actual=q.json(prior.prior.ACTUAL);prep=q.json(prior.prior.PREPARATION);baseline=q.json(BASELINE);light=q.json(next_build.LIGHT)
        b.require(actual['state']=='DEFERRED_NOT_STARTED' and actual['stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
            and actual['operation_phase']=='source_freeze' and actual['cleanup_confirmed'] and actual['owned_tree_empty']
            and actual['source_freeze']==[] and not actual['heavy_work_started'] and not actual['worker_created']
            and not actual['job_assigned'] and not actual['writer_authorized'] and actual['executable_pin'] is None
            and not actual['current_build_binding_accepted'] and not actual['source_freeze_exact_after'],'LOW_RATE_PRE_GO_STOP')
        samples=actual['samples'];b.require(len(samples)>=4 and all(v['system_cpu_percent']>=98 for v in samples[-4:])
            and all('job_cpu_seconds' not in v for v in samples),'ORIGINAL_CPU_STOP_WITHOUT_JOB')
        reads=actual['source_reader_passes'];b.require(len(reads)==1 and reads[0]['read_rates_by_kind']=={'binary':1048576,'other':2097152}
            and reads[0]['bytes_read']==reads[0]['pacer_bytes_read']==sum(reads[0]['bytes_read_by_kind'].values()),'ACTUAL_LOWER_RATE_PARTIAL_ONLY')
        b.require(prep['state']=='PASS_R07_CURRENT_SOURCE_PREPARATION_ONLY_NOT_BUILD_RUNTIME_OR_GATE'
            and prep['source_closing_exact'] and prep['contract_tests_passed']==262 and prep['protected_executables_exact']==67
            and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==1406
            and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed'],'PREP_NOT_AFTER_STOP')
        b.require(baseline['state']=='PASS_OWN_PARENT_CPU_BASELINE_ONLY_NOT_BUILD_OR_CAUSE' and baseline['contract_tests_passed']==7
            and baseline['parent_ProcessTimes_query_executed'] and not baseline['foreign_Process_query_executed']
            and not baseline['artifact_EXE_read_workload_started'] and not baseline['new_sampler_thread_started']
            and baseline['resource_stop_reason'] is None,'BASELINE_NOT_CAUSE')
        for name in ('light','observe'):
            old=q.json(f'implementation/p09/evidence/p09-179-parent-cpu-observer.{name}-run01.v1.json')
            b.require(old['state']=='FAILED_NOT_ACCEPTED' and old['resource_stop_reason']=='CPU_SAMPLE_INTERVAL_MISSING',
                'FIRST_ZERO_INTERVAL_FAILURES_PRESERVED')
        b.require(light['state']=='PASS_PARENT_OBSERVED_R07_BUILD_CONTRACTS_ONLY_NOT_ACTUAL_OR_CAUSE'
            and light['contract_tests_passed']==271 and not light['parent_observed_actual_build_executed']
            and not light['actual_Cargo_native_SQL_Hangul_or_child_started']
            and light['resource_stop_reason'] is None and light['resource_watcher_cleanup_confirmed'],'NEXT_CONTRACT_ONLY')
        q.finish();out.update(state=PASS,terminal_accounting_qualified=True,lower_owned_hash_read_executed=True,
            actual_Cargo_or_product_EXE_started=False,actual_receipt_pin=q.reader.snapshots[prior.prior.ACTUAL],
            preparation_receipt_pin=q.reader.snapshots[prior.prior.PREPARATION],baseline_receipt_pin=q.reader.snapshots[BASELINE],
            next_candidate_receipt_pin=q.reader.snapshots[next_build.LIGHT],
            original_host_CPU_max_percent=max(v['system_cpu_percent'] for v in samples),
            original_available_RAM_min_percent=min(v['available_ram_percent'] for v in samples),
            original_elapsed_seconds=actual['elapsed_seconds'],baseline_not_the_saturation_time=True)
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
