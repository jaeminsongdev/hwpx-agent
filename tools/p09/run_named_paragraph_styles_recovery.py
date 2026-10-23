"""338: supplement exact historical paragraph-test pin absent from335; no test/production changes."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_paragraph_styles as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-paragraph-styles-recovery338.v1.json';DRIVER='tools/p09/run_named_paragraph_styles_recovery.py'
SUPPLEMENT='implementation/p09/evidence/p09-361-paragraph-style-fixture-recovery142.v1.json'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_PARAGRAPH_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_PARAGRAPH_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,stored_product_common_dispatch_or_preview_connected=False,
        production_and_tests_unchanged_from337=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT));baseline=compact.unpack(q.json(previous.previous.OUTPUT));supplement=q.json(SUPPLEMENT)
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='ac2f7e9921e914169c4ea535df0a438166567b72b9fa552dbc54384893b41fb9'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==784 and failed['error_type']=='KeyError'and failed['steps']==[],'EXACT337_BEFORE_CARGO_MISSING_HISTORICAL_TEST_PIN_FAILURE_PRESERVED')
        c.require(q.snapshots[previous.previous.OUTPUT]['sha256']=='47073d385a8453f7d306dc36d15fda6d63765d4390c417e367db1280629e2d78'and baseline['cleanup'],'EXACT335_CURRENT_SOURCE_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(previous.CORE in old and previous.PARENT not in old,'EXACT_ORIGINAL_PARAGRAPH_TEST_OUTSIDE335_SOURCE_SCOPE')
        c.require(q.snapshots[SUPPLEMENT]['sha256']=='8d96f12627a043474a009552c0c51ee29f73f9b41c6eb5b62c66afc2cbb9eb91'and supplement['cleanup']
            and supplement['state']=='PASS_PARAGRAPH_STYLE_ONE_REPAIRED_THIRTY_SEVEN_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE','EXACT142_HISTORICAL_PARAGRAPH_TEST_SUPPLEMENT')
        historical={p['path']:p for p in supplement['source_pins']};old[previous.PARENT]=historical[previous.PARENT]
        c.require(old[previous.PARENT]==dict(path=previous.PARENT,bytes=20737,sha256='aedf1d89762b433850705903273c18a86bcacc3693ed73a77fd3ba4feaafb93d'),'EXACT_ORIGINAL_PARENT_BYTES_AND_SHA')
        for pin in failed['source_pins']:
            q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'ALL337_PRODUCTION_TEST_AND_VERIFIER_INPUTS_UNCHANGED')
        q.pin(DRIVER);previous.inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(previous.TEST))}|previous.AFFECTED
        c.require(len(cases)==26 and len(previous.AFFECTED)==7,'SAME_NEW19_UNEXECUTED_AFFECTED7_CASES')
        scratch=c.ROOT/'target/p09-named-paragraph-style-scratch-338';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_PARAGRAPH_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_PARAGRAPH_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),new_cases=19,affected_cases=7,production_and_tests_unchanged=True)),flush=True)
        harness.run_one('named_paragraph_styles19_affected_original7_historical_pin',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_paragraph_style_replacement',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'NAMED_PARAGRAPH_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_PARAGRAPH_STYLE_SOURCE_BATCH19_AFFECTED7_NOT_FULL_SEARCH025_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=19,affected_cases=7,next_work='named_style_current_stored_product_preview_and_character_style_support')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_PARAGRAPH_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_PARAGRAPH_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
