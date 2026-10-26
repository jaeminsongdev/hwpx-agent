"""Atomic target rename9 and actual8 generated outputs, no Native refresh or old replay."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture741 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_bookmark_rename742.py'
TEST='crates/product-cli/tests/bookmark_rename739.rs'
EXAMPLE='crates/product-cli/examples/p09_bookmark_rename740.rs'
EXE='target/debug/examples/p09_bookmark_rename740.exe'
DEP=EXE[:-4]+'.d'
PRIOR='implementation/p09/evidence/p09-361-single-page736-product001.v1.json'
CAPTURE='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-rename737/'
CHANGED={'crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets.rs','crates/product-cli/src/reference_validation_product/source_crossref.rs'}
OUTPUT='implementation/p09/evidence/p09-361-bookmark-rename742-product004.v1.json'
FAILED3='implementation/p09/evidence/p09-361-bookmark-rename742-product003.v1.json'
CORRECTION3='implementation/p09/source-archive/p361-bookmark-rename742-003/'
ENTRY_CHANGED={'crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets/rename737.rs',
    'crates/product-cli/src/reference_validation_product/source_crossref/bookmark_rename738.rs'}
FAILED2='implementation/p09/evidence/p09-361-bookmark-rename742-product002.v1.json'
CORRECTION2='implementation/p09/source-archive/p361-bookmark-rename742-002/'
FAILED='implementation/p09/evidence/p09-361-bookmark-rename742-product001.v1.json'
CORRECTION='implementation/p09/source-archive/p361-bookmark-rename742-001/'
GENERATED='implementation/p09/evidence/private/p09-361-bookmark-rename740-generated001'
def require(ok,code):
    if not ok:raise ValueError('XREF_RENAME742_'+code)
def main():
    require(sys.argv[1:]==['--atomic-target-and-crossref-rename-no-native']and not(r.c.ROOT/OUTPUT).exists()and not(r.c.ROOT/GENERATED).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED742_ATOMIC_TARGET_AND_CROSSREF_RENAME',steps=[],Native_started=False,
        passed736_730_725_721_713_Native249_replayed=False,public_output_revision_or_complete_F11_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='0c420358460ddfd1d78d6ced17a3bf7d352820541e4e707b23a984a58a9c8f81'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1238
            and prior['phase_resources']['original_sampler_calls']==566,'EXACT736_AND_RESOURCE_CONTRACT')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CODE_PRESERVED_AND_EXACT_SOURCE_ARCHIVES')
        failed=p.codec.unpack(q.json(FAILED),guard.check)
        require(q.snapshots[FAILED]['sha256']=='9a5bcbc6fe2622dce81c5717132f1aed19164c0942222b3602413f3e072f7d63'
            and failed['cleanup']is True and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101
            and not failed['steps'][0]['tests'],'PRESERVE_COMPILE_ONLY_FAILURE_NO_PRODUCT_CASE_EXECUTED')
        for pin in failed['source_pins']:
            name=CORRECTION+pin['path']if pin['path']in(SELF,TEST)else CORRECTION3+pin['path']if pin['path']in ENTRY_CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'UNCHANGED_FAILED_INPUTS_AND_EXACT_TEST_PRIVATE_API_CORRECTION_ARCHIVE')
        row['retained_compile_only_failure']=dict(receipt=FAILED,tests_executed=0,private_XML_API_not_made_public=True)
        failed2=p.codec.unpack(q.json(FAILED2),guard.check)
        prior_tests=failed2['steps'][0]['tests'];lock='observed_lock_blocks_the_atomic_rename'
        require(q.snapshots[FAILED2]['sha256']=='fc5777f329962e006a319c3b17b86d0561393df1bbcf8f09e83585f5b571adce'
            and failed2['cleanup']is True and len(prior_tests)==9 and sum(v=='ok'for _,v in prior_tests)==8
            and [name for name,value in prior_tests if value!='ok']==[lock],'RETAIN_EIGHT_SUCCESSFUL_OBSERVATIONS_AND_FAILED_LOCK_FIXTURE')
        for pin in failed2['source_pins']:
            name=CORRECTION2+pin['path']if pin['path']in(SELF,TEST)else CORRECTION3+pin['path']if pin['path']in ENTRY_CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_FAILED002_CODE_AND_LOCK_FIXTURE_ARCHIVES')
        failed3=p.codec.unpack(q.json(FAILED3),guard.check)
        require(q.snapshots[FAILED3]['sha256']=='970598967197663539a8799f97a40a0b40e7fd11529b45f69fd2a60e790e9c17'
            and failed3['cleanup']is True and failed3['steps'][0]['tests']==[[lock,'FAILED']],'PRESERVE003_LOCK_ONLY_FAILURE')
        for pin in failed3['source_pins']:
            name=CORRECTION3+pin['path']if pin['path']in(SELF,TEST)or pin['path']in ENTRY_CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_FAILED003_ENTRY_AND_FIXTURE_ARCHIVES')
        def except_lock(text):
            pieces=re.split(r'(?<=#\[test\])\s*fn observed_lock_blocks_the_atomic_rename\(\)->Result\{.*?\n\}',text,flags=re.S)
            require(len(pieces)==2,'EXACT_ONE_LOCK_FIXTURE');return pieces
        require(except_lock(q.text(CORRECTION3+TEST))==except_lock(q.text(TEST)),'OTHER_EIGHT_TEST_BODIES_UNCHANGED')
        core=next(path for path in ENTRY_CHANGED if path.endswith('rename737.rs'))
        marker='        let bindings=SourceBookmarkCrossReferenceBindings::import'
        require(q.text(CORRECTION3+core).split(marker,1)[1]==q.text(core).split(marker,1)[1],'ATOMIC_PATCH_AND_READBACK_LOGIC_UNCHANGED')
        row['retained_prior_eight_execution_observations']=dict(receipt=FAILED2,tests=[v for v in prior_tests if v[1]=='ok'],
            whole_prior_bundle_qualified=False,current_replayed=['point_marker_rename_rebinds_its_generated_crossref_without_block_promotion'],
            seven_other_conditions_not_replayed=True,source_final_hashes_in_prior_bundle=failed2['final_fresh_hashes'])
        captured=p.codec.unpack(q.json(CAPTURE),guard.check)
        require(q.snapshots[CAPTURE]['sha256']=='63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3'
            and captured['cleanup']is True and captured['fresh_inputs']==captured['final_fresh_hashes']==1054
            and captured['semantic_product_or_render_qualified']is False,'PRIOR_NATIVE_PRODUCER_BOUND_SOURCE_NOT_PREVIOUS_SEMANTIC_ACCEPTANCE')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,MANIFEST,'tools/p09/product_result_capture741.py'}
        for name in sorted(names):q.pin(name)
        manifest=q.json(MANIFEST)
        require(q.pin(manifest['source']['path'])==manifest['source'],'CURRENT_ORIGINAL_SOURCE')
        for case in manifest['cases']:
            for item in case['stages'].values():require(q.pin(item['pin']['path'])==item['pin'],'CURRENT32_CAPTURED_INPUTS')
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(cases)==9,'EXACT_NEW9')
        run_cases={lock,'point_marker_rename_rebinds_its_generated_crossref_without_block_promotion'}
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        def snapshot(capture,expected):
            value=r.snapshot(capture,expected);observer.phase('tests'if value.get('observed_harness_started')else'build');return value
        env=r.audit.environment();observer.phase('build');start=time.time_ns()
        r.harness.run_one('current_early_protection_and_point_entry2_seven_conditions_not_replayed',
            [r.harness.CARGO,'test',*common,'--test','bookmark_rename739','--',*sorted(run_cases),'--exact','--test-threads=1'],
            run_cases,guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NEW_TESTS_CLEAN')
        observer.phase('binary_binding');images=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('bookmark_rename739-*.d'):
            if path.stat().st_mtime_ns<start:continue
            require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPS_PREBOUND')
            images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
        require(len(images)==1,'ONE_CURRENT_TEST_IMAGE');row['compiled_tests']=images
        observer.phase('build')
        r.harness.run_one('build_atomic_rename_actual8_example740',[r.harness.CARGO,'build',*common,'--example','p09_bookmark_rename740'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPS_PREBOUND')
        observer.phase('readback')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--fixed-eight-atomic-rename-once'],env,row,'actual8_target_name_command_refpath_dirty_atomic_outputs_no_native')
        require(actual is not None and actual['state']=='QUALIFIED740_ATOMIC_TARGET_RENAME_AND_ALL_BOUND_CROSSREFS_ACTUAL8_CACHE_PRESERVED_NOT_REFRESHED'
            and len(actual['cases'])==8 and all(actual[k]is False for k in('Native_started','reference_refresh_or_publication_qualified','P09_complete')),'WHOLE8_ATOMIC_RENAME_NO_REFRESH_OR_GATE')
        row['generated_files']=[]
        for observed,case in zip(actual['cases'],manifest['cases'],strict=True):
            value=observed['receipt']
            require(observed['case_index']==case['case_index']and observed['source']==case['stages']['reopened']['pin']
                and observed['source_unchanged']is True and observed['output_readback_exact']is True
                and value['changed_crossrefs']==value['changed_parts']==1
                and all(value[k]is True for k in('target_and_all_admitted_refs_rebound','command_and_refpath_synchronized','affected_fields_marked_dirty','cache_bytes_preserved_not_refreshed','outside_selected_values_exact'))
                and value['native_refresh_or_execution_publication_revision_authority']is False,'EXACT_ATOMIC_RENAME_AND_PRESERVATION_RECEIPTS')
            require(observed['output']['path']==GENERATED+f"/case-{case['case_index']:02}.hwpx"
                and binary.pin(observed['output']['path'])==observed['output'],'EXACT_CREATED_PRIVATE_OUTPUT')
            row['generated_files'].append(observed['output'])
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED742_ATOMIC_RENAME_RETAINED8_CURRENT_ENTRY2_ACTUAL8_PRIVATE_OUTPUTS_NOT_NATIVE_REFRESH_OR_F11',
            product=actual,retained_prior_successful_conditions=8,current_corrected_lock_conditions=1,current_entry_conditions=2,actual_source_variants=8,all_same_target_command_refpath_dirty_and_name_atomic=True,
            original_sources_unchanged=True,cached_text_preserved_not_refreshed=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-bookmark-rename742-product004-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED742_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
