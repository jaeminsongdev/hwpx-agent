"""506: real paragraph-referenced tabs, new13/directly affected6; no Native or queue replay."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as inputs
import character_detail_receipt as layout
SELF='tools/p09/verify_tab_definition_search.py'
OUTPUT='implementation/p09/evidence/p09-361-tab-definition506.v1.json'
BASE='implementation/p09/evidence/p09-361-font-definition505.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-tab-definition506/'
DEFS=helpers.DEFS
CHANGED={DEFS:'definitions.rs',helpers.RESOLVED:'resolved.rs',DEFS[:-3]+'/font_details/output.rs':'font-output.rs',
    'crates/hwpx-package/tests/style_predicate_search.rs':'source-host.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/detail_axes_product.rs':'product-host.rs'}
CORE='crates/hwpx-package/tests/style_predicate_search.rs'
PRODUCT='crates/product-cli/tests/definition_detail_product.rs'
NEWCORE='crates/hwpx-package/tests/support/tab_definition_contract.rs'
NEWPRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/tab_definition_product.rs'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'TAB506_IMMUTABLE_NO_RETRY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_PARAGRAPH_REFERENCED_TAB_DEFINITIONS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,external003_replayed_or_cleanup_changed=False,
        native_layout_cascade_or_product_route_qualified=False,previous_passed_unaffected_matrix_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='e0dead884ac456336e54a2f063df96a21e54dc4699f1d2a7aa85fa0519f32334'
            and old['state'].startswith('PASS_')and old['cleanup']is True and old['fresh_inputs']==old['final_fresh_hashes']==944,'TAB506_EXACT505_ORIGINAL_CURRENT_RESULT')
        names=inventory.inventory(guard)|{pin['path']for pin in old['source_pins']}|{SELF,BASE,NEWCORE,NEWPRODUCT,DEFS[:-3]+'/tab_details.rs',
            'crates/hwpx-package/tests/support/tab_definition_fixture.rs'}|{ARCHIVE+name for name in CHANGED.values()}
        names|=inputs.test_inputs((CORE,PRODUCT),guard)
        for path in sorted(names):q.pin(path)
        for pin in old['source_pins']:
            if pin['path']in CHANGED:
                saved=q.snapshots[ARCHIVE+CHANGED[pin['path']]]
                c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'TAB506_PRIOR_CHANGED_INPUTS_EXACT_ARCHIVE')
            else:c.require(q.snapshots[pin['path']]==pin,'TAB506_OTHER_RUNTIME_LIBRARY_FIXTURE_AND_TEST_BODIES_UNCHANGED')
        # Added module links never alter the previous test bodies or shared provider helpers.
        r.audit.inverse(q.text(CORE).replace('#[path="support/tab_definition_contract.rs"] mod tab_definitions;\n',''),q.snapshots[ARCHIVE+'source-host.rs'],'TAB506_PREVIOUS_SOURCE_TEST_BODIES_UNCHANGED')
        parent=next(path for path,name in CHANGED.items()if name=='product-host.rs')
        r.audit.inverse(q.text(parent).replace('#[path="tab_definition_product.rs"] mod tab_definitions;\n',''),q.snapshots[ARCHIVE+'product-host.rs'],'TAB506_PREVIOUS_STORED_TEST_BODIES_UNCHANGED')
        core=helpers.tests(q,NEWCORE,'tab_definitions::');stored=helpers.tests(q,NEWPRODUCT,'product_host::detail_axes::tab_definitions::')
        c.require((len(core),len(stored))==(8,5),'TAB506_NEW_CORE8_STORED5_EXACT_ENABLED_CASES')
        core|={'explicit::definition_style_conditions_need_explicit_used_axes_and_reject_empty_filters',
            'resolved::resolved_styles_missing_direct_references_reject_before_even_an_absent_query',
            'font_definitions::font_name_and_binary_query_texts_are_redacted_in_debug_and_result_but_bound_to_identity'}
        stored|={'product_host::detail_axes::font_definitions::font_name_and_binary_text_remain_request_bound_without_leaking_from_retained_results',
            'product_host::detail_axes::font_definitions::font_predicates_never_bypass_current_acl_aead_or_closed_native_product_route',
            'product_host::detail_axes::exact16k_raw_padding_and_canonical_identity_preserve_previous_success_contract'}
        row.update(selected_source_cases=sorted(core),selected_stored_cases=sorted(stored),new_cases=13,directly_affected_cases=6)
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.176037330217578,'TAB506_RAM95_COMPILE_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-tab-definition-scratch506';c.require(not scratch.exists(),'TAB506_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='TAB_DEFINITION_PREFLIGHT',inputs=len(q.snapshots),source_cases=len(core),stored_cases=len(stored),CPU_cap_percent=6.25)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,cases in(('hwpx-package','style_predicate_search',core),('hwpx-agent-cli','definition_detail_product',stored)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'TAB506_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'TAB506_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'TAB506_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCED_TABS_CORE11_STORED8_NOT_NATIVE_OR_GATE',current_qualified_cases=19,stored_matrix_requests=96,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'TAB506_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),
            available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('panic_locations',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
