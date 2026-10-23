"""20 paragraph-reference cases plus18 affected definition/selector cases; no product/queue replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_style_product_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-components140.v1.json'
DEFS='crates/hwpx-package/src/document_import/search/inspection/definitions.rs'
MATCHER='crates/hwpx-package/src/document_import/search/reviews/selector/styles.rs';MATCH= MATCHER[:-3]+'/paragraphs.rs'
STYLE='crates/hwpx-package/src/document_import/search/replacement/atoms/styles.rs';CORE=STYLE[:-3]+'/paragraphs.rs';VERIFY=CORE[:-3]+'/verify.rs'
TEXT=STYLE[:-3]+'/text.rs';BUILD=TEXT[:-3]+'/output.rs'
TEST='crates/hwpx-package/tests/document_import_paragraph_style_replacement.rs';TARGET='crates/hwpx-package/tests/paragraph_style_replacement_focused.rs'
NEW={MATCH,CORE,VERIFY,TEST,TARGET};CHANGED={DEFS,MATCHER,STYLE,TEXT,BUILD}
TYPE='''
#[derive(Clone,Copy,Debug,Eq,PartialEq,Deserialize,Serialize)]
#[serde(tag="axis",content="declaration_id",rename_all="snake_case",deny_unknown_fields)]
pub enum SourceParagraphStyleTarget {ParagraphProperty(u32),ParagraphStyle(u32)}
impl SourceParagraphStyleTarget {
    #[must_use] pub const fn declaration_id(self)->u32 {match self {Self::ParagraphProperty(id)|Self::ParagraphStyle(id)=>id}}
    #[must_use] pub const fn attribute(self)->&'static str {match self {Self::ParagraphProperty(_)=>"paraPrIDRef",Self::ParagraphStyle(_)=>"styleIDRef"}}
}
'''
FIELD='    paragraph_declarations:BTreeMap<(CatalogKind,u32),SourceAnchorHandle>,\n'
BUILD_MAPS='''        let mut character_declarations=BTreeMap::new();let mut paragraph_declarations=BTreeMap::new();
        for d in definitions {
            match d.kind {
                CatalogKind::CharacterProperty=>{character_declarations.insert(d.native_id,d.source_anchor);},
                CatalogKind::ParagraphProperty=>{paragraph_declarations.insert((d.kind,d.native_id),d.source_anchor);},
                CatalogKind::NamedStyle if matches!(d.native_attributes.get("type"),Some(PropertyValue::Text(kind))if kind=="PARA")=>{
                    paragraph_declarations.insert((d.kind,d.native_id),d.source_anchor);
                },_=>{}
            }
        }
'''
GETTER='''    pub(in crate::document_import::search) fn paragraph_declaration(&self,target:SourceParagraphStyleTarget)->Result<SourceAnchorHandle,E> {
        let kind=match target {SourceParagraphStyleTarget::ParagraphProperty(_)=>CatalogKind::ParagraphProperty,SourceParagraphStyleTarget::ParagraphStyle(_)=>CatalogKind::NamedStyle};
        self.paragraph_declarations.get(&(kind,target.declaration_id())).cloned().ok_or(E::Definition)
    }
'''


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    text=q.text(DEFS)
    for marker in(TYPE,FIELD,BUILD_MAPS,GETTER):c.require(text.count(marker)==1,'ONLY_EXPLICIT_PARAGRAPH_TARGET_AND_MOVED_TYPED_DECLARATION_INDEX')
    text=text.replace(TYPE,'').replace(FIELD,'').replace(GETTER,'').replace(BUILD_MAPS,
        '        let character_declarations=definitions.into_iter().filter(|d|d.kind==CatalogKind::CharacterProperty).map(|d|(d.native_id,d.source_anchor)).collect();\n')
    text=text.replace('SourceStyleDefinitionIndex {inspection:self,characters,paragraphs,refs,receipt,character_declarations,paragraph_declarations}',
        'SourceStyleDefinitionIndex {inspection:self,characters,paragraphs,refs,receipt,character_declarations}')
    audit.inverse(text,old[DEFS],'WHOLE_ORIGINAL_TYPED_DEFINITION_PREDICATES_RECEIPTS_AND_CHARACTER_LOOKUP_UNCHANGED')
    for name,marker in[(MATCHER,'pub(in crate::document_import::search) mod paragraphs;\n'),(STYLE,'pub mod paragraphs;\n')]:
        text=q.text(name);c.require(text.count(marker)==1,'ONE_ADDITIVE_PARAGRAPH_MODULE_DECLARATION');audit.inverse(text.replace(marker,''),old[name],'WHOLE_ORIGINAL_RUN_TEXT_MATCHER_AND_COMPILER_BODY_UNCHANGED')
    audit.inverse(q.text(TEXT).replace('pub(super) mod output;','mod output;'),old[TEXT],'WHOLE_QUALIFIED_TEXT_COMPILER_BODY_UNCHANGED')
    audit.inverse(q.text(BUILD).replace('pub(in crate::document_import::search::replacement::atoms::styles) fn build','pub(super) fn build'),old[BUILD],
        'WHOLE_QUALIFIED_ID_PROFILE_PATCH_WRITER_PIPELINE_UNCHANGED_EXCEPT_HELPER_VISIBILITY')
    core=q.text(CORE);matcher=q.text(MATCH)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','find_style_for_paragraph_replacement(query,selector,policy,filter,target)',
        'super::text::output::build('):c.require(core.count(marker)==1,'ONE_PROOF_FIELD_REVIEW_INDEX_MATCH_AND_OUTPUT_BUILD_FOR_BATCH')
    c.require(matcher.count('self.resolve_windows(selector,policy)?')==1 and matcher.count('inspection.resolve_style_definitions()?')==1
        and 'selected.windows.clone()'not in matcher and 'Ok((value,declaration,selected.windows))'in matcher,
        'ONE_TYPED_IMPORT_AND_SCOPE_RESOLUTION_WINDOWS_MOVED_NOT_CLONED_OR_RECONSTRUCTED')
    c.require('IncompleteParagraphScope'in core and 'whole_paragraph_scope_verified:true'in core
        and 'guard.blocked(xml,i)?'in core and 'ranges.get(j).is_some_and(|(a,_)|*a<span.end())'in core
        and 'context.readback_receipt(review.receipt())'in q.text(VERIFY),'WHOLE_PARAGRAPH_SCOPE_DESCENDANT_FIELDS_PROTECTION_AND_OUTPUT_BOUNDARY')


def expected(q):
    cases=set()
    for module,file,count in[('paragraph_style','document_import_paragraph_style_replacement',20),('definitions','document_import_search_definitions',10),('selector_styles','document_import_selector_styles',8)]:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+file+'.rs'))
        c.require(len(names)==len(set(names))==count,'EXACT_TWENTY_NEW_AND_EIGHTEEN_AFFECTED_ORIGINAL_TEST_IDENTITIES');cases.update(module+'::'+n for n in names)
    return cases


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PARAGRAPH_STYLE_IMMUTABLE_RUN_EXISTS')
    selection=prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PARAGRAPH_STYLE_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_paragraph_style_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='29718112cc55901e2d8e694f918cc20ba9aad78def2137f9d4eb7226bddf089a'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['new_product_cases']==18
            and previous['fresh_inputs']==previous['final_fresh_hashes']==619,'EXACT_TEXT_SOURCE_AND_PRODUCT_BASELINE')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.base.prior.base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_PARAGRAPH_SOURCE_MODULES_AND_TWO_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_GUARD_PATCH_PRODUCT_FIXTURE_OR_PRIOR_TEST_INPUT_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='PARAGRAPH_STYLE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=20,affected_original_cases=18,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_paragraph_style_and_eighteen_affected_original_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','paragraph_style_replacement_focused','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,'ORIGINAL_ONE_CPU2_HARD_CAP_AND_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_PARAGRAPH_STYLE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_PARAGRAPH_STYLE_TWENTY_NEW_EIGHTEEN_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_paragraph_style_cases=20,affected_original_cases=18,total_executed_cases=38,previous_product_and_unrelated_cases_reexecuted=False,
            original_common_code_and_test_bodies_inverse_verified=True,target_anchor_from_same_typed_catalog=True,exact_selected_windows_moved_without_repeat_resolution=True,
            next_work='Current_stored_and_strict_product_binding_for_paragraph_axes_then_effective_style_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PARAGRAPH_STYLE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PARAGRAPH_STYLE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','closed_compile_error_variants','closed_static_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
