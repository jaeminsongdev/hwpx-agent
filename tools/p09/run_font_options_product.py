"""333: current stored optional-filter and strict v2 preview; new28 + unchanged affected v1 four."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_style_filter as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-options-product333.v1.json';DRIVER='tools/p09/run_font_options_product.py'
STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/fonts.rs';PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement/fonts.rs'
PARENT='crates/product-cli/tests/scoped_font_product.rs';TEST='crates/product-cli/tests/support/scoped_font_options.rs'
NEW={DRIVER,TEST,STORED[:-3]+'/options.rs',PRODUCT[:-3]+'/options.rs'}
LINK='#[path="support/scoped_font_options.rs"]mod font_options_v2;\n'
AFFECTED={'malformed_unknown_missing_and_enum_object_json_reject_before_artifact_reads','redacted_receipts_and_denied_route_leave_original_head_and_ingest_count_unchanged',
    'final_head_race_inside_delivery_blocks_consumer','product_document_candidate_is_owned_verified_and_changes_actual_source_refs'}

def inverse(q,old):
    for path in (STORED,PRODUCT):
        text=q.text(path);c.require(text.count('pub mod options;\n')==1,'ONE_OPTIONS_MODULE_EXPORT');audit.inverse(text.replace('pub mod options;\n',''),old[path],'ORIGINAL_V1_STORED_AND_PRODUCT_ALGORITHMS_UNCHANGED')
    text=q.text(PARENT);c.require(text.count(LINK)==1,'ONE_OPTIONS_TEST_MODULE_LINK');audit.inverse(text.replace(LINK,''),old[PARENT],'ALL_PREVIOUS80_PRODUCT_TESTS_AND_FIXTURES_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_OPTIONS_PRODUCT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_OPTIONS_PRODUCT',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False,common_v2_compiler_or_dispatcher_connected=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='1f9a46abf434fd5bcccae9d246f1861afb652e98ff6c6419bbde996357b08cfd'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==769 and passed['new_cases']==18 and passed['affected_cases']==6,'EXACT331_FILTERED_CORE24_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in {STORED,PRODUCT,PARENT}:c.require(q.snapshots[n]==old[n],'ALL_CORE_GUARDS_WRITER_READBACK_EXISTING_TESTS_AND_VERIFIERS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_STORED_OPTIONS_PRODUCT_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'font_options_v2::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}|AFFECTED
        c.require(len(cases)==32 and len(AFFECTED)==4,'EXACT_NEW28_AFFECTED_V1_FOUR')
        scratch=c.ROOT/'target/p09-font-options-product-scratch-333';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_OPTIONS_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='FONT_OPTIONS_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=28,affected_cases=4,official249_replayed=False)),flush=True)
        harness.run_one('font_options_product28_affected_v1_four',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.previous.previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_OPTIONS_PRODUCT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_OPTIONS_STORED_PRODUCT_PREVIEW28_AFFECTED_V1_FOUR_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=28,affected_cases=4,preview_output_artifact_discarded=True,preview_has_no_compiler_or_inventory_api=True,
            original_v1_algorithms_and_test_bodies_unchanged=True,next_work='common_v2_font_candidate_and_explicit_nonmutating_preview_dispatch')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_OPTIONS_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_OPTIONS_PRODUCT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
