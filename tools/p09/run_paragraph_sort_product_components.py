"""Actual retained source-sort candidate/current stored access/strict JSON, not full route/commit/Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_paragraph_sort_recovery as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-paragraph-sort-product-components235.v1.json'
DRIVER='tools/p09/run_paragraph_sort_product_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-source-paragraph-sort-sync-recovery234.v1.json'
STORED_ROOT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
STORED=STORED_ROOT[:-3]+'/sort.rs'
PRODUCT_ROOT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
PRODUCT=PRODUCT_ROOT[:-3]+'/sort.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/paragraph_sort_product.rs'
NEW={STORED,PRODUCT,TEST,DRIVER};CHANGED={STORED_ROOT,PRODUCT_ROOT,PARENT}
CHILD='#[path="paragraph_sort_product.rs"] mod sort_v1;\n'
PREFIX='actual_import::regex_replacement_product::unicode_v1::sort_v1::'


def inventory(check):return prior.inventory(check)|NEW|{'tools/p09/run_source_paragraph_sort_sync.py','tools/p09/run_source_paragraph_sort_sync_recovery.py','protocol/migrations/p09-source-paragraph-sort-v1.md'}


def expected(q):
    cases=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(cases)==len(set(cases))==20,'EXACT20_CURRENT_STORED_AND_STRICT_PRODUCT_SORT_CASES')
    return{PREFIX+n for n in cases}


def inverse(q,old):
    for path in (STORED_ROOT,PRODUCT_ROOT):
        text=q.text(path);marker='pub mod sort;\n';c.require(text.count(marker)==1,'ONE_SOURCE_SORT_CHILD_PER_EXISTING_ROOT')
        audit.inverse(text.replace(marker,''),old[path],'ALL_ORIGINAL_REPLACEMENT_CURRENT_ACCESS_AND_PRODUCT_BODIES_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_APPENDED_SOURCE_SORT_PRODUCT_TEST_CHILD')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL_ORIGINAL_PRODUCT_TESTS_AND_FIXTURES_BYTE_IDENTICAL')
    source=q.text(STORED);product=q.text(PRODUCT)
    for marker in ('self.fresh_source_reconstructed(provider,now)','proof.lower_selector_paragraph_sort_candidate','provider.check_head(fresh.head)',
        'LiteralSource::Borrowed(self)','LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)',
        'provider.check_head(self.source.source.head)','self.output.with_verified_bytes','AuthScope::DocumentWrite','Err(C::RouteUnqualified)'):
        c.require(marker in source,'SAME_ORIGINAL_COMPILER_CURRENT_WRITE_PROOF_RETAINED_OUTPUT_AND_FINAL_CONSUMER_HEAD_CHECK')
    for marker in ('parse_selector_object(raw)','Scope::shape','validate_shape','source_search_product_scope','provider.import_actual_forms(request.head()?,now)',
        'request.selector.revision_id!=request.base_revision','request.operation.sort_spec.max_comparison_bytes>32*1024*1024',
        'source.into_paragraph_sort_candidate','capability_id:"search.sort_text"','request.scoped_sha(scope)',
        'self.candidate.with_verified_bytes(provider,now,consume)','idempotency_key_claimed:false','full_sort_native_cas_execution_publication_authority:false'):
        c.require(marker in product,'STRICT_UNIQUE_BOUNDED_JSON_FOUR_SELECTORS_EXPLICIT_SPEC_AND_CURRENT_SCOPE_BINDING')
    for text in (source,product):
        c.require(all(marker not in text for marker in('SignatureVerified','std::fs::','std::process::','commit_success(','WorkspaceTransaction::create','unsafe')),
            'NO_TRUST_PROMOTION_EXTERNAL_IO_RAW_ACTION_OR_COMMIT')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_PRODUCT_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PARAGRAPH_SORT_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,common_dispatcher_compiler_or_route_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(prior.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='52c2dd96601597e716d8b5310c80848ad26194c14b01d202fcc9ada18e095f7b'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==796,'EXACT232_ACTUAL_SOURCE_SORT19_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='cfd7c53d05a0c7086aee95823b6075c4a9b53e1999f5aca2891585b2ea48a754'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==34,'EXACT234_CURRENT_SOURCE_SORT_DOCS')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_SORT_CURRENT_ACCESS_SCOPES_SECURITY_AND_ORIGINAL_PRODUCTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='PARAGRAPH_SORT_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_product_cases=20,old_source19_patch18_and_official249_reexecuted=False)),flush=True)
        harness.run_one('twenty_actual_stored_sort_strict_JSON_scope_access_and_head_race_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.base.prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_STORED_PARAGRAPH_SORT_AND_STRICT_PRODUCT20_NOT_FULL_SEARCH021_DISPATCH_TRANSACTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=20,
            original_source_sort_and_current_access_reused=True,old_source19_patch18_and_official249_reexecuted=False,
            next_work='source_bound_sort_splice_anchors_and_common_operation_compiler_dispatch_then_actual_execution_and_multi_group_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SORT_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
