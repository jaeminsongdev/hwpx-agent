"""Retain78 passes from158, repair three new oracles, execute exactly those three cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_normalization_recovery as previous
base=previous.base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-normalization-failed-cases159.v1.json'
CASES={'unicode::unicode_ancestor_tracking_is_checked_before_noop_elimination',
    'unicode::unicode_limits_reject_components_expansion_receipt_and_writer_without_partial_output',
    'unicode::unicode_partial_inverse_of_one_expanding_original_scalar_is_rejected'}
EXTRA='''    let expanded=fixture::package(&para(1,"ﬃ"))?;let ef=forms(&expanded)?;
    assert!(matches!(ef.lower_review_selector_unicode_candidate(&expanded,Scope::Document,all(),Form::Nfkd,Run::FirstOriginalRunRetainAllRuns,
        SourceSearchLimits::new(Config {decomposed_scalars:2,..Default::default()})?,Default::default()),Err(E::Limit)));
'''


def repairs(q,pins):
    text=q.text(base.TEST)
    for new,old in[("<hp:p paraTcId='0' id='1'","<hp:p charTcId='0' id='1'"),
        ('Form::Nfd),Err(E::Search(hwpx_package::document_import::search::SourceSearchError::Scope)))','Form::Nfd),Err(E::Selection))'),
        ('Form::Nfkc,Run::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(config)?','Form::Nfkd,Run::FirstOriginalRunRetainAllRuns,SourceSearchLimits::new(config)?'),(EXTRA,'')]:
        c.require(text.count(new)==1,'ONE_OF_EXACT_THREE_FAILED_TEST_ORACLE_REPAIRS');text=text.replace(new,old)
    audit.inverse(text,pins[base.TEST],'WHOLE_TEST_FILE_EXACTLY_UNCHANGED_OUTSIDE_THREE_FAILED_BODIES')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_FAILED_CASE_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_THREE_CASE_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search022_product_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(previous.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='ea53e63363b1b407028dc5f76af1421aa3873e1d960cddb00e27415984488628'
            and failed['state']=='FAILED_UNICODE_NORMALIZATION_RECOVERY'and failed['cleanup']and len(failed['steps'])==1,'EXACT_ORIGINAL_158_FAILURE_PRESERVED')
        step=failed['steps'][0];retained={n for n,s in step['tests']if s=='ok'}
        c.require(step['exit_code']==101 and len(retained)==78 and {n for n,s in step['tests']if s!='ok'}==CASES
            and step['safe_error_variants']==['Body']and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'EXACT_78_COMPLETED_PASSES_THREE_FAILED_ORACLES_AND_TERMINAL_JOB')
        pins={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_PRIOR_TESTS_FIXTURES_AND_LIMITS_UNCHANGED_AFTER158')
        repairs(q,pins);base.inverse(q,{p['path']:p for p in baseline['source_pins']});c.require(base.expected(q)==retained|CASES,'EXACT_81_DISTINCT_CASES_WITH78_RETAINED')
        print(json.dumps(dict(state='UNICODE_THREE_CASE_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),current_cases=3,retained_cases=78,one_cpu_mask=4)),flush=True)
        harness.run_one('three_repaired_new_normalization_oracles_only',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','unicode_normalization_focused','--message-format=short','--',*sorted(CASES),'--exact','--test-threads=1'],CASES,guard,audit.environment(),row,observe_capture=snapshot)
        base.good_step(row['steps'][0],CASES);c.require(base.inventory(guard.check)==names,'FINAL_UNICODE_THREE_CASE_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_3_REPAIRED_78_RETAINED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_source_cases=3,retained_source_cases=78,total_distinct_cases=81,new_source_cases=24,affected_source_cases=57,
            previous_78_passes_reexecuted=False,production_unchanged_after157=True,original_common_code_and_test_bodies_inverse_verified=True,
            next_work='Current_stored_service_strict_product_request_and_full_SEARCH022_contract_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_THREE_CASE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_THREE_CASE_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
