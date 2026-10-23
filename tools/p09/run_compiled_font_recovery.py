"""324: bind the actual prior18 schema test from249; retain323 before-Cargo failure."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_compiled_font_components as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-compiled-font-recovery324.v1.json';DRIVER='tools/p09/run_compiled_font_recovery.py'
SCHEMA_BASE='implementation/p09/evidence/p09-361-sort-groups-compiler-compact249.v1.json'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'COMPILED_FONT_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_COMPILED_FONT_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,previous36_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.previous.OUTPUT));failed=compact.unpack(q.json(previous.OUTPUT));schema=compact.unpack(q.json(SCHEMA_BASE))
        c.require(q.snapshots[previous.previous.OUTPUT]['sha256']=='cec5c861e4cd4a8386023d843835fc5cb0962479315cb282309e389e041d69ce'and passed['cleanup']and passed['final_fresh_hashes']==745,'EXACT320_COMPILED_SOURCE_BASELINE')
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='4c3b7a5956bbeaec6b5681cfbfe1e45d08a7f7a8e3df22925f339af471c9d26d'and failed['cleanup']and failed['steps']==[]
            and failed['error_code']=='ONLY_DECLARED_FONT_COMPILER_SOURCE_AND_TEST_FILES_ADDED','EXACT323_MISSING_HISTORICAL_TEST_PIN_BEFORE_BUILD')
        c.require(q.snapshots[SCHEMA_BASE]['sha256']=='0e118e7c6d12be8bb8792793e9eb4c4ed08974542f96a940bbd1b1911245e324'and schema['cleanup'],'EXACT249_EXISTING_EIGHTEEN_SCHEMA_TEST_EVIDENCE')
        old={p['path']:p for p in passed['source_pins']};historical={p['path']:p for p in schema['source_pins']}
        c.require(previous.OLD_TEST not in old and historical[previous.OLD_TEST]['sha256']=='4cf73cccbd191f3df87d1416bf3fe880de729ab7e96c34471dba349449c8d812','ONE_ADDITIONAL_HISTORICAL_TEST_INPUT_NOT_NEW_TEST_BODY')
        old[previous.OLD_TEST]=historical[previous.OLD_TEST];new=previous.NEW|{DRIVER};names=previous.closure.inventory(guard.check)|set(old)|new|previous.CHANGED
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in previous.CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_COMPILED_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in new,'ONLY_DECLARED_COMPILER_NEW_FILES')
        for pin in failed['source_pins']:c.require(q.snapshots[pin['path']]==pin,'ALL_SOURCE_INPUTS_REACHED_BY323_UNCHANGED')
        previous.inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'compiled_font_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(previous.TEST))};c.require(len(cases)==20,'SAME16_FONT_COMMON_AND4_AFFECTED_LEGACY_CASES')
        scratch=c.ROOT/'target/p09-compiled-font-scratch-324';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'COMPILED_FONT_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='COMPILED_FONT_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),font_common_cases=16,affected_legacy_cases=4,prior36_and_official249_replayed=False)),flush=True)
        harness.run_one('font_common_compiler16_and_legacy4',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','compiled_font_v1::','--test-threads=1'],cases,guard,env,row,observe_capture=previous.base.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'COMPILED_FONT_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_COMMON_COMPILER_DISPATCH16_LEGACY4_NOT_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_font_common_cases=16,affected_legacy_cases=4,production_changed_from323=False,next_work='qualified_registry_manifest_and_actual_font_execution_storage_with_remaining_full_options_and_native')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'COMPILED_FONT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'COMPILED_FONT_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
