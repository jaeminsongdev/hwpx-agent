"""326: real stored/common font review/field/protection16 against unchanged production."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_compiled_font_recovery as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-review-components326.v1.json';DRIVER='tools/p09/run_font_review_components.py'
PARENT=previous.previous.base.TEST;TEST='crates/product-cli/tests/support/scoped_font_review.rs';FIXTURE='crates/hwpx-package/tests/support/review_scope_fixture.rs'
NEW={DRIVER,TEST,FIXTURE};LINK='#[path="support/scoped_font_review.rs"]mod font_review_v1;\n'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_REVIEW_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_REVIEW_COMPONENTS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,previous56_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='03833b97cf9144c6095528edbb425611a7800dacb5b5a5835a97a3dca051a545'and passed['cleanup']and passed['final_fresh_hashes']==753,'EXACT324_FONT_COMMON_SOURCE_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW|{PARENT}
        for n in sorted(names):
            q.pin(n)
            if n in old and n!=PARENT:c.require(q.snapshots[n]==old[n],'ALL_PRODUCTION_PARSER_GUARDS_MATCHER_RENDERER_WRITER_READBACK_AND_PREVIOUS_TESTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_REVIEW_TEST_AND_ORIGINAL_FIXTURE_INPUTS_ADDED')
        text=q.text(PARENT);c.require(text.count(LINK)==1,'ONE_REVIEW_TEST_MODULE_LINK');audit.inverse(text.replace(LINK,''),old[PARENT],'ALL_PREVIOUS56_TEST_BODIES_UNCHANGED')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'font_review_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))};c.require(len(cases)==16,'EXACT16_REVIEW_CACHE_AND_ANCESTOR_PROTECTION_CASES')
        scratch=c.ROOT/'target/p09-font-review-scratch-326';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_REVIEW_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='FONT_REVIEW_PREFLIGHT',inputs=len(q.snapshots),new_review_cases=16,production_unchanged_from324=True,old56_and_official249_replayed=False)),flush=True)
        harness.run_one('font_review_field_protection16',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','font_review_v1::','--test-threads=1'],cases,guard,env,row,observe_capture=previous.previous.base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_REVIEW_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_REVIEW_CACHE_AND_ANCESTOR_PROTECTION16_NOT_FULL_OPTIONS_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=16,
            next_work='remaining_font_style_filter_preview_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_REVIEW_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_REVIEW_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
