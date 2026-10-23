"""Original compiler + selected stored candidates; affected12/new8, no Native/SQL/queue."""
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
SELF='tools/p09/verify_compiled_bookmark623.py'
OUTPUT='implementation/p09/evidence/p09-361-compiled-bookmark623-audit002.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-compiled-bookmark623-audit002-forensic'
PRIOR='implementation/p09/evidence/p09-361-stored-bookmark-commands622-audit002.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-compiler623/'
PARENT='crates/product-cli/src/form_stored_provider/actual_import/bookmark_command_output.rs'
TEST='crates/product-cli/tests/stored_bookmark_command_output622.rs'
CORE='crates/product-cli/tests/support/stored_bookmark_compiler623.rs'
EXAMPLE='crates/product-cli/examples/p09_compiled_bookmark623.rs'
CORPUS='implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json'
OBSERVER_SOURCES=('metadata_cpu_observer620','native_process_cpu_attribution_v1','native_process_cpu_attribution_v2','native_process_cpu_attribution_v3','native_process_cpu_attribution_v4',
    'bounded_cpu_attribution_probe_v1','bounded_cpu_attribution_probe_v2','serial_observer_attribution','serial_cpu_attribution')

def observe_fixed(guard,env,row,args):
    owned=capture=None;begin=time.monotonic();step=dict(stage='actual_saved_source_authenticated_fixture',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[r.harness.CARGO],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-begin<120,'P623_FIXED_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        step.update(exit_code=owned.returncode,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not any(v.startswith(('error','warning'))for v in err.splitlines()),'P623_FIXED_NO_ERRORS_OR_WARNINGS')
        result=json.loads(out);r.c.require(result['state']=='compiled_bookmark623_actual_source_fixture_not_native_CAS_or_route','P623_FIXED_SCOPE')
        for key in('actual_native_started','head_changed','result_ingested','source_overwritten','route_qualified','P09_complete'):r.c.require(result[key]is False,'P623_NO_FALSE_AUTHORITY')
        v=result['receipt'];r.c.require(v['execution_or_publication_authority']is False and v['cached_values_preserved_not_refreshed']is True
            and v['source_field_operations']==1 and v['capability_id']=='ref.crossref_command_edit','P623_STORED_RECEIPT_BOUND')
        step['observations']=result;return result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-begin,3)

def main():
    c,a,s=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--bounded-compiled-bookmark'],'P623_BOUNDED_ONLY');c.require(not(c.ROOT/OUTPUT).exists(),'P623_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();s.host.configure_host_policy(c)
    guard=s.baseline.guard_type(s.policy.guard_type(s.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    begin=time.monotonic();q=artifact=observer=None;observer_clean=True
    row=dict(state='FAILED623_STORED_BOOKMARK_COMMANDS',steps=[],own_cpu_selection=selection,actual_Hancom_COM_Native_or_SQL_started=False,
        official249_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,source_schema_unchanged='v15',field_meaning_schema_unchanged='v2',PC_freeze_resolved=False,
        operating_registry_scanner_key_custody_CAS_or_route_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=receipt.unpack(q.json(PRIOR));c.require(q.snapshots[PRIOR]['sha256']=='20672e8fa4ef505d9394f7da0baa31ffd8da015b44d89fdf03f5e16ac1698f26'
            and prior['state']=='PASS622_STORED_BOOKMARK_COMMANDS_12_AND_ACTUAL_SOURCE_FIXTURE_NOT_NATIVE_CAS_OR_ROUTE'and prior['cleanup']is True,'P623_CURRENT621_PRESERVED')
        previous={v['path']:v for v in prior['source_pins']}
        # Bind the already-qualified low-cost observer once, then cover the
        # expensive initial metadata reads too. Reuse these pins in the union.
        for name in OBSERVER_SOURCES:
            path='tools/p09/'+name+'.py';c.require(q.pin(path)==previous[path],'P623_OBSERVER_CODE_IDENTICAL_TO_QUALIFIED621')
        guard.check(force=True)
        if guard.samples[-1]['system_cpu_percent']<75:observer=attribution.Attached(guard)
        else:row['observer_unavailable_reason']='INITIAL_CPU_WARNING_NO_OPTIONAL_PROCESS_QUERY_OR_AUTOMATIC_REATTACH'
        names=inventory.inventory(guard)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,TEST,CORE,EXAMPLE,CORPUS,PRIOR,ARCHIVE+'bookmark_command_output.rs',ARCHIVE+'stored_bookmark_command_output622.rs',
            'target/debug/examples/p09_crossref_capture010_probe.exe',ARCHIVE+'compiler-tests-audit001.rs',ARCHIVE+'verifier-audit001.py',
            'implementation/p09/evidence/p09-361-compiled-bookmark623-audit001.v1.json'}
        corpus=q.json(CORPUS);c.require(q.snapshots[CORPUS]['sha256']=='9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f','P623_FIXED_CORPUS')
        fixed=corpus['cases'][2]['artifacts']['saved'];names.add(fixed['path'])
        for name in sorted(names):
            if name not in q.snapshots:q.pin(name)
        c.require(q.snapshots[fixed['path']]==fixed,'P623_ACTUAL_SAVED_SOURCE')
        inverse=q.text(PARENT)
        for addition in ('pub mod compiled;\n','    anchors: Vec<domain_ir::SourceAnchorHandle>,\n',
            '        let anchors = compiled::selected_anchors(&fields, output.receipt())?;\n','            anchors,\n'):
            c.require(inverse.count(addition)==1,'P623_ONLY_EXPECTED_ANCHOR_ADDITIONS');inverse=inverse.replace(addition,'',1)
        c.require(inverse==q.text(ARCHIVE+'bookmark_command_output.rs')and q.snapshots[ARCHIVE+'bookmark_command_output.rs']['sha256']==previous[PARENT]['sha256'],
            'P623_ALL_ORIGINAL_STORED_ACCESS_DELIVERY_GUARDS_UNCHANGED')
        addition='#[path = "support/stored_bookmark_compiler623.rs"]\npub(crate) mod compiler623;\n'
        test=q.text(TEST);c.require(test.count(addition)==1 and test.replace(addition,'',1)==q.text(ARCHIVE+'stored_bookmark_command_output622.rs')
            and q.snapshots[ARCHIVE+'stored_bookmark_command_output622.rs']['sha256']==previous[TEST]['sha256'],'P623_ORIGINAL12_TEST_BODIES_AND_ALL_HELPERS_UNCHANGED')
        for path,pin in previous.items():
            if path.startswith('crates/')and '/src/'in path and path!=PARENT:c.require(q.snapshots[path]==pin,'P623_ALL_OTHER_COMPILED_RUST_BODIES_UNCHANGED')
        c.require('#[ignore]'not in test+q.text(CORE),'P623_NO_IGNORED_TESTS')
        pattern=r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)'
        oldcases=set(re.findall(pattern,test));newcases={'compiler623::'+v for v in re.findall(pattern,q.text(CORE))}
        c.require((len(oldcases),len(newcases))==(12,8),'P623_AFFECTED12_AND_NEW8_CASES');cases=oldcases|newcases
        c.require(q.snapshots['target/debug/examples/p09_crossref_capture010_probe.exe']['sha256']=='379d55499a0e4acefb323fc0904e03809f099416239c2c6757fe2b5d2a76a46c','P623_CONSUMED010_IMAGE_UNCHANGED')
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P623_NO_HWP_BEFORE')
        scratch=c.ROOT/'target/p09-stored-bookmark623-audit002-scratch';c.require(not scratch.exists(),'P623_FRESH_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1');artifact=a.AcceptanceReader(c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture','--message-format=short',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        print(json.dumps(dict(state='P623_FRESH_PREFLIGHT',inputs=len(q.snapshots),new_compiler_tests=8,affected_stored_tests=12,previous621_tests_replayed=False,previous620_observer_models_replayed=False,
            actual_captured_source_count=1,CPU_RAM_guards_unchanged=True,observer_covers_initial_preflight=observer is not None)),flush=True)
        target='stored_bookmark_command_output622';build_begin=time.time_ns()
        r.harness.run_one(target,[r.harness.CARGO,'test',*common,'--test',target,'--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'P623_TEST_NO_WARNINGS');row['compiled_inputs']=[]
        for path in(c.ROOT/'target/debug/deps').glob(target+'-*.d'):
            if path.stat().st_mtime_ns<build_begin:continue
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'P623_ACTUAL_TEST_COMPILER_INPUTS_PREPINNED')
            row['compiled_inputs'].append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),binary=artifact.pin(path.with_suffix('.exe').relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
        c.require(bool(row['compiled_inputs']),'P623_TEST_DEP_INFO_REQUIRED')
        example='p09_compiled_bookmark623';r.harness.run_one('normal_stored_bookmark_example',[r.harness.CARGO,'build',*common,'--example',example],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P623_NORMAL_BUILD_NO_WARNINGS')
        binary=artifact.pin('target/debug/examples/'+example+'.exe');dep=artifact.pin('target/debug/examples/'+example+'.d');declared=deps.dependencies(c.ROOT/dep['path'])
        c.require({TEST,EXAMPLE,CORPUS}<=declared and declared<=set(q.snapshots),'P623_NORMAL_COMPILER_INPUTS_PREPINNED')
        row['actual_stored_observation']=observe_fixed(guard,env,row,[r.harness.CARGO,'run',*common,'--example',example,'--','--fixed-captured-readonly'])
        c.require(not startup.hwp_pids(guard.windows,guard.check),'P623_NO_HWP_AFTER');c.require(not any(scratch.iterdir()),'P623_SCRATCH_EMPTY')
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS623_ORIGINAL_BOOKMARK_COMPILER_8_AND_AFFECTED_STORED12_NOT_NATIVE_CAS_OR_ROUTE',new_compiler_tests=8,affected_stored_tests=12,
            actual_captured_source_count=1,compiled_normal_example=binary,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes,previous621_lowerer_and_original_compiler_owner_code_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P623_FAILURE_NO_RAW_VALUES')
        print(json.dumps(dict(state='P623_FAILURE_RECORDED_BEFORE_ENCODING',error_code=row['error_code'],work_continuing=False)),flush=True)
    finally:
        if observer is not None:observer_clean=observer.close();row['resource_attribution']=observer.summary()
        guard.close();row.update(cleanup=guard.cleanup and observer_clean and all(v['cleanup']for v in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        normalized,retained=retention.retain(c.ROOT,SPOOL,row);pin=s.publisher.publish(c.ROOT,OUTPUT,receipt.pack(normalized,lambda:None),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','new_compiler_tests','affected_stored_tests','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=v['stage'],exit_code=v.get('exit_code'),cleanup=v.get('cleanup'),diagnostics=v.get('diagnostics'),panic_locations=v.get('panic_locations'),
                safe_error_variants=v.get('safe_error_variants'),compile=v.get('bounded_output_observation',{}).get('short_error_locations'),rust_codes=v.get('bounded_output_observation',{}).get('rust_error_codes'),
                failed_cases=[name for name,status in v.get('tests',[])if status!='ok'])for v in row['steps']],
            'resource_attribution':row.get('resource_attribution'),'receipt':pin,'retained_metadata':retained}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith('PASS623_')else 2
if __name__=='__main__':raise SystemExit(main())

