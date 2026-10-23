"""Keep205 failure and16 passes; correct unsupported legacy fixture attribute, run only failed10."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_mutation_dispatch_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-search-mutation-dispatch-recovery206.v1.json'
DRIVER='tools/p09/run_search_mutation_dispatch_recovery.py'
SOURCE_ADDITION='        0..=6 => definition::package(&para(1,"K").replace(" charStyleIDRef=\'0\'","")),\n'
OLD_END='    assert_eq!(s.metadata.audit_events()?.len(),before);assert!(!called.get());Ok(())\n'
NEW_END='''    assert_eq!(s.metadata.audit_events()?.len(),before);assert!(!called.get());
    let Operation::SearchMutation(candidate)=out else{return Err("kind".into())};
    assert_eq!(format!("{:?}",candidate.receipt()),"SearchMutationReceiptRef(<redacted>; candidate_only)");Ok(())
'''
DEBUG_ADDITION='''impl std::fmt::Debug for SearchMutationReceiptRef<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("SearchMutationReceiptRef(<redacted>; candidate_only)")
    }
}
'''


def inventory(check):return base.inventory(check)|{DRIVER}


def snapshot(capture,expected):
    result=base.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    # Closed identifier/code domains only, never source text, values or full error/log lines.
    allowed={'Stored','Output','Compile','Patch','Source','Search','Value','Selection','Protection','FieldContent','NoMatches','NoChange','Limit','Writer','Readback','Preservation','Definition','Request','Binding','Import','Body','SearchMutation','Literal','LiteralAtoms','ReviewLiteral','SelectorLiteral','Regex','RegexInsertion','CharacterStyle'}
    result['closed_nested_error_variants']=[n for n in re.findall(r'\b([A-Za-z_]+)\(',raw)if n in allowed]
    codes={'id_index_unknown_id_like_attribute','id_index_dangling_reference','id_index_duplicate_declaration','id_index_invalid_value','id_index_invalid_profile','patch_selector_stale','patch_conflict','patch_limit_exceeded'}
    result['closed_patch_codes']=[n for n in re.findall(r'Patch\("([a-z0-9_]{1,96})"\)',raw)if n in codes]
    return result


def inverse(q,old):
    text=q.text(base.TEST);c.require(text.count(SOURCE_ADDITION)==text.count(NEW_END)==1,'ONLY_LEGACY_ZERO_TO_SIX_ATTRIBUTE_AND_FAILED_BINDING_DEBUG_ASSERTION_CHANGED')
    audit.inverse(text.replace(SOURCE_ADDITION,'').replace(NEW_END,OLD_END),old[base.TEST],'ENTIRE26_TEST_BODIES_EXCEPT_ONE_FAILED_DEBUG_ASSERTION_AND_ALL_OTHER_FIXTURE_BRANCHES_PRESERVED')
    text=q.text(base.MODEL);c.require(text.count(DEBUG_ADDITION)==1,'ONE_ADDITIVE_REDACTED_BORROWED_RECEIPT_DEBUG')
    audit.inverse(text.replace(DEBUG_ADDITION,''),old[base.MODEL],'ENTIRE_PRODUCT_DISPATCH_TABLE_OWNERS_ORIGINAL_PARSERS_BUDGETS_VERIFICATION_AND_ROUTE_BODIES_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SEARCH_DISPATCH_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_MUTATION_DISPATCH_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,
        compiled_queue_reexecuted=False,full_search_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);c.require(q.snapshots[base.OUTPUT]['sha256']=='38c9ea9baa45d7a83eee1b6088a7991796cbae071e05cb241fec62ee2cd6aebf'
            and failed['state']=='FAILED_SEARCH_MUTATION_DISPATCH_COMPONENTS'and failed['cleanup'],'EXACT205_FAILED_RECORD_AND_TERMINAL_CLEANUP_PRESERVED')
        tests=failed['steps'][0]['tests'];passed={n for n,s in tests if s=='ok'};cases={n for n,s in tests if s!='ok'}
        c.require(len(passed)==16 and len(cases)==10 and passed|cases==base.expected(q),'ORIGINAL16_PASS_AND10_FAILURE_IDENTITIES')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{DRIVER,base.MODEL,base.TEST}:c.require(q.snapshots[name]==old[name],'ALL_OTHER205_PRODUCT_SERVICE_SOURCE_WRITER_AND_TEST_INPUTS_UNCHANGED')
        inverse(q,old);baseline=q.json(base.prior.OUTPUT);base.inverse(q,{p['path']:p for p in baseline['source_pins']})
        print(json.dumps(dict(state='SEARCH_DISPATCH_FAILED10_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained_passes=16,only_failed_cases=10)),flush=True)
        harness.run_one('ten_failed_dispatch_cases_legacy_fixture_recovery',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_DISPATCH_RETAINED16_RECOVERED10_NOT_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_recovery_cases=10,retained_passed_cases=16,distinct_current_dispatch_cases=26,dispatched_mutation_families=16,old292_products_reexecuted=False,
            passed16_reexecuted=False,original_form_formula_bodies_inverse_verified=True,original_mutation_product_bodies_unchanged=True,
            legacy_fixture_attribute_removed_only_for_unsupported_families=True,borrowed_receipt_debug_redacted=True,
            next_work='actual_product_transaction_route_manifest_and_durable_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SEARCH_DISPATCH_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_DISPATCH_RECOVERY_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
