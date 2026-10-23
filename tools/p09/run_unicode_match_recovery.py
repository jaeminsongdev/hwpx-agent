"""Retain41 passes; repair one regex-over-NFC test oracle and run that case alone."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_match_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-match-recovery164.v1.json'
CASE='matches::unicode_match_selected_tab_is_retained_and_splits_normalization_groups'
OLD='''    let c=run(&f,&raw,Query {mode:Mode::Regex,..query("a\\t̀à")},Scope::Document,all(),None,Form::Nfc)?;
'''
NEW='''    assert!(matches!(run(&f,&raw,Query {mode:Mode::Regex,..query("a\\t̀à")},Scope::Document,all(),None,Form::Nfc),Err(E::NoMatches)));
    let c=run(&f,&raw,Query {mode:Mode::Regex,..query("a\\t̀à")},Scope::Document,all(),None,Form::Nfc)?;
'''


def repair(q,pins):
    text=q.text(base.TEST);c.require(text.count(NEW)==1,'ONE_FAILED_REGEX_TEST_EXPLICITLY_RETAINS_OLD_NOMATCHES_AND_USES_NFC_PATTERN')
    audit.inverse(text.replace(NEW,OLD),pins[base.TEST],'ENTIRE_NEW_MATCH_SUITE_EXACTLY_RESTORED_EXCEPT_ONE_FAILED_REGEX_ORACLE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_MATCH_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=base.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_MATCH_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,match_normalization_stored_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='7cd0d7c55159120bd313949f3bffa04657f0b390a6b6e49f4acd84a80b9e6485'
            and failed['state']=='FAILED_UNICODE_MATCH_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'EXACT_ORIGINAL163_NOMATCHES_FAILURE_PRESERVED')
        step=failed['steps'][0];retained={n for n,s in step['tests']if s=='ok'}
        c.require(step['exit_code']==101 and len(retained)==41 and {n for n,s in step['tests']if s!='ok'}=={CASE}
            and step['safe_error_variants']==['NoMatches']and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'EXACT_41_SOURCE_PASSES_ONE_REGEX_ORACLE_FAILURE_AND_TERMINAL_JOB')
        pins={p['path']:p for p in failed['source_pins']}
        for name in names-{base.TEST}:c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_GUARDS_LIMITS_PRIOR_TESTS_AND_FIXTURES_UNCHANGED_AFTER163')
        repair(q,pins);c.require(q.snapshots[base.prior.OUTPUT]['sha256']=='1e3606982c37b493d59756f55daca0e7b029439fcaa3f4734881a43525b537af','EXACT_PRIOR161_SCOPE_PRODUCT_BASELINE')
        base.inverse(q,{p['path']:p for p in baseline['source_pins']});c.require(base.expected(q)==retained|{CASE},'EXACT_42_DISTINCT_IDENTITIES_WITH41_RETAINED')
        print(json.dumps(dict(state='UNICODE_MATCH_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),current_cases=1,retained_cases=41,one_cpu_mask=4)),flush=True)
        harness.run_one('one_corrected_regex_pattern_over_original_nfc_corpus',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','unicode_match_normalization_focused','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,audit.environment(),row,observe_capture=snapshot)
        base.base.good_step(row['steps'][0],{CASE});c.require(base.inventory(guard.check)==names,'FINAL_UNICODE_MATCH_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_MATCH1_REPAIRED_41_RETAINED_NOT_MATCH_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_source_cases=1,retained_source_cases=41,new_source_cases=18,affected_scope_cases=24,total_distinct_cases=42,
            production_unchanged_after163=True,passed41_cases_reexecuted=False,unrelated57_source_and150_products_reexecuted=False,
            original_scope_body_and_all_other_matcher_product_inputs_inverse_verified=True,
            next_work='Current_stored_service_and_strict_match_normalization_product_request_then_remaining_full_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_MATCH_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_UNICODE_MATCH_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
