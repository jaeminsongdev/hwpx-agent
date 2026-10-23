"""350: optional named source filters through stored/strict v2/preview; new28 + affected v1 four."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_filtered_named_styles as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-options-product350.v1.json';DRIVER='tools/p09/run_named_style_options_product.py'
STORED_PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/named_styles.rs';PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement/named_styles.rs'
STORED=STORED_PARENT[:-3]+'/options.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/options.rs';PARENT='crates/product-cli/tests/named_style_product.rs';TEST='crates/product-cli/tests/support/named_style_options_product.rs'
NEW={DRIVER,STORED,PRODUCT,TEST};CHANGED={STORED_PARENT,PRODUCT_PARENT,PARENT};LINK='#[path="support/named_style_options_product.rs"]mod named_options;\n'
AFFECTED={'borrowed_owned_and_product_share_original_named_candidate_receipt_and_output','preview_predicts_same_result_but_discards_output_and_never_calls_byte_consumer',
    'unknown_filters_full_catalog_options_and_caller_approval_or_graph_data_are_rejected','exact_sixteen_kib_and_query_and_request_count_limits_reject_before_source_reads'}

def inverse(q,old):
    for path in(STORED_PARENT,PRODUCT_PARENT):
        text=q.text(path);c.require(text.count('pub mod options;\n')==1,'ONE_OPTIONAL_FILTER_MODULE_EXPORT');audit.inverse(text.replace('pub mod options;\n',''),old[path],'ALL_V1_STORED_PRODUCT_MUTATION_PREVIEW_COMPILER_BINDINGS_AND_GUARDS_UNCHANGED')
    text=q.text(PARENT);c.require(text.count(LINK)==1,'ONE_OPTIONAL_FILTER_PRODUCT_TEST_LINK');audit.inverse(text.replace(LINK,''),old[PARENT],'ALL_PREVIOUS31_V1_PRODUCT_AND19_COMMON_TEST_BODIES_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_OPTIONS_PRODUCT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_OPTIONS_PRODUCT',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,options_common_compiler_or_preview_dispatch_connected=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='75f0ead9d37f20d8e3cffb74353f13f2a02286e4f1374b301a91a121256f5b6d'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==810 and passed['new_cases']==18 and passed['affected_source_cases']==6,'EXACT348_ORIGINAL_FILTER_SOURCE_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_FILTER_CORE_MATCHERS_READBACK_COMPILER_RESOURCE_GUARDS_AND_OTHER_TESTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_OPTIONS_STORED_PRODUCT_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'named_options::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}|AFFECTED
        c.require(len(cases)==32 and len(AFFECTED)==4,'EXACT_NEW28_AFFECTED_V1_FOUR')
        scratch=c.ROOT/'target/p09-named-style-options-product-scratch-350';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_OPTIONS_PRODUCT_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_OPTIONS_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=28,affected_cases=4)),flush=True)
        harness.run_one('named_options_current_stored_strict_v2_preview28_affected_v1_four',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','named_style_product','--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,
            observe_capture=previous.previous.base.previous.previous.previous.base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'NAMED_OPTIONS_PRODUCT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_OPTIONS_STORED_STRICT_V2_PREVIEW28_AFFECTED_V1_FOUR_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=28,affected_cases=4,preview_output_artifact_discarded=True,preview_has_no_inventory_or_compiler_api=True,server_outer_metadata_budget_honored=True,
            next_work='named_options_common_mutation_compiler_separate_preview_dispatch_and_character_style_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_OPTIONS_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_OPTIONS_PRODUCT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
