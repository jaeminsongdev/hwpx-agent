"""22 current-store/strict-case products; retain64 source and172 older product results."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_case_conversion_recovery as prior
from run_regex_replacement_focused import select_own_single_cpu
from run_style_replacement_sync import good_step
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-case-product-components173.v1.json'
STORED_PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs'
STORED=STORED_PARENT[:-3]+'/case.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/case.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/case_conversion_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={STORED_PARENT,PRODUCT_PARENT,PARENT}


def inventory(check):return prior.base.inventory(check)|NEW


def inverse(q,old):
    for name in(STORED_PARENT,PRODUCT_PARENT):
        text=q.text(name);marker='pub mod case;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_CASE_MODULE_WITHOUT_CHANGING_OLD_PRODUCT_MEANINGS')
        audit.inverse(text.replace(marker,''),old[name],'ENTIRE_OLD_LITERAL_REGEX_STYLE_UNICODE_PRODUCT_SOURCE_ACCESS_AND_CONSUMER_BOUNDARIES_UNCHANGED')
    text=q.text(PARENT);marker='#[path="case_conversion_product.rs"] mod case_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_CASE_PRODUCT_CHILD_AFTER_ALL_OLD_CASES_AND_HELPERS')
    audit.inverse(text.replace(marker,''),old[PARENT],'ENTIRE_ORIGINAL_UNICODE_V1_V2_PRODUCT_TEST_BODIES_AND_FIXTURES_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?','proof.lower_review_selector_case_candidate(&self.imported,query,selector,body,filter,mode,policy,limits,writer)?',
        'source:LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)?'):
        c.require(stored.count(marker)==1,'ONE_CURRENT_PROOF_COMPILER_OWNER_TRANSFER_NO_REIMPORT_OR_QUERY_REPLAY_ON_DELIVERY')
    product=q.text(PRODUCT)
    c.require('super::selector::parse_selector_object(raw)'in product and 'enum Kind {ConvertCaseMatches}'in product
        and 'filter.validate().map_err(|_|C::Request)?'in product and 'mode:SourceCaseMode,case_policy:SourceCasePolicy'in product,
        'ORIGINAL_STRICT_UNIQUE_JSON_SELECTOR_QUERY_CAP_AND_EXPLICIT_CASE_MODE_AND_POLICY')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==22,'EXACT_TWENTY_TWO_NEW_CASE_PRODUCTS')
    return {'actual_import::regex_replacement_product::unicode_v1::case_v1::'+n for n in names}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CASE_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CASE_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search013_transaction_native_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='9052f0f34c12c073122b4ed0cf1f13c111a0baef83720e151675db6ef6b738b5'
            and baseline['state']=='PASS_CASE1_REPAIRED63_RETAINED_NOT_CASE_STORED_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==673 and baseline['total_distinct_cases']==64
            and baseline['production_unchanged_after169']and not baseline['passed63_cases_reexecuted'],'EXACT64_DISTINCT_CASE_AND_UNICODE_SOURCE_BASELINE_RETAINED')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_CASE_PRODUCT_FILES_DO_NOT_OVERWRITE_EXISTING_SOURCE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_SOURCE_COMPILERS_MATCHERS_GUARDS_WRITERS_OLD_PRODUCTS_AND_TESTS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='CASE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_product_cases=22,source_cases_retained=64,old_products_retained=172,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_two_current_stored_and_strict_default_case_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_CASE_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_CASE_TWENTY_TWO_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=22,source64_reexecuted=False,old172_products_reexecuted=False,original_product_and_source_test_bodies_inverse_verified=True,
            one_current_source_proof_case_compiler_and_no_query_replay_on_delivery=True,
            next_work='SEARCH014_explicit_width_conversion_policy_source_compiler_and_remaining_P09_full_contract_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CASE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CASE_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
