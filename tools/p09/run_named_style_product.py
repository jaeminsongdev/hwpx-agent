"""343: named PARA current stored source, strict product and output-discarded preview29 only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_paragraph_styles_empty_recovery as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-style-product343.v1.json';DRIVER='tools/p09/run_named_style_product.py'
ROOT_STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs';ROOT_PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORED=ROOT_STORED[:-3]+'/named_styles.rs';PRODUCT=ROOT_PRODUCT[:-3]+'/named_styles.rs';TEST='crates/product-cli/tests/named_style_product.rs'
NEW={DRIVER,STORED,PRODUCT,TEST};CHANGED={ROOT_STORED,ROOT_PRODUCT}

def inverse(q,old):
    for path in CHANGED:
        text=q.text(path);c.require(text.count('pub mod named_styles;\n')==1,'ONE_NAMED_STYLE_MODULE_EXPORT');audit.inverse(text.replace('pub mod named_styles;\n',''),old[path],'ALL_PREVIOUS_STORED_AND_PRODUCT_ALGORITHMS_AND_SCHEMA_EXPORTS_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_STYLE_PRODUCT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_STYLE_PRODUCT',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,common_dispatcher_or_compiler_connected=False,
        previous_source26_or_font35_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='93794d7832e36c503c2ff59dccfa1a18286ae1d3a8e824b88a1a308822bde63d'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==793 and passed['executed_cases']==1 and passed['retained_cases']==25,'EXACT341_NAMED_SOURCE26_CURRENT_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_ORIGINAL_CORE_TEST_FIXTURE_AUTHORITY_AND_VERIFIER_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_NAMED_STORED_PRODUCT_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));c.require(len(cases)==29,'EXACT_NEW29_STORED_PRODUCT_PREVIEW_CASES')
        scratch=c.ROOT/'target/p09-named-style-product-scratch-343';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_STYLE_PRODUCT_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_STYLE_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=29,previous_source26_or_font35_replayed=False)),flush=True)
        harness.run_one('named_style_current_stored_strict_product_preview29',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','named_style_product',
            '--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=previous.base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'NAMED_STYLE_PRODUCT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_STYLE_CURRENT_STORED_STRICT_PRODUCT_PREVIEW29_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=29,preview_output_artifact_discarded=True,preview_has_no_compiler_or_inventory_api=True,next_work='named_style_common_mutation_compiler_and_separate_preview_dispatch')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_STYLE_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_STYLE_PRODUCT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
