"""Preserve154/24 passes; correct unreachable MEMO oracle, run only2 source +26 products."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_control_style_context_components as base
harness,shared,c,a,audit,snapshot=base.harness,base.shared,base.c,base.a,base.audit,base.snapshot
OUTPUT='implementation/p09/evidence/p09-361-control-style-context-recovery155.v1.json'
SOURCE_CURRENT={
    'control_context::control_style_memo_retains_original_admission_rejection_and_hidden_paragraph_axis_is_independent',
    'control_context::control_style_policy_excludes_context_before_resolution_without_leaking_into_siblings'}
SOURCE_OLD_NAME='control_style_memo_context_is_unresolved_but_unrequested_character_axis_does_not_block_paragraphs'
SOURCE_NEW_NAME='control_style_memo_retains_original_admission_rejection_and_hidden_paragraph_axis_is_independent'
SOURCE_NEW='''    for id in[0,1] {let raw=fixture::package(&memo(id))?;let original=Sha256::digest(&raw);
        let error=forms(&raw).expect_err("MEMO control style is outside original admission");
        assert!(matches!(error.downcast_ref::<hwpx_package::document_import::forms::FormImportError>(),Some(hwpx_package::document_import::forms::FormImportError::Body(_))));
        assert_eq!(Sha256::digest(&raw),original);
    }
    let raw=fixture::package(&hidden(1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
'''
SOURCE_OLD='''    let raw=fixture::package(&memo(1))?;let f=forms(&raw)?;let i=f.source_review_scope_index(&raw,Default::default())?;
    assert!(matches!(i.find_resolved_style(q("ABSENT"),Scope::Document,all(),bold()),Err(RE::Unresolved(_))));
'''
PRODUCT_NEW='''            if is_memo {
                assert!(matches!(resolved!(&provider,&v),Err(PE::Import(hwpx_agent_cli::form_stored_provider::actual_import::StoredActualFormImportError::Import(
                    hwpx_package::document_import::forms::FormImportError::Body(_))))));
            }else{assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));}
'''
PRODUCT_OLD='''            assert!(matches!(resolved!(&provider,&v),Err(PE::Stored(SE::Resolution(RE::Unresolved(_))))));
'''


def repairs(q,pins):
    text=q.text(base.SOURCE_TEST)
    for current,original in[(SOURCE_NEW_NAME,SOURCE_OLD_NAME),(SOURCE_NEW,SOURCE_OLD),('for body in[hidden(0),hidden(1)]','for body in[hidden(1),memo(1)]')]:
        c.require(text.count(current)==1,'ONE_OF_TWO_FAILED_SOURCE_ORACLE_CORRECTIONS');text=text.replace(current,original)
    audit.inverse(text,pins[base.SOURCE_TEST],'WHOLE_SOURCE_CONTEXT_TEST_FILE_RESTORED_EXCEPT_TWO_FAILED_ORACLES')
    text=q.text(base.PRODUCT_TEST)
    for current,original in[(
        'control_product_hidden_context_is_unresolved_and_memo_keeps_exact_original_admission_rejection',
        'control_product_hidden_and_memo_contexts_propagate_unresolved_before_absent_query'),(
        'for (body,is_memo) in[(hidden(),false),(body().replace("<hp:ctrl><hp:fieldBegin","<hp:ctrl charStyleIDRef=\'0\'><hp:fieldBegin"),true)]',
        'for body in[hidden(),body().replace("<hp:ctrl><hp:fieldBegin","<hp:ctrl charStyleIDRef=\'0\'><hp:fieldBegin")]'),(PRODUCT_NEW,PRODUCT_OLD)]:
        c.require(text.count(current)==1,'ONE_UNEXECUTED_PRODUCT_ORACLE_CORRECTION_TO_EXACT_ORIGINAL_ADMISSION');text=text.replace(current,original)
    audit.inverse(text,pins[base.PRODUCT_TEST],'WHOLE_UNEXECUTED_PRODUCT_CONTEXT_TEST_FILE_RESTORED_EXCEPT_MEMO_ORACLE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_CONTEXT_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=base.prior.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_STYLE_CONTEXT_RECOVERY',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_effective_cascade_or_visibility_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);baseline=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='3e7a183a9c09988b7d1633795992d6f5d583456692133b85cd2fa7dc478b6f95'
            and failed['state']=='FAILED_CONTROL_STYLE_CONTEXT_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,
            'EXACT_FAILED154_SOURCE_ONLY_RESULT_PRESERVED')
        step=failed['steps'][0];retained={n for n,s in step['tests']if s=='ok'};negative={n for n,s in step['tests']if s!='ok'}
        c.require(step['exit_code']==101 and len(retained)==24 and step['safe_error_variants']==['Body','Body']
            and negative=={n.replace(SOURCE_NEW_NAME,SOURCE_OLD_NAME)for n in SOURCE_CURRENT}
            and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'EXACT_24_PASSES_TWO_UNADMITTED_MEMO_FIXTURES_AND_TERMINAL_JOB_NOT_PRODUCT_EXECUTION')
        pins={p['path']:p for p in failed['source_pins']}
        for name in names-{base.SOURCE_TEST,base.PRODUCT_TEST}:c.require(q.snapshots[name]==pins[name],'ALL_PRODUCTION_CORE_POLICY_AND_OTHER_TESTS_UNCHANGED_AFTER154')
        repairs(q,pins);base.inverse(q,{p['path']:p for p in baseline['source_pins']});source,product=base.expected(q)
        c.require(source==retained|SOURCE_CURRENT and len(product)==26,'EXACT24_RETAINED_TWO_REPAIRED_AND26_UNEXECUTED_PRODUCTS')
        print(json.dumps(dict(state='CONTROL_CONTEXT_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),repaired_source_cases=2,retained_source_cases=24,product_cases=26,one_cpu_mask=4)),flush=True)
        harness.run_one('two_repaired_source_oracles_only',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_resolved_style_search','--message-format=short','--',*sorted(SOURCE_CURRENT),'--exact','--test-threads=1'],SOURCE_CURRENT,guard,audit.environment(),row,observe_capture=snapshot)
        harness.run_one('six_new_and_twenty_affected_v9_product_context_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(product),'--exact','--test-threads=1'],product,guard,audit.environment(),row,observe_capture=snapshot)
        for step in row['steps']:
            limits=step['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
                'ORIGINAL_ONE_CPU2_HARD_CAP_AND_PRIORITY_FOR_SERIAL_JOBS')
        c.require(base.inventory(guard.check)==names,'FINAL_CONTROL_CONTEXT_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_CONTEXT_2_REPAIRED_24_RETAINED_26_PRODUCTS_NOT_CASCADE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_source_cases=2,retained_source_cases=24,current_product_cases=26,total_executed_cases=28,total_distinct_cases=52,
            new_source_cases=8,new_product_cases=6,affected_source_cases=18,affected_product_cases=20,passed24_source_cases_reexecuted=False,
            unrelated104_products_reexecuted=False,production_unchanged_after154=True,failed_oracles_now_require_exact_original_body_rejection=True,
            original_source_filter_receipt_and_prior_test_bodies_inverse_verified=True,native_inheritance_or_target_domain_inferred=False,
            next_work='Qualified_native_text_control_style_precedence_missing_axes_visibility_and_original_MEMO_admission_then_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_STYLE_CONTEXT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONTROL_CONTEXT_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
