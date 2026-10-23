"""Keep78 actual passes; correct only invalid empty-query test inputs and execute8 failures+1 new case."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-recovery119.v1.json'
NEW_TEST='insertions_empty_query_remains_rejected_separately_from_a_regex_that_matches_empty'
SUFFIX='''#[test]
fn insertions_empty_query_remains_rejected_separately_from_a_regex_that_matches_empty()->TestResult {
    let raw=package("AB")?;let f=forms(&raw)?;
    assert!(matches!(replace(&f,&raw,"",Scope::Document,all(),"X"),Err(E::Search(SourceSearchError::Limit))));
    let out=replace(&f,&raw,"(?:)",Scope::Document,all(),"X")?;exact(&raw,&out,section(&raw)?.replace(">AB<",">XAXBX<"))?;Ok(())
}
'''


def test_inverse(q,old):
    text=q.text(base.TEST);c.require(text.endswith(SUFFIX)and text.count(SUFFIX)==1,'ONE_ADDITIVE_EMPTY_QUERY_CONTRACT_NEGATIVE_TEST')
    prefix=text[:-len(SUFFIX)];c.require(prefix.count('"(?:)"')==11,'ELEVEN_INVALID_EMPTY_QUERY_INPUTS_CORRECTED_ONLY_IN_EIGHT_FAILED_CASES')
    audit.inverse(prefix.replace('"(?:)"','""'),old[base.TEST],'WHOLE_ORIGINAL_TEST_FILE_RESTORED_BY_ONLY_QUERY_CORRECTIONS_AND_ADDITIVE_CASE_REMOVAL')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_RECOVERY',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_zero_width_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);c.require(q.snapshots[base.OUTPUT]['sha256']=='209ef610f9b8f4024b12eec7edc398658637c00274f0415289e7c67493b929c0'
            and failed['state']=='FAILED_REGEX_INSERTION_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_EIGHT_FAILURES_WITH_TERMINAL_CLEANUP_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==old[name],'NO_PRODUCTION_GUARD_WRITER_FIXTURE_OR_PREVIOUSLY_PASSING_ORIGINAL_TEST_INPUT_CHANGED')
        test_inverse(q,old);base.boundaries(q)
        step=failed['steps'][0];retained={n for n,s in step['tests']if s=='ok'};retry={n for n,s in step['tests']if s=='FAILED'}
        c.require(len(retained)==78 and len(retry)==8 and step['exit_code']==101 and all(n.startswith('regex_insertions::')for n in retry),'EXACT_SEVENTY_EIGHT_PASSES_EIGHT_NEW_TEST_INPUT_FAILURES')
        core=retry|{'regex_insertions::'+NEW_TEST};products=base.prior.expected(q)
        print(json.dumps(dict(state='REGEX_INSERTION_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),retained_cases=78,recovery_cases=9,affected_product_cases=29)),flush=True)
        harness.run_one('eight_corrected_failed_queries_and_one_empty_query_negative',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','regex_insertion_focused','--',*sorted(core),'--exact','--test-threads=1'],core,guard,audit.environment(),row,observe_capture=snapshot)
        harness.run_one('twenty_nine_original_v1_regex_and_selector_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--','--test-threads=1'],products,guard,audit.environment(),row,observe_capture=snapshot)
        for step in row['steps']:
            limits=step['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
                'ORIGINAL_SINGLE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(base.inventory(guard.check)==names,'FINAL_INSERTION_RECOVERY_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_NINETEEN_NEW_NINETY_SEVEN_AFFECTED_NOT_STORED_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_core_cases=19,retained_core_passes=78,actual_recovery_cases=9,affected_core_patch_cases=68,affected_original_product_cases=29,
            total_distinct_core_cases=87,total_distinct_cases=116,total_executed_cases=38,previous_seventy_eight_passes_reexecuted=False,
            original_failure_record_and_production_code_preserved=True,whole_test_file_inverse_verified=True,
            next_work='Explicit_v2_zero_width_current_stored_and_strict_product_binding_then_remaining_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSERTION_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
