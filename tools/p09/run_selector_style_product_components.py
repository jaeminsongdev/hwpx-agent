"""Twelve current v7 style products plus33 affected legacy search/navigation cases, one bounded binary."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_styles_components as prior
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-selector-style-product-components105.v1.json'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
NAV=SERVICE[:-3]+'/navigation.rs';STORED=SERVICE[:-3]+'/review_styles.rs'
PARENT='crates/product-cli/src/form_product_request/stored_source_search/selector.rs'
PRODUCT=PARENT[:-3]+'/styles.rs'
FIXTURE='crates/hwpx-package/tests/support/review_style_fixture.rs'
TARGET='crates/product-cli/tests/selector_style_product.rs'
WRAPPER='crates/product-cli/tests/selector_style_product/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/selector_style_product.rs'
OLD_SEARCH='crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'
OLD_NAV='crates/product-cli/tests/form_stored_provider/actual_import/source_search_navigation.rs'
NEW={STORED,PRODUCT,FIXTURE,TARGET,WRAPPER,TEST};CHANGED={SERVICE,NAV,PARENT}


def inventory(check):return prior.inventory(check)|{TARGET,WRAPPER}


def inverse(q,old):
    text=q.text(SERVICE)
    for addition in('pub mod review_styles;\n',',ReviewStyle(review_styles::ReviewStyleResult)',',Self::ReviewStyle(r)=>r.index()',
        ',Self::ReviewStyle(r)=>&r.scope',',Self::ReviewStyle(r)=>r.request_sha()',',Self::ReviewStyle(r)=>r.json()',',Self::ReviewStyle(_)=>"hwpx-agent.stored-source-search/v7"'):
        c.require(text.count(addition)==1,'ONLY_PRIVATE_STYLE_RESULT_VARIANT_AND_TYPED_ACCESSORS');text=text.replace(addition,'')
    audit.inverse(text,old[SERVICE],'WHOLE_ORIGINAL_SEARCH_PREPARE_FINISH_FRESH_JSON_AUTH_AND_FINAL_HEAD_BODY_UNCHANGED')
    for name,addition in((NAV,',Self::ReviewStyle(r)=>r.navigate(request,context)'),(PARENT,'pub mod styles;\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ONE_ADDITIVE_STYLE_RESULT_ROUTE_OR_MODULE')
        audit.inverse(text.replace(addition,''),old[name],'WHOLE_ORIGINAL_NEXT_ENGINE_PARSER_V5_SCOPE_AND_PREPARED_PRODUCT_BODY_UNCHANGED')
    core=q.text(prior.TEST);fixture=q.text(FIXTURE)
    original=core[core.index('fn body()->String{'):core.index('fn forms(',core.index('fn body()->String{'))]
    shared_body=fixture[fixture.index('pub fn body()->String{')+4:fixture.index('pub fn package(')]
    c.require(original==shared_body,'EXACT_SYNTHETIC_STYLE_BODY_REUSED_FROM_QUALIFIED_CORE_WITHOUT_OLD_TEST_EDITS')
    new=q.text(STORED)
    c.require(new.count('self.fresh_source_reconstructed(provider,now)?')==1 and new.count('proof.source_review_scope_index(&self.imported,limits)?')==1
        and new.count('index.find_style(query,selector,policy,filter)?')==1 and new.count('self.finish_search(provider,result,fresh.head)')==1,
        'ONE_OPERATION_LOCAL_ORIGINAL_PROOF_REVIEW_INDEX_AND_STYLE_QUERY_WITH_ORIGINAL_FINISH')


def cases(q,path,module):return {'actual_import::'+module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))}
def expected(q):
    groups=[cases(q,TEST,'selector_style_product'),cases(q,OLD_SEARCH,'source_search'),cases(q,OLD_NAV,'source_search_navigation')]
    c.require(tuple(map(len,groups))==(12,26,7),'EXACT_TWELVE_NEW_THIRTY_THREE_AFFECTED_PRODUCT_IDENTITIES');return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_STYLE_PRODUCT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_STYLE_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_control_coordinate_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='1b06a32b67977b36b32eef0f9db9bf6044be64c6795414eaff1eafbf0af42119'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==35 and previous['cleanup'],'EXACT_PREVIOUS_THIRTY_FIVE_STYLE_CORE_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.prior.prior.prior.base.prior.base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_SIX_NEW_STYLE_SERVICE_PRODUCT_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CORE_STYLE_MATCHER_SCOPE_WRITER_CRYPTO_OR_EXISTING_TEST_INPUT_CHANGE')
        inverse(q,old);expected_cases=expected(q)
        print(json.dumps(dict(state='SELECTOR_STYLE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=33,retained_core_cases=35,test_binaries=1)),flush=True)
        harness.run_one('twelve_selector_style_products_thirty_three_legacy_search_navigation',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','selector_style_product','--','--test-threads=1'],expected_cases,guard,audit.environment(),row,observe_capture=prior.prior.prior.prior.prior.base.base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_SELECTOR_STYLE_PRODUCT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_STYLE_V7_TWELVE_NEW_THIRTY_THREE_AFFECTED_NOT_CONTROL_COORDINATES_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=12,affected_cases=33,total_executed_cases=45,
            previous_thirty_five_style_core_and_other_completed_suites_reexecuted=False,original_service_finish_fresh_crypto_authorization_and_final_head_inverse_verified=True,
            old_product_schemas_and_navigation_preserved=True,new_product_schema='hwpx-agent.product-source-search-request/v7',
            retained_output_and_next_do_not_repeat_query_or_definition_lookup=True,all_four_source_scopes_and_explicit_policies_bound=True,
            next_work='Exact_control_anchor_scope_projection_without_paragraph_widening_then_full_search_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_STYLE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_STYLE_PRODUCT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
