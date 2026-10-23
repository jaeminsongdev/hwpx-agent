"""Preserve222, keep source10/products32; two valid locked-table fixtures, exact original Protection denial."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_protection_manifest_components as base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-protection-manifest-recovery223.v1.json'
DRIVER='tools/p09/run_source_protection_manifest_recovery.py'
OLD_POS='    let body=para(1,"K")+&para(2,"OTHER").replace("id=\'2\'","id=\'2\' lock=\'1\'");\n'
NEW_POS='''    let locked=table::table(300).replace("lock='0'","lock='1'");
    let body=para(1,"K")+&para(2,&format!("OTHER</hp:t>{locked}<hp:t>TAIL"));
'''
OLD_NEG='''    let bytes=security_fixture::package(&para(1,"K").replace("id='1'","id='1' lock='1'").replace(" charStyleIDRef='0'",""))?;
'''
NEW_NEG='''    use hwpx_agent_cli::form_product_request::stored_operations::compiled_search::CompiledSearchError as CE;
    use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::StoredLiteralSearchError as SE;
    let locked=table::table(300).replace("lock='0'","lock='1'");
    let bytes=security_fixture::package(&para(1,&format!("K</hp:t>{locked}<hp:t>TAIL")).replace(" charStyleIDRef='0'",""))?;
'''
OLD_ASSERT='    assert!(Dispatch::prepare_compiled_search_json(&p,&wire(&req(3,&s,&bytes)?)?,Limits::standard()?,4).is_err());Ok(())\n'
NEW_ASSERT='''    let mut v=req(3,&s,&bytes)?;v["operation"]["query"]=json!("CELL-OLD");
    assert!(matches!(Dispatch::prepare_compiled_search_json(&p,&wire(&v)?,Limits::standard()?,4),
        Err(CE::Request(DE::SearchMutation(ME::SelectorLiteral(LE::Stored(SE::Output(Compile::Protection))))))));Ok(())
'''


def inventory(check):return base.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_PROTECTION_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_PROTECTION_MANIFEST_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_protection_or_crypto_signature_attested=False,trusted_registry_or_native_evidence=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='01f0cc12f4412febddfbd15c74fb2071bbe467d8aedc073086716154b74be024'
            and failed['cleanup']and failed['steps'][0]['exit_code']==0 and failed['steps'][1]['exit_code']==101,
            'EXACT222_SOURCE10_AND_PRODUCT33_PASS_ONE_IMPORT_BODY_FAILURE_PRESERVED')
        names=inventory(guard.check);old={p['path']:p for p in failed['source_pins']}
        for name in sorted(names):
            q.pin(name)
            if name not in{DRIVER,base.TEST}:c.require(q.snapshots[name]==old[name],'ALL222_PRODUCTION_SOURCE_CORE_TESTS_OTHER_PRODUCTS_AND_INPUTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        text=q.text(base.TEST)
        for new,previous in((NEW_POS,OLD_POS),(NEW_NEG,OLD_NEG),(NEW_ASSERT,OLD_ASSERT)):
            c.require(text.count(new)==1,'TWO_TABLE_FIXTURES_AND_ONE_STRONG_EXACT_PROTECTION_ASSERTION_ONLY');text=text.replace(new,previous)
        audit.inverse(text,old[base.TEST],'OTHER32_PASSED_PRODUCT_CASES_ALL_REQUIREMENTS_AND_HELPERS_UNCHANGED')
        core,product,affected=base.expected(q);all_products=product|affected
        core_passed={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        previous_products={n for n,s in failed['steps'][1]['tests']if s=='ok'};failed_cases={n for n,s in failed['steps'][1]['tests']if s!='ok'}
        repaired_negative=base.prior.PREFIX+'protection_v1::protection_selected_local_lock_keeps_original_candidate_rejection'
        c.require(core_passed==core and len(previous_products)==33 and len(failed_cases)==1 and previous_products|failed_cases==all_products
            and repaired_negative in previous_products,'EXACT_SOURCE10_AND_PRODUCT32_RETAINED_FAILED_ONE_AND_STRENGTHENED_ONE')
        cases=failed_cases|{repaired_negative};base.inverse(q,{p['path']:p for p in q.json(base.BASELINE)['source_pins']})
        print(json.dumps(dict(state='SOURCE_PROTECTION_TWO_CASE_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),retained_source_cases=10,retained_product_cases=32,
            current_product_cases=len(cases),unchanged_production=True)),flush=True)
        harness.run_one('two_valid_locked_table_selection_and_exact_original_protection_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_WHOLE_SOURCE_PROTECTION10_PRODUCT8_AFFECTED_MANIFEST26_RETAINED42_NOT_NATIVE_PROTECTION_CRYPTO_TRUST_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,distinct_source_cases=10,distinct_new_product_cases=8,distinct_affected_manifest_cases=26,
            retained_source_cases=10,retained_product_cases=32,total_executed_cases=2,distinct_component_cases=44,passed42_cases_reexecuted=False,
            source_observation_once_no_verify_rescan_reimport_or_unprotected_inference=True,
            original_native_signal_predicate_and_local_lock_algorithms_unchanged=True,
            next_work='qualified_native_protection_and_trusted_current_registry_target_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_PROTECTION_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_PROTECTION_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
