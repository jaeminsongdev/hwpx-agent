"""Six selector-core +10 product cases and17 original navigation cases, two serial bounded Jobs."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_selector_product_components as prior
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-selector-navigation-components101.v1.json'
CORE='crates/hwpx-package/src/document_import/search/selector.rs'
REVIEW='crates/hwpx-package/src/document_import/search/reviews/selector.rs'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/source_search/'
NAV=SERVICE+'navigation.rs';SCOPE=SERVICE+'selector.rs';REVIEW_SCOPE=SERVICE+'review_selector.rs'
PRODUCT_NAV='crates/product-cli/src/form_product_request/stored_source_search/navigation.rs'
CORE_TEST='crates/hwpx-package/tests/document_import_selector_navigation.rs'
CORE_BUNDLE='crates/hwpx-package/tests/selector_navigation_bundle.rs'
OLD_CORE='crates/hwpx-package/tests/document_import_search_navigation.rs'
TARGET='crates/product-cli/tests/selector_navigation_product.rs'
WRAPPER='crates/product-cli/tests/selector_navigation_product/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/selector_navigation_product.rs'
OLD_PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/source_search_navigation.rs'
NEW={CORE_TEST,CORE_BUNDLE,TARGET,WRAPPER,TEST}
CHANGED={CORE,REVIEW,NAV,SCOPE,REVIEW_SCOPE,PRODUCT_NAV,prior.SELECTOR,prior.SEARCH}


def inventory(check):return prior.inventory(check)|{CORE_TEST,CORE_BUNDLE,TARGET,WRAPPER}


def inverse(q,old):
    for name,owner in((CORE,'SourceSelectorSearchResult'),(REVIEW,'SourceReviewSelectorResult')):
        text=q.text(name);start=text.index('impl '+owner+' {\n')+len('impl '+owner+' {\n');end=text.index('    #[must_use]',start);extra=text[start:end]
        c.require(extra.count('pub fn navigate')==1 and extra.count('navigation::navigate(self,navigation::Occurrences::Text(')==1,'ONE_THIN_ORIGINAL_ENGINE_SELECTOR_WRAPPER')
        audit.inverse(text[:start]+text[end:],old[name],'WHOLE_ORIGINAL_SELECTOR_FIND_WINDOWS_POLICIES_AND_RECEIPTS_UNCHANGED')
    for name,owner,data in((SCOPE,'ScopeResult','ScopeData'),(REVIEW_SCOPE,'ReviewScopeResult','ReviewScopeData')):
        text=q.text(name);addition='use hwpx_package::document_import::search::navigation as source_navigation;\n'
        c.require(text.count(addition)==1,'ONLY_EXPLICIT_PUBLIC_CORE_NAVIGATION_TYPE_IMPORT');text=text.replace(addition,'')
        start=text.index('impl '+owner+' {\n')+len('impl '+owner+' {\n');end=text.index('    pub(super) fn index',start);extra=text[start:end]
        c.require(extra.count('pub(super) fn navigate')==1 and f'{data}::Inventory(_)=>Err(SourceSearchError::Cursor)'in extra
            and f'{data}::Find(r)=>r.navigate(request,context)'in extra,'SEARCH_ONLY_RETAINED_RESULT_DISPATCH_WITH_INVENTORY_DENIED')
        audit.inverse(text[:start]+text[end:],old[name],'WHOLE_ORIGINAL_SCOPE_PREPARE_AND_SEALED_SOURCE_BOUNDARY_UNCHANGED')
    text=q.text(NAV)
    for current,previous in((',Self::Scope(r)=>r.navigate(request,context)',',Self::Scope(_)=>Err(SourceSearchError::Cursor)'),
        (',Self::ReviewScope(r)=>r.navigate(request,context)',',Self::ReviewScope(_)=>Err(SourceSearchError::Cursor)')):
        c.require(text.count(current)==1,'ONLY_NEW_SCOPE_VARIANT_NAVIGATION_ROUTING');text=text.replace(current,previous)
    audit.inverse(text,old[NAV],'WHOLE_ORIGINAL_FRESH_JSON_SOURCE_VERIFY_AND_FINAL_HEAD_CALLBACK_BODY_UNCHANGED')
    text=q.text(PRODUCT_NAV);start=text.index('pub(super) fn receipt_context(');end=text.index('impl PreparedStoredSourceSearchProduct',start);extra=text[start:end]
    c.require('let request=NextRequest::parse(raw)?;let context=receipt_context(receipt)?;'in extra and
        'if request.search_receipt_sha256!=hex::encode(context){return Err(E::Binding);}'in extra,'STRICT_ORIGINAL_NEXT_PARSER_AND_CONTEXT_BEFORE_ANY_SOURCE_READ')
    audit.inverse(text[:start]+text[end:],old[PRODUCT_NAV],'WHOLE_V1_V4_NEXT_PARSER_CONTEXT_AUTH_AND_CALLBACK_BODY_UNCHANGED')
    for name,owner,base in((prior.SELECTOR,'PreparedStoredSourceScopeProduct','self.request'),(prior.SEARCH,'PreparedStoredReviewScopeProduct','self.request.base')):
        text=q.text(name);start=text.index('impl '+owner+' {\n')+len('impl '+owner+' {\n');end=text.index('    #[must_use]',start);extra=text[start:end]
        c.require(extra.count('pub fn navigation_receipt_sha256')==1 and extra.count('pub fn with_next_verified_json')==1
            and extra.count(base+'.operation.query().is_none()')==2 and 'self.check(provider)?;'in extra
            and 'self.candidate.with_next_verified_json(provider,&request,context,now,consume)'in extra,'TYPED_FIND_ONLY_CONTINUATION_WITH_ORIGINAL_PRODUCT_AND_STORED_AUTH_CHECKS')
        audit.inverse(text[:start]+text[end:],old[name],'WHOLE_ORIGINAL_V5_V6_PARSER_PREPARE_RECEIPT_VERIFY_AND_OUTPUT_UNCHANGED')


def cases(q,path,prefix):return {prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))}


def expected(q):
    groups=[cases(q,CORE_TEST,'selector_navigation::'),cases(q,OLD_CORE,'legacy_navigation::'),
        cases(q,TEST,'actual_import::selector_navigation_product::'),cases(q,OLD_PRODUCT,'actual_import::source_search_navigation::')]
    c.require(tuple(map(len,groups))==(6,10,10,7),'EXACT_SIX_TEN_TEN_SEVEN_NAVIGATION_IDENTITIES')
    return groups[0]|groups[1],groups[2]|groups[3]


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_NAVIGATION_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_NAVIGATION_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_selector_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='592c485efebf36cdb45431215b18c4b9de7d55087c1a98004aa2f38af97e136f'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==36 and previous['cleanup'],'EXACT_PREVIOUS_THIRTY_SIX_PRODUCT_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.prior.base.prior.base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_FIVE_NEW_CORE_AND_PRODUCT_NAVIGATION_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'MATCHER_SELECTOR_WRITER_NAV_ENGINE_AUTH_AND_OLD_TEST_BODIES_UNCHANGED')
        inverse(q,old);core,product=expected(q)
        print(json.dumps(dict(state='SELECTOR_NAVIGATION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_core_cases=6,new_product_cases=10,affected_cases=17,serial_test_binaries=2)),flush=True)
        env=audit.environment();observe=prior.prior.prior.base.base.prior.prior.snapshot
        harness.run_one('six_new_selector_ten_original_core_navigation',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','selector_navigation_bundle','--','--test-threads=1'],core,guard,env,row,observe_capture=observe)
        harness.run_one('ten_selector_products_seven_original_product_navigation',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','selector_navigation_product','--','--test-threads=1'],product,guard,env,row,observe_capture=observe)
        c.require(inventory(guard.check)==names,'FINAL_SELECTOR_NAVIGATION_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_NAVIGATION_SIX_CORE_TEN_PRODUCT_SEVENTEEN_AFFECTED_NOT_FULL_SELECTOR_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=6,new_product_cases=10,affected_cases=17,total_executed_cases=33,
            previous_fifty_two_core_sixty_one_stored_thirty_six_product_cases_reexecuted=False,original_navigation_engine_parsers_current_authorization_and_final_consumer_preserved=True,
            selector_and_policy_bound_cursor_without_query_reexecution=True,original_full_result_serialization_and_fresh_checks_retained=True,
            inventory_navigation_rejected_before_source_access=True,next_work='Selector_style_and_control_filter_combinations_and_full_search_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_NAVIGATION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_NAVIGATION_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
