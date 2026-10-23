"""Recover one fixture and diagnose one still-required review failure; never promote197 to full PASS."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_number_control_source_components as prior
harness,shared,c,a,audit,snapshot,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-number-control-source-selection-recovery198.v1.json'
FIXED='numbers::number_control_source_document_section_node_and_selection_are_exact'
UNRESOLVED='numbers::number_control_source_review_exclusion_precedes_match_limit'
DIAGNOSTIC='numbers::number_control_source_review_failure_is_numbering_coverage_not_policy_or_resource_stop'
OLD='''    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};let end=Boundary{normalized_scalar:2,..start.clone()};
'''
CORRECT='''    let start=Boundary{paragraph_handle:b.paragraph_handle.clone(),block_index:0,normalized_scalar:0};
    let last=inv.inventory.blocks.iter().filter(|n|n.paragraph_handle==b.paragraph_handle).last().ok_or("last original block")?;
    let end=Boundary{paragraph_handle:last.paragraph_handle.clone(),block_index:last.block_index,normalized_scalar:last.normalized_scalars};
'''


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_SELECTION_RECOVERY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_SELECTION_RECOVERY',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        original_required_review_case=UNRESOLVED,original_required_review_case_still_failed=True,full_number_control_source_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=prior.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(prior.OUTPUT);baseline=q.json(prior.prior.OUTPUT);step=failed['steps'][0]
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='fb2db6f720cc563578f668dd071946806c947e14b06b34687050fdb2454129b3'
            and failed['state']=='FAILED_NUMBER_CONTROL_SOURCE_COMPONENTS'and failed['cleanup']and step['cleanup']
            and step['exit_code']==101 and{n for n,status in step['tests']if status!='ok'}=={FIXED,UNRESOLVED}
            and sum(status=='ok'for _,status in step['tests'])==54 and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'EXACT_ORIGINAL197_54PASS_TWO_FAILURES_TERMINAL_PRESERVED_NOT_FULL_PASS')
        old={p['path']:p for p in failed['source_pins']}
        for name in names-{prior.TEST}:c.require(q.snapshots[name]==old[name],'ALL197_PRODUCT_SOURCE_MATCHER_GUARDS_STREAM_COMPILER_OTHER_TESTS_UNCHANGED')
        text=q.text(prior.TEST);marker='#[test]\nfn '+DIAGNOSTIC.split('::')[-1]+'()->TestResult{';start=text.index(marker)
        c.require(text.count(CORRECT)==1 and start>text.index(CORRECT),'ONE_ORIGINAL_BLOCK_BOUNDARY_FIX_AND_APPENDED_COVERAGE_DIAGNOSIS')
        audit.inverse(text[:start].replace(CORRECT,OLD),old[prior.TEST],'ENTIRE197_TEST_FILE_RESTORED_EXCEPT_ONE_SCOPE_FIXTURE_AND_ADDITIVE_DIAGNOSIS')
        prior.inverse(q,{p['path']:p for p in baseline['source_pins']})
        all_cases={'numbers::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',text)}
        c.require(len(all_cases)==21 and all_cases=={n for n,_ in step['tests']if n.startswith('numbers::')}|{DIAGNOSTIC},'EXACT20_ORIGINAL_NUMBER_CASES_PLUS_ONE_DIAGNOSIS')
        cases={FIXED,DIAGNOSTIC};command=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','control_replacement_focused','--message-format=short','--','numbers::','--test-threads=1']
        for name in sorted(all_cases-cases):command+=['--skip',name]
        print(json.dumps(dict(state='NUMBER_CONTROL_SELECTION_DIAGNOSIS_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),executed=2,retained_passes=54,required_review_failure_preserved=True)),flush=True)
        harness.run_one('one_original_block_fixture_recovery_and_one_review_coverage_diagnosis',command,cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);c.require(prior.inventory(guard.check)==names,'FINAL_NUMBER_CONTROL_RECOVERY_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='MIXED_NUMBER_CONTROL_SOURCE19_DIAGNOSTIC1_REQUIRED_REVIEW_CASE_UNRESOLVED',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            recovered_source_cases=1,new_diagnostic_cases=1,retained_passes=54,new_functional_source_cases_passed=19,new_functional_source_cases_required=20,
            affected_control_cases_retained=36,production_code_changed=False,original_positive_review_test_unchanged=True,
            unresolved_cause='original_complete_numbering_import_rejects_unrepresented_review_paragraph_controls_with_Coverage_after_search_policy_correctly_excludes_them',
            old266_products_and_official249_reexecuted=False,next_work='implement_review_bound_complete_number_stream_input_output_admission_without_weakening_original_coverage_checks')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_SELECTION_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NUMBER_CONTROL_RECOVERY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('MIXED_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
