"""344: named receipt metadata uses validated server result budget; new384/exact-bound tests + affected3."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_style_product as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-product-metadata344.v1.json';DRIVER='tools/p09/run_named_style_product_metadata.py'
SEARCH='crates/hwpx-package/src/document_import/search.rs';PRODUCT=previous.PRODUCT;TEST=previous.TEST
AFFECTED={'preview_predicts_same_result_but_discards_output_and_never_calls_byte_consumer','exact_sixteen_kib_and_query_and_request_count_limits_reject_before_source_reads','request_server_and_writer_limits_apply_to_mutation_and_preview'}

def inverse(q,old):
    text=q.text(SEARCH);marker='    #[must_use] pub const fn maximum_result_bytes(self)->usize{self.0.result_bytes}\n';c.require(text.count(marker)==1,'ONE_IMMUTABLE_SERVER_RESULT_BUDGET_GETTER')
    audit.inverse(text.replace(marker,''),old[SEARCH],'ALL_ORIGINAL_SEARCH_LIMIT_CONSTRUCTION_VALIDATION_AND_ALGORITHMS_UNCHANGED')
    text=q.text(PRODUCT)
    text=text.replace('NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES:usize=4*1024*1024','NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES:usize=64*1024')
    text=text.replace(',maximum_metadata_bytes:usize}', '}').replace('        let maximum_metadata_bytes=limits.maximum_result_bytes().min(NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES);\n','')
    text=text.replace('bounded(&receipt,maximum_metadata_bytes)','bounded(&receipt,NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES)').replace('{request,prepared,receipt,maximum_metadata_bytes}','{request,prepared,receipt}')
    text=text.replace('        if self.maximum_metadata_bytes==0||self.maximum_metadata_bytes>NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES{return Err(N::Binding);}\n','').replace('bounded(&self.receipt,self.maximum_metadata_bytes)','bounded(&self.receipt,NAMED_STYLE_PRODUCT_MAX_METADATA_BYTES)')
    audit.inverse(text,old[PRODUCT],'ALL_PREVIOUS_STRICT_JSON_QUERY_AUTHORITY_HEAD_PREVIEW_DISCARD_AND_WRITER_GUARDS_UNCHANGED')
    text=q.text(TEST);start=text.index('// Named metadata server-budget boundary cases begin.\n');end=text.index('// Named metadata server-budget boundary cases end.\n',start)+len('// Named metadata server-budget boundary cases end.\n')
    audit.inverse(text[:start]+text[end:],old[TEST],'ALL_PREVIOUS29_TEST_BODIES_AND_FIXTURE_HELPERS_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_STYLE_PRODUCT_METADATA_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_STYLE_PRODUCT_METADATA',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,common_dispatcher_or_compiler_connected=False,previous_source26_or_font35_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='97b2c77bf78accbaf2a75c9095a7ac9443b2154838ffcd0e20dd6e487f521b95'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==798 and len(passed['steps'])==1 and len(passed['steps'][0]['tests'])==29,'EXACT343_ORIGINAL29_PASSED_PRODUCT_CASES')
        old={p['path']:p for p in passed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n not in {SEARCH,PRODUCT,TEST}:c.require(q.snapshots[n]==old[n],'ALL_STORED_CORE_WRITER_SCANNER_AND_OTHER_INPUTS_UNCHANGED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        current=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));retained={n for n,status in passed['steps'][0]['tests']if status=='ok'}
        new=current-retained;cases=new|AFFECTED;c.require(len(current)==31 and len(new)==2 and len(cases)==5 and len(retained-AFFECTED)==26,'EXACT_NEW2_AFFECTED3_RETAINED26_CURRENT31')
        scratch=c.ROOT/'target/p09-named-style-product-metadata-scratch-344';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_STYLE_PRODUCT_METADATA_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_STYLE_PRODUCT_METADATA_PREFLIGHT',inputs=len(q.snapshots),new_cases=2,affected_cases=3,retained_cases=26,sample_paragraphs=384)),flush=True)
        harness.run_one('named_style_server_metadata_new2_affected3',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','named_style_product',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.previous.base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'NAMED_STYLE_PRODUCT_METADATA_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_STYLE_SERVER_METADATA_NEW2_AFFECTED3_RETAINED26_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_cases=5,new_cases=2,affected_cases=3,retained_cases=26,distinct_product_cases=31,server_result_budget_honored=True,sample_paragraphs=384,
            next_work='named_style_common_mutation_compiler_and_separate_preview_dispatch')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_STYLE_PRODUCT_METADATA_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_STYLE_PRODUCT_METADATA_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
