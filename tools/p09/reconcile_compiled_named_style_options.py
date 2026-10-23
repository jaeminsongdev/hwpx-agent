"""352: reconcile original27 PASS after missing post-check helper, no Cargo/product replay."""
import json,re,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as runtime
import run_compiled_named_style_options as base
shared,c,a,tools,compact,harness,audit=runtime.shared,runtime.c,runtime.a,runtime.tools,runtime.compact,runtime.harness,runtime.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-named-style-options-reconciled352.v1.json';DRIVER='tools/p09/reconcile_compiled_named_style_options.py'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_OPTIONS_RECONCILIATION_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_OPTIONS_RECONCILIATION',own_cpu_selection=selection,Cargo_tests_DB_or_Native_replayed=False,
        metadata_and_changed_source_audit_not_fresh_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(base.OUTPUT));baseline=compact.unpack(q.json(base.previous.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='11bbf8033db14c59af5f439e6d1aef70705865ca1c0d6d9fb99641879481051f'and failed['state']=='FAILED_COMPILED_NAMED_OPTIONS'
            and failed['error_type']=='AttributeError'and failed['cleanup']and failed['fresh_inputs']==failed['final_fresh_hashes']==821 and len(failed['steps'])==1,'EXACT351_ORIGINAL_POSTCHECK_FAILURE_RETAINED')
        c.require(q.snapshots[base.previous.OUTPUT]['sha256']=='04f732999478a7068a2b5c2063e967f34f0c1cde750401e63f7b38e1b0f75788'and baseline['cleanup'],'EXACT350_STANDALONE_OPTIONS_BASELINE')
        old={p['path']:p for p in failed['source_pins']};source=base.CHANGED|base.NEW|{'tools/p09/run_style_replacement_sync.py','tools/p09/run_source_note_api_components.py',
            'tools/p09/run_stored_note_kind_components.py','tools/p09/run_whitespace_patch_components.py','crates/product-cli/src/form_product_request/stored_operations/compiled_search.rs',
            'crates/product-cli/src/form_product_request/stored_operations/compiled_search/owners.rs','crates/product-cli/src/form_product_request/stored_operations/compiled_search/build.rs'}
        for path in sorted(source):
            q.pin(path)
            if path!=base.RUNTIME:c.require(q.snapshots[path]==old[path],'CURRENT_PRODUCTION_TESTS_DRIVER_AND_ORIGINAL_RUNTIME_MATCH351')
        audit.inverse(q.text(base.RUNTIME).replace('import run_whitespace_patch_components as tools','import run_regex_replacement_focused as tools'),old[base.RUNTIME],'ONLY_EXACT_ORIGINAL_TOOLS_MODULE_IMPORT_CORRECTED')
        base.inverse(q,{p['path']:p for p in baseline['source_pins']});base.preserve_import_failure(q)
        # Qualification-only identity comparison. This import does not invoke historical main/test functions.
        import run_named_style_options_product as historical
        c.require(all(getattr(runtime,n)is getattr(historical,n)for n in('shared','c','a','tools','compact','harness','audit')),'ALL_EXISTING_RUNTIME_OBJECT_IDENTITIES_UNCHANGED')
        c.require(runtime.snapshot is historical.previous.previous.base.previous.previous.previous.base.snapshot and sys.getrecursionlimit()==1000,'ORIGINAL_CLOSED_OBSERVER_AND_DEFAULT_RECURSION_LIMIT')
        cases={'named_options::compiled::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}|base.AFFECTED_OPTIONS|base.AFFECTED_COMMON
        c.require(len(cases)==27,'EXACT_ORIGINAL_NEW18_AFFECTED9');step=failed['steps'][0];tools.good_step(step,cases)
        c.require(step['diagnostics']==[]and step['bounded_output_observation']['safe_warning_locations']==[],'NO_ORIGINAL_COMPILE_OR_WARNING_DIAGNOSTICS')
        c.require(failed['elapsed_seconds']==136.828 and failed['system_CPU_max']==26.56 and 40.4820<failed['available_RAM_min_percent']<40.4821
            and step['owned_job']['last_job_accounting']['peak_job_private_mib']==924.94,'EXACT_ORIGINAL_COMMAND_RESOURCE_METADATA')
        q.pin(DRIVER);q.finish();guard.check(force=True);row.update(state='PASS_ORIGINAL_COMMON_NAMED_OPTIONS_NEW18_AFFECTED9_RECONCILED_NO_REPLAY_NOT_FRESH_RUNTIME_OR_NATIVE_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            original_runtime_fresh_inputs=821,original_runtime_final_fresh_hashes=821,original_case_count=27,new_common_cases=18,affected_cases=9,mutation_families=22,
            original_failure_receipt_unchanged=True,runtime_objects_and_closed_observer_identical=True,default_recursion_limit=1000,
            original_result_receipt=base.OUTPUT,next_work='named_character_style_semantics_full_options_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_OPTIONS_RECONCILIATION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
