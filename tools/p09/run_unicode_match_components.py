"""18 match-normalization cases plus24 affected scope cases, not57 old suites/150 products."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_product_components as prior
base=prior.base
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-match-components163.v1.json'
CORE=base.CORE;PLAN=base.PLAN;SELECTOR=base.SELECTOR
MATCHES=CORE[:-3]+'/matches.rs';TEST='crates/hwpx-package/tests/document_import_unicode_match_normalization.rs'
BUNDLE='crates/hwpx-package/tests/unicode_match_normalization_focused.rs'
NEW={MATCHES,TEST,BUNDLE};CHANGED={CORE,PLAN,SELECTOR}
EXCLUSIONS='''    pub(in crate::document_import::search) const fn transformation_exclusions(&self)->(usize,usize) {
        (self.excluded_hidden_paragraphs,self.excluded_memo_paragraphs)
    }
'''
PLAN_EXTRACTION='''    compile_selected(index,fields,context,groups,selected,form)
}
pub(super) fn compile_found<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    found:&crate::document_import::search::SourceSearchResult,form:SourceUnicodeNormalizationForm)->Result<Plan<'a>,E> {
    if found.matches().is_empty(){return Err(E::NoMatches);}
    let mut selected=BTreeSet::new();let mut groups=Vec::new();
    for m in found.matches() {
        let origins=selected_origins(index,m)?;
        for &origin in &origins {if !selected.insert(origin){return Err(E::Selection);}}
        // Each match is a separate normalization group, even when matches are adjacent.
        groups.push(origins.into_iter().collect());
    }compile_selected(index,fields,context,groups,selected,form)
}
fn compile_selected<'a>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    groups:Vec<Vec<usize>>,selected:BTreeSet<usize>,form:SourceUnicodeNormalizationForm)->Result<Plan<'a>,E> {
    let source=index.original.source();
'''


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    for name,marker in[(CORE,'pub mod matches;\n'),(SELECTOR,EXCLUSIONS)]:
        text=q.text(name);c.require(text.count(marker)==1,'ONE_ADDITIVE_MATCH_NORMALIZATION_MODULE_OR_EXCLUSION_ACCESSOR')
        audit.inverse(text.replace(marker,''),old[name],'WHOLE_ORIGINAL_SCOPE_RECEIPT_HASH_SHAPE_MATCHER_AND_CURRENT_PRODUCT_CORE_BODY_UNCHANGED')
    text=q.text(PLAN);c.require(text.count(PLAN_EXTRACTION)==1,'ONE_SHARED_ORIGINAL_COMPONENT_COMPILER_EXTRACTION')
    text=text.replace(PLAN_EXTRACTION,'');new='    let mut selected=BTreeSet::new();let mut groups=Vec::new();\n'
    c.require(text.count(new)==1,'ONE_ORIGINAL_SCOPE_SELECTION_RETAINED')
    text=text.replace(new,'    let source=index.original.source();let mut selected=BTreeSet::new();let mut groups=Vec::new();\n')
    audit.inverse(text,old[PLAN],'EXACT_WHOLE_ORIGINAL_SCOPE_GUARDS_PROVENANCE_NORMALIZER_PATCH_PLAN_AND_LIMITS_RECONSTRUCTED')
    match=q.text(MATCHES)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','plan::compile_found(','styles::text::output::build(','readback::verify_artifact('):
        c.require(match.count(marker)==1,'ONE_PROOF_FIELDS_REVIEW_INDEX_PLAN_WRITER_AND_OUTPUT_IMPORT')
    c.require(match.count('index.find_style(query,selector,policy,filter)')==1 and match.count('index.find(query,selector,policy)')==1
        and 'if let Some(filter)=filter'in match and 'SourceUnicodeMatchSearch::Text'in match,'EXCLUSIVE_SINGLE_MATCHER_BRANCH_NOT_TWO_SEARCH_PASSES')


def expected(q):
    result=set()
    for name,module,count in[(TEST,'matches',18),(base.TEST,'scope',24)]:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name));c.require(len(names)==len(set(names))==count,'EXACT18_NEW_AND24_AFFECTED_SCOPE_CASE_IDENTITIES')
        result.update(module+'::'+n for n in names)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_MATCH_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_MATCH_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,match_normalization_stored_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='1e3606982c37b493d59756f55daca0e7b029439fcaa3f4734881a43525b537af'
            and baseline['state']=='PASS_UNICODE_TWENTY_SCOPE_PRODUCTS_NOT_QUERY_FILTER_FULL_TRANSACTION_NATIVE_OR_GATE'
            and baseline['cleanup']and baseline['fresh_inputs']==baseline['final_fresh_hashes']==657 and baseline['new_product_cases']==20,'EXACT_PRIOR20_SCOPE_PRODUCTS_WITH81_SOURCE_RETAINED')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'MATCH_NORMALIZATION_FILES_ARE_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SOURCE_MATCHERS_GUARDS_WRITERS_PRODUCTS_FIXTURES_AND_TESTS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='UNICODE_MATCH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,affected_scope_cases=24,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_match_and_twenty_four_affected_scope_normalization_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','unicode_match_normalization_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        base.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_UNICODE_MATCH_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_MATCH18_SCOPE24_NOT_MATCH_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=18,affected_scope_cases=24,total_executed_cases=42,unrelated57_source_and150_products_reexecuted=False,
            original_scope_body_and_all_other_matcher_product_inputs_inverse_verified=True,single_matcher_exact_original_groups_and_no_scope_widening=True,
            next_work='Current_stored_service_and_strict_match_normalization_product_request_then_remaining_full_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_MATCH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_MATCH_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
