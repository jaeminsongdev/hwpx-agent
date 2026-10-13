"""P169 independent current-r05 whole249 listing closure, not test bodies."""
import json
import time
from unittest.mock import patch
import run_writer_xml_product_inventory as v

d=v.d
SELF='tools/p09/audit_writer_xml_product_inventory.py'
ACTUAL='implementation/p09/evidence/p09-169-writer-xml-product-inventory.actual-run01.v1.json'
PASS='PASS_WRITER_XML_CURRENT_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'

def main():
    v.require(d.c.Path.cwd().resolve()==d.c.ROOT,'AUDIT_CWD')
    destination=d.s.scoped_path('implementation/p09/evidence/p09-169-writer-xml-product-inventory.terminal-audit-run01.v1.json',fresh=True)
    resources=d.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,runtime_test_bodies_executed=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_SQL_native_or_audit_OS_child_executed=False,
        fixture_pipe_reader_threads_started_and_joined=True,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=d.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_inventory_receipt_pin']=q.reader.snapshots[ACTUAL];accepted=row['state']==v.PASS
        v.require(row['state'] in (v.PASS,'STOPPED_NOT_ACCEPTED','DEFERRED_NOT_STARTED')
            and row['compiled_inventory_exact']==row['current_compiled249_qualified']==accepted
            and row['fresh_EXE_list_only'] and not row['runtime_tests_executed']
            and not row['full249_current_qualified'] and not row['signed16_current_qualified']
            and row['current_Rust_input_count']==785 and row['expected_test_count']==249
            and row['current_compile_closing_pin']==v.CLOSING and not row['native_Process_query_executed']
            and not row['product_complete'] and row['P09_gate']==row['A12_gate']==row['A13_gate']=='OPEN',
            'LISTING_NOT_BODIES_OR_GATE')
        v.require(row['cleanup_confirmed'] and row['owned_tree_empty'] and row['maximum_seconds']==180
            and row['policy']==d.c.POLICY,'ORIGINAL_GUARDS_CLEANUP')
        if row['heavy_work_started']:
            v.require(row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[]
                and row['owned_limits_readback']['verified']
                and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25,'JOB_TERMINAL')
        cap=row['capture_diagnostics']
        if accepted:
            v.require(row['exit_code']==0 and row['stop_reason'] is None and cap['error_code'] is None
                and cap['per_stream_limit_bytes']==32768 and not cap['raw_log_content_included']
                and cap['received_bytes']['stderr']==0,'COMPLETE_LIST_CAPTURE')
        else:v.require(row['stop_reason'] is not None,'STOP_NOT_PASS')
        v.require(q.pin(v.CLOSING['path'])==v.CLOSING,'BUILD_CLOSING_IMMUTABLE')
        closing=q.json(v.CLOSING['path']);expected,exe=v.closing_scope(closing)
        frozen=d.s.inputs.inventory(row['source_freeze']) if row['source_freeze'] else {}
        if row['heavy_work_started']:v.require(all(frozen.get(n)==pin for n,pin in expected.items()),'WHOLE_BUILD_IN_FREEZE')
        for n,pin in {**expected,**frozen}.items():v.require(q.pin(n)==pin,'WHOLE_CURRENT_INPUT')
        v.require(row['compiled_test_executable_pin']==exe and expected.get(exe['path'])==exe,'CURRENT_R05')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        v.require(len(rust)==785 and d.s.inputs.rust_inputs(d.c.ROOT,resources.checkpoint_io)==rust,'RUST785')
        names,modules=d.p.source_scope(q,expected)
        v.require(row['source_test_names']==names==closing['source_test_names']
            and row['source_module_instances']==modules==closing['source_module_instances'],'EXACT249_59')
        with patch('subprocess.Popen',side_effect=AssertionError('P169_LIST_AUDIT_OS_CHILD_FORBIDDEN')), \
                patch('subprocess.run',side_effect=AssertionError('P169_LIST_AUDIT_OS_CHILD_FORBIDDEN')):
            v.contracts();d.contracts()
        for n in (*d.helpers(),v.SELF,v.TEST,SELF):q.pin(n)
        q.finish()
        out.update(state=PASS if accepted else 'PASS_WRITER_XML_PRODUCT_LIST_STOP_ACCOUNTED_ONLY_NOT_COMPILED249_OR_GATE',
            source_closing_exact=True,current_compiled249_qualified=accepted,contract_tests_passed=190,
            current_Rust_input_count=785,source_test_names=names,source_module_instances=modules,
            compiled_test_count=249 if accepted else None,source_module_instance_count=59,
            compiled_test_executable_pin=exe,current_compile_closing_pin=v.CLOSING,
            protected_parent_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),
            owned_inventory_job_final=row.get('job_final'),capture_diagnostics=cap,
            original_stop_reason=row['stop_reason'],original_source_final_hash_not_retroactively_promoted=not accepted,
            host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']) if row['samples'] else None,
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']) if row['samples'] else None)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=d.writer.b.prior.d.original.closed_error(e)
    finally:
        d.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','compiled_test_count',
            'error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2

if __name__=='__main__':raise SystemExit(main())
