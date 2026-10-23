"""Keep37 passed bodies/production unchanged; repair and execute only the nonadmitted fixture case."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_paragraph_style_recovery as previous
base=previous.base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-paragraph-style-fixture-recovery142.v1.json'
FAILED='implementation/p09/evidence/p09-361-paragraph-style-recovery141.v1.json'
CASE='paragraph_style::paragraph_style_one_protected_request_rejects_the_whole_multi_paragraph_batch'
OLD='''    let bytes=fixture::package(&(p(1,"K")+&p(2,"K").replace("<hp:p id='2'","<hp:p id='2' lock='1'")))?;let original=bytes.clone();let f=forms(&bytes)?;
'''
NEW='''    let locked=table::table(300).replace("lock='0'","lock='1'");let bytes=fixture::package(&(p(1,"K")+&p(2,&format!("K</hp:t>{locked}<hp:t>TAIL"))))?;let original=bytes.clone();let f=forms(&bytes)?;
'''


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PARAGRAPH_FIXTURE_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PARAGRAPH_STYLE_FIXTURE_RECOVERY',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_paragraph_style_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(FAILED);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[FAILED]['sha256']=='e1e216f549d24c71c873be0692aa7ca6969c9a003b2f21389aa557ddb1c2d40b'
            and failed['state']=='FAILED_PARAGRAPH_STYLE_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1
            and failed['steps'][0]['safe_error_variants']==['Body'],'EXACT_37_PASS_ONE_NONADMITTED_FIXTURE_FAILURE_PRESERVED')
        all_cases=base.expected(q);retained={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        c.require(len(retained)==37 and all_cases==retained|{CASE}
            and {n for n,s in failed['steps'][0]['tests']if s!='ok'}=={CASE},'EXACT_THIRTY_SEVEN_PASSES_AND_ONE_FAILED_CASE_IDENTITY')
        pins={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_OLD_TESTS_AND_FIXTURE_HELPERS_UNCHANGED')
        text=q.text(base.TEST);c.require(text.count(NEW)==1,'ONE_NONADMITTED_PARAGRAPH_LOCK_FIXTURE_REPLACED_BY_ADMITTED_LOCKED_TABLE')
        audit.inverse(text.replace(NEW,OLD),pins[base.TEST],'WHOLE_NEW_TEST_FILE_UNCHANGED_EXCEPT_ONE_FAILED_INPUT_LINE')
        c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='29718112cc55901e2d8e694f918cc20ba9aad78def2137f9d4eb7226bddf089a','EXACT_PREVIOUS_TEXT_PRODUCT_BASELINE')
        previous.original_inverse(q,{p['path']:p for p in baseline['source_pins']})
        print(json.dumps(dict(state='PARAGRAPH_FIXTURE_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),failed_case_only=1,retained_passes=37,one_cpu_mask=4)),flush=True)
        harness.run_one('one_paragraph_atomicity_case_with_admitted_locked_descendant',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','paragraph_style_replacement_focused','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,'ORIGINAL_JOB_LIMITS_PRESERVED')
        c.require(base.inventory(guard.check)==names,'FINAL_PARAGRAPH_FIXTURE_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_PARAGRAPH_STYLE_ONE_REPAIRED_THIRTY_SEVEN_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            actual_current_cases=1,retained_cases=37,total_distinct_cases=38,new_paragraph_style_cases=20,affected_original_cases=18,previous_passed_cases_reexecuted=False,
            original_common_code_and_test_bodies_inverse_verified=True,one_failed_fixture_line_only=True,
            next_work='Current_stored_and_strict_product_binding_for_paragraph_axes_then_effective_style_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PARAGRAPH_FIXTURE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PARAGRAPH_FIXTURE_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','safe_error_variants')},
                'warnings':s.get('bounded_output_observation',{}).get('safe_warning_locations',[]),'short_errors':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
