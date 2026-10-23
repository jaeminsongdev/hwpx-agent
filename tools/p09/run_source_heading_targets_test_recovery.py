"""420: capture exact existing Paragraph rejection in the two failed tests; retain22, no production changes."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_source_heading_targets as first
import run_source_heading_targets_recovery as prior
OUTPUT='implementation/p09/evidence/p09-361-source-heading-targets-test-recovery420.v1.json'
DRIVER='tools/p09/run_source_heading_targets_test_recovery.py'
BEFORE={
'foreign_namespace_heading_and_reference_attributes_do_not_become_native_declarations':'''fn foreign_namespace_heading_and_reference_attributes_do_not_become_native_declarations()->TestResult{
    for(reference,declaration)in [("paraPrIDRef='0'",OUTLINE.replace("hh:heading","u:heading")),("u:paraPrIDRef='0'",OUTLINE.to_owned())]{
        let bytes=package(&para(1,reference,"body"),&header(&declaration))?;let source=imported(&bytes)?;assert!(Headings::import(&source,limits()?)?.targets().is_empty());}Ok(())
}
''',
'dangling_invalid_or_overflowing_paragraph_property_reference_rejects':'''fn dangling_invalid_or_overflowing_paragraph_property_reference_rejects()->TestResult{
    for id in ["8","-1","+0","4294967296"]{let bytes=package(&para(1,&format!("paraPrIDRef='{id}'"),"body"),&header(OUTLINE))?;
        let source=imported(&bytes)?;assert!(matches!(Headings::import(&source,limits()?),Err(ReferenceTargetImportError::Binding)));}Ok(())
}
'''}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HEADING_TEST420_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_SOURCE_HEADING_TEST_RECOVERY420',steps=[],own_cpu_selection=selection,
        production_algorithms_changed=False,prior_successes_replayed=False,actual_DB_Hangul_or_COM_started=False,Native011_executed=False,
        prior_Native_replayed=False,official249_replayed=False,source_API_schema_changed=False,native_number_or_navigation_qualified=False,
        complete_reference_state_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(prior.OUTPUT));selected={'source_headings::'+n for n in BEFORE}
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='d31afb6bbea88adca0b10a7404307cca5557af79138861aaa938e76968c8b047'
            and failed['state']=='FAILED_HEADING_RECOVERY419'and failed['cleanup']is True and failed['fresh_inputs']==failed['final_fresh_hashes']==787
            and len(failed['steps'])==1,'EXACT419_FAILED_TWO_FIXTURE_PROPAGATIONS_AND_CURRENT_SOURCE_CLOSURE')
        step=failed['steps'][0];c.require(step['exit_code']==101 and len(step['tests'])==24 and {n for n,status in step['tests']if status!='ok'}==selected
            and step['safe_error_variants']==['Paragraph','Paragraph']and not step['panic_locations'],'EXACT22_PASS_TWO_UPSTREAM_PARAGRAPH_REJECTIONS_NOT_PRODUCT_FAILURES')
        old={p['path']:p for p in failed['source_pins']}
        for path in sorted(set(old)|{DRIVER}):
            pin=q.pin(path)
            if path in old and path!=first.TEST:c.require(pin==old[path],'ALL_PRODUCTION_SOURCE_AND_PASSED_TESTS_UNCHANGED')
        text=q.text(first.TEST)
        for name,before in BEFORE.items():
            found=re.search(r'^fn '+name+r'\(\)->TestResult\{.*?^\}\n',text,re.M|re.S);c.require(found is not None,'ONE_EXACT_FAILED_TEST_BODY')
            text=text[:found.start()]+before+text[found.end():]
        r.audit.inverse(text,old[first.TEST],'ONLY_TWO_FAILED_TEST_ERROR_CAPTURE_BRANCHES_CHANGED_ALL_OTHER_BODIES_AND_HELPERS_PRESERVED')
        current=q.text(first.TEST);c.require(current.count('downcast_ref::<hwpx_package::document_import::structure::StructureImportError>()')==2
            and 'original paragraph parser must reject foreign reference attribute'in current,'EXACT_ORIGINAL_PARAGRAPH_ERROR_ASSERTED_NOT_ANY_ERROR_OR_SKIPPED_IMPORT')
        scratch=c.ROOT/'target/p09-source-heading-targets-scratch-420';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING420_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='HEADING420_PREFLIGHT',inputs=len(q.snapshots),failed_cases_to_execute=2,prior_passes_retained=22)),flush=True)
        r.harness.run_one('only_two_failed_upstream_paragraph_rejection_cases',[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',
            'document_import_reference_targets','--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'FAILED_CASES2_PASS_WITHOUT_WARNINGS')
        c.require(not any(scratch.iterdir()),'HEADING420_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_HEADING_FAILED2_RETAINED22_CURRENT24_NOT_API_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=22,affected_cases=2,current_distinct_cases=24,last_executed_cases=2,retained_cases=22,
            next_work='versioned_actual_reference_source_API_heading_target_integration_retain_four_unresolved_stages')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'HEADING420_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
