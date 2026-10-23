"""First CROSSREF creation + original8 impact, normal local product8; no Native."""
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
SELF='tools/p09/verify_bookmark_creation627.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-creation627-audit003.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-bookmark-creation627-audit003-forensic'
PRIOR='implementation/p09/evidence/p09-361-bookmark-insertion626-audit003.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-creation627/'
PARENT='crates/hwpx-package/src/document_import/fields/bookmark_insertion.rs'
PRODUCT='crates/product-cli/src/reference_validation_product/source_crossref.rs'
OLD='crates/hwpx-package/tests/bookmark_source_insertion626.rs'
TEST='crates/hwpx-package/tests/bookmark_source_creation627.rs'
EXAMPLE='crates/product-cli/examples/p09_bookmark_creation627.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
FAILED='implementation/p09/evidence/p09-361-bookmark-creation627-audit001.v1.json'
OBSERVER=('metadata_cpu_observer620','native_process_cpu_attribution_v1','native_process_cpu_attribution_v2','native_process_cpu_attribution_v3','native_process_cpu_attribution_v4',
    'bounded_cpu_attribution_probe_v1','bounded_cpu_attribution_probe_v2','serial_observer_attribution','serial_cpu_attribution')

def observe_fixed(guard,env,row,args):
    owned=capture=None;begin=time.monotonic();step=dict(stage='normal_product_first_insertion8_original_parameter16',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<120,'P627_FIXED_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(v.startswith(('error','warning'))for v in err.splitlines()),'P627_FIXED_NO_ERRORS_OR_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='bookmark_creation627_first_insert8_captured_parameter16_not_native_or_route'
            and len(result['observations'])==8,'P627_FIXED_EIGHT')
        for key in('actual_native_started','source_overwritten','P09_complete','cache_currentness_qualified','product_route_qualified'):r.c.require(result[key]is False,'P627_NO_FALSE_AUTHORITY')
        for v in result['observations']:
            item=v['receipt'];r.c.require(item['inserted_fields']==1 and item['requires_existing_crossref_envelope']is False
                and item['inserted_parameter_envelope_readback_verified']is True and item['outside_insertions_exact']is True
                and item['original_selected_run_exact']is True and item['native_currentness_execution_or_publication_qualified']is False
                and v['original_saved_and_reopened_parameter_equality']is True,'P627_EVERY_GENERATED_OUTPUT_VERIFIED')
        step['observations']=result;return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-begin,3)

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-first-insertion'],'P627_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P627_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=observer=None;observer_clean=True
    row=dict(state='FAILED627_FIRST_BOOKMARK_INSERTION',steps=[],own_cpu_selection=selection,actual_Hancom_COM_Native_or_SQL_started=False,
        official249_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,PC_freeze_resolved=False,
        full_F11_or_product_route_or_native_display_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='ab0f33440a08a7d79182c3d396a51de1b03afe8e9475cdf6c7ee2292d96651c6'
            and prior['state']=='PASS626_NEW_FIELD_INSERTION_SOURCE_ENVELOPE8_ACTUAL8_NOT_FULL_F11_OR_NATIVE'and prior['cleanup']is True,'P627_PREVIOUS626_UNCHANGED')
        failed=receipt.unpack(q.json(FAILED));c.require(q.snapshots[FAILED]['sha256']=='05ad13de5551770cc53b6f2597e181ff85ae71176997f5dc5cc2d8d6039a62dc'
            and failed['state']=='FAILED627_FIRST_BOOKMARK_INSERTION'and failed['cleanup']is True,'P627_ORIGINAL_COMPILE_FAILURE_PRESERVED')
        passed={name for step in failed['steps']for name,status in step.get('tests',[])if status=='ok'}
        c.require(len(passed)==8 and len(failed['compiled_inputs'])==1 and failed['steps'][0]['exit_code']==0
            and failed['steps'][1]['bounded_output_observation']['observed_harness_started']is False,'P627_AFFECTED8_PASS_NEW_CORE_NEVER_EXECUTED')
        failedpins={v['path']:v for v in failed['source_pins']}
        previous={v['path']:v for v in prior['source_pins']}
        for name in OBSERVER:
            path='tools/p09/'+name+'.py';c.require(q.pin(path)==previous[path],'P627_QUALIFIED_OBSERVER_UNCHANGED')
        guard.check(force=True)
        if guard.samples[-1]['system_cpu_percent']<75:observer=attribution.Attached(guard)
        else:row['observer_unavailable_reason']='INITIAL_CPU_WARNING_NO_OPTIONAL_PROCESS_QUERY'
        names=inventory.inventory(guard)|includes.test_inputs((OLD,TEST,EXAMPLE),guard)|{SELF,PRIOR,OLD,TEST,EXAMPLE,CORPUS,ARCHIVE+'bookmark_insertion626.rs',ARCHIVE+'source_crossref.rs',
            'target/debug/examples/p09_crossref_capture010_probe.exe'}
        names|={FAILED,ARCHIVE+'verifier-audit001.py',ARCHIVE+'test-audit001.rs',ARCHIVE+'Cargo.lock',ARCHIVE+'product-cli.Cargo.toml'}
        names|={'implementation/p09/evidence/p09-361-bookmark-creation627-audit002.v1.json',ARCHIVE+'verifier-audit002.py',ARCHIVE+'test-audit002.rs'}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P627_ACTUAL_CORPUS')
        pins=[corpus['source']]+[v['artifacts'][stage]for v in corpus['cases']for stage in('saved','reopened')]
        c.require(len(pins)==17,'P627_ACTUAL_ORIGINAL_AND_PARAMETER16');names|={v['path']for v in pins}
        for path in sorted(names):
            if path not in q.snapshots:q.pin(path)
        for pin in pins:c.require(q.snapshots[pin['path']]==pin,'P627_FIXED_SOURCE_EXACT')
        c.require(q.snapshots[ARCHIVE+'bookmark_insertion626.rs']['sha256']==previous[PARENT]['sha256'],'P627_ORIGINAL626_SOURCE_ARCHIVE')
        old=q.text(ARCHIVE+'bookmark_insertion626.rs');current=q.text(PARENT)
        c.require(old.split('        let rebuilt',1)[1].split('        let meanings',1)[0]
            ==current.split('        let rebuilt',1)[1].split('        let (begin, end, source_envelope_sha256)',1)[0],'P627_ORIGINAL_WHOLE_SOURCE_PROTECTION_SELECTION_ID_AND_OVERLAP_GUARDS_UNCHANGED')
        c.require(old.split('fn named(',1)[1].split('impl ImportedDocumentFields',1)[0]
            ==current.split('fn named(',1)[1].split('impl ImportedDocumentFields',1)[0],'P627_ORIGINAL_ENVELOPE_PATCH_HELPERS_UNCHANGED')
        addition='pub mod bookmark_insertion;\n'
        c.require(q.text(PRODUCT).count(addition)==1 and q.text(PRODUCT).replace(addition,'',1)==q.text(ARCHIVE+'source_crossref.rs')
            and q.snapshots[ARCHIVE+'source_crossref.rs']['sha256']==previous[PRODUCT]['sha256'],'P627_EXISTING_PRODUCT_BODIES_UNCHANGED')
        for path,pin in previous.items():
            if path.startswith('crates/')and '/src/'in path and path not in(PARENT,PRODUCT):c.require(q.snapshots[path]==pin,'P627_ALL_OTHER_COMPILED_RUST_UNCHANGED')
        for path,pin in failedpins.items():
            if path.startswith('crates/')and '/src/'in path:c.require(q.snapshots[path]==pin,'P627_ALL_ALREADY_TESTED_PRODUCT_BODIES_IDENTICAL')
        c.require(q.snapshots[ARCHIVE+'test-audit001.rs']['sha256']==failedpins[TEST]['sha256'],'P627_UNEXECUTED_TEST_ORIGINAL_PRESERVED')
        manifest='crates/product-cli/Cargo.toml';oldmanifest=q.text(ARCHIVE+'product-cli.Cargo.toml')
        c.require(q.snapshots[ARCHIVE+'product-cli.Cargo.toml']['sha256']==failedpins[manifest]['sha256']
            and q.text(manifest).replace('quick-xml.workspace = true\n','',1)==oldmanifest,'P627_ONLY_NORMAL_EXAMPLE_DEV_DEPENDENCY_ADDED')
        oldlock=q.text(ARCHIVE+'Cargo.lock');currentlock=q.text('Cargo.lock')
        c.require(q.snapshots[ARCHIVE+'Cargo.lock']['sha256']==failedpins['Cargo.lock']['sha256'],'P627_ORIGINAL_LOCK')
        start=currentlock.index('[[package]]\nname = "hwpx-agent-cli"');stop=currentlock.index('[[package]]',start+12);segment=currentlock[start:stop]
        c.require(segment.count(' "quick-xml",\n')==1 and currentlock.replace(segment,segment.replace(' "quick-xml",\n','',1),1)==oldlock,
            'P627_LOCK_ONLY_DECLARES_EXISTING_QUICK_XML_FOR_CLI_DEV_NO_VERSION_OR_OTHER_GRAPH_CHANGES')
        c.require(q.snapshots[OLD]==previous[OLD],'P627_ORIGINAL_EIGHT_TESTS_UNCHANGED')
        c.require(q.snapshots['target/debug/examples/p09_crossref_capture010_probe.exe']==previous['target/debug/examples/p09_crossref_capture010_probe.exe'],'P627_CONSUMED010_IMAGE_UNCHANGED_NOT_RUN')
        hosts=[]
        for path,count in((OLD,8),(TEST,7)):
            text=q.text(path);cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text));c.require(len(cases)==count and '#[ignore]'not in text,'P627_EXPECTED_CASES')
            hosts.append((path.rsplit('/',1)[1][:-3],cases))
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P627_NO_HWP_BEFORE')
        c.require(hosts[0][1]==passed,'P627_RETAINED8_EXACT_CASE_SET');hosts=hosts[1:]
        scratch=c.ROOT/'target/p09-bookmark-creation627-audit003-scratch';c.require(not scratch.exists(),'P627_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1');artifact=a.AcceptanceReader(c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--features','p09-installed-format-fixture','--message-format=short']
        print(json.dumps(dict(state='P627_PREFLIGHT',new_core_tests=7,retained_affected8_not_replayed=True,actual_original=1,actual_parameter_specimens=16,
            previous624_tests_replayed=False,CPU_RAM_guards_unchanged=True)),flush=True)
        for entry in failed['compiled_inputs']:
            for key in('dep_info','binary'):c.require(artifact.pin(entry[key]['path'])==entry[key],'P627_ORIGINAL_PASSED_TEST_ARTIFACT_STILL_EXACT')
        row.update(retained_pass_tests=sorted(passed),retained_source_receipt=FAILED,retained_compiled_inputs=failed['compiled_inputs'],original_eight_not_replayed=True)
        row['compiled_inputs']=[]
        for target,cases in hosts:
            build_begin=time.time_ns()
            r.harness.run_one(target,[r.harness.CARGO,'test',*common,'-p','hwpx-package','--test',target,'--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,env,row,observe_capture=r.snapshot)
            for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<build_begin:continue
                declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P627_ALL_ACTUAL_TEST_COMPILER_INPUTS_PREPINNED')
                row['compiled_inputs'].append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P627_NO_TEST_WARNINGS')
        c.require(len(row['compiled_inputs'])==1,'P627_NEW_TEST_DEP_INFO_REQUIRED')
        product_args=[*common,'-p','hwpx-agent-cli','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        example='p09_bookmark_creation627'
        r.harness.run_one('normal_first_bookmark_insertion_build',[r.harness.CARGO,'build',*product_args,'--example',example],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P627_NORMAL_BUILD_NO_WARNINGS')
        image=artifact.pin('target/debug/examples/'+example+'.exe');dep=artifact.pin('target/debug/examples/'+example+'.d');declared=deps.dependencies(c.ROOT/dep['path'])
        c.require({TEST,EXAMPLE,CORPUS}<=declared and declared<=set(q.snapshots),'P627_NORMAL_PRODUCT_DEPENDENCIES_PREPINNED')
        row['actual_product_observation']=observe_fixed(guard,env,row,[r.harness.CARGO,'run',*product_args,'--example',example,'--','--fixed-first-insertion-readonly'])
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P627_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P627_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS627_FIRST_INSERTION_CORE7_AFFECTED8_NORMAL_PRODUCT8_ORIGINAL_PARAMETER16_NOT_NATIVE',new_core_tests=7,affected_tests=8,
            current_executed_tests=7,retained_affected_tests=8,total_unique_conditions=15,actual_original_source_count=1,actual_saved_and_reopened_parameter_specimens=16,normal_product_insertions=8,
            compiled_normal_example=image,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P627_FAILURE_NO_RAW_VALUES')
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
    return 0 if row['cleanup']and row['state'].startswith('PASS627_')else 2
if __name__=='__main__':raise SystemExit(main())
