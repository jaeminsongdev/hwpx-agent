"""Recover the single borrow error from300; original failed receipt and test bodies preserved."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_reference_components as prior
shared,c,a,tools,compact,harness,audit=prior.shared,prior.c,prior.a,prior.tools,prior.compact,prior.harness,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-font-reference-recovery301.v1.json'
DRIVER='tools/p09/run_font_reference_recovery.py'
SCRATCH='target/p09-font-reference-scratch-301'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_REFERENCE_RECOVERY',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,prior_Native_replayed=False,
        actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_or_scoped_product_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='ad10008fb87f05f1dce80c757f6817f0d753d2c7aef2ee2fac371b90f3214981'and failed['cleanup']
            and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0308'],'EXACT300_COMPILE_FAILURE_BEFORE_TESTS')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=prior.CORE:c.require(q.snapshots[n]==old[n],'ALL300_TESTS_FIXTURES_GUARDS_AND_OTHER_SOURCES_UNCHANGED')
        q.pin(DRIVER);text=q.text(prior.CORE);marker='PatchText::new(&c.target.to_string())'
        c.require(text.count(marker)==1,'ONE_TYPED_BORROW_FIX')
        audit.inverse(text.replace(marker,'PatchText::new(c.target.to_string())'),old[prior.CORE],'ONLY_ONE_BORROW_NO_ALGORITHM_OR_TEST_CHANGE')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(prior.TEST)));c.require(len(cases)==14,'ORIGINAL14_TEST_BODIES_PRESERVED')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='FONT_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),prior249_replayed=False)),flush=True)
        harness.run_one('font_reference_source14_after_borrow_fix',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_font_replacement','--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_REFERENCE_SOURCE14_NOT_SCOPED_SEARCH_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=14,
            official249_and_other_old_suites_replayed=False,next_work='font_name_query_and_scoped_selection_then_current_stored_and_product_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
