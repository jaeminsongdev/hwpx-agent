"""312: hash the canonical checked path string, not non-serializable PackagePath."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_scoped_font_recovery as previous
base=previous.previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-scoped-font-path-recovery312.v1.json';DRIVER='tools/p09/run_scoped_font_path_recovery.py'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SCOPED_PATH_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SCOPED_PATH_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='9f3942592f9419c5a267feada29ab18e985abd414de2dd89afd9167e8e901d32'and failed['cleanup']and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['bounded_output_observation']['safe_compiler_traits']==['path::PackagePath: serde::Serialize'],'EXACT311_PATH_SERIALIZATION_COMPILE_FAILURE')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=base.CORE:c.require(q.snapshots[n]==old[n],'ALL_TESTS_FIXTURES_AND_OTHER_SOURCE_CODE_UNCHANGED')
        text=q.text(base.CORE);marker='|(a,e)|(p.as_str(),*a,e.end,';c.require(text.count(marker)==1,'ONE_CHECKED_PATH_STRING_SERIALIZATION_FIX')
        audit.inverse(text.replace(marker,'|(a,e)|(p,*a,e.end,'),old[base.CORE],'ALL_SCOPE_NAME_CLONE_PROTECTION_AND_READBACK_ALGORITHMS_UNCHANGED')
        q.pin(DRIVER)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'scoped::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))};c.require(len(cases)==20,'SAME20_UNEXECUTED_CASES')
        scratch=c.ROOT/'target/p09-scoped-font-scratch-312';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'SCOPED_PATH_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='SCOPED_PATH_PREFLIGHT',inputs=len(q.snapshots),selected_cases=20,old24_and_official249_replayed=False)),flush=True)
        harness.run_one('scoped_font20_canonical_checked_path',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_scoped_fonts',
            '--message-format=short','--','scoped::','--test-threads=1'],cases,guard,env,row,observe_capture=previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'SCOPED_PATH_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SCOPED_FONT_NAME_AND_RUN_TEXT_CLONE20_NOT_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=20,
            old24_and_official249_replayed=False,next_work='current_stored_access_and_strict_product_binding_of_scoped_font_candidates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'SCOPED_PATH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'SCOPED_PATH_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
