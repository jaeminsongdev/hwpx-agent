"""423: exact shared-fixture warning annotation; recover the full v13 final source proof, no Native."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import run_reference_source_heading_api_recovery as failed
prior,r,layout=failed.prior,failed.r,failed.layout
OUTPUT='implementation/p09/evidence/p09-361-reference-source-heading-api-final423.v1.json'
DRIVER='tools/p09/run_reference_source_heading_api_final.py'
FIXTURE='crates/hwpx-package/tests/support/search_review_fixture.rs'
ANNOTATION='#[allow(dead_code)] // Shared fixture: some integration binaries use only body and with_body.\n'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HEADING423_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_REFERENCE_SOURCE_HEADING_API_FINAL423',steps=[],own_cpu_selection=selection,
        source_API_schema='hwpx-agent.product.reference-source-assessment/v13',source_API_unresolved_stages_cleared=False,
        prior77_repetition_reason='421_unpublished_final_proof_not_routine_revalidation_of_accepted_results',
        stored3_repetition_reason='exact_shared_fixture_warning_annotation_changed_this_test_binary_no_test_assertion_changed',
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        strict_core_prior24_replayed=False,native_number_or_navigation_qualified=False,effective_style_cascade_qualified=False,
        complete_reference_state_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=layout.unpack(q.json(failed.OUTPUT))
        c.require(q.snapshots[failed.OUTPUT]['sha256']=='b68c3c608a49470030db0abe5fc33541098e480538d13be89cd5af6aac1c451f'
            and previous['error_code']=='HEADING_V13_CASES_NO_WARNINGS'and previous['cleanup']is True
            and previous['fresh_inputs']==previous['final_fresh_hashes']==806 and len(previous['steps'])==1,
            'EXACT422_STORED3_PASS_ONLY_SHARED_FIXTURE_WARNING_FAILURE_RETAINED')
        step=previous['steps'][0];r.tools.good_step(step,prior.STORED)
        c.require(step['diagnostics']==['warning: `hwpx-agent-cli` (test "form_stored_provider") generated 1 warning']
            and step['bounded_output_observation']['safe_warning_locations']==[dict(path='crates/product-cli/tests/form_stored_provider/actual_import/../../../../hwpx-package/tests/support/search_review_fixture.rs',
                line=4,column=8,kind='dead_code',symbols=['package'])],'EXACT_ONE_SHARED_FIXTURE_UNUSED_PACKAGE_WARNING_NOT_PRODUCT_OR_COMPILER_ERROR')
        old={p['path']:p for p in previous['source_pins']}
        for path in sorted(set(old)|{DRIVER}):
            pin=q.pin(path)
            if path in old and path!=FIXTURE:c.require(pin==old[path],'ALL_V13_PRODUCTION_TEST_ASSERTIONS_RUNTIME_GUARDS_AND_LAYOUT_UNCHANGED_SINCE422')
        text=q.text(FIXTURE);c.require(text.count(ANNOTATION)==1,'ONE_FUNCTION_SCOPED_SHARED_FIXTURE_ANNOTATION')
        r.audit.inverse(text.replace(ANNOTATION,''),old[FIXTURE],'ALL_FIXTURE_FUNCTION_BODIES_AND_TEST_ASSERTIONS_UNCHANGED')
        core={n for n in prior.cases(q.text(prior.first.TEST),'source_headings::')if n.startswith('source_headings::partial_assessment_')}
        api=set()
        for path,prefix in prior.PARTS.items():api.update(prior.cases(q.text(path),prefix))
        c.require(len(core)==7 and len(api)==70,'EXACT_V13_CORE7_AND_API70_NO_SKIPS')
        scratch=c.ROOT/'target/p09-reference-source-heading-api-scratch-423'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING423_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='HEADING423_PREFLIGHT',inputs=len(q.snapshots),stored_first=3,core=7,API_CLI=70,layout6_retained=True)),flush=True)
        commands=[('affected_stored3_after_exact_fixture_annotation','hwpx-agent-cli','form_stored_provider',prior.STORED,True),
            ('new_heading_adapter7_complete_final_proof','hwpx-package','document_import_reference_targets',core,True),
            ('actual_v13_source_API_CLI70_complete_final_proof','hwpx-agent-cli','reference_source_product',api,False)]
        for label,package,test,expected,filtered in commands:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',test,'--message-format=short','--']
            if filtered:args.extend(sorted(expected))
            args.append('--test-threads=1')
            r.harness.run_one(label,args,expected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],expected);c.require(row['steps'][-1]['diagnostics']==[],'ALL_CURRENT_V13_CASES_NO_WARNINGS')
            print(json.dumps(dict(state='HEADING423_STEP_PASS',stage=label,cases=len(expected))),flush=True)
        c.require(not any(scratch.iterdir()),'HEADING423_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCE_SOURCE_HEADING_V13_CORE7_API70_STORED3_LAYOUT6_RETAINED_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_product_cases=80,last_executed_product_cases=80,new_product_cases=20,affected_product_cases=60,
            layout_contracts_retained=previous['layout_contracts'],next_work='effective_heading_style_cascade_and_complete_reference_stage_implementation_requiring_source_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'HEADING423_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            try:final_attempted=True;q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
