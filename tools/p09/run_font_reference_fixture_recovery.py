"""302: public XML spans fix a fixture-only private-method error; no production change."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_reference_recovery as previous
prior=previous.prior
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-reference-fixture-recovery302.v1.json'
DRIVER='tools/p09/run_font_reference_fixture_recovery.py'
SCRATCH='target/p09-font-reference-scratch-302'
BEFORE='                Ok(n.attributes().iter().find(|a|a.name().local_name()=="id").ok_or("font id")?.semantic_value().parse()?)\n'
AFTER='                let span=n.attributes().iter().find(|a|a.name().local_name()=="id").ok_or("font id")?.value_span();\n                Ok(text[span.start()..span.end()].parse()?)\n'

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_FIXTURE_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_FIXTURE_RECOVERY',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False,prior_Native_replayed=False,
        actual_DB_or_Hangul_or_COM_started=False,full_SEARCH024_or_scoped_product_execution_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='ee9c2be82850874a83005ee4026dd040384d770675d935ef673c26bba9225b22'and failed['cleanup']
            and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0624'],'EXACT301_FIXTURE_PRIVATE_METHOD_COMPILE_FAILURE')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=prior.TEST:c.require(q.snapshots[n]==old[n],'ALL_PRODUCTION_PREVIOUS_DRIVERS_AND_INPUTS_UNCHANGED')
        text=q.text(prior.TEST);c.require(text.count(AFTER)==1,'ONE_FIXTURE_SPAN_READ_FIX')
        audit.inverse(text.replace(AFTER,BEFORE),old[prior.TEST],'ALL_TEST_BODIES_UNCHANGED_EXCEPT_PUBLIC_SPAN_READER')
        q.pin(DRIVER)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text));c.require(len(cases)==14,'EXACT14_UNEXECUTED_FONT_CASES')
        scratch=c.ROOT/SCRATCH;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_FIXTURE_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='FONT_FIXTURE_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),prior249_replayed=False)),flush=True)
        harness.run_one('font_reference_source14_public_fixture_reader',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_font_replacement','--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_FIXTURE_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_REFERENCE_SOURCE14_NOT_SCOPED_SEARCH_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=14,
            official249_and_other_old_suites_replayed=False,next_work='font_name_query_and_scoped_selection_then_current_stored_and_product_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_FIXTURE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_FIXTURE_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
