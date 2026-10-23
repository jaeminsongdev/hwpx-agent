"""22 new current-store/strict-v2 match normalization cases, no42-source/150-product replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_match_recovery as prior
from run_regex_replacement_focused import select_own_single_cpu
from run_style_replacement_sync import good_step
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-match-product-components166.v1.json'
STORED_PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/unicode.rs'
PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement/unicode.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs'
STORED=STORED_PARENT[:-3]+'/matches.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/matches.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/unicode_match_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={STORED_PARENT,PRODUCT_PARENT,PARENT}


def inventory(check):return prior.base.inventory(check)|NEW


def inverse(q,old):
    for name in(STORED_PARENT,PRODUCT_PARENT):
        text=q.text(name);marker='pub mod matches;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_V2_MATCH_MODULE_WITHOUT_CHANGING_V1')
        audit.inverse(text.replace(marker,''),old[name],'ENTIRE_ORIGINAL_SCOPE_PRODUCT_SOURCE_ACCESS_PARSER_RECEIPT_AND_CONSUMER_BOUNDARY_UNCHANGED')
    text=q.text(PARENT);marker='#[path="unicode_match_product.rs"] mod matches_v2;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_MATCH_PRODUCT_CHILD_AFTER_ALL_V1_CASES_AND_HELPERS')
    audit.inverse(text.replace(marker,''),old[PARENT],'ENTIRE_ORIGINAL_V1_PRODUCT_TEST_BODIES_AND_FIXTURES_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?','proof.lower_review_selector_unicode_matches(&self.imported,query,selector,policy,filter,form,run,limits,writer)?',
        'source:LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)?'):
        c.require(stored.count(marker)==1,'ONE_CURRENT_PROOF_AND_COMPILER_OWNER_TRANSFER_NO_REIMPORT_OR_REQUERY_ON_DELIVERY')
    product=q.text(PRODUCT)
    c.require('super::super::selector::parse_selector_object(raw)'in product and 'enum Kind {NormalizeUnicodeMatches}'in product
        and 'filter.validate().map_err(|_|M::Request)?'in product and 'max_matches:usize'in product,
        'ORIGINAL_STRICT_UNIQUE_JSON_SELECTOR_REQUIRED_QUERY_MODE_CAP_AND_OPTIONAL_TYPED_FILTER')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==22,'EXACT_TWENTY_TWO_NEW_MATCH_NORMALIZATION_PRODUCTS')
    return {'actual_import::regex_replacement_product::unicode_v1::matches_v2::'+n for n in names}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_MATCH_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_MATCH_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search022_transaction_native_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='f4e9af5273787ab26e600dcc5e7c9c9302a076f4b264813325b6ba5d10bdf86d'
            and baseline['state']=='PASS_UNICODE_MATCH1_REPAIRED_41_RETAINED_NOT_MATCH_STORED_PRODUCT_NATIVE_OR_GATE'
            and baseline['cleanup']and baseline['fresh_inputs']==baseline['final_fresh_hashes']==663 and baseline['total_distinct_cases']==42
            and baseline['production_unchanged_after163'],'EXACT42_DISTINCT_MATCH_SOURCE_AND_SCOPE_BASELINE_RETAINED')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_MATCH_PRODUCT_FILES_DO_NOT_OVERWRITE_EXISTING_SOURCE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_SOURCE_COMPILERS_MATCHERS_GUARDS_WRITERS_OLD_PRODUCTS_AND_TESTS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='UNICODE_MATCH_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_product_cases=22,source_cases_retained=42,old_products_retained=150,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_two_current_stored_and_strict_v2_unicode_match_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_UNICODE_MATCH_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_MATCH_TWENTY_TWO_V2_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=22,source42_reexecuted=False,old150_products_reexecuted=False,original_v1_scope_product_and_source_test_bodies_inverse_verified=True,
            one_current_source_proof_match_compiler_and_no_query_replay_on_delivery=True,
            next_work='Remaining_SEARCH022_full_contract_target_evidence_and_other_P09_source_transformations_before_transaction_native_gate_closure')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_MATCH_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_MATCH_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
