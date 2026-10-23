"""Repair only text output's missing explicit ID domain; retain four unaffected negative passes."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_style_components as base
harness,shared,c,a,audit=base.harness,base.shared,base.c,base.a,base.audit
OUTPUT='implementation/p09/evidence/p09-361-text-style-id-recovery135.v1.json'
IDS='crates/hwpx-package/src/id_index.rs';BUILD=base.TEXT[:-3]+'/output.rs'
OFFICIAL='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/t.cpp'
NEW=base.NEW|{BUILD};CHANGED=base.CHANGED|{IDS}
RETAINED={'text_style_caches_and_enclosing_fields_reject_including_noop_targets',
    'text_style_fresh_source_proof_and_selector_identities_are_required',
    'text_style_empty_filters_missing_targets_no_matches_and_noops_are_errors',
    'text_style_tracked_and_unsupported_text_attributes_do_not_duplicate_identity'}
METHOD='''    /// Immutable shape/v6 plus explicit paragraph t.charStyleIDRef -> header charPr.
    /// Static CT vocabulary from model 1453388472c703a4b299a0834f425cdac16644b9 t.cpp;
    /// character domain is the existing qualified typed reader's explicit text-style axis.
    /// No chart/caption-owner rules, implicit defaults or licensed-target qualification.
    #[must_use]
    pub const fn hwpml_2011_text_style_v9() -> Self {
        Self(ProfileKind::Hwpml2011TextStyleV9)
    }

'''
RULE='''const TEXT_STYLE_REFERENCE_RULES: &[ReferenceRule] = &[
    reference(
        PartSelector::SpineDocument,
        HWPML_2011_PARAGRAPH_NAMESPACE,
        "t",
        "charStyleIDRef",
        TargetSelector::Exact(HEADER_PART),
        IdKind::CharacterProperties,
        ValueSyntax::Decimal,
    ),
];

'''


def inventory(check):return base.inventory(check)|{BUILD,OFFICIAL}


def inverse(q,old,failed):
    text=q.text(base.STYLE);c.require(text.count('pub mod text;\n')==1,'ONE_ADDITIVE_TEXT_AXIS_MODULE')
    audit.inverse(text.replace('pub mod text;\n',''),old[base.STYLE],'WHOLE_RUN_STYLE_COMPILER_BODY_UNCHANGED')
    text=q.text(base.RENDER);audit.inverse(text.replace('pub(super) fn namespaces(','fn namespaces('),old[base.RENDER],'WHOLE_RUN_STYLE_RENDER_BODY_UNCHANGED')
    text=q.text(base.VERIFY)
    for current,original in[('pub(super) enum Scalar','enum Scalar'),
        ('pub(super) struct PointValue {pub(super) scalar:Scalar,pub(super) run:Option<u32>,pub(super) text:Option<u32>}',
        'struct PointValue {scalar:Scalar,run:Option<u32>,text:Option<u32>}'),('pub(super) fn values(','fn values(')]:text=text.replace(current,original)
    audit.inverse(text,old[base.VERIFY],'WHOLE_RUN_STYLE_READBACK_BODY_UNCHANGED')
    text=q.text(IDS)
    changes=[('    Hwpml2011TextStyleV9,\n',''),(METHOD,''),
        ('            ProfileKind::Hwpml2011TextStyleV9 => "hwpml-2011-text-style-static/v9",\n',''),
        ('                | ProfileKind::Hwpml2011TextStyleV9\n',''),
        ('            ProfileKind::Hwpml2011TextStyleV9 => {\n                PreservationRuleProfile::Hangul2020PreviewTextV2\n            }\n',''),
        (RULE,''),('        .chain(if matches!(profile.0, ProfileKind::Hwpml2011TextStyleV9) { TEXT_STYLE_REFERENCE_RULES } else { &[] })\n','')]
    for current,original in changes:
        c.require(text.count(current)==(5 if current.startswith('                |')else 1),'ONLY_EXPLICIT_NEW_PROFILE_KIND_METHOD_INHERITANCE_AND_REFERENCE_RULE')
        text=text.replace(current,original)
    audit.inverse(text,old[IDS],'WHOLE_ORIGINAL_V1_TO_V8_ID_ENGINE_AND_RULES_EXACT_INVERSE')
    build=q.text(BUILD).split('pub(super) fn ',1)[1].replace('build<T>','build_artifact<T>').replace('hwpml_2011_text_style_v9()','hwpml_2011_shape_v6()')
    original=q.text('crates/hwpx-package/src/document_import/search/replacement/output.rs').split('pub(super) fn build_artifact',1)[1]
    c.require(build=='build_artifact'+original,'EXACT_ORIGINAL_PRESERVING_BUILD_PIPELINE_EXCEPT_EXPLICIT_PROFILE')
    core=q.text(base.TEXT)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','find_style_for_character_replacement(query,selector,policy,filter,text_character_style)',
        'output::build(','let output=ImportedSourcePackage::import('):c.require(core.count(marker)==1,'ONE_ORIGINAL_IMPORT_MATCH_WRITER_AND_OUTPUT_READBACK')
    previous={p['path']:p for p in failed['source_pins']}
    old_text=q.text(base.TEXT).replace('mod output;\n','').replace('output::build(source,','super::super::super::output::build_artifact(source,')
    audit.inverse(old_text,previous[base.TEXT],'WHOLE_NEW_TEXT_COMPILER_UNCHANGED_EXCEPT_EXPLICIT_OUTPUT_PROFILE')
    audit.inverse(q.text(base.TEXT_RENDER),previous[base.TEXT_RENDER],'WHOLE_TEXT_EDGE_RENDERER_UNCHANGED')
    tests=q.text(base.TEST);original=tests.split('\nfn id_result(',1)[0]
    original=original.replace('assert!(matches!(f.lower_review_selector_text_style_candidate(&raw,query("K"),Scope::Document,all(),filter(),1,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?),Err(E::Compile(Compile::Writer))));',
        'assert!(f.lower_review_selector_text_style_candidate(&raw,query("K"),Scope::Document,all(),filter(),1,Default::default(),WriterLimits::new(WriterLimitConfig {max_output_bytes:1,..Default::default()})?).is_err());')
    audit.inverse(original,previous[base.TEST],'ALL_PREVIOUS_SIXTEEN_CASE_BODIES_EXACT_EXCEPT_STRONGER_WRITER_ERROR_ASSERTION')
    for marker in('CT::CT()','m_uCharStyleIDRef','L"charStyleIDRef"'):c.require(marker in q.text(OFFICIAL),'PINNED_PRIMARY_MODEL_TEXT_ATTRIBUTE_VOCABULARY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_STYLE_ID_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_STYLE_ID_RECOVERY',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_text_style_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(base.prior.OUTPUT);failed=q.json('implementation/p09/evidence/p09-361-text-style-recovery132.v1.json')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='bfcece3d80b9a8cf588ca019744537554c51328f401d165c95f30bb8ce8d5c56'
            and baseline['cleanup']and baseline['new_product_cases']==18,'EXACT_PRIOR_RUN_STYLE_SOURCE_PRODUCT_BASELINE')
        c.require(q.snapshots['implementation/p09/evidence/p09-361-text-style-recovery132.v1.json']['sha256']=='30bf84adfdb437c1c4f7f00cda02813332106f23b9d4a90748c1b1c684f4e08f'
            and failed['cleanup']and sum(s=='ok'for n,s in failed['steps'][0]['tests'])==5
            and RETAINED<={n for n,s in failed['steps'][0]['tests']if s=='ok'},'FIVE_PRIOR_PASSES_FOUR_UNAFFECTED_RETAINED_WRITER_LIMIT_RECHECKED')
        old={p['path']:p for p in baseline['source_pins']}
        for name in names-NEW-CHANGED-{OFFICIAL}:c.require(q.snapshots[name]==old[name],'NO_OTHER_MATCHER_GUARD_PATCH_PRODUCT_FIXTURE_OR_CASE_INPUT_CHANGE')
        inverse(q,old,failed);all_cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST)))
        c.require(len(all_cases)==21,'SIXTEEN_TEXT_STYLE_PLUS_FIVE_NEW_ID_PROFILE_TESTS');cases=all_cases-RETAINED
        c.require(len(cases)==17,'ELEVEN_FAILED_ONE_WRITER_LIMIT_FIVE_PROFILE_CASES_ONLY')
        print(json.dumps(dict(state='TEXT_STYLE_ID_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),cases=17,retained_unaffected=4,one_cpu_mask=4)),flush=True)
        harness.run_one('seventeen_text_style_and_explicit_id_profile_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','text_style_replacement','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,'ORIGINAL_JOB_LIMITS_UNCHANGED')
        c.require(inventory(guard.check)==names,'FINAL_TEXT_STYLE_ID_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_STYLE_SEVENTEEN_CURRENT_FOUR_RETAINED_NOT_STORED_PRODUCT_EFFECTIVE_STYLE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_cases=17,retained_unaffected_cases=4,total_distinct_cases=21,retained_cases_reexecuted=False,original_profiles_v1_to_v8_inverse_verified=True,
            source_model_attribute_not_native_domain_authority=True,next_work='Current_stored_and_strict_product_binding_for_text_style_then_paragraph_named_effective_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_STYLE_ID_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_STYLE_ID_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','safe_error_variants')},
                'warnings':s.get('bounded_output_observation',{}).get('safe_warning_locations',[]),'short_errors':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
