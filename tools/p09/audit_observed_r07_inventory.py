"""P184 separate whole listing closing, original P182 main guards inverse exact."""
import io
import json
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import audit_r07_postclosed_inventory as core
import run_observed_r07_inventory as run
v=SimpleNamespace(ACTUAL=run.ACTUAL,PREP=run.PREP,PASS=run.PASS,
    CLOSING=run.prior.CLOSING,closing_scope=run.prior.closing_scope,closing=run.prior.closing,
    require=run.prior.require,contracts=run.contracts,helpers=run.helpers)
b=run.b; c=run.c; s=run.s
SELF='tools/p09/audit_observed_r07_inventory.py'
TEST='tools/p09/tests/test_observed_r07_inventory_closing.py'
DEST='implementation/p09/evidence/p09-184-observed-r07-inventory.terminal-audit-run01.v1.json'
PASS='PASS_OBSERVED_POSTCLOSED_R07_COMPILED249_WHOLE_CLOSING_ONLY_NOT_RUNTIME_OR_GATE'
CORE_PIN=dict(path=core.SELF,bytes=9362,sha256='aaa1b8fe207dceeaf32088ec054371ccdc16427807c4d14224c51cda35ddd415')
MAIN_ROLES=[["resources=s.SQLRuntimeResources();q=None;started=time.monotonic()","resources=run.observation.ObservedResources();q=None;started=time.monotonic()"],["resources.admit();q=b.weighted.WeightedLiveReader(resources);q.pin(SELF);q.pin(TEST)","resources.admit();q=run.Reader(resources);q.pin(SELF);q.pin(TEST);body_inverse(q)"],["prep=q.json(v.PREP);prepared=s.inputs.inventory(prep['bound_input_pins'])","prep=q.json(v.PREP);prepared=s.inputs.inventory(prep['bound_input_pins']);extra_preparation_scope(q,prep)"],["prep['contract_tests_passed']==18","prep['contract_tests_passed']==33"],["listing_contract_tests_passed=18,audit_contract_tests_passed=4","listing_contract_tests_passed=33,audit_contract_tests_passed=6"],["total_contract_tests_passed=22","total_contract_tests_passed=39"],["out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=b.weighted.resource_tail(resources))","out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=run.observation.parent_tail(resources))"]]

def body_inverse(q):
    v.require(q.pin(CORE_PIN['path'])==CORE_PIN,'ORIGINAL_WHOLE_AUDITOR_PIN')
    old=q.text(core.SELF);new=q.text(SELF)
    old=old[old.index('def main():\n'):old.index("\nif __name__=='__main__'")]
    new=new[new.index('def main():\n'):new.index("\nif __name__=='__main__'")]
    for before,after in reversed(MAIN_ROLES):
        v.require(new.count(after)==1,'DECLARED_MAIN_ROLE_UNIQUE')
        new=new.replace(after,before,1)
    v.require(new==old,'WHOLE_ORIGINAL_MAIN_GUARDS_INVERSE_EXACT')

def actual_scope(row):
    with patch.object(core,'v',v):frozen=core.actual_scope(row)
    v.require(row['readonly_parent_ProcessTimes_observation_connected']
        and row['readonly_parent_Process_query_executed'] and not row['readonly_extra_sampler_thread_started']
        and row['readonly_observation_scope']=='current_parent_pseudo_handle_only'
        and row['original_P182_CPU_stop_receipt_preserved']
        and row['original_resource_guards_and_read_rates_preserved'],'READONLY_OBSERVATION_EXPLICIT')
    return frozen

def extra_preparation_scope(q,prep):
    v.require(prep['readonly_parent_ProcessTimes_observation_connected']
        and prep['readonly_parent_Process_query_executed'] and not prep['foreign_Process_query_executed']
        and not prep['readonly_extra_sampler_thread_started']
        and prep['readonly_observation_scope']=='current_parent_pseudo_handle_only'
        and prep['original_P182_CPU_stop_receipt_preserved']
        and prep['original_resource_guards_and_read_rates_preserved'],'OBSERVED_PREPARATION_SCOPE')
    context=prep['IO']['protected_file_read_context']
    v.require(context['every_original_fresh_read_and_guard_preserved']
        and not context['arbitrary_source_paths_or_private_artifact_names_saved']
        and context['interrupted_protected_EXE_path'] is None,'PREPARATION_NO_PARTIAL_READ_PROMOTION')
    tail=prep['resource_tail']
    v.require(tail['existing_samples_only'] and not tail['extra_sampler_thread_started']
        and not tail['foreign_Process_query_executed'] and 1<=len(tail['samples'])<=8
        and all(row['parent_process_only'] and not row['foreign_Process_query_executed'] for row in tail['samples']),
        'PREPARATION_PARENT_SAMPLES')
    light=q.json(run.LIGHT)
    v.require(light['state']=='PASS_OBSERVED_R07_LISTING_CONTRACT33_ONLY_NOT_ACTUAL_OR_CAUSE'
        and light['contract_tests_passed']==33 and light['resource_stop_reason'] is None
        and light['resource_watcher_cleanup_confirmed']
        and q.pin(run.FAILED_PREP)==light['original_P182_preparation_pin'],'IMMUTABLE_P182_STOP_FROM_LIGHT')
    failed=q.json(run.FAILED_PREP)
    v.require(failed['state']=='FAILED_NOT_ACCEPTED' and not failed['source_closing_exact']
        and failed['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and failed['resource_watcher_cleanup_confirmed'] and not failed['actual_EXE_executed'],'P182_STOP_STILL_NOT_RUN')

def contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_r07_inventory_closing')
    with patch('subprocess.Popen',side_effect=AssertionError('P184_AUDIT_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P184_AUDIT_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P184_AUDIT_NO_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    v.require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'AUDIT_ORIGINAL4_PLUS2')

def main():
    v.require(c.Path.cwd().resolve()==c.ROOT,'AUDIT_CWD');destination=s.scoped_path(DEST,fresh=True)
    resources=run.observation.ObservedResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',goal_status='active',source_closing_exact=False,
        current_compiled249_qualified=False,full249_current_qualified=False,signed16_current_qualified=False,
        runtime_test_bodies_executed=False,product_complete=False,P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',
        PC_freeze_resolved=False,actual_new_Cargo_SQL_Hangul_or_child_executed=False,
        remaining_non_permission_work_units=76,original_STOP_receipt_unchanged=True)
    try:
        resources.admit();q=run.Reader(resources);q.pin(SELF);q.pin(TEST);body_inverse(q)
        row=q.json(v.ACTUAL);frozen=actual_scope(row)
        v.require(q.pin(v.CLOSING['path'])==v.CLOSING,'IMMUTABLE_BUILD_CLOSING')
        parent=q.json(v.CLOSING['path']);expected,exe=v.closing_scope(parent)
        prep=q.json(v.PREP);prepared=s.inputs.inventory(prep['bound_input_pins']);extra_preparation_scope(q,prep)
        v.require(prep['state']=='PASS_R07_LISTING_PREPARATION_ONLY_NOT_ACTUAL_OR_GATE'
            and prep['source_closing_exact'] and prep['contract_tests_passed']==33
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
            protected_parent_EXE_inputs_exact=68,listing_contract_tests_passed=33,audit_contract_tests_passed=6,
            total_contract_tests_passed=39,actual_inventory_receipt_pin=q.reader.snapshots[v.ACTUAL],
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
        out.update(wall_seconds=round(time.monotonic()-started,4),resource_tail=run.observation.parent_tail(resources))
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','compiled_test_count','total_contract_tests_passed',
            'error_code','resource_stop_reason','wall_seconds')}))
    return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
