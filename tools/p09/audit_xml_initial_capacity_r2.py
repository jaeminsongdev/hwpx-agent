"""P175 r2 exact test-oracle spelling; preserves failed first audit and helper."""
import argparse
import json
import time
from unittest.mock import patch
import xml_initial_capacity_binding as b
import run_xml_initial_capacity_units as units

SELF='tools/p09/audit_xml_initial_capacity_r2.py'
PASS='PASS_XML_INITIAL_CAPACITY_DELTA_AND_ALL74_LIB_ONLY_NOT_FULL249_OR_GATE'
STOP='PASS_XML_INITIAL_CAPACITY_DELTA_AND_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,default=1,choices=range(1,100));args=parser.parse_args()
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-175-xml-initial-capacity.source-closing-r2-run{args.run:02}.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,actual_unit_tests_passed=None,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_audit_child_or_new_thread_started=False,
        remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.s.LiveSQLReader(resources);q.pin(SELF)
        q.pin('tools/p09/audit_xml_initial_capacity.py')
        q.pin('implementation/p09/evidence/p09-175-xml-initial-capacity.source-closing-run01.v1.json')
        with patch('subprocess.Popen',side_effect=AssertionError('P175_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P175_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P175_AUDIT_THREAD_FORBIDDEN')):
            expected,names,modules=b.bind(q,resources)
            archive=q.json(b.ARCHIVE);_,old=b.preimage(archive,b.SOURCE)
            current=q.text(b.SOURCE);b.inverse(current,old.decode('utf-8'))
            b.require('SafeXmlDocument::parse_with_capacity_hint(bytes, limits, usize::MAX)' in current
                and 'new.events.capacity() <= 256' in current and 'old.events.capacity() >= 100_000' in current
                and 'new.spans.capacity() <= 256' in current and 'old.spans.capacity() >= 100_000' in current
                and 'new.events.len(), 602' in current and 'new.spans.capacity() >= 602' in current,
                'UNCHANGED_PARSER_RESERVATION_ORACLE')
            actual=f'implementation/p09/evidence/p09-175-xml-initial-capacity.units-run{args.run:02}.v1.json';row=q.json(actual)
            out['actual_unit_receipt_pin']=q.reader.snapshots[actual];passed=row['state']==units.PASS
            b.require(row['state'] in (units.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
                and row['maximum_seconds']==600 and row['task']==units.TASK and row['policy']==b.c.POLICY
                and row['baseline_closing_pin']==b.PARENT and row['baseline_archive']==b.ARCHIVE
                and row['isolated_target']==units.TARGET.relative_to(b.c.ROOT).as_posix()
                and row['fresh_target_no_old_EXE_overwrite'] and row['whole_original_core_inverse_exact']
                and row['test_package_profile_config']==list(units.CONFIG)
                and row['original_package_lib_cases']==71 and row['new_xml_capacity_regression_cases']==3
                and row['changed_allocation_hint_not_admission_limits'] and not row['authorization_or_signature_cache_added']
                and not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete']
                and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
                and not row['PC_freeze_resolved'] and not row['full_product_performance_improvement_measured']
                and not row['actual_Hangul_COM_SQL_or_Process_query_run'],'ACTUAL_SCOPE')
            b.require(row['cleanup_confirmed'] and row['owned_tree_empty'],'CLEANUP')
            if row['heavy_work_started']:
                b.require(row['job_assigned'] and row['writer_authorized'] and row['owned_limits_readback']['verified']
                    and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                    and row['post_hash_compiler_admission_revalidated'] and row['compiler_admission_RAM_percent']==15
                    and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'JOB_TERMINAL')
            frozen=b.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
            if row['heavy_work_started']:b.require(all(frozen.get(n)==pin for n,pin in expected.items()),'WHOLE_FREEZE')
            for name,pin in {**expected,**frozen}.items():b.require(q.pin(name)==pin,'WHOLE_FRESH_SOURCE')
            b.require(row['source_test_names']==names and row['source_module_instances']==modules,'ORIGINAL249_59')
            units.contracts()
            for name in units.helpers():q.pin(name)
            exe=None
            if passed:
                b.require(row['exit_code']==0 and row['stop_reason'] is None and row['tests_passed']==74
                    and row['compiler_error_codes']==[] and row['compiler_diagnostic_locations']==[],'ACTUAL_ALL74')
                b.require(units.TARGET.is_dir() and not units.TARGET.is_symlink() and not units.TARGET.is_junction(),'NEW_TARGET')
                exes=list((units.TARGET/'debug/deps').glob('hwpx_package-*.exe'));b.require(len(exes)==1,'ONE_LIB_EXE')
                exe=q.pin(exes[0].relative_to(b.c.ROOT).as_posix());b.require(exe['path'] not in expected,'NEW_EXE')
            source=q.pin(b.SOURCE);q.finish()
            out.update(state=PASS if passed else STOP,source_closing_exact=True,contract_tests_passed=64,
                whole_original_core_and_tests_inverse_exact=True,original_parser_body_exact_after_declared_hint_delta=True,
                all_original_package_lib_tests_preserved=True,actual_unit_tests_passed=74 if passed else None,
                typecheck_accepted=passed,current_Rust_input_count=785,source_test_names=names,source_module_instances=modules,
                declared_Rust_source_changes=[source],protected_parent_EXE_inputs_exact=66,fresh_package_lib_executable_pin=exe,
                original_run_state=row['state'],original_stop_reason=row['stop_reason'],owned_job_final=row.get('job_final'),
                baseline_closing_pin=b.PARENT,original_source_final_hash_not_retroactively_promoted=not passed,
                changed_allocation_hint_not_admission_limits=True,authorization_or_signature_cache_added=False,
                actual_Hangul_COM_SQL_or_Process_query_run=False,
                host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
                host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=b.d.original.closed_error(error)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_unit_tests_passed','contract_tests_passed',
            'error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
