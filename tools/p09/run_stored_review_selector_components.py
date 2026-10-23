"""Twelve new stored selector cases +49 affected source/product cases in one bounded Job."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_review_selector_recovery as prior
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-stored-review-selector-components097.v1.json'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
NAV=SERVICE[:-3]+'/navigation.rs'
SEARCH=SERVICE[:-3]+'/review_selector.rs'
REVIEW='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/atoms/review.rs'
LITERAL=REVIEW[:-3]+'/selector.rs'
TARGET='crates/product-cli/tests/review_selector_stored.rs'
WRAPPER='crates/product-cli/tests/review_selector_stored/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/review_selector_stored.rs'
NEW={SEARCH,LITERAL,TARGET,WRAPPER,TEST}
CHANGED={SERVICE,NAV,REVIEW}
MODULES=('review_selector_stored','source_scope_product','source_search','source_search_navigation','review_literal_output')


def inventory(check):return prior.prior.inventory(check)|{TARGET,WRAPPER}


def method(text,name):
    match=re.search(r'(?m)^    (?:pub(?:\(crate\))? )?fn '+name+r'[<(]',text)
    c.require(match is not None,'STORED_BOUNDARY_METHOD_PRESENT')
    start=text.index('\n',text.index('    where ',match.start()))+1;end=text.index('\n    }',start)
    return text[start:end]


def inverse(q,old):
    text=q.text(SERVICE)
    for addition in('pub mod review_selector;\n',',ReviewScope(review_selector::ReviewScopeResult)',',Self::ReviewScope(r)=>r.index()',
        ',Self::ReviewScope(r)=>&r.scope',',Self::ReviewScope(r)=>r.request_sha',',Self::ReviewScope(r)=>r.json()',',Self::ReviewScope(_)=>"hwpx-agent.stored-source-search/v6"'):
        c.require(text.count(addition)==1,'ONLY_NEW_PRIVATE_REVIEW_SCOPE_VARIANT_AND_ACCESSORS');text=text.replace(addition,'')
    audit.inverse(text,old[SERVICE],'ORIGINAL_SEARCH_FINISH_FRESH_JSON_AND_FINAL_HEAD_WHOLE_FILE_EXACT_INVERSE')
    for name,addition in((NAV,',Self::ReviewScope(_)=>Err(SourceSearchError::Cursor)'),(REVIEW,'pub mod selector;\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ONE_ADDITIVE_REVIEW_PROFILE_MODULE_OR_DENIED_CURSOR')
        audit.inverse(text.replace(addition,''),old[name],'OLD_NAVIGATION_AND_V3_PREPARE_FRESH_OUTPUT_BODIES_EXACT_INVERSE')
    legacy=q.text(REVIEW);current=q.text(LITERAL)
    for name in('verify','with_verified_bytes'):
        c.require(method(current,name)==method(legacy,name),'SAME_ORIGINAL_WRITER_INTEGRITY_AND_FINAL_CONSUMER_HEAD_BODY')
    body=method(current,'prepare_review_selector_literal_candidate')
    for new,previous in(('let(fresh,proof)','let (fresh,proof)'),('lower_review_selector_literal_candidate','lower_review_literal_candidate'),
        ('query,selector,policy','query,scope,policy'),('output.receipt().body_candidate.output.source_package_sha256','output.receipt().output.source_package_sha256'),
        ('StoredSelectorLiteralReceipt','StoredReviewLiteralReceipt'),('hwpx-agent.stored-selector-literal-candidate/v1','hwpx-agent.stored-literal-search-candidate/v3'),
        ('PreparedStoredSelectorLiteralCandidate {source:LiteralSource::Borrowed(self)','PreparedStoredReviewLiteralCandidate {source:super::super::product::LiteralSource::Borrowed(self)')):
        c.require(body.count(new)==1,'ONLY_NEW_TYPED_COMPILER_AND_RESULT_PROFILE_SUBSTITUTION');body=body.replace(new,previous)
    c.require(body==method(legacy,'prepare_review_literal_candidate'),'SAME_CURRENT_WRITE_WHOLE_SOURCE_PROOF_DIGEST_AND_PREPARATION_HEAD')
    owner=method(current,'into_review_selector_literal_candidate')
    old_owner=method(q.text(REVIEW[:-3]+'/product.rs'),'into_review_literal_candidate')
    owner=owner.replace('let(output,receipt)','let (output,receipt)').replace('prepare_review_selector_literal_candidate','prepare_review_literal_candidate')
    owner=owner.replace('query,selector,policy','query,scope,policy').replace('PreparedStoredSelectorLiteralCandidate','PreparedStoredReviewLiteralCandidate')
    c.require(owner==old_owner,'SAME_PREPARED_OUTPUT_RECEIPT_MOVE_AND_BOX_OWNER_WITHOUT_CLONE_OR_REIMPORT')


def expected(q):
    groups=[]
    for module in MODULES:
        path='crates/product-cli/tests/form_stored_provider/actual_import/'+module+'.rs'
        groups.append({'actual_import::'+module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))})
    c.require(tuple(map(len,groups))==(12,10,26,7,6),'EXACT_TWELVE_NEW_AND_FORTY_NINE_AFFECTED_TEST_IDENTITIES')
    return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_REVIEW_SELECTOR_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_REVIEW_SELECTOR_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,strict_product_json_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='cab7ad4d39fcba40f3ddb492d82347a2a4549d6bded1c31479a89df7d4f56f32'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==52 and previous['cleanup'],'EXACT_PREVIOUS_FIFTY_TWO_REVIEW_SELECTOR_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.prior.base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_NEW_STORED_SELECTOR_MODULES_AND_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'CORE_COMPILER_PROOF_PROTECTION_PARSER_AND_OLD_TESTS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='STORED_REVIEW_SELECTOR_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=49,retained_core_cases=52,test_binaries=1)),flush=True)
        harness.run_one('twelve_stored_review_selector_and_forty_nine_affected_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','review_selector_stored','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.base.base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_STORED_REVIEW_SELECTOR_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_REVIEW_SELECTOR_TWELVE_NEW_FORTY_NINE_AFFECTED_NOT_PRODUCT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_stored_cases=12,affected_cases=49,total_executed_cases=61,
            previous_fifty_two_core_cases_reexecuted=False,original_search_finish_fresh_authorization_and_final_head_bodies_preserved=True,
            original_v3_literal_bodies_and_owned_transfer_preserved=True,retained_verify_does_not_repeat_query_lowering_or_review_import=True,
            next_work='Strict_review_scope_search_and_selector_literal_product_JSON_requests')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STORED_REVIEW_SELECTOR_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STORED_REVIEW_SELECTOR_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
