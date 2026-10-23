"""421: actual v13 heading API/CLI integration; new7 + affected70 + stored3, no Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_source_heading_targets as first
import run_source_heading_targets_test_recovery as prior

OUTPUT='implementation/p09/evidence/p09-361-reference-source-heading-api421.v1.json'
DRIVER='tools/p09/run_reference_source_heading_api.py'
ROOT_TEST='crates/product-cli/tests/reference_source_product.rs'
NEW_TEST='crates/product-cli/tests/reference_source_product/heading_targets.rs'
LINK='mod source_heading_targets {include!("reference_source_product/heading_targets.rs");}\n'
OBSERVED_PREIMAGES={
ROOT_TEST:(59487,'475e06f890cef9a9f9156b6546ed20fc74d3bcc2a2cf5b426c71789446fe44c7'),
'crates/product-cli/tests/reference_source_product/caption_state.rs':(9665,'7e20bfe191e86e2aeb85111047ebf40c0a029f611ca7cdf91d50b835b239cd6d'),
'crates/product-cli/tests/reference_source_product/note_selection.rs':(8163,'8338c3cc08bd50309d46a656f4396854a5a46c2458459cfc17cb7ed2b9b53bc7'),
'crates/product-cli/tests/reference_source_product/note_style_selection.rs':(9265,'d137ce3efd9c7b5659ef7b937f2fed2f1224d4d779f70822369c60d5c7f49a27'),
'crates/product-cli/tests/form_stored_provider/actual_import/source_note_style.rs':(27044,'2011907255bab692ede666092b2e66e6cc558c52dd8ee52c13173debddf26b18'),
'crates/product-cli/tests/form_stored_provider/actual_import/source_note_file_request.rs':(21770,'6266a460fa1625f47faaa373a8e15d03e7554fa17c82f7c9f4f75a02bacba9f2'),
'crates/product-cli/tests/form_stored_provider/actual_import/source_note_conversion.rs':(23841,'8d012bf82ddd79c4beaa3a0d02b6649bb806b7c51ae9e784aa04f3a39e5d4504'),
}
PARTS={ROOT_TEST:'',
'crates/product-cli/tests/reference_source_product/caption_state.rs':'joined_caption_state::',
'crates/product-cli/tests/reference_source_product/note_selection.rs':'source_note_selection::',
'crates/product-cli/tests/reference_source_product/note_style_selection.rs':'source_note_style_selection::',
NEW_TEST:'source_heading_targets::'}
STORED={
'actual_import::source_note_style::stored_note_style_v12_api_json_alone_builds_requests_and_rejects_foreign_stale_tampered_or_revoked_access',
'actual_import::source_note_file_request::note_file_product_api_source_json_prepares_owned_files_for_all_families_without_caller_import_or_commit',
'actual_import::source_note_conversion::stored_note_kind_reference_source_api_json_builds_requests_and_rejects_foreign_stale_or_revoked_access'}
CHANGED={first.CORE,first.TEST,first.SOURCE_API}|set(OBSERVED_PREIMAGES)
CORE_ADDITION='''    /// # Errors
    /// An unobserved header declaration model is unavailable, not an empty native heading inventory.
    /// Any actual HH heading marker invokes the strict whole-source importer; errors are never swallowed.
    pub fn for_partial_source_assessment(source:&'a ImportedDocumentStructure,limits:ReferenceAuxiliaryLimits)->Result<Option<Self>,E>{
        if source.source().parts().iter().filter_map(|p|p.xml()).any(|xml|xml.elements().iter().any(|e|named(e,HH,"heading"))){
            Ok(Some(Self::import(source,limits)?))
        }else{Ok(None)}
    }
'''
API_ADDITIONS=(
'    reference_targets::headings::{ImportedReferenceHeadingTargets,ReferenceHeadingTargetReceipt},\n',
'    // None is an unobserved header declaration model, not a confirmed empty heading inventory.\n    heading_target_import: Option<ReferenceHeadingTargetReceipt>,\n',
'    #[must_use]\n    pub const fn heading_target_receipt(&self) -> Option<&ReferenceHeadingTargetReceipt> { self.heading_target_import.as_ref() }\n',
'''        let headings=ImportedReferenceHeadingTargets::for_partial_source_assessment(structure,reference_limits).map_err(|error|match error{
            ReferenceTargetImportError::Limit=>ReferenceSourceError::InputLimit,
            ReferenceTargetImportError::Coverage=>ReferenceSourceError::Coverage,
            _=>ReferenceSourceError::Binding,
        })?;
        if let Some(heading)=&headings{
            targets.try_reserve(heading.targets().len()).map_err(|_|ReferenceSourceError::InputLimit)?;
            targets.extend_from_slice(heading.targets());
        }
''',
'            heading_target_import: headings.as_ref().map(|h|h.receipt().clone()),\n')


def cases(text,prefix=''):
    r.c.require('#[ignore]'not in text,'NO_IGNORED_HEADING_API_CASES')
    return {prefix+n for n in re.findall(r'#\[test\]\s*fn\s+(\w+)',text)}


def check_inverse(q,old):
    c=r.c;text=q.text(first.CORE);c.require(text.count(CORE_ADDITION)==1,'ONE_ADDITIVE_PARTIAL_ASSESSMENT_ADAPTER')
    r.audit.inverse(text.replace(CORE_ADDITION,''),old[first.CORE],'STRICT_CORE_PRODUCTION_BODY_UNCHANGED')
    text=q.text(first.TEST);marker='\n#[test]\nfn partial_assessment_legacy_header_is_unavailable_not_confirmed_empty'
    c.require(text.count(marker)==1,'ONE_APPENDED_SEVEN_CASE_SECTION');original,addition=text.split(marker)
    r.audit.inverse(original,old[first.TEST],'ALL_ORIGINAL22_CORE_TEST_BODIES_AND_HELPERS_PRESERVED')
    c.require(len(cases('#[test]\nfn partial_assessment_legacy_header_is_unavailable_not_confirmed_empty'+addition))==7,'ONLY_NEW_SEVEN_ADAPTER_CASES')
    text=q.text(first.SOURCE_API)
    for addition in API_ADDITIONS:c.require(text.count(addition)==1,'ONE_DECLARED_ADDITIVE_API_CHANGE');text=text.replace(addition,'')
    r.audit.inverse(text.replace('reference-source-assessment/v13','reference-source-assessment/v12'),old[first.SOURCE_API],
        'ALL_EXISTING_ASSESSMENT_STAGES_LIMITS_AND_FOUR_UNRESOLVED_STAGES_UNCHANGED')
    for path,(size,sha)in OBSERVED_PREIMAGES.items():
        text=q.text(path)
        if path==ROOT_TEST:c.require(text.count(LINK)==1,'ONE_NEW_API_TEST_CHILD');text=text.replace(LINK,'')
        r.audit.inverse(text.replace('reference-source-assessment/v13','reference-source-assessment/v12'),dict(bytes=size,sha256=sha),
            'ONLY_SCHEMA_EXPECTATION_CHANGED_EXISTING_TEST_BODIES_PRESERVED')


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HEADING421_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_REFERENCE_SOURCE_HEADING_API421',steps=[],own_cpu_selection=selection,
        source_API_schema='hwpx-agent.product.reference-source-assessment/v13',source_API_unresolved_stages_cleared=False,
        unrelated_successes_replayed=False,strict_core_prior24_replayed=False,actual_DB_Hangul_or_COM_started=False,
        Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,native_number_or_navigation_qualified=False,
        effective_style_cascade_qualified=False,complete_reference_state_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=r.compact.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='043c89e1851288f08a676cbec4dafa6b6860b8a923b53844b70db09d7a72e57f'
            and base['cleanup']is True and base['current_distinct_cases']==24 and base['fresh_inputs']==base['final_fresh_hashes']==789,
            'EXACT420_STRICT_HEADING_CORE24_AND_SOURCE_CLOSURE')
        old={p['path']:p for p in base['source_pins']}
        extra={DRIVER,NEW_TEST,'crates/product-cli/tests/form_stored_provider.rs','crates/product-cli/tests/form_stored_provider/actual_import.rs',
            'crates/hwpx-package/tests/support/document_import_field_fixture.rs','crates/hwpx-package/tests/support/document_import_bookmark_fixture.rs'}
        for path in sorted(set(old)|r.closure.inventory(guard.check)|extra|CHANGED):
            pin=q.pin(path)
            if path in old and path not in CHANGED:c.require(pin==old[path],'ALL_OTHER_PRODUCT_SOURCE_RUNTIME_MODELS_AND_GUARDS_UNCHANGED')
        check_inverse(q,old)
        core={n for n in cases(q.text(first.TEST),'source_headings::')if n.startswith('source_headings::partial_assessment_')}
        api=set()
        for path,prefix in PARTS.items():api.update(cases(q.text(path),prefix))
        c.require(len(core)==7 and len(api)==70 and len(cases(q.text(NEW_TEST)))==13,'EXACT_NEW7_NEW_API13_AFFECTED_API57')
        for full in STORED:
            module,name=full.removeprefix('actual_import::').split('::')
            c.require(name in cases(q.text('crates/product-cli/tests/form_stored_provider/actual_import/'+module+'.rs')),'EXACT_THREE_STORED_V13_JSON_JOIN_CASES')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch=c.ROOT/'target/p09-reference-source-heading-api-scratch-421'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING421_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='HEADING421_PREFLIGHT',inputs=len(q.snapshots),core_new=7,API_new=13,API_affected=57,stored_affected=3)),flush=True)
        commands=[('only_new_heading_adapter7','hwpx-package','document_import_reference_targets',core,True),
            ('actual_v13_reference_source_API_CLI70','hwpx-agent-cli','reference_source_product',api,False),
            ('only_affected_stored_v13_API_joins3','hwpx-agent-cli','form_stored_provider',STORED,True)]
        for label,package,test,expected,filtered in commands:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',test,'--message-format=short','--']
            if filtered:args.extend(sorted(expected))
            args.append('--test-threads=1')
            r.harness.run_one(label,args,expected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],expected);c.require(row['steps'][-1]['diagnostics']==[],'HEADING_V13_CASES_NO_WARNINGS')
            print(json.dumps(dict(state='HEADING421_STEP_PASS',stage=label,cases=len(expected))),flush=True)
        c.require(not any(scratch.iterdir()),'HEADING421_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCE_SOURCE_HEADING_V13_CORE7_API70_STORED3_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=20,affected_cases=60,current_distinct_cases=80,last_executed_cases=80,
            observed_test_preimage_pins=[dict(path=p,bytes=n,sha256=s)for p,(n,s)in OBSERVED_PREIMAGES.items()],
            test_preimage_origin='observed_before_version_only_edit_not_historical_test_acceptance',
            next_work='effective_heading_style_cascade_and_complete_reference_stage_implementation_requiring_source_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'HEADING421_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
