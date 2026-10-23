"""Original review-body text search: fixed new/affected tests, never Native or queue replay."""
import hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared,c,a=harness.shared,harness.c,harness.a
OUTPUT='implementation/p09/evidence/p09-361-search-review-text-components056.v1.json'
PRIOR='implementation/p09/evidence/p09-361-search-definition-recovery054.v1.json'
PRIOR_SHA='5045862a5e3285136f8e3fdb9e9f2fd84139258e46cf31abe78207588a579766'
TEST='crates/hwpx-package/tests/document_import_search_review_text.rs'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'
CORE='crates/hwpx-package/src/document_import/search.rs'
EXTRACT='crates/hwpx-package/src/document_import/search/extract.rs'
RETAINED=('document_import_search','document_import_search_scope','document_import_search_inspection','document_import_search_definitions')
HEADER='crates/hwpx-package/src/hancom_2020_minimal_header.xml'
MODELS=tuple('fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/'+p
    for p in ('Para/hiddenComment.cpp','Head/StyleType.cpp','Head/CharShapeType.cpp'))
NEW={TEST,'crates/hwpx-package/src/document_import/search/reviews.rs','crates/hwpx-package/tests/support/search_review_fixture.rs'}
CHANGED={CORE,EXTRACT,PRODUCT,'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
    'crates/product-cli/src/form_product_request/stored_source_search.rs'}
TARGETED={'literal_crosses_runs_and_entities_with_exact_decoded_scalar_provenance',
    'hangul_jamo_composes_across_three_runs_without_losing_original_locations',
    'opaque_content_and_unmapped_paragraphs_are_barriers_not_silently_searchable_text',
    'mapped_note_paragraphs_are_searchable_without_crossing_the_note_control'}


def inverse(text,pin,label):
    candidates=(text.encode(),text.replace('\n','\r\n').encode())
    c.require(any(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']for raw in candidates),label)


def original_core_inverse(q,old):
    text=q.text(CORE)
    for addition in ('pub mod reviews;\n','    #[error("SOURCE_SEARCH_REVIEW_BODY_REJECTED")] Review,\n'):
        c.require(text.count(addition)==1,'ONE_ADDITIVE_REVIEW_DECLARATION');text=text.replace(addition,'')
    for current,original in (('(self.receipt.profile,query)','(SOURCE_SEARCH_PROFILE,query)'),
        ('SourceSearchResult {profile:self.receipt.profile,','SourceSearchResult {profile:SOURCE_SEARCH_PROFILE,')):
        c.require(text.count(current)==1,'ONLY_PROFILE_SPECIFIC_RESULT_IDENTITY');text=text.replace(current,original)
    inverse(text,old[CORE],'ORIGINAL_MATCHER_BODY_EXACT_INVERSE')
    text=q.text(EXTRACT)
    replacements=(
        ('pub(super) fn paragraphs(','fn paragraphs('),
        ("    build_extended(original,limits,None)\n}\npub(super) fn build_extended<'a>(original:&'a ImportedDocumentStructure,limits:SourceSearchLimits,\n    review:Option<&reviews::ReviewProjection>)->Result<SourceTextIndex<'a>,E> {\n",''),
        ('    if let Some(review)=review {for id in review.regions.keys() {\n        if !wanted.insert(id.clone()){return Err(E::Mapping);}if wanted.len()>cap.paragraphs{return Err(E::Limit);}\n    }}\n',''),
        ('profile:if review.is_some(){reviews::REVIEW_TEXT_INDEX_PROFILE}else{SOURCE_SEARCH_PROFILE},','profile:SOURCE_SEARCH_PROFILE,'),
        ('    if review.is_some(){reviews::order_source_blocks(&mut index)?;}\n',''),
        ('hash.update(index.receipt.profile.as_bytes());','hash.update(SOURCE_SEARCH_PROFILE.as_bytes());'),
        ('    if let Some(review)=review {hash.update(review.binding_sha256(limits.0.result_bytes)?);}\n',''))
    for current,original in replacements:
        c.require(text.count(current)==1,'ONE_EXPLICIT_REVIEW_EXTRACT_EXTENSION');text=text.replace(current,original)
    inverse(text,old[EXTRACT],'ORIGINAL_NONE_EXTRACTION_ORDER_AND_HASH_EXACT_INVERSE')


def inventory(check):
    return shared.source_inventory(check)|{TEST,HEADER}|{'crates/hwpx-package/tests/'+n+'.rs'for n in RETAINED}|set(MODELS)


def environment():
    return dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),CARGO_PROFILE_TEST_OPT_LEVEL='0',
        CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
        CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',
        CARGO_PROFILE_TEST_CODEGEN_UNITS='16',CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_TEXT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_REVIEW_TEXT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_cascade_visibility_or_search_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        prior=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']==PRIOR_SHA and prior['state'].startswith('PASS_')and prior['cleanup'],'EXACT_PRIOR_STYLE_DEFINITION_PASS')
        old={p['path']:p for p in prior['source_pins']};prior_names={n for n in old if n.startswith('crates/')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(names-set(MODELS)==prior_names|NEW,'EXACT_REVIEW_SOURCE_INVENTORY_EXTENSION')
        for name in names-set(MODELS)-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_UNRELATED_SOURCE_TEST_OR_HEADER_CHANGE')
        original_core_inverse(q,old)
        prefix=q.text(PRODUCT).split('// Additive v4 review-text cases;',1)[0]
        c.require(prefix.endswith('\n\n'),'ONE_APPENDED_REVIEW_TEST_SEPARATOR');inverse(prefix[:-1],old[PRODUCT],'ORIGINAL_TWENTY_PRODUCT_BODIES_UNCHANGED')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        product={'actual_import::source_search::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT))}
        base=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/document_import_search.rs')))
        c.require(len(core)==8 and len(product)==26 and TARGETED<=base and len(TARGETED)==4,'EXACT_EIGHT_NEW_CORE_FOUR_TARGETED_TWENTY_SIX_PRODUCT')
        c.require(len(prior['steps'][1]['tests'])==20 and all(s=='ok'for n,s in prior['steps'][1]['tests'])
            and {n for n,s in prior['steps'][1]['tests']}<product,'PRESERVED_PRIOR_TWENTY_PRODUCT_PASS_IDENTITIES')
        env=environment();common=[harness.CARGO,'test','--offline','--locked','-j','1']
        print(json.dumps(dict(state='REVIEW_TEXT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=14,affected_cases=24)),flush=True)
        harness.run_one('eight_new_original_review_text_cases',common+['-p','hwpx-package','--test','document_import_search_review_text','--','--test-threads=1'],core,guard,env,row)
        harness.run_one('four_targeted_original_extraction_cases',common+['-p','hwpx-package','--test','document_import_search','--',*sorted(TARGETED),'--exact','--test-threads=1'],TARGETED,guard,env,row)
        harness.run_one('six_new_v4_and_twenty_affected_product_cases',common+['-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(product),'--exact','--test-threads=1'],product,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_REVIEW_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_ORIGINAL_REVIEW_TEXT_EIGHT_CORE_FOUR_TARGETED_TWENTY_SIX_PRODUCT_NOT_APP_VISIBILITY_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=8,new_product_cases=6,
            affected_core_cases=4,affected_product_cases=20,total_executed_cases=38,unrelated_stored_suites_reexecuted=False,
            original_matcher_and_none_extraction_inverse_verified=True,original_twenty_product_bodies_unchanged=True,
            caller_review_graph_required=False,source_body_policy_explicit=True,exclusions_applied_before_match_limits=True,
            source_order_not_native_layout=True,command_line_or_server_route_added=False,idempotency_key_claimed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_TEXT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
