"""504: preserve503 and search18; rerun affected writer6, execute previously unrun stored8.

Conditional existing font/text ID vocabulary, never relaxed reference/asset checks.
No Native, cleanup action, source fixture widening or official249 execution.
"""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import verify_font_definition_search as prior
r,layout=prior.r,prior.layout
SELF='tools/p09/verify_font_definition_recovery.py'
OUTPUT='implementation/p09/evidence/p09-361-font-definition504.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-font-definition503-failure/'
ROOT='crates/hwpx-package/src/document_import/search/replacement'
NEW_PROFILE=ROOT+'/font_profile.rs'
TEST='crates/hwpx-package/tests/support/font_definition_replacement.rs'
FAILED='font_definitions::font_name_and_binary_query_texts_are_redacted_in_debug_and_result_but_bound_to_identity'
CHANGED={ROOT+'.rs':'replacement-module503.rs',ROOT+'/output.rs':'legacy-output503.rs',
    ROOT+'/atoms/styles/text/output.rs':'text-output503.rs',TEST:'replacement-test503.rs'}
WRITERS={
    'fonts::filtered::definition_filter_resolves_original_bold_once_not_an_inferred_axis',
    'fonts::filtered::filter_metadata_binds_even_when_output_and_original_receipt_are_identical',
    'paragraphs::named::filtered::definition_character_axis_uses_original_typed_properties_and_preserves_header',
    'paragraphs::named::filtered::definition_paragraph_axis_is_explicit_and_combines_with_character_axis',
    'paragraphs::paragraph_style_declared_and_definition_filters_use_original_direct_and_named_values'}


def original_writer_bodies(q):
    c=r.c;path=ROOT+'.rs';text=q.text(path);marker='mod font_profile;\n'
    c.require(text.count(marker)==1,'FONT504_ONE_LAZY_PROFILE_MODULE')
    r.audit.inverse(text.replace(marker,''),q.snapshots[ARCHIVE+CHANGED[path]],'FONT504_ENTIRE_ORIGINAL_REPLACEMENT_MODULE_RESTORED')
    paths=((ROOT+'/output.rs','super::font_profile::select(source,IdRuleProfile::hwpml_2011_shape_v6())','IdRuleProfile::hwpml_2011_shape_v6()'),
        (ROOT+'/atoms/styles/text/output.rs','crate::document_import::search::replacement::font_profile::select(source,IdRuleProfile::hwpml_2011_text_style_v9())','IdRuleProfile::hwpml_2011_text_style_v9()'))
    for path,new,old in paths:
        text=q.text(path);c.require(text.count(new)==1,'FONT504_ONE_EXPLICIT_PROFILE_SELECTION_PER_WRITER')
        r.audit.inverse(text.replace(new,old),q.snapshots[ARCHIVE+CHANGED[path]],'FONT504_ENTIRE_OLD_WRITER_AND_ALL_GUARDS_RESTORED')


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'FONT504_IMMUTABLE_NO_RETRY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_FONT_REFERENCE_WRITER_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,capture003_replayed_or_cleanup_changed=False,
        previous503_failure_and_missing_final_fresh_preserved=True,previous18_search_bodies_replayed=False,
        font_file_validity_activation_native_or_product_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);old=layout.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='c359def4a4099dba9163d1c3f7d15b69154a5ba74d38c9f7b25b10a58bf17d4c'
            and old['state']=='FAILED_ORIGINAL_FONT_DEFINITION_SEARCH'and old['error_code']=='SOURCE_NOTE_API_COMMAND_FAILED'
            and old['cleanup']is True and old['fresh_inputs']==932 and old['final_fresh_hashes']==0 and len(old['steps'])==1,'FONT504_EXACT503_ORIGINAL_FAILURE')
        step=old['steps'][0];passed={name for name,status in step['tests']if status=='ok'}
        c.require(step['exit_code']==101 and len(step['tests'])==24 and len(passed)==23
            and [(name,status)for name,status in step['tests']if status!='ok']==[(FAILED,'FAILED')]
            and step['bounded_output_observation']['closed_static_patch_codes']==['id_index_validation_failed'],
            'FONT504_EXACT23_OBSERVED_AND_ONE_UNCLOSED_ID_FAILURE')
        names=prior.inventory.inventory(guard)|{pin['path']for pin in old['source_pins']}|{SELF,NEW_PROFILE}
        names|={ARCHIVE+saved for saved in CHANGED.values()};names.add(ARCHIVE+'runner503.py')
        names|=prior.inputs.test_inputs((prior.CORE,prior.PRODUCT_HOST),guard)
        for path in sorted(names):q.pin(path)
        for pin in old['source_pins']:
            if pin['path']in CHANGED:
                saved=q.snapshots[ARCHIVE+CHANGED[pin['path']]]
                c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'FONT504_EXACT_FAILED_INPUTS_ARCHIVED')
            else:c.require(q.snapshots[pin['path']]==pin,'FONT504_UNCHANGED_OTHER_RUNTIME_SOURCE_FIXTURE_AND_TEST_BODIES')
        original_writer_bodies(q);core,product=prior.cases(q);selected=WRITERS|{FAILED};retained=core-selected
        c.require(len(selected)==6 and len(retained)==18 and len(product)==8 and retained<=passed and WRITERS<=passed,'FONT504_EXACT_IMPACT_RETAIN18_EXECUTE6_PLUS_UNRUN8')
        row.update(retained_search_case_names=sorted(retained),retained_search_cases=18,selected_writer_case_names=sorted(selected),selected_stored_case_names=sorted(product))
        guard.check(force=True);c.require(guard.samples[-1]['available_ram_percent']>11.176037330217578,'FONT504_RAM95_PEAK_PLUS_RESERVE')
        scratch=c.ROOT/'target/p09-font-definition-scratch504';c.require(not scratch.exists(),'FONT504_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='FONT_REFERENCE_WRITER_PREFLIGHT',inputs=len(q.snapshots),retained_search=18,affected_writer=6,previously_unrun_stored=8,
            CPU_cap_percent=6.25,missing_manifest_target_still_rejected=True,opaque_test_resources_not_valid_font_files=True)),flush=True)
        row['actual_compiled_test_inputs']=[]
        for package,target,selected in(('hwpx-package','style_predicate_search',selected),('hwpx-agent-cli','definition_detail_product',product)):
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',target,'--message-format=short','--',*sorted(selected),'--exact','--test-threads=1']
            r.harness.run_one(target,command,selected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],selected);c.require(not row['steps'][-1]['diagnostics'],'FONT504_NO_COMPILER_WARNINGS')
            actual=[]
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                declared=prior.helpers.dependencies(path);c.require(declared<=set(q.snapshots),'FONT504_ACTUAL_COMPILER_INPUTS_PINNED_BEFORE_RUN')
                actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'FONT504_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs'].extend(actual)
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCED_FONT_DEFINITIONS_RETAINED_SEARCH18_WRITER6_STORED8_NOT_NATIVE_OR_GATE',current_qualified_cases=32,
            writer_cases_executed=6,previously_unrun_stored_cases_executed=8,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'FONT504_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(step['cleanup']for step in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),
            available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=step['stage'],exit_code=step.get('exit_code'),cases=len(step.get('tests',[])),cleanup=step['cleanup'],diagnostics=step.get('diagnostics',[]),
                failed_cases=[name for name,status in step.get('tests',[])if status!='ok'],safe_errors=step.get('safe_error_variants',[]),locations=step.get('bounded_output_observation',{}).get('short_error_locations',[]))for step in row['steps']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
