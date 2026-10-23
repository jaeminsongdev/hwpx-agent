"""20 new current-store/strict-JSON normalization products; retain81 source/130 old products."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_normalization_failed_cases as prior
base=prior.base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-product-components161.v1.json'
ROOT_STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
ROOT_PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORED=ROOT_STORED[:-3]+'/unicode.rs';PRODUCT=ROOT_PRODUCT[:-3]+'/unicode.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/regex_replacement_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={ROOT_STORED,ROOT_PRODUCT,PARENT}


def inventory(check):return base.inventory(check)|NEW


def inverse(q,old):
    for name in(ROOT_STORED,ROOT_PRODUCT):
        text=q.text(name);marker='pub mod unicode;\n';c.require(text.count(marker)==1,'ONLY_ONE_ADDITIVE_UNICODE_PRODUCT_MODULE')
        audit.inverse(text.replace(marker,''),old[name],'WHOLE_ORIGINAL_LITERAL_REGEX_STYLE_SOURCE_ACCESS_AND_PARSER_BODY_UNCHANGED')
    text=q.text(PARENT);marker='#[path="unicode_normalization_product.rs"] mod unicode_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_UNICODE_PRODUCT_TEST_MODULE')
    audit.inverse(text.replace(marker,''),old[PARENT],'ALL_EXISTING_130_PRODUCT_TEST_BODIES_AND_HELPERS_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?','proof.lower_review_selector_unicode_candidate(&self.imported,selector,policy,form,run,limits,writer)?',
        'source:LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)?'):
        c.require(stored.count(marker)==1,'ONE_PROOF_NORMALIZATION_AND_OWNER_TRANSFER_NO_REPEAT_IMPORT_OR_RELOWERING_ON_VERIFY')
    product=q.text(PRODUCT)
    c.require('super::selector::parse_selector_object(raw)'in product and 'enum Kind {NormalizeUnicodeScope}'in product
        and 'form:SourceUnicodeNormalizationForm,run_policy:RunPolicy,review_policy:SourceReviewTextPolicy'in product,
        'EXPLICIT_SCOPE_ONLY_OPERATION_FOUR_FORMS_REQUIRED_POLICIES_AND_ORIGINAL_UNIQUE_JSON_PARSER')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==20,'EXACT_TWENTY_NEW_UNICODE_PRODUCT_CASES')
    return {'actual_import::regex_replacement_product::unicode_v1::'+n for n in names}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search022_query_filter_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='d8b44843bb5ecc8959625c7614d3ac126d5b75f927dd2347173ccda29fe7899a'
            and baseline['state']=='PASS_UNICODE_3_REPAIRED_78_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==654 and baseline['total_distinct_cases']==81,'EXACT_81_DISTINCT_SOURCE_CASE_BASELINE_RETAINED')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_UNICODE_PRODUCTS_DO_NOT_OVERWRITE_EXISTING_SOURCE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_SOURCE_CORE_PROTECTION_OLD_PRODUCTS_AND_TESTS_UNCHANGED_AFTER159')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='UNICODE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_product_cases=20,retained_source_cases=81,retained_original_products=130,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_new_unicode_current_store_and_strict_product_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        base.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_UNICODE_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_TWENTY_SCOPE_PRODUCTS_NOT_QUERY_FILTER_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=20,source81_reexecuted=False,original130_products_reexecuted=False,
            original_common_access_request_parser_and_test_bodies_inverse_verified=True,explicit_unimplemented_query_filter_rejected_not_ignored=True,
            next_work='Full_SEARCH022_query_style_filter_semantics_then_remaining_P09_operations_and_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
