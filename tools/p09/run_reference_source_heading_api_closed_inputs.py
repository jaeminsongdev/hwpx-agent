"""424: explicit actual Rust test dependency closure; complete v13 product evidence, not Native."""
import json,posixpath,re,subprocess,time
from types import SimpleNamespace as NS
import run_reference_source_heading_api_final as failed
prior,r,layout=failed.prior,failed.r,failed.layout
OUTPUT='implementation/p09/evidence/p09-361-reference-source-heading-api-closed-inputs424.v1.json'
DRIVER='tools/p09/run_reference_source_heading_api_closed_inputs.py'
MANIFEST='tools/p09/reference_source_heading_test_inputs.json'


def observed_dependencies(root,binary):
    path=binary['dep_info'];r.c.require(path.startswith('target/debug/deps/')and path.endswith('.d')
        and '..'not in path.split('/'),'FIXED_LOCAL_TEST_DEP_INFO_PATH')
    raw=(root/path).read_bytes();r.c.require(0<len(raw)<=131072,'BOUNDED_TEST_DEP_INFO')
    line=raw.decode('utf-8').splitlines()[0];r.c.require(': 'in line,'TEST_DEP_INFO_TARGET')
    paths=sorted(set(posixpath.normpath(x.replace('\\','/'))for x in line.split(': ',1)[1].split()))
    r.c.require(all(p.startswith('crates/')and '..'not in p.split('/')for p in paths),'ONLY_ROOT_BOUND_TEST_INPUTS')
    r.c.require(paths==binary['dependency_paths'],'ACTUAL_COMPILED_TEST_DEPENDENCIES_EXACT_MANIFEST')
    return paths


def validate_dependencies(q,root,manifest):
    c=r.c;c.require(manifest['schema_version']=='hwpx-agent.observed-rust-test-input-closure/v1'
        and {b['test']for b in manifest['binaries']}=={'form_stored_provider','reference_source_product','document_import_reference_targets'},'EXACT_THREE_COMPILED_TEST_CLOSURES')
    wanted=set()
    for binary in manifest['binaries']:wanted.update(observed_dependencies(root,binary))
    declared={p['path']:p for p in manifest['source_pins']}
    c.require(len(declared)==len(manifest['source_pins'])==87 and wanted==set(declared),'ALL87_DISTINCT_TEST_INPUTS_DECLARED_NO_OMISSION')
    for path,pin in declared.items():c.require(q.pin(path)==pin,'ALL_CURRENT_OBSERVED_TEST_INPUT_BYTES_EXACT')
    return wanted


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'HEADING424_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_REFERENCE_SOURCE_HEADING_API_CLOSED_INPUTS424',steps=[],own_cpu_selection=selection,
        source_API_schema='hwpx-agent.product.reference-source-assessment/v13',source_API_unresolved_stages_cleared=False,
        current_test_input_closure_is_not_historical_test_acceptance=True,original421_final_proof_not_reconstructed=True,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        strict_core_prior24_replayed=False,native_number_or_navigation_qualified=False,effective_style_cascade_qualified=False,
        complete_reference_state_qualified=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=layout.unpack(q.json(failed.OUTPUT))
        c.require(q.snapshots[failed.OUTPUT]['sha256']=='e31f06f59e1e668b4d52c120fa6524503095a87fce3442896bc1057f7abf85f3'
            and previous['error_type']=='KeyError'and previous['cleanup']is True and previous['steps']==[]
            and previous['fresh_inputs']==previous['final_fresh_hashes']==809,'EXACT423_PRE_EXECUTION_FIXTURE_BASELINE_LOOKUP_FAILURE_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        for path in sorted(set(old)|{DRIVER,MANIFEST}):
            pin=q.pin(path)
            if path in old:c.require(pin==old[path],'ALL_CURRENT_PRODUCT_TEST_RUNTIME_GUARD_AND_FIXTURE_INPUTS_UNCHANGED_SINCE423')
        manifest=q.json(MANIFEST);test_inputs=validate_dependencies(q,c.ROOT,manifest)
        c.require(failed.FIXTURE in test_inputs and q.text(failed.FIXTURE).count(failed.ANNOTATION)==1,'THE_ACTUAL_SHARED_FIXTURE_IS_A_FRESH_INPUT_NOT_AN_ASSUMED_HISTORICAL_PIN')
        prior_result=layout.unpack(q.json(failed.failed.OUTPUT))
        c.require(q.snapshots[failed.failed.OUTPUT]['sha256']=='b68c3c608a49470030db0abe5fc33541098e480538d13be89cd5af6aac1c451f'
            and prior_result['layout_contracts']==dict(cases=6,failures=0,errors=0,skipped=0),'EXACT_UNCHANGED_LOSSLESS_LAYOUT6')
        core={n for n in prior.cases(q.text(prior.first.TEST),'source_headings::')if n.startswith('source_headings::partial_assessment_')}
        api=set()
        for path,prefix in prior.PARTS.items():api.update(prior.cases(q.text(path),prefix))
        c.require(len(core)==7 and len(api)==70,'EXACT_CURRENT7_AND70_NO_SKIPS')
        scratch=c.ROOT/'target/p09-reference-source-heading-api-scratch-424'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'HEADING424_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='HEADING424_PREFLIGHT',inputs=len(q.snapshots),exact_compiled_test_inputs=len(test_inputs),stored=3,core=7,API_CLI=70)),flush=True)
        commands=[('stored_v13_API_joins3_closed_compile_inputs','hwpx-agent-cli','form_stored_provider',prior.STORED,True),
            ('heading_adapter7_closed_compile_inputs','hwpx-package','document_import_reference_targets',core,True),
            ('actual_source_API_CLI70_closed_compile_inputs','hwpx-agent-cli','reference_source_product',api,False)]
        for label,package,test,expected,filtered in commands:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',test,'--message-format=short','--']
            if filtered:args.extend(sorted(expected))
            args.append('--test-threads=1')
            r.harness.run_one(label,args,expected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],expected);c.require(row['steps'][-1]['diagnostics']==[],'ALL_CURRENT_V13_CASES_NO_WARNINGS')
            for binary in manifest['binaries']:
                if binary['test']==test:observed_dependencies(c.ROOT,binary)
            print(json.dumps(dict(state='HEADING424_STEP_PASS',stage=label,cases=len(expected))),flush=True)
        c.require(not any(scratch.iterdir()),'HEADING424_COMPILER_TEMP_EMPTY');validate_dependencies(q,c.ROOT,manifest)
        final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_REFERENCE_SOURCE_HEADING_V13_CORE7_API70_STORED3_COMPILE_INPUTS87_LAYOUT6_RETAINED_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_product_cases=80,last_executed_product_cases=80,new_product_cases=20,affected_product_cases=60,
            current_compiled_test_dependency_paths=len(test_inputs),layout_contracts_retained=prior_result['layout_contracts'],
            next_work='effective_heading_style_cascade_and_complete_reference_stages_against_source_evidence')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'HEADING424_FAILURE_NO_RAW_VALUES')
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
