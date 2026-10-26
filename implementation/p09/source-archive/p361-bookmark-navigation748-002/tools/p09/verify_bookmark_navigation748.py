"""New source cursor navigation9 and existing original/renamed16, no Native or old replay."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture747 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_bookmark_navigation748.py'
TEST='crates/product-cli/tests/bookmark_navigation745.rs'
EXAMPLE='crates/product-cli/examples/p09_bookmark_navigation746.rs'
EXE='target/debug/examples/p09_bookmark_navigation746.exe'
DEP=EXE[:-4]+'.d'
PRIOR='implementation/p09/evidence/p09-361-bookmark-rename742-product004.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-bookmark-navigation743-inputs.v1.json'
ORIGINAL='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-navigation743/'
CHANGED={'crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets.rs','crates/product-cli/src/reference_validation_product/source_crossref.rs'}
OUTPUT='implementation/p09/evidence/p09-361-bookmark-navigation748-product002.v1.json'
FAILED='implementation/p09/evidence/p09-361-bookmark-navigation748-product001.v1.json'
CORRECTION='implementation/p09/source-archive/p361-bookmark-navigation748-001/'

def require(ok,code):
    if not ok:raise ValueError('XREF_NAV748_'+code)

def main():
    require(sys.argv[1:]==['--current-source-navigation-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED748_CURRENT_SOURCE_BOOKMARK_NAVIGATION',steps=[],Native_started=False,
        passed742_736_730_725_721_713_Native249_replayed=False,native_cursor_or_complete_F11_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='da36826af43cd85c933b1549204a3b29aefc7fac62e9619ec97be23324350cb3'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1258
            and prior['phase_resources']['original_sampler_calls']==587 and prior['artifact_final_fresh_hashes']==12,'EXACT742_AND_RESOURCE_CONTRACT')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CODE_PRESERVED_AND_EXACT_SOURCE_ARCHIVES')
        failed=p.codec.unpack(q.json(FAILED),guard.check)
        require(q.snapshots[FAILED]['sha256']=='072056425df4a23fc92b088c4820aea79ad4f63e01149f7d4561eac68c6628d8'
            and failed['cleanup']is True and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101
            and not failed['steps'][0]['tests'],'EXACT_COMPILE_ONLY_FAILURE_NO_TEST_EXECUTED')
        for pin in failed['source_pins']:
            name=CORRECTION+pin['path']if pin['path']in(SELF,TEST)else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_FAILED_CODE_PRESERVED_PUBLIC_TOKEN_API_CORRECTION_ONLY')
        row['retained_compile_only_failure']=dict(receipt=FAILED,tests_executed=0,public_XML_API_not_widened=True)
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,MANIFEST,ORIGINAL,'tools/p09/product_result_capture747.py'}
        for name in sorted(names):q.pin(name)
        manifest=q.json(MANIFEST);original=q.json(ORIGINAL)
        require(len(manifest['cases'])==8 and manifest['scope']=='input_pins_not_navigation_or_native_acceptance','INPUT_ONLY_NOT_ACCEPTANCE')
        for case,old,generated in zip(manifest['cases'],original['cases'],prior['generated_files'],strict=True):
            require(case['case_index']==old['case_index']and case['original']==old['stages']['reopened']['pin']and case['renamed']==generated,'EXACT_PRIOR_SOURCE_AND_GENERATED_PINS')
            for stage in('original','renamed'):require(q.pin(case[stage]['path'])==case[stage],'CURRENT16_SOURCES')
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(cases)==9,'EXACT_NEW9')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        def snapshot(capture,expected):
            value=r.snapshot(capture,expected);observer.phase('tests'if value.get('observed_harness_started')else'build');return value
        env=r.audit.environment();observer.phase('build');start=time.time_ns()
        r.harness.run_one('new_navigation9_no_previous_tests_replayed',
            [r.harness.CARGO,'test',*common,'--test','bookmark_navigation745','--',*sorted(cases),'--exact','--test-threads=1'],
            cases,guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NEW_TESTS_CLEAN')
        observer.phase('binary_binding');images=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('bookmark_navigation745-*.d'):
            if path.stat().st_mtime_ns<start:continue
            require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPS_PREBOUND')
            images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
        require(len(images)==1,'ONE_CURRENT_TEST_IMAGE');row['compiled_tests']=images
        observer.phase('build')
        r.harness.run_one('build_navigation_actual16_example746',[r.harness.CARGO,'build',*common,'--example','p09_bookmark_navigation746'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPS_PREBOUND')
        observer.phase('readback')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--original-and-renamed-navigation-no-native'],env,row,'actual16_original_and_renamed_current_destinations_no_native')
        require(actual is not None and actual['state']=='QUALIFIED746_ORIGINAL_AND_RENAMED16_CURRENT_SOURCE_NAVIGATION8_DISABLED8_NOT_NATIVE_CURSOR_OR_F11'
            and len(actual['cases'])==16 and actual['resolved']==actual['disabled']==8
            and all(actual[k]is False for k in('Native_started','native_cursor_moved','full_F11_or_P09_qualified')),'WHOLE16_NAVIGATION_NOT_NATIVE_OR_GATE')
        expected=[(c,stage)for c in manifest['cases']for stage in('original','renamed')]
        for observed,(case,stage)in zip(actual['cases'],expected,strict=True):
            require(observed['case_index']==case['case_index']and observed['stage']==stage and observed['source']==case[stage]
                and observed['source_unchanged']is True,'EXACT_SOURCE_AND_ORDER')
            enabled=case['case_index']%2==0;position=observed['source_position']
            require(observed['status']==('source_destination_resolved'if enabled else'hyperlink_disabled')
                and (isinstance(position,list)and len(position)==2 and 0<=position[0]<position[1]if enabled else position is None),'EXACT_SOURCE_RANGE_OR_NO_DESTINATION')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED748_CURRENT_SOURCE_BOOKMARK_NAVIGATION_NEW9_ACTUAL16_NOT_NATIVE_CURSOR_OR_F11',
            product=actual,new_tests=9,actual_source_variants=16,source_destinations=8,disabled_without_destination=8,
            original_sources_unchanged=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-bookmark-navigation748-product002-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED748_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
