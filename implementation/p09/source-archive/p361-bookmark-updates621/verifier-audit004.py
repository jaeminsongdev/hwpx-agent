"""Focused real source-bound command updates, no Native or original overwrite."""
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
SELF='tools/p09/verify_bookmark_command_updates621.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-command-updates621-audit004.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-bookmark-command-updates621-audit004-forensic'
FAILED='implementation/p09/evidence/p09-361-bookmark-command-updates621-audit002.v1.json'
PRIOR='implementation/p09/evidence/p09-361-bookmark-cache-diagnostics620-audit002.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-updates621/'
EXAMPLE='crates/product-cli/examples/p09_bookmark_command_updates621.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
PARENTS={'crates/hwpx-package/src/document_import/fields/semantics/source_index.rs':('source_index.rs','pub mod bookmark_updates;\n'),
 'crates/product-cli/src/reference_validation_product/source_crossref.rs':('source_crossref.rs','pub mod bookmark_updates;\n'),
 'crates/hwpx-package/src/document_import/reference_targets/sdk.rs':('sdk.rs','\n    /// Hash of the exact imported target state, not a current service capability.\n    #[must_use]\n    pub fn source_target_state_sha256(&self) -> &str {\n        &self.receipt.target_state_sha256\n    }\n')}

def snapshot(capture,expected):
    result=r.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    result['closed_bookmark_protection_cases']=sorted(set(re.findall(r'P621_PROTECTION_CASE_[0-4]_(?:PROTECTION|SOURCE|SELECTION|TARGET|OTHER_ERROR|UNEXPECTED_SUCCESS)\b',raw)))
    return result

def read_only(guard,env,row,args):
    owned=capture=None;begin=time.monotonic();step=dict(stage='actual_fixed16_update_candidates',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<120,'P621_READONLY_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(line.startswith(('error','warning'))for line in err.splitlines()),'P621_READONLY_NO_ERRORS_OR_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='source_bookmark_updates621_candidates_not_native_or_currentness'and len(result['observations'])==16
            and result['actual_native_started']is False and result['cache_currentness_qualified']is False and result['source_overwritten']is False and result['P09_complete']is False,'P621_FIXED16_NOT_NATIVE')
        for item in result['observations']:
            v=item['receipt'];r.c.require(v['changed_command_leaves']==1 and len(v['changes'])==1 and v['outside_selected_command_contents_exact']is True
                and v['cached_values_preserved_not_refreshed']is True and v['native_protection_currentness_execution_or_publication_qualified']is False,'P621_EACH_OUTPUT_PRESERVING_NOT_NATIVE')
        step['observations']=result;return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-begin,3)

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-source-updates'],'P621_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P621_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=observer=None;observer_clean=True
    row=dict(state='FAILED621_BOOKMARK_COMMAND_UPDATES',steps=[],own_cpu_selection=selection,actual_Hancom_COM_Native_or_DB_started=False,
        official249_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,source_schema_unchanged='v15',field_meaning_schema_unchanged='v2',
        native_display_or_cache_currentness_qualified=False,PC_freeze_resolved=False,original_source_overwritten=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='6f9f0298096fdb1042bdefb805446b9c8800c0a2b095951666f745ee859bacb3'
            and prior['state']=='PASS620_TYPED_BOOKMARK_CACHE_DIAGNOSTICS_31_AND_FIXED24_NOT_NATIVE_OR_CURRENTNESS'and prior['cleanup']is True,'P621_PREVIOUS620_PRESERVED')
        failed=receipt.unpack(q.json(FAILED));c.require(q.snapshots[FAILED]['sha256']=='1c3d35c49aec52dec943b11221aa82a479853b54f2e5c82d8698b84e37c58c50'
            and failed['state']=='FAILED621_BOOKMARK_COMMAND_UPDATES'and failed['cleanup']is True,'P621_FAILED002_PRESERVED')
        retained={name for step in failed['steps']for name,status in step.get('tests',[])if status=='ok'}
        corrected={name for step in failed['steps']for name,status in step.get('tests',[])if status!='ok'}
        c.require(len(retained)==7 and corrected=={'tests::finite_output_budget_and_private_values_never_become_public_authority','tests::observed_locks_tracked_changes_table_protection_and_outer_field_locks_reject'},'P621_EXACT7_PASS2_FAILED')
        previous='implementation/p09/evidence/p09-361-bookmark-command-updates621-audit003.v1.json';delta=receipt.unpack(q.json(previous))
        c.require(q.snapshots[previous]['sha256']=='24b3edde07babd0c0282acf02fab7ba55b5574738b50fdea2953ce87ebe5ad21'and delta['cleanup']is True,'P621_FAILED003_PRESERVED')
        retained|={name for step in delta['steps']for name,status in step.get('tests',[])if status=='ok'};corrected-={name for step in delta['steps']for name,status in step.get('tests',[])if status=='ok'}
        c.require(len(retained)==8 and len(corrected)==1,'P621_EXACT8_PASS1_FAILED')
        names=inventory.inventory(guard)|includes.test_inputs((EXAMPLE,),guard)|{SELF,CORPUS,PRIOR,
            ARCHIVE+'bookmark_updates-audit001.rs',ARCHIVE+'example-audit001.rs',ARCHIVE+'verifier-audit001.py',
            'implementation/p09/evidence/p09-361-bookmark-command-updates621-audit001.v1.json',FAILED,previous,ARCHIVE+'example-audit002.rs',ARCHIVE+'verifier-audit002.py',ARCHIVE+'example-audit003.rs',ARCHIVE+'verifier-audit003.py'}|{pin['path']for pin in prior['source_pins']}|{ARCHIVE+old for old,_ in PARENTS.values()}|{pin['path']for pin in delta['source_pins']}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P621_FIXED_CORPUS')
        fixed=[corpus['source'],*[pin for case in corpus['cases']for pin in case['artifacts'].values()]];names|={pin['path']for pin in fixed}
        for name in sorted(names):
            if name not in q.snapshots:q.pin(name)
        for pin in fixed:c.require(q.snapshots[pin['path']]==pin,'P621_FIXED25_ORIGINALS')
        for pin in delta['source_pins']:
            if pin['path']not in(SELF,EXAMPLE):c.require(q.snapshots[pin['path']]==pin,'P621_RETAINED7_ALL_PRODUCT_AND_OTHER_INPUTS_UNCHANGED')
        c.require(q.snapshots[ARCHIVE+'example-audit003.rs']['sha256']==next(v['sha256']for v in delta['source_pins']if v['path']==EXAMPLE),'P621_ORIGINAL_FAILED_TESTS_ARCHIVED')
        old=q.text(ARCHIVE+'example-audit003.rs');current=q.text(EXAMPLE)
        for name in corrected:
            pattern=r'    #\[test\]\n    fn '+name.split('::')[-1]+r'\(\).*?(?=    #\[test\]|\n\}\n?\Z)'
            old,n=re.subn(pattern,'',old,flags=re.S);current,m=re.subn(pattern,'',current,flags=re.S);c.require(n==m==1,'P621_EXACT_FAILED_TEST_FUNCTION')
        c.require(old==current,'P621_OTHER7_HELPERS_AND_FIXED16_OBSERVER_UNCHANGED')
        for pin in prior['source_pins']:
            name=pin['path']
            if name in PARENTS:
                old,insertion=PARENTS[name];text=q.text(name);c.require(text.count(insertion)==1 and text.replace(insertion,'',1)==q.text(ARCHIVE+old)
                    and q.snapshots[ARCHIVE+old]['sha256']==pin['sha256'],'P621_ONLY_MODULE_DECLARATIONS_EXISTING_PRODUCT_BODIES_UNCHANGED')
            else:c.require(q.snapshots[name]==pin,'P621_PREVIOUS_PRODUCT_TEST_HELPER_INPUTS_UNCHANGED')
        row.update(previous620_source_checks_retained_without_replay=True,observer20_models_retained_by_identical_inputs=True,prior_receipt=q.snapshots[PRIOR])
        text=q.text(EXAMPLE);c.require('#[ignore]'not in text,'P621_NO_IGNORED_TESTS');cases={'tests::'+v for v in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(cases)==9,'P621_EXACT9_TESTS');guard.check(force=True);observer=attribution.Attached(guard)
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P621_NO_HWP_BEFORE')
        c.require(q.snapshots['target/debug/examples/p09_crossref_capture010_probe.exe']['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P621_CONSUMED010_IMAGE_UNCHANGED')
        scratch=c.ROOT/'target/p09-bookmark-updates621-audit004-scratch';c.require(not scratch.exists(),'P621_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1');artifact=a.AcceptanceReader(c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture','--message-format=short',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        example='p09_bookmark_command_updates621';row['compiled_inputs']=[]
        c.require(cases==retained|corrected,'P621_ALL9_ACCOUNTED_FOR');row.update(retained_tests=sorted(retained),retained_test_count=8,retained_test_bodies_reexecuted=False,prior_failed_receipt=q.snapshots[previous]);cases=corrected
        print(json.dumps(dict(state='P621_FRESH_PREFLIGHT',inputs=len(q.snapshots),new_rust_tests=9,current_rust_tests=2,retained_tests=7,previous620_tests_replayed=False,actual_saved_or_reopened_inputs=16,CPU_RAM_guards_unchanged=True)),flush=True)
        build_begin=time.time_ns();r.harness.run_one(example,[r.harness.CARGO,'test',*common,'--example',example,'--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P621_NO_WARNINGS')
        for path in(c.ROOT/'target/debug/examples').glob(example+'-*.d'):
            if path.stat().st_mtime_ns<build_begin:continue
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P621_ACTUAL_COMPILER_INPUTS_PREPINNED')
            row['compiled_inputs'].append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
        c.require(bool(row['compiled_inputs']),'P621_FRESH_TEST_ARTIFACTS')
        r.harness.run_one('normal_bookmark_update_build',[r.harness.CARGO,'build',*common,'--example',example],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P621_NORMAL_BUILD_NO_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+example+'.exe');dep=artifact.pin('target/debug/examples/'+example+'.d');declared=deps.dependencies(c.ROOT/dep['path'])
        c.require({EXAMPLE,CORPUS}<=declared and declared<=set(q.snapshots),'P621_NORMAL_COMPILED_INPUTS_PINNED')
        row['actual_update_candidates']=read_only(guard,env,row,[r.harness.CARGO,'run',*common,'--example',example,'--','--fixed-captured-readonly'])
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P621_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P621_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS621_SOURCE_BOOKMARK_COMMAND_UPDATES_9_AND_FIXED16_NOT_NATIVE_OR_CACHE_REFRESH',
            new_rust_tests=9,current_executed_rust_tests=1,retained_test_count=8,actual_saved_or_reopened_inputs=16,compiled_normal_example=binary,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P621_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P621_FAILURE_RECORDED_BEFORE_ENCODING',error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        if observer is not None:observer_clean=observer.close();row['resource_attribution']=observer.summary()
        guard.close();row.update(cleanup=guard.cleanup and observer_clean and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','new_rust_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),locations=v.get('locations'),panic_locations=v.get('panic_locations'),safe_error_variants=v.get('safe_error_variants'),
                protection_cases=v.get('bounded_output_observation',{}).get('closed_bookmark_protection_cases'),failed_cases=[name for name,status in v.get('tests',[])if status!='ok'])for v in row['steps']],
            'resource_attribution':row.get('resource_attribution'),'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS621_')else 2
if __name__=='__main__':raise SystemExit(main())
