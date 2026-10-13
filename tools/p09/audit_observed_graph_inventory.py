"""Independently close current graph EXE249 listing, not actual test bodies."""
import json
import re
import time
import run_observed_graph_inventory as v

p=v.p
SELF='tools/p09/audit_observed_graph_inventory.py'
ACTUAL='implementation/p09/evidence/p09-158-current-graph-inventory.actual-run01.v1.json'
PASS='PASS_CURRENT_GRAPH_COMPILED249_INVENTORY_CLOSING_ONLY_NOT_FULL_RUNTIME_OR_GATE'


def main():
    v.require(p.c.Path.cwd().resolve()==p.c.ROOT,'AUDIT_CWD')
    destination=p.s.scoped_path('implementation/p09/evidence/p09-158-current-graph-inventory.terminal-audit-run01.v1.json',fresh=True)
    resources=p.s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,current_compiled249_qualified=False,
        full249_current_qualified=False,signed16_current_qualified=False,runtime_test_bodies_executed=False,
        product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',PC_freeze_resolved=False,
        full_product_performance_improvement_measured=False,actual_SQL_native_or_audit_OS_child_executed=False,
        remaining_non_permission_work_units=76,resource_samples=resources.samples)
    try:
        resources.admit();q=p.s.LiveSQLReader(resources);q.pin(SELF);row=q.json(ACTUAL)
        out['actual_inventory_receipt_pin']=q.reader.snapshots[ACTUAL]
        v.require(row['state']==v.PASS and row['compiled_inventory_exact'] and row['current_compiled249_qualified']
            and row['fresh_EXE_list_only'] and row['runtime_tests_executed'] is False
            and row['full249_current_qualified'] is False and row['signed16_current_qualified'] is False
            and row['current_Rust_input_count']==785 and row['expected_test_count']==249
            and row['current_compile_closing_pin']==v.CLOSING,'AUDIT_LISTING_ONLY')
        v.require(row['exit_code']==0 and row['stop_reason'] is None and row['cleanup_confirmed'] and row['owned_tree_empty']
            and row['job_final']['active_processes']==0 and row['job_final']['owned_processes']==[]
            and row['maximum_seconds']==180 and row['policy']==p.c.POLICY and row['owned_limits_readback']['verified']
            and row['owned_limits_readback']['cpu_hard_cap_machine_percent']==6.25,'AUDIT_JOB_CLEANUP')
        cap=row['capture_diagnostics'];v.require(cap['error_code'] is None and cap['per_stream_limit_bytes']==32768
            and cap['raw_log_content_included'] is False and cap['received_bytes']['stderr']==0,'AUDIT_COMPLETE_LIST_CAPTURE')
        frozen=p.s.inputs.inventory(row['source_freeze'])
        for n,pin in frozen.items():v.require(q.pin(n)==pin,'AUDIT_WHOLE_CURRENT_INPUT')
        v.require(q.pin(v.CLOSING['path'])==v.CLOSING,'AUDIT_BUILD_CLOSING_IMMUTABLE')
        closing=q.json(v.CLOSING['path']);expected,exe=v.closing_scope(closing)
        v.require(all(frozen.get(n)==pin for n,pin in expected.items()) and row['compiled_test_executable_pin']==exe
            and frozen.get(exe['path'])==exe,'AUDIT_WHOLE_CURRENT_BUILD_EXE')
        rust={n for n in frozen if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        v.require(len(rust)==785 and p.s.inputs.rust_inputs(p.c.ROOT,resources.checkpoint_io)==rust,'AUDIT_WHOLE_RUST785')
        names,modules=p.source_scope(q,frozen)
        v.require(row['source_test_names']==names==closing['source_test_names']
            and row['source_module_instances']==modules==closing['source_module_instances'],'AUDIT_EXACT249_NAMES59')
        for n in (*p.helpers(),v.SELF,v.TEST):q.pin(n)
        v.contracts();v.d.contracts();q.finish()
        out.update(state=PASS,source_closing_exact=True,current_compiled249_qualified=True,contract_tests_passed=58,
            current_Rust_input_count=785,source_test_names=names,source_module_instances=modules,compiled_test_count=249,
            source_module_instance_count=59,compiled_test_executable_pin=exe,current_compile_closing_pin=v.CLOSING,
            protected_parent_EXE_inputs_exact=sum(n.endswith('.exe') for n in frozen),owned_inventory_job_final=row['job_final'],
            capture_diagnostics=cap,host_CPU_max_percent=max(x['system_cpu_percent'] for x in row['samples']),
            host_available_RAM_min_percent=min(x['available_ram_percent'] for x in row['samples']))
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        code=str(e) if isinstance(e,ValueError) else 'P158_INVENTORY_AUDIT_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P158_INVENTORY_AUDIT_REDACTED_FAILURE'
    finally:
        p.s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','compiled_test_count','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
