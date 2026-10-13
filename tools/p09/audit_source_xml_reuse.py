"""Independent P161 single-source delta and actual LIB units terminal audit."""
import argparse
import json
import time
from unittest.mock import patch
import source_xml_reuse_binding as b
import run_source_xml_reuse_units as units

SELF='tools/p09/audit_source_xml_reuse.py'
ACTUAL='implementation/p09/evidence/p09-161-source-xml-reuse.units-run01.v1.json'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,default=1,choices=range(1,100))
    parser.add_argument('--audit-run',type=int,default=2,choices=range(1,100));a=parser.parse_args()
    b.require(b.p.c.Path.cwd().resolve()==b.p.c.ROOT,'AUDIT_CWD')
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-161-source-xml-reuse.source-closing-run{a.audit_run:02}.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,actual_unit_tests_passed=None,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_audit_child_or_new_thread_started=False,
        remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P161_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P161_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P161_AUDIT_THREAD_FORBIDDEN')):
            expected,names,modules=b.bind(q,resources)
            actual=f'implementation/p09/evidence/p09-161-source-xml-reuse.units-run{a.run:02}.v1.json';row=q.json(actual)
            out['actual_unit_receipt_pin']=q.reader.snapshots[actual]
            passed=row['state']=='PASS_SOURCE_XML_REUSE_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE'
            b.require(row['state'] in ('PASS_SOURCE_XML_REUSE_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE',
                'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED') and row['maximum_seconds']==600
                and row['task']==units.TASK and row['policy']==b.p.c.POLICY
                and row['baseline_closing_pin']==b.PARENT and row['baseline_archive']==b.ARCHIVE
                and row['isolated_target']==units.TARGET.relative_to(b.p.c.ROOT).as_posix()
                and row['test_package_profile_config']==list(b.s.profile.CONFIG)
                and row['original_package_lib_cases']==64 and row['new_source_xml_regression_cases']==4
                and not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete']
                and row['P09_gate']=='OPEN' and not row['PC_freeze_resolved'],'AUDIT_SCOPE')
            b.require(row['cleanup_confirmed'] and row['owned_tree_empty'],'AUDIT_CLEANUP')
            if row['heavy_work_started']:
                b.require(row['job_assigned'] and row['writer_authorized'] and row['owned_limits_readback']['verified']
                    and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                    and row['post_hash_compiler_admission_revalidated'] and row['compiler_admission_RAM_percent']==15
                    and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'AUDIT_JOB_TERMINAL')
            frozen=b.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
            if row['heavy_work_started']:b.require(all(frozen.get(n)==pin for n,pin in expected.items()),'AUDIT_WHOLE_SOURCE_CLOSURE')
            for n,pin in {**expected,**frozen}.items():b.require(q.pin(n)==pin,'AUDIT_FRESH_CLOSURE')
            b.require(row['source_test_names']==names and row['source_module_instances']==modules,'AUDIT_ORIGINAL249_59')
            q.pin(units.SELF);exe=None
            if passed:
                b.require(row['exit_code']==0 and row['stop_reason'] is None and row['tests_passed']==68
                    and row['compiler_error_codes']==[] and row['compiler_diagnostic_locations']==[],'AUDIT_REAL68_NOT_FULL249')
                exes=list((units.TARGET/'debug/deps').glob('hwpx_package-*.exe'))
                b.require(len(exes)==1,'AUDIT_ONE_FRESH_PACKAGE_LIB_EXE');exe=q.pin(exes[0].relative_to(b.p.c.ROOT).as_posix())
                b.require(exe['path'] not in expected,'AUDIT_NEW_LIB_EXE_NOT_OLD_PRODUCT')
            declared_pin=q.pin(b.SOURCE);q.finish()
            out.update(state='PASS_SOURCE_XML_REUSE_DELTA_AND_ALL68_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE' if passed else
                'PASS_SOURCE_XML_REUSE_DELTA_AND_UNIT_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE',
                source_closing_exact=True,whole_original_core_inverse_exact=True,all_original_package_lib_tests_preserved=True,
                actual_unit_tests_passed=68 if passed else None,typecheck_accepted=passed,current_Rust_input_count=785,
                source_test_names=names,source_module_instances=modules,declared_Rust_source_changes=[declared_pin],
                protected_parent_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),fresh_package_lib_executable_pin=exe,
                old_product_EXE_not_current_qualified=True,original_run_state=row['state'],original_stop_reason=row['stop_reason'],
                owned_job_final=row.get('job_final'),baseline_closing_pin=b.PARENT,
                host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
                host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:out['error_code']=b.prior.full.s.original.closed_error(e)
    finally:
        b.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_unit_tests_passed','error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
