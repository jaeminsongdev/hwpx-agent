"""P182 independent whole current-r07 list closing; not test bodies or Gate."""
import io
import json
import math
import sys
import time
import unittest
from unittest.mock import patch
import run_r07_postclosed_inventory as v
b=v.b; c=v.c; s=v.s
SELF='tools/p09/audit_r07_postclosed_inventory.py'
TEST='tools/p09/tests/test_r07_inventory_closing.py'
DEST='implementation/p09/evidence/p09-182-r07-postclosed-inventory.terminal-audit-run01.v1.json'
PASS='PASS_POSTCLOSED_R07_COMPILED249_WHOLE_CLOSING_ONLY_NOT_TEST_RUNTIME_OR_GATE'

def actual_scope(row):
    v.require(row['state']==v.PASS and row['compiled_inventory_exact'] and row['current_compiled249_qualified']
        and row['fresh_EXE_list_only'] and not row['runtime_tests_executed']
        and not row['full249_current_qualified'] and not row['signed16_current_qualified']
        and row['current_Rust_input_count']==785 and row['expected_test_count']==249
        and row['current_compile_closing_pin']==v.CLOSING and row['test_package_profile_config']==list(b.b.CONFIG)
        and not row['product_complete'] and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
        and not row['PC_freeze_resolved'] and row['original_STOP_receipt_unchanged'], 'LIST_ONLY_CURRENT')
    v.require(row['cleanup_confirmed'] and row['owned_tree_empty'] and row['maximum_seconds']==180
        and row['policy']==c.POLICY and row['heavy_work_started'] and row['worker_created']
        and row['job_assigned'] and row['writer_authorized'] and row['exit_code']==0
        and row['stop_reason'] is None and row['job_final']['active_processes']==0
        and row['job_final']['owned_processes']==[] and row['owned_limits_readback']['verified']
        and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25, 'ORIGINAL_JOB_GO_GUARDS_TERMINAL')
    v.require(row['native_Process_query_executed'] and row['parent_ProcessTimes_observation_connected']
        and not row['foreign_Process_query_executed'] and not row['additional_observer_thread_started']
        and row['additional_Process_query_scope']=='current_parent_pseudo_handle_only'
        and not row['source_read_checks_skipped'],'EXPLICIT_OWN_PARENT_ONLY')
    cap=row['capture_diagnostics']
    v.require(cap['error_code'] is None and cap['per_stream_limit_bytes']==32768
        and not cap['raw_log_content_included'] and cap['received_bytes']['stderr']==0
        and 0<cap['received_bytes']['stdout']<=32768
        and cap['received_bytes']==cap['buffered_bytes'],'COMPLETE_CAPTURE')
    frozen=s.inputs.inventory(row['source_freeze'])
    v.require(sum(n.endswith('.exe') for n in frozen)==68 and len(row['source_reader_passes'])==2,'ALL68_PRE_POST')
    for reader in row['source_reader_passes']:
        v.require(reader['read_passes']==len(frozen)
            and reader['bytes_read']==sum(p['bytes'] for p in frozen.values())
            and reader['read_rates_by_kind']=={'binary':1048576,'other':2097152}
            and sum(reader['bytes_read_by_kind'].values())==reader['bytes_read'],'WHOLE_READS_NO_SKIP')
    samples=row['samples'];v.require(bool(samples),'SAMPLES_PRESENT')
    for sample in samples:
        raw=sample['raw_system_cpu_delta_100ns'];total=raw['total'];own=sample['parent_cpu_delta_100ns']
        v.require(all(type(x) is int and x>=0 for x in raw.values()) and total>0
            and total==raw['kernel_including_idle']+raw['user'] and raw['idle']<=total and type(own) is int and own>=0
            and sample['system_cpu_percent']==round(100*(total-raw['idle'])/total,2)
            and sample['parent_cpu_machine_percent']==round(100*own/total,6)
            and sample['parent_affinity_mask'].bit_count()==1 and sample['parent_priority_readback']=='BelowNormal'
            and sample['parent_process_only'] and not sample['foreign_Process_query_executed'],'RAW_PARENT_REPLAY')
    v.require(row['parent_CPU_max_machine_percent']==max(r['parent_cpu_machine_percent'] for r in samples),
        'PARENT_MAX_EXACT')
    return frozen

def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_r07_inventory_closing')
    with patch('subprocess.Popen',side_effect=AssertionError('P182_AUDIT_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P182_AUDIT_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P182_AUDIT_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    v.require(result.wasSuccessful() and result.testsRun==4 and not result.skipped,'AUDIT_CONTRACT4')

def main():
    v.require(c.Path.cwd().resolve()==c.ROOT,'AUDIT_CWD');destination=s.scoped_path(DEST,fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        runtime_test_bodies_executed=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        PC_freeze_resolved=False,actual_new_Cargo_SQL_Hangul_or_child_executed=False,
        remaining_non_permission_work_units=76,original_STOP_receipt_unchanged=True)
    try:
        resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF);q.pin(TEST)
        row=q.json(v.ACTUAL);frozen=actual_scope(row)
        v.require(q.pin(v.CLOSING['path'])==v.CLOSING,'IMMUTABLE_BUILD_CLOSING')
        parent=q.json(v.CLOSING['path']);expected,exe=v.closing_scope(parent)
        prep=q.json(v.PREP);prepared=s.inputs.inventory(prep['bound_input_pins'])
        v.require(prep['state']=='PASS_R07_LISTING_PREPARATION_ONLY_NOT_ACTUAL_OR_GATE'
            and prep['source_closing_exact'] and prep['contract_tests_passed']==18
            and prep['resource_stop_reason'] is None and prep['resource_watcher_cleanup_confirmed']
            and prep['IO']['finished'] and prep['IO']['bound_inputs']==prep['IO']['final_fresh_hashes']==len(prepared)
            and prep['current_compile_closing_pin']==v.CLOSING and prep['compiled_test_executable_pin']==exe
            and prep['protected_executables_exact']==68 and all(frozen.get(n)==pin for n,pin in {**expected,**prepared}.items()),
            'WHOLE_BUILD_AND_PREPARATION_IN_FREEZE')
        for n,pin in {**expected,**prepared,**frozen}.items():v.require(q.pin(n)==pin,'EVERY_CURRENT_BYTE')
        v.require(row['compiled_test_executable_pin']==exe and q.pin(exe['path'])==exe,'FRESH_R07_ONLY')
        v.require(q.pin(v.closing.ACTUAL['path'])==v.closing.ACTUAL,'ORIGINAL_CPU_STOP_PRESERVED')
        v.closing.metadata_scope(q.json(v.closing.ACTUAL['path']))
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        v.require(len(rust)==785 and s.inputs.rust_inputs(c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=b.p.source_scope(q,frozen)
        v.require(names==row['source_test_names']==parent['source_test_names']==prep['source_test_names']
            and modules==row['source_module_instances']==parent['source_module_instances']==prep['source_module_instances'],
            'EXACT_ORIGINAL249_59')
        v.contracts();contracts()
        for n in v.helpers():q.pin(n)
        q.finish();out.update(state=PASS,source_closing_exact=True,current_compiled249_qualified=True,
            compiled_test_count=249,source_test_names=names,source_module_instances=modules,
            current_Rust_input_count=785,current_compile_closing_pin=v.CLOSING,compiled_test_executable_pin=exe,
            protected_parent_EXE_inputs_exact=68,listing_contract_tests_passed=18,audit_contract_tests_passed=4,
            total_contract_tests_passed=22,actual_inventory_receipt_pin=q.reader.snapshots[v.ACTUAL],
            preparation_receipt_pin=q.reader.snapshots[v.PREP],owned_job_final=row['job_final'],capture_diagnostics=row['capture_diagnostics'],
            host_CPU_max_percent=max(r['system_cpu_percent'] for r in row['samples']),
            own_parent_CPU_max_machine_percent=row['parent_CPU_max_machine_percent'],
            host_available_RAM_min_percent=min(r['available_ram_percent'] for r in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.parser.d.original.closed_error(error)
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):
            out['state']='FAILED_NOT_ACCEPTED';out['current_compiled249_qualified']=False
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=b.weighted.resource_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','compiled_test_count','total_contract_tests_passed',
            'error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
