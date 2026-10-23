"""Keep six owner units and29 products; one review case preserves protected-main rejection explicitly."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_search_owner_admission_recovery as prior
base=prior.base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-search-review-compiler-recovery216.v1.json'
DRIVER='tools/p09/run_source_search_review_compiler_recovery.py'
ADDITION='''        if i==8{
            use hwpx_agent_cli::form_stored_provider::actual_import::literal_search_output::paragraph_styles::StoredParagraphStyleError as StoredPara;
            use hwpx_package::document_import::search::replacement::atoms::styles::paragraphs::SourceParagraphStyleReplacementError as CorePara;
            let protected=definition::package(&body)?;let guarded=StoredFixture::new(&protected,ArtifactKind::Result,false)?;write_provider!(guarded,guard_actor,guard_provider);
            let error=Dispatch::prepare_compiled_search_json(&guard_provider,&wire(&req(i,&guarded,&protected)?)?,Limits::standard()?,4).err().ok_or("whole cached paragraph unexpectedly admitted")?;
            assert!(matches!(error,CE::Request(DE::SearchMutation(ME::ParagraphStyle(paragraph_styles::ParagraphStyleProductError::Stored(
                StoredPara::Output(CorePara::Compile(Compile::FieldContent))))))));
            body=body.replace("BODY K K","BODY");
        }
'''
HEAD_NEW='''fn compiled_final_head_check_after_operation_construction_rejects_raced_plan()->TestResult{
    let bytes=source(3)?;let s=StoredFixture::new(&bytes,ArtifactKind::Result,false)?;write_provider!(s,actor,_p);let b=wire(&req(3,&s,&bytes)?)?;
'''
HEAD_OLD=HEAD_NEW.replace('actor,_p','actor,p')


def inventory(check):return prior.inventory(check)|{DRIVER}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_REVIEW_COMPILER_RECOVERY_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_REVIEW_COMPILER_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,
        compiled_queue_reexecuted=False,trusted_route_full_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(prior.OUTPUT);original=q.json(base.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='6dde02878a95f427df70e171358086e77fed33200c9da560e87ba90f3b158684'
            and failed['cleanup']and len(failed['steps'])==2 and failed['steps'][0]['exit_code']==0 and failed['steps'][1]['exit_code']==101,'EXACT215_RECOVERED_OWNER_UNIT_AND_PRODUCT29_PASS_ONE_FAILURE')
        c.require(q.snapshots[base.OUTPUT]['sha256']=='30d6a01aa8e88be436d9ec8a468a1929ffb8f5b99ac4786d355ccac28d7fe694'and original['cleanup'],'ORIGINAL213_FIVE_OWNER_PASSES_AND_FAILED_CASE_PRESERVED')
        units,products=base.expected(q);owner5={n for n,s in original['steps'][0]['tests']if s=='ok'};owner1={n for n,s in failed['steps'][0]['tests']if s=='ok'}
        product29={n for n,s in failed['steps'][1]['tests']if s=='ok'};cases={n for n,s in failed['steps'][1]['tests']if s!='ok'}
        c.require(len(owner5)==5 and len(owner1)==1 and owner5|owner1==units and len(product29)==29 and len(cases)==1 and product29|cases==products,'EXACT_RETAINED_SIX_OWNER_UNITS_AND29_PRODUCTS_ONLY_ONE_FAILED_PRODUCT')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{DRIVER,base.TEST}:c.require(q.snapshots[name]==old[name],'ALL_PRODUCTION_SOURCE_OWNER_UNITS_AND_OTHER_TEST_INPUTS_UNCHANGED_FROM215')
        text=q.text(base.TEST);c.require(text.count(ADDITION)==text.count(HEAD_NEW)==1,'ONE_FAILED_CASE_EXPLICIT_CACHE_REJECTION_AND_REVIEW_POSITIVE_FIXTURE_WITH_ONE_UNUSED_BINDING_RENAME')
        audit.inverse(text.replace(ADDITION,'').replace(HEAD_NEW,HEAD_OLD),old[base.TEST],'ALL30_PRODUCT_REQUIREMENTS_AND29_PASSED_BODIES_UNCHANGED_EXCEPT_NONSEMANTIC_LOCAL_BINDING_NAME')
        base.inverse(q,{p['path']:p for p in q.json(base.BASELINE)['source_pins']})
        print(json.dumps(dict(state='SOURCE_REVIEW_COMPILER_FAILED_ONE_PREFLIGHT',inputs=len(q.snapshots),retained_owner_units=6,retained_product_cases=29,recovery_product_cases=1)),flush=True)
        harness.run_one('one_review_compiler_actual_payload_and_exact_cached_paragraph_rejection',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_SIXTEEN_FAMILY_SOURCE_OPERATION_COMPILER30_OWNER6_RETAINED35_NOT_TRUSTED_ROUTE_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,distinct_product_cases=30,distinct_actual_owner_unit_cases=6,
            retained_owner_unit_cases=6,retained_product_cases=29,recovered_product_cases=1,total_executed_cases=1,distinct_component_cases=36,
            passed35_cases_reexecuted=False,old50_products_reexecuted=False,original16_parsers_source_security_delivery_and_route_bodies_inverse_verified=True,
            one_borrowed_source_graph_selected_part_parent_maps_original_snapshot_and_operation_compiler=True,
            no_candidate_clone_reimport_matcher_replay_or_invented_owner=True,
            next_work='real_target_registry_route_manifest_and_durable_transaction_commit_CAS_idempotency_with_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_REVIEW_COMPILER_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_REVIEW_COMPILER_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
