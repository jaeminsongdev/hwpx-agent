"""20 new v9 resolution products only; retain104 products/source18 without replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_resolved_style_components as prior
from run_paragraph_style_product_components import expected as paragraph_expected,legacy_expected,run_expected,text_expected
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-resolved-style-product-components150.v1.json'
ROOT_STORED='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
NAV=ROOT_STORED[:-3]+'/navigation.rs';STORED=ROOT_STORED[:-3]+'/resolved_styles.rs'
ROOT_PRODUCT='crates/product-cli/src/form_product_request/stored_source_search/selector.rs'
PRODUCT=ROOT_PRODUCT[:-3]+'/resolved_styles.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/regex_replacement_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/resolved_style_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={ROOT_STORED,NAV,ROOT_PRODUCT,PARENT}
ERROR='    #[error("STORED_SOURCE_STYLE_RESOLUTION_REJECTED")] Resolution(#[from] hwpx_package::document_import::search::reviews::selector::resolved_styles::SourceResolvedStyleSearchError),\n'
ARMS=(',ResolvedStyle(resolved_styles::ResolvedStyleResult)',',Self::ResolvedStyle(r)=>r.index()',',Self::ResolvedStyle(r)=>&r.scope',
    ',Self::ResolvedStyle(r)=>r.request_sha()',',Self::ResolvedStyle(r)=>r.json()',',Self::ResolvedStyle(_)=>"hwpx-agent.stored-source-search/v9"')


def inventory(check):return prior.inventory(check)|NEW


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(names)==len(set(names))==20,'EXACT_TWENTY_NEW_RESOLVED_STYLE_PRODUCT_IDENTITIES')
    return {'actual_import::regex_replacement_product::resolved_style_v9::'+n for n in names}


def inverse(q,old):
    text=q.text(ROOT_STORED)
    for marker in('pub mod resolved_styles;\n',ERROR,*ARMS):
        c.require(text.count(marker)==1,'ONE_ADDITIVE_RESOLVED_RESULT_ARM_OR_TYPED_ERROR');text=text.replace(marker,'')
    audit.inverse(text,old[ROOT_STORED],'WHOLE_ORIGINAL_V1_V8_CONSTRUCTORS_RECEIPTS_ACCESS_SOURCE_INTEGRITY_AND_FINAL_HEAD_BODY_UNCHANGED')
    for name,marker in[(NAV,',Self::ResolvedStyle(r)=>r.navigate(request,context)'),(ROOT_PRODUCT,'pub mod resolved_styles;\n'),
        (PARENT,'#[path="resolved_style_product.rs"] mod resolved_style_v9;\n')]:
        text=q.text(name);c.require(text.count(marker)==1,'ONE_ADDITIVE_V9_MODULE_OR_NAVIGATION_ARM')
        audit.inverse(text.replace(marker,''),old[name],'WHOLE_ORIGINAL_NAVIGATION_REQUEST_PARSER_AND_PREVIOUS_PRODUCT_TEST_BODIES_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?','proof.source_review_scope_index(&self.imported,limits)?',
        'index.find_resolved_style(query,selector,policy,filter)?','self.finish_search(provider,result,fresh.head)'):
        c.require(stored.count(marker)==1,'ONE_CURRENT_WHOLE_PROOF_INDEX_RESOLUTION_AND_SHARED_FINISH_BOUNDARY')
    text=q.text(PRODUCT)
    c.require('Request::parse_object(raw)?'in text and 'request.operation.style_filter.validate()'in text
        and 'enum Kind {FindResolvedStyle}'in text and 'super::super::navigation::bound_next(raw,&self.receipt)?'in text,
        'ORIGINAL_STRICT_UNIQUE_OBJECT_AND_NEXT_PARSERS_REQUIRED_FILTER_POLICY_AND_MODE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'RESOLVED_STYLE_PRODUCT_IMMUTABLE_RUN_EXISTS')
    selection=prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_RESOLVED_STYLE_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_effective_cascade_or_visibility_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        source=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='e6b9b79a4f241f9510edf6aaa8d46364765439a80a81be842f99475752ab16a1'
            and source['state']=='PASS_RESOLVED_DIRECT_STYLE_EIGHTEEN_NEW_NOT_FULL_CASCADE_STORED_NATIVE_OR_GATE'and source['cleanup']
            and source['fresh_inputs']==source['final_fresh_hashes']==635 and source['new_resolution_cases']==18,
            'EXACT_QUALIFIED_RESOLUTION_SOURCE_BASELINE_NOT_PRODUCT_OR_NATIVE_AUTHORITY')
        old={p['path']:p for p in source['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_V9_ADAPTERS_AND_ONE_NEW_PRODUCT_TEST_FILE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CORE_RESOLUTION_SOURCE_WRITER_GUARD_FIXTURE_OR_PRIOR_TEST_CHANGE')
        inverse(q,old);cases=expected(q)
        c.require(len(legacy_expected(q))==47 and len(run_expected(q))==18 and len(text_expected(q))==18 and len(paragraph_expected(q))==21,
            'ALL_104_ORIGINAL_PRODUCT_CASE_IDENTITIES_RETAINED_NOT_REEXECUTED')
        print(json.dumps(dict(state='RESOLVED_STYLE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=20,retained_products=104,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_new_v9_resolved_style_product_cases_only',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_RESOLVED_STYLE_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_RESOLVED_STYLE_TWENTY_PRODUCTS_NOT_FULL_CASCADE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=20,total_executed_cases=20,retained_original_products=104,retained_source_resolution_cases=18,
            previous_product_source_and_unrelated_cases_reexecuted=False,original_search_navigation_parser_and_test_whole_file_inverse_verified=True,
            one_proof_one_resolution_without_query_replay=True,typed_unresolved_rejection_preserved=True,
            next_work='Qualified_text_style_precedence_missing_axes_native_visibility_then_full_scope_filter_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'RESOLVED_STYLE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_RESOLVED_STYLE_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
