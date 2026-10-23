"""500: borrow full predicates; one allocation-free last-pair memo per operation, unchanged wire contracts."""
import json,re,subprocess,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as prior
import verify_character_detail_search as helpers
import character_detail_receipt as layout
SELF='tools/p09/verify_style_predicate_search.py'
OUTPUT='implementation/p09/evidence/p09-361-style-predicate500.v1.json'
BASE='implementation/p09/evidence/p09-361-border-definition499.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-style-predicate500/'
PREFIX='crates/hwpx-package/src/document_import/search/'
DEFS=PREFIX+'inspection/definitions.rs'
CACHE=PREFIX+'inspection/definitions/last_predicate.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/detail_axes_product.rs'
CORE='crates/hwpx-package/tests/style_predicate_search.rs'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/style_predicate_product.rs'
CHANGED={PREFIX+name for name in('inspection/definitions.rs','inspection/definitions/details.rs','inspection/definitions/paragraph_details.rs',
    'inspection/definitions/resolved.rs','reviews/selector/styles.rs','reviews/selector/styles/paragraphs.rs','reviews/selector/resolved_styles.rs',
    'replacement/atoms/styles/fonts/filtered.rs','replacement/atoms/styles/paragraphs/named/filtered.rs')}|{PARENT}

def test_inputs(roots,guard):
    # Only literal Rust include/path dependencies of selected hosts, not whole test/source-history walks.
    pending=list(roots);seen=set();root=r.c.ROOT
    pattern=r'(?:#\s*\[\s*path\s*=\s*"([^"\n]+)"\s*\]|include(?:_str|_bytes)?!\s*\(\s*"([^"\n]+)")'
    while pending:
        name=pending.pop()
        if name in seen:continue
        guard.check();path=root/name;r.c.require(path.is_file()and not path.is_symlink()and not path.is_junction(),'STYLE500_LITERAL_REGULAR_INPUT')
        seen.add(name);r.c.require(len(seen)<=256,'STYLE500_FOCUSED_TEST_INPUT_BOUND')
        if path.suffix!='.rs':continue
        raw=path.read_bytes();r.c.require(len(raw)<=512*1024,'STYLE500_BOUNDED_TEST_SOURCE')
        for match in re.finditer(pattern,raw.decode('utf-8')):
            child=(path.parent/(match[1]or match[2])).resolve();r.c.require(child.is_relative_to(root),'STYLE500_INCLUDE_IN_WORKSPACE')
            pending.append(child.relative_to(root).as_posix())
    return seen

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'STYLE500_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_OPERATION_LOCAL_STYLE_PREDICATES',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,capture003_probe_or_previous_unaffected_tests_replayed=False,
        full_effective_style_font_resource_search_native_or_execution_qualified=False,source_mutation_or_publication=False,
        predicate_memo_entries_maximum=1,predicate_memo_uses_heap=False,predicate_memo_shared_between_operations=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);baseline=layout.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='e75e701e3e80e879e7f2c35d33c612cad5af72ee56c77c0326cc6487168ca375'
            and baseline['state'].startswith('PASS_')and baseline['cleanup']is True and baseline['fresh_inputs']==baseline['final_fresh_hashes']==824,
            'EXACT499_ORIGINAL_BORDER_ACCEPTANCE_RETAINED')
        names=prior.inventory(guard)|{p['path']for p in baseline['source_pins']}|{SELF,CACHE,CORE,PRODUCT}
        names|={ARCHIVE+path for path in CHANGED};names|=test_inputs((CORE,'crates/product-cli/tests/definition_detail_product.rs'),guard)
        for path in sorted(names):q.pin(path)
        for pin in baseline['source_pins']:
            if pin['path']in CHANGED:
                saved=q.snapshots[ARCHIVE+pin['path']];c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'EXACT499_CHANGED_CODE_ARCHIVED')
            else:c.require(q.snapshots[pin['path']]==pin,'STYLE500_UNCHANGED_OTHER_SOURCE_PRODUCT_PARSER_GUARDS_AND_FIXTURES')
        r.audit.inverse(q.text(PARENT).replace('#[path="style_predicate_product.rs"] mod predicate_cache;\n',''),q.snapshots[ARCHIVE+PARENT],
            'PREVIOUS_EXPLICIT_BORDER_PRODUCT_CASES_AND_ALL_HELPERS_UNCHANGED')
        core=helpers.tests(q,CORE);product=helpers.tests(q,PRODUCT,'product_host::detail_axes::predicate_cache::')
        c.require((len(core),len(product))==(5,2),'STYLE500_NEW_CORE5_STORED2')
        groups={
            'explicit::':('definition_style_source_axes_distinguish_run_text_and_named_definitions_without_precedence_inference',
                'definition_style_results_obey_scope_zero_width_and_accepted_match_limits'),
            'resolved::':('resolved_styles_false_predicates_are_not_absent_and_both_axes_are_conjunctive',
                'resolved_styles_missing_direct_references_reject_before_even_an_absent_query','resolved_styles_all_original_nfc_contributors_must_match_not_just_the_first'),
            'selector::':('selector_styles_both_predicate_families_use_document_section_actual_memo_node_and_partial_windows',
                'selector_styles_every_original_nfc_contributor_must_satisfy_the_predicate'),
            'border::':('every_border_resource_property_matches_both_typed_axes_positive_and_negative',
                'character_and_paragraph_use_their_own_referenced_resource_not_matching_any_catalog_entry'),
            'fonts::filtered::':('definition_filter_resolves_original_bold_once_not_an_inferred_axis','filter_metadata_binds_even_when_output_and_original_receipt_are_identical'),
            'paragraphs::named::filtered::':('definition_character_axis_uses_original_typed_properties_and_preserves_header',
                'definition_paragraph_axis_is_explicit_and_combines_with_character_axis'),
            'paragraphs::':('paragraph_style_declared_and_definition_filters_use_original_direct_and_named_values',)}
        for prefix,names in groups.items():core|={prefix+name for name in names}
        product|={'product_host::detail_axes::'+name for name in('explicit_run_text_named_and_direct_paragraph_axes_are_not_native_precedence',
            'v7_all_four_review_scopes_and_both_style_families_remain_conjunctive',
            'border_definitions::same_hits_different_border_predicates_cannot_reuse_retained_v7_or_v9_cursor')}
        c.require((len(core),len(product))==(19,5),'STYLE500_NEW7_DIRECTLY_AFFECTED17_ONLY')
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];c.require(available>11.176037330217578,'STYLE500_RAM95_PREVIOUS_COMPILE_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-style-predicate-scratch500';c.require(not scratch.exists(),'STYLE500_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='STYLE_PREDICATE_PREFLIGHT',inputs=len(q.snapshots),new_core=5,new_product=2,affected=17,CPU_cap_percent=6.25)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,cases in(('hwpx-package','style_predicate_search',core),('hwpx-agent-cli','definition_detail_product',product)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'STYLE500_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=helpers.dependencies(path);c.require(declared<=set(q.snapshots),'STYLE500_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'STYLE500_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_BORROWED_STYLE_PREDICATES_CORE5_STORED2_AFFECTED17_NOT_NATIVE_OR_GATE',new_core_cases=5,new_product_cases=2,affected_cases=17,
            fixed_storage_repeated_20000_calls_evaluate_twice=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'STYLE500_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],locations=step.get('bounded_output_observation',{}).get('short_error_locations',[]))for step in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
