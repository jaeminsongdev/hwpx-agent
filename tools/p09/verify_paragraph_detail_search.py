"""495: paragraph detail source/stored implementation, new14 + affected22, original bounded Jobs."""
import ast,json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import verify_character_detail_search as prior
import character_detail_receipt as layout
r=prior.r
SELF='tools/p09/verify_paragraph_detail_search.py'
OUTPUT='implementation/p09/evidence/p09-361-paragraph-detail495.v1.json'
CORE='crates/hwpx-package/tests/'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/'
DEFS=prior.DEFS;RESOLVED=prior.RESOLVED
DETAIL=DEFS[:-3]+'/paragraph_details.rs'
PARENT=PRODUCT+'resolved_style_product.rs'
ARCHIVE='implementation/p09/source-archive/p361-paragraph-detail495/'
NEWCORE=CORE+'document_import_paragraph_detail_search.rs'
NEWPRODUCT=PRODUCT+'paragraph_detail_product.rs'

def inverse(q):
    field='    #[serde(skip_serializing_if="Option::is_none")]\n    pub paragraph_details:Option<paragraph_details::SourceParagraphDetailFilter>,\n'
    text=q.text(DEFS).replace('pub mod paragraph_details;\n','').replace(field,'')
    text=text.replace('        if let Some(details)=self.paragraph_details {details.validate()?;}\n','')
    text=text.replace('''        let paragraphs=self.alignment.is_some()||self.paragraph_details.is_some();
        if self.character_source.is_some()!=characters||self.paragraph_source.is_some()!=paragraphs
            ||!characters&&!paragraphs{return Err(E::Filter);}Ok(())''','''        if self.character_source.is_some()!=characters||self.paragraph_source.is_some()!=self.alignment.is_some()
            ||!characters&&self.alignment.is_none(){return Err(E::Filter);}Ok(())''')
    text=text.replace('''            if filter.alignment.is_some_and(|v|v.native()!=style.horizontal_alignment)
                ||filter.paragraph_details.as_ref().is_some_and(|details|!details.matches(style)){return false;}''',
        '            if filter.alignment.is_some_and(|v|v.native()!=style.horizontal_alignment){return false;}')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'definitions-original.rs'],'ENTIRE_ORIGINAL_DEFINITION_RESOLUTION_BINDING_AND_MATCHER_BODY_RESTORED')
    text=q.text(RESOLVED).replace(field,'').replace('    fn paragraphs(self)->bool {self.alignment.is_some()||self.paragraph_details.is_some()}\n','')
    text=text.replace('if let Some(details)=self.paragraph_details {details.validate()?;}','').replace('!self.characters()&&!self.paragraphs()','!self.characters()&&self.alignment.is_none()')
    text=text.replace('''            paragraph_source:self.paragraphs().then_some(ParagraphDefinitionSource::DirectProperty),alignment:self.alignment,character_details:self.character_details,
            paragraph_details:self.paragraph_details}''','''            paragraph_source:self.alignment.map(|_|ParagraphDefinitionSource::DirectProperty),alignment:self.alignment,character_details:self.character_details}''')
    text=text.replace('!filter.paragraphs()||coverage.resolved_paragraph_segments','filter.alignment.is_none()||coverage.resolved_paragraph_segments')
    r.audit.inverse(text,q.snapshots[ARCHIVE+'resolved-original.rs'],'ENTIRE_ORIGINAL_CHARACTER_CONTROL_CONTEXT_AND_REQUIRED_AXIS_COVERAGE_RESTORED')
    r.audit.inverse(q.text(PARENT).replace('#[path="paragraph_detail_product.rs"] mod paragraph_details;\n',''),q.snapshots[ARCHIVE+'product-original.rs'],
        'ALL_ORIGINAL_STORED_CHARACTER_RESOLVED_STYLE_TEST_AND_FIXTURE_BODIES_UNCHANGED')

def inventory(guard):
    # Compile inputs only: no Git/history/target tree walk or unrelated test source trees.
    names={'Cargo.toml','Cargo.lock','rust-toolchain.toml',SELF,DEFS,RESOLVED,DETAIL,PARENT,NEWCORE,NEWPRODUCT,
        CORE+'paragraph_detail_search.rs',CORE+'support/paragraph_detail_fixture.rs',
        'crates/product-cli/tests/character_detail_product.rs','crates/hwpx-package/src/hancom_2020_minimal_header.xml',
        'implementation/p04/trust/p04-direct-route-attestation.json','implementation/p04/trust/p04-direct-route-attestation.sig'}
    names|={ARCHIVE+name for name in('definitions-original.rs','resolved-original.rs','product-original.rs')}
    for package in r.shared.PACKAGES:
        names.add(f'crates/{package}/Cargo.toml');root=r.c.ROOT/f'crates/{package}/src'
        r.c.require(root.is_dir()and not root.is_symlink()and not root.is_junction(),'PARAGRAPH_DETAIL_REGULAR_COMPILED_SOURCE_ROOT')
        for directory,dirs,files in os.walk(root,followlinks=False):
            guard.check()
            for name in dirs:
                child=Path(directory)/name;r.c.require(not child.is_symlink()and not child.is_junction(),'PARAGRAPH_DETAIL_SOURCE_LINK')
            for name in files:
                if name.endswith('.rs'):names.add((Path(directory)/name).relative_to(r.c.ROOT).as_posix())
                r.c.require(len(names)<=2048,'PARAGRAPH_DETAIL_SOURCE_BOUND')
    for path in(r.c.ROOT/'migrations/postgres').glob('*.sql'):names.add(path.relative_to(r.c.ROOT).as_posix())
    for target in('character_detail_product','document_import_character_detail_search','document_import_search_definitions','document_import_resolved_style_search'):
        for path in(r.c.ROOT/'target/debug/deps').glob(target+'-*.d'):names|=prior.dependencies(path)
    for module in tuple(sys.modules.values()):
        value=getattr(module,'__file__',None)
        if value:
            path=Path(value).absolute()
            if path.is_relative_to(r.c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(r.c.ROOT).as_posix())
    return names

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PARAGRAPH_DETAIL495_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_PARAGRAPH_DETAIL_SOURCE_AND_STORED_PRODUCTS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,old_native_or_compiled003_probe_replayed=False,
        source_mutation_or_publication=False,full_native_paragraph_cascade_visibility_or_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        for path in sorted(inventory(guard)):q.pin(path)
        inverse(q)
        core=prior.tests(q,NEWCORE,'paragraph_details::');product=prior.tests(q,NEWPRODUCT,'product_host::resolved_style_v9::paragraph_details::')
        c.require(len(core)==8 and len(product)==6,'EXACT_NEW_CORE8_PRODUCT6')
        groups={
            'definition_regression::':('definition_style_search_binds_typed_bold_italic_height_color_and_paragraph_alignment',
                'definition_style_source_axes_distinguish_run_text_and_named_definitions_without_precedence_inference',
                'definition_style_absent_direct_axes_never_fall_back_to_zero_or_named_style','definition_style_conditions_need_explicit_used_axes_and_reject_empty_filters'),
            'resolved_regression::':('resolved_styles_direct_values_use_original_typed_readers_not_named_defaults',
                'resolved_styles_false_predicates_are_not_absent_and_both_axes_are_conjunctive','resolved_styles_missing_direct_references_reject_before_even_an_absent_query',
                'resolved_styles_present_text_style_is_unresolved_even_when_its_value_agrees','resolved_styles_only_requested_axes_require_resolution',
                'resolved_styles_empty_selection_has_no_invented_formatting_or_zero_width_match'),
            'character_regression::':('detail_legacy_filter_serialization_is_byte_exact_and_new_conditions_bind_hash','detail_explicit_axis_is_required_and_uses_the_original_definition_matcher')}
        for prefix,names in groups.items():core|={prefix+name for name in names}
        prefix='product_host::resolved_style_v9::'
        product|={prefix+name for name in('resolved_product_direct_values_false_and_combined_predicates_match_original_source',
            'resolved_product_unresolved_required_axes_remain_typed_errors_even_for_absent_queries',
            'resolved_product_unrequested_axis_and_outside_scope_uncertainty_do_not_override_selected_contract',
            'resolved_product_closed_required_shapes_values_and_decoded_duplicates_reject_before_reads',
            'resolved_product_exact_16k_raw_canonical_scope_key_plan_predicate_and_policy_bindings_are_distinct',
            'resolved_product_current_write_and_five_foreign_scopes_deny_full_result_and_navigation',
            'resolved_product_acl_revoke_regrant_quarantine_and_aead_deny_retained_and_new_searches',
            'resolved_product_prepare_verify_json_and_next_final_head_races_block_consumers')}
        product|={prefix+'character_details::'+name for name in('detail_product_all24_predicates_use_current_stored_source_and_strict_json',
            'detail_product_missing_or_uninterpreted_direct_axis_still_rejects_without_matches')}
        c.require((len(core),len(product))==(20,16),'NEW14_AFFECTED22_EXACT_ENABLED_CASES')
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];required=11.036870455636344
        row['memory_admission']=dict(available_ram_percent=available,required_available_percent=required,global_RAM_commit_ceiling_percent=95)
        c.require(available>required,'PARAGRAPH_DETAIL_COMPARABLE_COMPILE_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-paragraph-detail-scratch495';c.require(not scratch.exists(),'PARAGRAPH_DETAIL_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='PARAGRAPH_DETAIL_PREFLIGHT',inputs=len(q.snapshots),new_core=8,new_product=6,affected_core=12,affected_product=10,CPU_cap_percent=6.25)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,cases in(('hwpx-package','paragraph_detail_search',core),('hwpx-agent-cli','character_detail_product',product)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(target,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'PARAGRAPH_DETAIL_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=prior.dependencies(path);c.require(declared<=set(q.snapshots),'ALL_ACTUAL_PARAGRAPH_DETAIL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'PARAGRAPH_DETAIL_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_PARAGRAPH_DETAIL_CORE8_STORED6_AFFECTED22_NOT_FULL_STYLE_NATIVE_OR_GATE',
            new_core_cases=8,new_product_cases=6,affected_core_cases=12,affected_product_cases=10,total_executed_cases=36,
            paragraph_detail_predicate_families=27,explicit_current_and_fallback_branches_not_native_precedence=True,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PARAGRAPH_DETAIL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cases=len(s.get('tests',[])),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]),
                failed_cases=[name for name,status in s.get('tests',[])if status!='ok'],locations=s.get('bounded_output_observation',{}).get('short_error_locations',[]))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
