"""Independent P168 original-core/source and actual LIB71 terminal accounting."""
import argparse
import json
import time
from unittest.mock import patch
import writer_xml_reuse_binding as b
import run_writer_xml_reuse_units as units

SELF='tools/p09/audit_writer_xml_reuse.py'

def verify_original_oracle(current,old):
    current=current.replace('\r\n','\n');old=old.replace('\r\n','\n')
    start=old.index('fn validate_archive<R: Read + Seek>(')
    original=old[start:old.index('\n}\n',start)+2]
    start=current.index('    fn validate_archive_original<R: Read + Seek>(')
    oracle=current[start:current.index('\n    fn same_result(',start)].rstrip()
    oracle='\n'.join(line[4:] if line.startswith('    ') else line for line in oracle.split('\n'))
    oracle=oracle.replace('fn validate_archive_original<','fn validate_archive<',1)
    formatted='''    let index = IdIndex::build_with_graph_limits(
        &mut reader,
        &graph,
        graph_limits,
        profile,
        id_limits,
    )?;'''
    b.require(original.count(b.OLD_INDEX)==1,'ORACLE_ONE_OLD_INDEX')
    b.require(oracle==original.replace(b.OLD_INDEX,formatted,1),'ORACLE_WHOLE_ORIGINAL_BODY_EXACT')
    return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,default=1,choices=range(1,100))
    parser.add_argument('--audit-run',type=int,default=1,choices=range(1,100));args=parser.parse_args()
    b.require(b.c.Path.cwd().resolve()==b.c.ROOT,'AUDIT_CWD')
    destination=b.s.scoped_path(f'implementation/p09/evidence/p09-168-writer-xml-reuse.source-closing-run{args.audit_run:02}.v1.json',fresh=True)
    resources=b.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        actual_unit_tests_passed=None,current_compiled249_qualified=False,full249_current_qualified=False,
        signed16_current_qualified=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_or_new_thread_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=b.s.LiveSQLReader(resources);q.pin(SELF)
        with patch('subprocess.Popen',side_effect=AssertionError('P168_AUDIT_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P168_AUDIT_CHILD_FORBIDDEN')), \
                patch('threading.Thread.start',side_effect=AssertionError('P168_AUDIT_THREAD_FORBIDDEN')):
            expected,names,modules=b.bind(q,resources)
            archive=q.json(b.ARCHIVE);_,old=b.preimage(archive,b.SOURCE)
            verify_original_oracle(q.text(b.SOURCE),old.decode('utf-8'))
            actual=f'implementation/p09/evidence/p09-168-writer-xml-reuse.units-run{args.run:02}.v1.json';row=q.json(actual)
            out['actual_unit_receipt_pin']=q.reader.snapshots[actual]
            passed=row['state']==units.PASS
            b.require(row['state'] in (units.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
                and row['maximum_seconds']==600 and row['task']==units.TASK and row['policy']==b.c.POLICY
                and row['baseline_closing_pin']==b.PARENT and row['baseline_archive']==b.ARCHIVE
                and row['isolated_target']==units.TARGET.relative_to(b.c.ROOT).as_posix()
                and row['fresh_target_no_old_EXE_overwrite'] and row['whole_original_core_inverse_exact']
                and row['test_package_profile_config']==list(b.p.b.CONFIG)
                and row['original_package_lib_cases']==68 and row['new_writer_xml_regression_cases']==3
                and not row['current_compiled249_qualified'] and not row['full249_current_qualified']
                and not row['signed16_current_qualified'] and not row['product_complete']
                and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN'
                and not row['PC_freeze_resolved'] and not row['full_product_performance_improvement_measured']
                and not row['actual_Hangul_COM_SQL_or_Process_query_run'],'AUDIT_SCOPE')
            b.require(row['cleanup_confirmed'] and row['owned_tree_empty'],'AUDIT_CLEANUP')
            if row['heavy_work_started']:
                b.require(row['job_assigned'] and row['writer_authorized'] and row['owned_limits_readback']['verified']
                    and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25
                    and row['post_hash_compiler_admission_revalidated'] and row['compiler_admission_RAM_percent']==15
                    and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[],'AUDIT_JOB_TERMINAL')
            frozen=b.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
            if row['heavy_work_started']:b.require(all(frozen.get(n)==pin for n,pin in expected.items()),'AUDIT_WHOLE_FREEZE')
            for n,pin in {**expected,**frozen}.items():b.require(q.pin(n)==pin,'AUDIT_FRESH_SOURCE')
            b.require(row['source_test_names']==names and row['source_module_instances']==modules,'ORIGINAL249_59')
            q.pin(units.SELF);q.pin(units.TEST);units.contracts();exe=None
            if passed:
                b.require(row['exit_code']==0 and row['stop_reason'] is None and row['tests_passed']==71
                    and row['compiler_error_codes']==[] and row['compiler_diagnostic_locations']==[],'ACTUAL_ALL71')
                b.require(units.TARGET.is_dir() and not units.TARGET.is_symlink()
                    and not units.TARGET.is_junction(),'FRESH_TARGET_NO_LINK')
                exes=list((units.TARGET/'debug/deps').glob('hwpx_package-*.exe'))
                b.require(len(exes)==1,'ONE_NEW_LIB_EXE');exe=q.pin(exes[0].relative_to(b.c.ROOT).as_posix())
                b.require(exe['path'] not in expected,'NEW_LIB_NOT_HISTORICAL_PRODUCT')
            selected=q.pin(b.SOURCE);q.finish()
            out.update(state='PASS_WRITER_XML_REUSE_DELTA_AND_ALL71_LIB_UNITS_ONLY_NOT_FULL249_OR_GATE' if passed else
                'PASS_WRITER_XML_REUSE_DELTA_AND_UNIT_STOP_ACCOUNTED_ONLY_NOT_RUNTIME_OR_GATE',
                source_closing_exact=True,contract_tests_passed=136,whole_original_core_inverse_exact=True,
                test_oracle_whole_original_body_exact_after_declared_formatting=True,
                all_original_package_lib_tests_preserved=True,actual_unit_tests_passed=71 if passed else None,
                typecheck_accepted=passed,current_Rust_input_count=785,source_test_names=names,source_module_instances=modules,
                declared_Rust_source_changes=[selected],protected_parent_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),
                fresh_package_lib_executable_pin=exe,old_product_EXE_not_current_qualified=True,
                original_run_state=row['state'],original_stop_reason=row['stop_reason'],owned_job_final=row.get('job_final'),
                baseline_closing_pin=b.PARENT,original_source_final_hash_not_retroactively_promoted=not passed,
                host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
                host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=b.prior.d.original.closed_error(e)
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
