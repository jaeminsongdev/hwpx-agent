"""503: font source8/stored5 plus directly affected paths; no Native or official queue replay.

Invoke only after the external003 execution status has been reconciled. This file
does not supply that user confirmation and never starts or changes that capture.
"""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_character_detail_search as helpers
import verify_style_predicate_search as inputs
import character_detail_receipt as layout

SELF='tools/p09/verify_font_definition_search.py'
OUTPUT='implementation/p09/evidence/p09-361-font-definition503.v1.json'
BASE='implementation/p09/evidence/p09-361-style-predicate502.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-font-definition503/'
CORE='crates/hwpx-package/tests/style_predicate_search.rs'
PRODUCT_HOST='crates/product-cli/tests/definition_detail_product.rs'
FONT_CORE='crates/hwpx-package/tests/support/font_definition_contract.rs'
FONT_PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/font_definition_product.rs'


def cases(q):
    core=helpers.tests(q,FONT_CORE,'font_definitions::')
    product=helpers.tests(q,FONT_PRODUCT,'product_host::detail_axes::font_definitions::')
    r.c.require((len(core),len(product))==(8,5),'FONT503_NEW_SOURCE8_STORED5')
    groups={
        'explicit::':('definition_style_source_axes_distinguish_run_text_and_named_definitions_without_precedence_inference',
            'definition_style_results_obey_scope_zero_width_and_accepted_match_limits'),
        'resolved::':('resolved_styles_false_predicates_are_not_absent_and_both_axes_are_conjunctive',
            'resolved_styles_missing_direct_references_reject_before_even_an_absent_query',
            'resolved_styles_all_original_nfc_contributors_must_match_not_just_the_first',
            'resolved_styles_filter_is_closed_nonempty_and_rejects_old_axis_and_bad_value_shapes'),
        'selector::':('selector_styles_both_predicate_families_use_document_section_actual_memo_node_and_partial_windows',
            'selector_styles_every_original_nfc_contributor_must_satisfy_the_predicate',
            'selector_styles_bind_predicates_scope_policy_and_navigation_without_exposing_body_or_author'),
        'border::':('every_border_resource_property_matches_both_typed_axes_positive_and_negative',
            'character_and_paragraph_use_their_own_referenced_resource_not_matching_any_catalog_entry'),
        'fonts::filtered::':('definition_filter_resolves_original_bold_once_not_an_inferred_axis',
            'filter_metadata_binds_even_when_output_and_original_receipt_are_identical'),
        'paragraphs::named::filtered::':('definition_character_axis_uses_original_typed_properties_and_preserves_header',
            'definition_paragraph_axis_is_explicit_and_combines_with_character_axis'),
        'paragraphs::':('paragraph_style_declared_and_definition_filters_use_original_direct_and_named_values',)}
    for prefix,names in groups.items():core|={prefix+name for name in names}
    product|={'product_host::detail_axes::'+name for name in(
        'explicit_run_text_named_and_direct_paragraph_axes_are_not_native_precedence',
        'v7_all_four_review_scopes_and_both_style_families_remain_conjunctive',
        'border_definitions::same_hits_different_border_predicates_cannot_reuse_retained_v7_or_v9_cursor')}
    r.c.require((len(core),len(product))==(24,8),'FONT503_NEW13_AND_DIRECT_AFFECTED19')
    return core,product


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'FONT503_IMMUTABLE_NO_RETRY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_ORIGINAL_FONT_DEFINITION_SEARCH',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_Hancom_COM_DB_or_Native_started=False,
        official249_replayed=False,capture003_started_or_replayed=False,previous502_cache_tests_replayed=False,
        installed_font_availability_activation_native_execution_or_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='e6d4136554170c8c07d0554a9ae00e694e92f5729ea8f27ac34eb0a9a6c26f2b'
            and base['state']=='PASS_OPERATION_LOCAL_STYLE_PREDICATES_RETAINED19_NEW_REVIEW1_STORED5_NOT_NATIVE_OR_GATE'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==854,
            'FONT503_PRESERVE_EXACT502_NOT_CURRENT_FONT_ACCEPTANCE')
        names=inventory.inventory(guard)|{pin['path']for pin in base['source_pins']}|{SELF,FONT_CORE,FONT_PRODUCT}
        names|=inputs.test_inputs((CORE,PRODUCT_HOST),guard)
        originals=[]
        for path in(c.ROOT/ARCHIVE/'crates').rglob('*.rs'):
            guard.check();c.require(path.is_file()and not path.is_symlink()and not path.is_junction(),'FONT503_REGULAR_ARCHIVED_ORIGINAL')
            originals.append(path.relative_to(c.ROOT).as_posix());c.require(len(originals)<=69,'FONT503_BOUNDED_ORIGINALS')
        c.require(len(originals)==69,'FONT503_PRESERVED_ORIGINAL69');names.update(originals)
        for path in sorted(names):q.pin(path)
        changed=[]
        for pin in base['source_pins']:
            if q.snapshots[pin['path']]==pin:continue
            archived=q.snapshots.get(ARCHIVE+pin['path']);c.require(archived is not None,'FONT503_CHANGED_PRIOR_INPUT_REQUIRES_ORIGINAL')
            c.require((archived['bytes'],archived['sha256'])==(pin['bytes'],pin['sha256']),'FONT503_EXACT_PRE_CHANGE_ORIGINAL')
            changed.append(pin['path'])
        c.require(bool(changed),'FONT503_ACTUAL_SOURCE_IMPLEMENTATION_CHANGE');row['changed_prior_inputs']=changed
        core,product=cases(q);row['selected_test_cases']={'source':sorted(core),'stored':sorted(product)}
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.176037330217578,'FONT503_RAM95_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-font-definition-scratch503';c.require(not scratch.exists(),'FONT503_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='FONT_DEFINITION_PREFLIGHT',inputs=len(q.snapshots),source_cases=len(core),stored_cases=len(product),
            new_cases=13,direct_affected_cases=19,CPU_cap_percent=6.25,official249_replayed=False)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,selected in(('hwpx-package','style_predicate_search',core),('hwpx-agent-cli','definition_detail_product',product)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(selected),'--exact','--test-threads=1']
            r.harness.run_one(target,command,selected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],selected);c.require(not row['steps'][-1]['diagnostics'],'FONT503_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'FONT503_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'FONT503_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_ORIGINAL_FONT_DEFINITION_SOURCE8_STORED5_AFFECTED19_NOT_NATIVE_OR_GATE',new_core_cases=8,new_product_cases=5,
            directly_affected_cases=19,current_qualified_cases=32,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'FONT503_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),
            available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('bounded_output_observation',{}).get('short_error_locations',[]))for step in row['steps']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
