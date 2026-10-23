"""422: preserve unpublished421; lossless sample layout and a fresh final proof of actual v13 APIs."""
import io,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import run_reference_source_heading_api as prior
import resource_sample_table as layout
import test_resource_sample_table as layout_tests
r=prior.r
OUTPUT='implementation/p09/evidence/p09-361-reference-source-heading-api-recovery422.v1.json'
DRIVER='tools/p09/run_reference_source_heading_api_recovery.py'
FAILURE='implementation/p09/evidence/p09-361-reference-source-heading-api421-publication-failure.v1.json'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HEADING422_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_REFERENCE_SOURCE_HEADING_API_RECOVERY422',steps=[],own_cpu_selection=selection,
        source_API_schema='hwpx-agent.product.reference-source-assessment/v13',source_API_unresolved_stages_cleared=False,
        prior77_observed_steps_not_promoted_to_complete_proof=True,
        prior77_repetition_reason='421_did_not_publish_final_fresh_or_cleanup_proof_not_a_routine_revalidation_of_accepted_results',
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        strict_core_prior24_replayed=False,native_number_or_navigation_qualified=False,effective_style_cascade_qualified=False,
        complete_reference_state_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failure=q.json(FAILURE)
        c.require(failure['observed_error_code']=='COMPACT_RECEIPT_PAYLOAD_LIMIT'and not failure['acceptance_promoted']
            and not(c.ROOT/prior.OUTPUT).exists(),'ORIGINAL421_PUBLICATION_FAILURE_PRESERVED_NOT_RECONSTRUCTED_AS_ORIGINAL')
        base=r.compact.unpack(q.json(prior.prior.OUTPUT))
        c.require(q.snapshots[prior.prior.OUTPUT]['sha256']=='043c89e1851288f08a676cbec4dafa6b6860b8a923b53844b70db09d7a72e57f'
            and base['cleanup']is True and base['current_distinct_cases']==24 and base['fresh_inputs']==base['final_fresh_hashes']==789,
            'EXACT420_STRICT_HEADING_CORE24_AND_SOURCE_CLOSURE')
        old={p['path']:p for p in base['source_pins']}
        extra={DRIVER,prior.DRIVER,prior.NEW_TEST,'tools/p09/resource_sample_table.py','tools/p09/test_resource_sample_table.py',
            'crates/product-cli/tests/form_stored_provider.rs','crates/product-cli/tests/form_stored_provider/actual_import.rs',
            'crates/hwpx-package/tests/support/document_import_field_fixture.rs','crates/hwpx-package/tests/support/document_import_bookmark_fixture.rs'}
        for path in sorted(set(old)|r.closure.inventory(guard.check)|extra|prior.CHANGED):
            pin=q.pin(path)
            if path in old and path not in prior.CHANGED:c.require(pin==old[path],'ALL_OTHER_PRODUCT_SOURCE_RUNTIME_MODELS_AND_GUARDS_UNCHANGED')
        prior.check_inverse(q,old)
        suite=unittest.defaultTestLoader.loadTestsFromModule(layout_tests);stream=io.StringIO()
        result=unittest.TextTestRunner(stream=stream).run(suite)
        c.require(result.wasSuccessful()and result.testsRun==6,'EXACT6_LOSSLESS_SAMPLE_LAYOUT_CONTRACTS_NO_LIMIT_RELAXATION')
        row['layout_contracts']=dict(cases=6,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped))
        core={n for n in prior.cases(q.text(prior.first.TEST),'source_headings::')if n.startswith('source_headings::partial_assessment_')}
        api=set()
        for path,prefix in prior.PARTS.items():api.update(prior.cases(q.text(path),prefix))
        c.require(len(core)==7 and len(api)==70 and len(prior.cases(q.text(prior.NEW_TEST)))==13,'EXACT_NEW7_NEW_API13_AFFECTED_API57')
        for full in prior.STORED:
            module,name=full.removeprefix('actual_import::').split('::')
            c.require(name in prior.cases(q.text('crates/product-cli/tests/form_stored_provider/actual_import/'+module+'.rs')),'EXACT_THREE_STORED_V13_JSON_JOIN_CASES')
        for module in tuple(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if filename:
                path=Path(filename).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        scratch=c.ROOT/'target/p09-reference-source-heading-api-scratch-422'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING422_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='HEADING422_PREFLIGHT',inputs=len(q.snapshots),layout_contracts=6,stored_first=3,core=7,API_CLI=70)),flush=True)
        commands=[('affected_stored_v13_API_joins3_first','hwpx-agent-cli','form_stored_provider',prior.STORED,True),
            ('new_heading_adapter7_final_source_proof','hwpx-package','document_import_reference_targets',core,True),
            ('actual_v13_reference_source_API_CLI70_final_source_proof','hwpx-agent-cli','reference_source_product',api,False)]
        for label,package,test,expected,filtered in commands:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',test,'--message-format=short','--']
            if filtered:args.extend(sorted(expected))
            args.append('--test-threads=1')
            r.harness.run_one(label,args,expected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],expected);c.require(row['steps'][-1]['diagnostics']==[],'HEADING_V13_CASES_NO_WARNINGS')
            print(json.dumps(dict(state='HEADING422_STEP_PASS',stage=label,cases=len(expected))),flush=True)
        c.require(not any(scratch.iterdir()),'HEADING422_COMPILER_TEMP_EMPTY');final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCE_SOURCE_HEADING_V13_CORE7_API70_STORED3_LAYOUT6_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=20,affected_cases=60,current_distinct_product_cases=80,last_executed_product_cases=80,
            test_preimage_origin='observed_before_version_only_edit_not_historical_test_acceptance',
            next_work='effective_heading_style_cascade_and_complete_reference_stage_implementation_requiring_source_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'HEADING422_FAILURE_NO_RAW_VALUES')
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
