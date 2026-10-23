"""Current-source owned insertion8 + eight new private copies; no Native/CAS/SQL."""
import hashlib,json,re,subprocess,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
import metadata_cpu_observer620 as attribution
SELF='tools/p09/verify_stored_bookmark_insertion628.py'
OUTPUT='implementation/p09/evidence/p09-361-stored-bookmark-insertion628-audit001.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-stored-bookmark-insertion628-audit001-forensic'
PRIOR='implementation/p09/evidence/p09-361-bookmark-creation627-audit003.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-stored-bookmark-insertion628/'
PARENT='crates/product-cli/src/form_stored_provider/actual_import.rs'
ACCESS='crates/product-cli/src/form_stored_provider/actual_import/bookmark_command_output.rs'
TEST='crates/product-cli/tests/stored_bookmark_insertion628.rs'
EXAMPLE='crates/product-cli/examples/p09_stored_bookmark_insertion628.rs'
EXPECTED='implementation/p09/evidence/p09-361-bookmark-creation627-output-digests.v1.json'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
GENERATION=1
DIRECTORY='implementation/p09/evidence/private/p09-361-bookmark-insertion628-prepared-001'
OBSERVER=('metadata_cpu_observer620','native_process_cpu_attribution_v1','native_process_cpu_attribution_v2','native_process_cpu_attribution_v3','native_process_cpu_attribution_v4',
    'bounded_cpu_attribution_probe_v1','bounded_cpu_attribution_probe_v2','serial_observer_attribution','serial_cpu_attribution')

def observe_fixed(guard,env,row,args,artifact,expected):
    owned=capture=None;begin=time.monotonic();step=dict(stage='current_stored_source_eight_private_evidence_copies',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<120,'P628_FIXED_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(v.startswith(('error','warning'))for v in err.splitlines()),'P628_FIXED_NO_ERRORS_OR_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='stored_bookmark_insertion628_prepared_eight_private_copies_not_CAS_or_native'
            and len(result['observations'])==8 and result['generation']==GENERATION,'P628_EXACT_BATCH')
        for key in('actual_native_started','head_changed','result_ingested','source_overwritten','product_route_qualified','P09_complete'):r.c.require(result[key]is False,'P628_NO_FALSE_AUTHORITY')
        r.c.require(result['memory_repositories_scanner_and_keys_are_fixtures']is True,'P628_MODEL_QUALIFICATION_EXPLICIT')
        for i,(v,want)in enumerate(zip(result['observations'],expected['cases']),1):
            output=v['output'];r.c.require(v['case_index']==i and output['path']==DIRECTORY+f'/case-{i:02}.hwpx'
                and output['sha256']==want['output_sha256'] and v['exact627_candidate_bytes']is True,'P628_EVERY_OUTPUT_BOUND_TO627')
            r.c.require(artifact.pin(output['path'])==output,'P628_ACTUAL_NEW_OUTPUT_BYTES')
            s=v['receipt'];r.c.require(s['execution_or_publication_authority']is False and s['output']['inserted_fields']==1
                and s['output']['requires_existing_crossref_envelope']is False and s['output']['native_currentness_execution_or_publication_qualified']is False,'P628_CURRENT_STORED_RECEIPT')
        r.c.require(len(list((r.c.ROOT/DIRECTORY).iterdir()))==8,'P628_ONLY_EXPECTED_NEW_COPIES')
        step['observations']=result;return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-begin,3)

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-current-stored-insertion'],'P628_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P628_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=observer=None;observer_clean=True
    row=dict(state='FAILED628_CURRENT_STORED_BOOKMARK_INSERTION',steps=[],own_cpu_selection=selection,actual_Hancom_COM_Native_or_SQL_started=False,
        official249_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,PC_freeze_resolved=False,
        project_membership_lease_CAS_operating_scanner_keys_or_route_qualified=False,private_evidence_copies_are_not_result_ingestion=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='0b61edcc5b7ef4975b72ea20013863d1111d1da022ef263e893e5abd287e7a6f'
            and prior['state']=='PASS627_FIRST_INSERTION_CORE7_AFFECTED8_NORMAL_PRODUCT8_ORIGINAL_PARAMETER16_NOT_NATIVE'and prior['cleanup']is True,'P628_PRIOR627_PRESERVED')
        previous={v['path']:v for v in prior['source_pins']}
        for name in OBSERVER:
            path='tools/p09/'+name+'.py';c.require(q.pin(path)==previous[path],'P628_QUALIFIED_OBSERVER_UNCHANGED')
        guard.check(force=True)
        if guard.samples[-1]['system_cpu_percent']<75:observer=attribution.Attached(guard)
        else:row['observer_unavailable_reason']='INITIAL_CPU_WARNING_NO_OPTIONAL_PROCESS_QUERY'
        names=inventory.inventory(guard)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,PRIOR,TEST,EXAMPLE,EXPECTED,CORPUS,
            ARCHIVE+'actual_import.rs',ARCHIVE+'bookmark_command_output.rs','target/debug/examples/p09_crossref_capture010_probe.exe'}
        expected=q.json(EXPECTED);corpus=q.json(CORPUS);names.add(corpus['source']['path'])
        c.require(expected['provenance_receipt']==PRIOR and expected['provenance_sha256']==q.snapshots[PRIOR]['sha256']and expected['source']==corpus['source'],'P628_DERIVED_FIXED_SOURCE_AND_PROVENANCE')
        observed=prior['actual_product_observation']['observations'];c.require(len(observed)==len(expected['cases'])==8,'P628_EXACT_EIGHT_EXPECTATIONS')
        for i,(v,want,case)in enumerate(zip(observed,expected['cases'],corpus['cases']),1):
            c.require(v['case_index']==want['case_index']==case['case_index']==i and want['display']==case['display']and want['hyperlink']==case['hyperlink']
                and want['output_sha256']==bytes(v['receipt']['output_package_sha256']).hex()and want['command_sha256']==bytes(v['receipt']['command_sha256']).hex(),'P628_DERIVED_DIGESTS_EXACT627')
        for path in sorted(names):
            if path not in q.snapshots:q.pin(path)
        c.require(q.snapshots[corpus['source']['path']]==corpus['source'],'P628_ACTUAL_SOURCE_PIN')
        c.require(q.snapshots[ARCHIVE+'actual_import.rs']['sha256']==previous[PARENT]['sha256']
            and q.text(PARENT).replace('pub mod bookmark_insertion_output;\n','',1)==q.text(ARCHIVE+'actual_import.rs'),'P628_ORIGINAL_ACTUAL_IMPORT_BODIES_UNCHANGED')
        c.require(q.snapshots[ARCHIVE+'bookmark_command_output.rs']['sha256']==previous[ACCESS]['sha256']
            and q.text(ACCESS).replace('pub(super) fn final_access<','fn final_access<',1)==q.text(ARCHIVE+'bookmark_command_output.rs'),'P628_ORIGINAL_WRITE_ACCESS_AND_OLD_CALLBACK_BODIES_IDENTICAL')
        for path,pin in previous.items():
            if path.startswith('crates/')and '/src/'in path and path not in(PARENT,ACCESS):c.require(q.snapshots[path]==pin,'P628_ALL_OTHER_COMPILED_RUST_UNCHANGED')
        c.require(q.snapshots['target/debug/examples/p09_crossref_capture010_probe.exe']==previous['target/debug/examples/p09_crossref_capture010_probe.exe'],'P628_CONSUMED010_NOT_CHANGED_OR_RUN')
        tests=q.text(TEST);cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',tests));c.require(len(cases)==8 and '#[ignore]'not in tests,'P628_EXACT_NEW_EIGHT')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P628_NO_HWP_BEFORE');c.require(not(c.ROOT/DIRECTORY).exists(),'P628_NEW_OUTPUT_DIRECTORY_ONLY')
        scratch=c.ROOT/'target/p09-stored-bookmark-insertion628-audit001-scratch';c.require(not scratch.exists(),'P628_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1');artifact=a.AcceptanceReader(c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture','--message-format=short',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        print(json.dumps(dict(state='P628_PREFLIGHT',new_stored_tests=8,previous627_core15_not_replayed=True,new_private_output_count=8,
            original_guard_bodies_identical=True,CPU_RAM_guards_unchanged=True)),flush=True)
        target='stored_bookmark_insertion628';build_begin=time.time_ns()
        r.harness.run_one(target,[r.harness.CARGO,'test',*common,'--test',target,'--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,env,row,observe_capture=r.snapshot)
        row['compiled_inputs']=[]
        for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
            if path.stat().st_mtime_ns<build_begin:continue
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P628_ACTUAL_TEST_INPUTS_PREPINNED')
            row['compiled_inputs'].append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P628_NO_TEST_WARNINGS');c.require(len(row['compiled_inputs'])==1,'P628_TEST_DEP_INFO')
        example='p09_stored_bookmark_insertion628'
        r.harness.run_one('normal_stored_first_insertion_build',[r.harness.CARGO,'build',*common,'--example',example],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P628_NORMAL_BUILD_NO_WARNINGS')
        image=artifact.pin('target/debug/examples/'+example+'.exe');dep=artifact.pin('target/debug/examples/'+example+'.d');declared=deps.dependencies(c.ROOT/dep['path'])
        c.require({TEST,EXAMPLE,EXPECTED}<=declared and declared<=set(q.snapshots),'P628_NORMAL_INPUTS_PREPINNED')
        row['actual_current_stored_observation']=observe_fixed(guard,env,row,[r.harness.CARGO,'run',*common,'--example',example,'--','--fixed-private-output-generation',str(GENERATION)],artifact,expected)
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P628_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P628_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS628_CURRENT_STORED_INSERTION8_AND_PRIVATE_OUTPUT8_NOT_CAS_NATIVE_OR_ROUTE',new_stored_tests=8,prepared_private_candidate_files=8,
            previous627_tests_replayed=False,compiled_normal_example=image,compiled_and_new_output_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P628_FAILURE_NO_RAW_VALUES')
    finally:
        if observer is not None:observer_clean=observer.close();row['resource_attribution']=observer.summary()
        guard.close();row.update(cleanup=guard.cleanup and observer_clean and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),diagnostics=v.get('diagnostics'),panic_locations=v.get('panic_locations'),safe_error_variants=v.get('safe_error_variants'),
                compile=v.get('bounded_output_observation',{}).get('short_error_locations'),rust_codes=v.get('bounded_output_observation',{}).get('rust_error_codes'),
                failed_cases=[name for name,status in v.get('tests',[])if status!='ok'])for v in row['steps']], 'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS628_')else 2
if __name__=='__main__':raise SystemExit(main())
