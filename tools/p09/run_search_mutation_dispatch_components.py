"""Existing common dispatcher: all16 strict mutation families,26 new cases, no transaction/Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_number_control_product_components as prior
harness,shared,c,a,audit,snapshot,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-search-mutation-dispatch-components205.v1.json'
ROOT='crates/product-cli/src/form_product_request/stored_operations.rs'
REQUEST=ROOT[:-3]+'/request.rs';MODEL=ROOT[:-3]+'/search_mutations.rs'
PARENT=prior.PARENT;TEST='crates/product-cli/tests/form_stored_provider/actual_import/search_mutation_dispatch.rs'
DRIVER='tools/p09/run_search_mutation_dispatch_components.py'
NEW={MODEL,TEST,DRIVER};CHANGED={ROOT,REQUEST,PARENT}
PREFIX='actual_import::regex_replacement_product::unicode_v1::dispatch_v1::'


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    text=q.text(ROOT)
    text=text.replace('//! Common strict candidate API: original Form/Formula plus closed search mutation schemas.',
        '//! Common strict product API: unchanged v1 form input or source-only v2 formula recalculation.')
    text=text.replace('pub mod search_mutations;\n','').replace('/// All variants preserve their original authentication and route guards.',
        '/// Both variants preserve their original authentication and route guards.')
    text=text.replace('    SearchMutation(Box<search_mutations::PreparedStoredSearchMutation>),\n','')
    for call in ('Ok(candidate.with_verified_bytes(provider, now, consume)?)','Ok(candidate.require_current_product_route(provider, now)?)'):
        addition='''            Self::SearchMutation(candidate) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                %s
            }
'''%call
        c.require(text.count(addition)==1,'ONE_ADDITIVE_ORIGINAL_VERIFIED_DELIVERY_OR_ROUTE_ARM');text=text.replace(addition,'')
    text=text.replace('    /// bindings; formulas and search mutations reject them and derive results from actual source.',
        '    /// bindings; v2 formulas reject them and derive all targets/results from actual source.')
    start=text.index('        Self::prepare_json_with_search_limits(');end=text.index('        match request::classify(raw)?',start)
    text=text[:start]+text[end:]
    addition='''            request::Kind::SearchMutation(family) => {
                if bindings.is_some() {
                    return Err(StoredProductOperationError::Bindings);
                }
                Ok(PreparedStoredProductOperation::SearchMutation(Box::new(
                    search_mutations::prepare(family, provider, raw, limits, now)?,
                )))
            }
'''
    c.require(text.count(addition)==1,'ONE_COMMON_SEARCH_PREPARATION_ARM');text=text.replace(addition,'')
    text=text.replace('    #[error("product_operation_search_mutation_rejected")]\n    SearchMutation(#[from] search_mutations::SearchMutationError),\n','')
    audit.inverse(text,old[ROOT],'ENTIRE_ORIGINAL_FORM_AND_FORMULA_DISPATCH_DELIVERY_ROUTE_AND_ERROR_BODIES_PRESERVED')
    text=q.text(REQUEST).replace('    SearchMutation(super::search_mutations::Family),\n','')
    start=text.index('        schema => match super::search_mutations::classify(schema) {');end=text.index('\n    }\n}',start)
    text=text[:start]+'        _ => Err(RequestError::Request.into()),'+text[end:]
    audit.inverse(text,old[REQUEST],'ENTIRE_ORIGINAL_DUPLICATE_FREE_FORM_FORMULA_CLASSIFICATION_AND_BINDINGS_PRESERVED')
    text=q.text(PARENT);marker='#[path="search_mutation_dispatch.rs"] mod dispatch_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_ADDITIVE_DISPATCH_TEST_CHILD')
    audit.inverse(text.replace(marker,''),old[PARENT],'ALL_ORIGINAL292_PRODUCT_TEST_BODIES_AND_HELPERS_UNCHANGED')
    table=q.text(MODEL);rows=re.findall(r'^    \(([A-Za-z]+), ([a-z_]+), (Stored[A-Za-z]+), (Prepared[A-Za-z]+), ([A-Za-z]+Receipt),',table,re.M)
    c.require(len(rows)==len({r[0]for r in rows})==16,'EXACT16_CLOSED_MUTATION_FAMILY_ROWS')
    for marker in ('candidate.verify(provider, now)','candidate.with_verified_bytes(provider, now, consume)',
        'candidate.require_current_product_route(provider, now)','candidate.receipt()',
        '$limits.search, $limits.auxiliary, $limits.writer, $now','SearchMutationReceiptRef<\'a>'):
        c.require(table.count(marker)==1,'ONE_TABLE_ORIGINAL_TYPED_SOURCE_OWNERS_RECEIPT_BORROW_AND_BUDGET_PRESERVING_DISPATCH')


def expected(q):
    text=q.text(TEST);ordinary=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',text)
    generated=re.findall(r'^dispatch_case!\(([A-Za-z0-9_]+),',text,re.M)
    c.require(len(ordinary)==10 and len(generated)==16 and len(set(ordinary+generated))==26,'EXACT26_COMMON_DISPATCH_CASE_IDENTITIES')
    return {PREFIX+n for n in ordinary+generated}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_DISPATCH_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_MUTATION_DISPATCH_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='9909a7cb2f031ffce55d1395b041cc15ce6cd0fef117472a009852b80efecad0'
            and baseline['state']=='PASS_NUMBER_CONTROL_TWENTY_SIX_PRODUCTS_NOT_NATIVE_COUNTER_FULL_TRANSACTION_OR_GATE'
            and baseline['cleanup']and baseline['fresh_inputs']==baseline['final_fresh_hashes']==727,'EXACT203_CURRENT_MUTATION_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'COMMON_DISPATCH_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_SOURCE_IMPORT_COMPILER_MATCHER_WRITER_ACCESS_AND_ORIGINAL292_PRODUCTS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='COMMON_SEARCH_DISPATCH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=26,old292_and_official249_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_six_common_search_mutation_dispatch_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_SEARCH_DISPATCH_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_DISPATCH_SIXTEEN_FAMILIES_TWENTY_SIX_CASES_NOT_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=26,dispatched_mutation_families=16,old292_products_reexecuted=False,original_form_formula_bodies_inverse_verified=True,
            original_mutation_parsers_compilers_and_fresh_source_delivery_route_checks_preserved=True,borrowed_typed_receipts_and_moved_original_candidate_owners=True,
            next_work='actual_product_transaction_route_manifest_and_durable_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_DISPATCH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_DISPATCH_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
