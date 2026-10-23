"""Focused typed stored-name diagnostics + original guarded resource observer."""
import hashlib,importlib,json,re,subprocess,sys,time,unittest
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_lossless_receipt610 as receipt
import metadata_forensic_retention615 as retention
import crossref_native_startup as startup
import metadata_cpu_observer620 as attribution
SELF='tools/p09/verify_bookmark_cache_diagnostics620.py'
OUTPUT='implementation/p09/evidence/p09-361-bookmark-cache-diagnostics620-audit002.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-bookmark-cache-diagnostics620-audit002-forensic'
PRIOR='implementation/p09/evidence/p09-361-bookmark-cache-diagnostics620-audit001.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-cache-diagnostics620/'
NEW='crates/product-cli/examples/p09_bookmark_cache_diagnostics620.rs'
EXAMPLES=(NEW,'crates/product-cli/examples/p09_field_cached_source619.rs','crates/product-cli/examples/p09_bookmark_command_bindings613.rs')
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
MODELS=('test_metadata_cpu_observer620','test_native_process_cpu_attribution_v4','test_bounded_cpu_attribution_probe_v2')

def tests(q,path):
    text=q.text(path);r.c.require('#[ignore]'not in text,'P620_NO_IGNORED_TESTS')
    return {'tests::'+v for v in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}

def read_only(guard,env,row,args):
    owned=capture=None;begin=time.monotonic();step=dict(stage='fixed24_typed_diagnostics',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<120,'P620_READONLY_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(line.startswith(('error','warning'))for line in err.splitlines()),'P620_READONLY_NO_ERRORS_OR_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='source_bookmark_cache620_observed_not_native_or_currentness'and len(result['observations'])==24
            and result['stored_name_matches_command']==4 and result['other_display_not_compared']==12
            and result['actual_native_started']is False and result['cache_currentness_qualified']is False and result['P09_complete']is False,'P620_FIXED24_NOT_NATIVE')
        step['observations']=result;return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-begin,3)

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-source-diagnostics'],'P620_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P620_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=observer=None;observer_clean=True
    row=dict(state='FAILED620_BOOKMARK_CACHE_DIAGNOSTICS',steps=[],own_cpu_selection=selection,actual_Hancom_COM_Native_or_DB_started=False,
        official249_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,source_schema_unchanged='v15',field_meaning_schema_unchanged='v2',
        native_display_or_cache_currentness_qualified=False,PC_freeze_resolved=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='a41f34696fd45b331d025e6592b7659fa2d8e098b32c8f0f553c13055a1a200a'
            and prior['state']=='FAILED620_BOOKMARK_CACHE_DIAGNOSTICS'and prior['cleanup']is True,'P620_ORIGINAL_FAILED001_PRESERVED')
        retained={name for step in prior['steps']for name,status in step.get('tests',[])if status=='ok'}
        failed={name for step in prior['steps']for name,status in step.get('tests',[])if status!='ok'}
        c.require(len(retained)==10 and failed=={'tests::requested_output_boundary_and_text_and_item_limits_remain_effective'},'P620_EXACT10_PASS1_FAILED')
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        modules=[importlib.import_module(name)for name in MODELS]
        names=inventory.inventory(guard)|includes.test_inputs(EXAMPLES,guard)|{SELF,CORPUS,ARCHIVE+'bookmark_crossref.rs',ARCHIVE+'source_crossref.rs',
            ARCHIVE+'example-audit001.rs',ARCHIVE+'verifier-audit001.py',PRIOR}|{pin['path']for pin in prior['source_pins']}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P620_FIXED_CORPUS')
        fixed=[corpus['source'],*[pin for case in corpus['cases']for pin in case['artifacts'].values()]];names|={pin['path']for pin in fixed}
        for name in sorted(names):
            if name not in q.snapshots:q.pin(name)
        for pin in fixed:c.require(q.snapshots[pin['path']]==pin,'P620_FIXED25_ORIGINALS')
        for pin in prior['source_pins']:
            if pin['path']not in(SELF,NEW):c.require(q.snapshots[pin['path']]==pin,'P620_RETAINED_ALL_OTHER_PRODUCT_MODEL_AND_INPUT_PINS_IDENTICAL')
        c.require(q.snapshots[ARCHIVE+'example-audit001.rs']['sha256']==next(v['sha256']for v in prior['source_pins']if v['path']==NEW),'P620_EXACT_OLD_FAILED_TEST_SOURCE_ARCHIVED')
        pattern=r'    #\[test\]\n    fn requested_output_boundary_and_text_and_item_limits_remain_effective\(\).*?(?=    #\[test\])'
        current,count=re.subn(pattern,'',q.text(NEW),flags=re.S);old,old_count=re.subn(pattern,'',q.text(ARCHIVE+'example-audit001.rs'),flags=re.S)
        c.require(count==old_count==1 and current==old,'P620_ONLY_FAILED_TEST_CHANGED_OTHER10_AND_ALL_HELPERS_UNCHANGED')
        for current,old,insertion in [('crates/hwpx-package/src/document_import/fields/bookmark_crossref.rs','bookmark_crossref.rs','pub mod cache_diagnostics;\n'),
            ('crates/product-cli/src/reference_validation_product/source_crossref.rs','source_crossref.rs','pub mod bookmark_cache_diagnostics;\n')]:
            text=q.text(current);c.require(text.count(insertion)==1 and text.replace(insertion,'',1)==q.text(ARCHIVE+old),'P620_PARENT_MODULE_ONLY_EXISTING_READERS_UNCHANGED')
        suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module)for module in modules)
        c.require(suite.countTestCases()==20 and prior['observer_models']==dict(expected=20,executed=20,failures=0,errors=0,skipped=0,failed_test_ids=[]),'P620_OBSERVER20_MODELS_RETAINED_SAME_INPUTS')
        row['observer_models']={**prior['observer_models'],'currently_executed':0,'retained_by_identical_inputs':True}
        row.update(retained_tests=sorted(retained),retained_test_count=10,retained_test_bodies_reexecuted=False,prior_failed_receipt=q.snapshots[PRIOR])
        guard.check(force=True);observer=attribution.Attached(guard)
        cases=[tests(q,path)for path in EXAMPLES];c.require(tuple(map(len,cases))==(11,10,10),'P620_FOCUSED31_RUST_TESTS')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P620_NO_HWP_BEFORE')
        old_probe=q.pin('target/debug/examples/p09_crossref_capture010_probe.exe');c.require(old_probe['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P620_CONSUMED010_IMAGE_UNCHANGED')
        scratch=c.ROOT/'target/p09-cache-diagnostics620-audit002-scratch';c.require(not scratch.exists(),'P620_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);row['compiled_inputs']=[]
        common=['--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture','--message-format=short',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        print(json.dumps(dict(state='P620_FRESH_PREFLIGHT',inputs=len(q.snapshots),retained_observer_models=20,retained_rust_tests=10,corrected_tests=1,affected_tests=20,total_rust_tests=31,
            actual010_outputs=24,CPU_RAM_guards_unchanged=True,additional_process_observation_cold_seconds=8)),flush=True)
        for path,selected in zip(EXAMPLES,cases):
            if path==NEW:
                c.require(selected==retained|failed,'P620_ALL11_TESTS_ACCOUNTED_FOR');selected=failed
            target=path.rsplit('/',1)[-1][:-3];build_begin=time.time_ns()
            r.harness.run_one(target,[r.harness.CARGO,'test',*common,'--example',target,'--',*sorted(selected),'--exact','--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],selected);c.require(not row['steps'][-1]['diagnostics'],'P620_NO_WARNINGS')
            found=[]
            for path in(c.ROOT/'target/debug/examples').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<build_begin:continue
                declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P620_ACTUAL_COMPILER_INPUTS_PREPINNED')
                found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
            c.require(bool(found),'P620_FRESH_COMPILER_ARTIFACTS');row['compiled_inputs'].append(dict(target=target,artifacts=found))
        example='p09_bookmark_cache_diagnostics620'
        r.harness.run_one('normal_diagnostic_build',[r.harness.CARGO,'build',*common,'--example',example],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P620_NORMAL_BUILD_NO_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+example+'.exe');dep=artifact.pin('target/debug/examples/'+example+'.d');declared=deps.dependencies(c.ROOT/dep['path'])
        c.require({NEW,CORPUS}<=declared and declared<=set(q.snapshots),'P620_NORMAL_COMPILED_INPUTS_PINNED')
        row['actual_cache_diagnostics']=read_only(guard,env,row,[r.harness.CARGO,'run',*common,'--example',example,'--','--fixed-captured-readonly'])
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P620_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P620_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS620_TYPED_BOOKMARK_CACHE_DIAGNOSTICS_31_AND_FIXED24_NOT_NATIVE_OR_CURRENTNESS',
            new_tests=11,affected_tests=20,total_rust_tests=31,actual010_outputs=24,compiled_normal_example=binary,
            current_executed_rust_tests=21,retained_test_count=10,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P620_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P620_FAILURE_RECORDED_BEFORE_ENCODING',error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        if observer is not None:observer_clean=observer.close();row['resource_attribution']=observer.summary()
        guard.close();row.update(cleanup=guard.cleanup and observer_clean and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','total_rust_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),locations=v.get('locations'),panic_locations=v.get('panic_locations'),
                failed_cases=[name for name,status in v.get('tests',[])if status!='ok'])for v in row['steps']],
            'observer_models':row.get('observer_models'),'resource_attribution':row.get('resource_attribution'),'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS620_')else 2
if __name__=='__main__':raise SystemExit(main())
