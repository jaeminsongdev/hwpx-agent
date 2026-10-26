"""New conditional single-page oracle8 and exact existing16 snapshots, no Native."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture735 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_single_page736.py'
TEST='crates/product-cli/tests/single_page733.rs'
EXAMPLE='crates/product-cli/examples/p09_single_page734.rs'
EXE='target/debug/examples/p09_single_page734.exe'
DEP=EXE[:-4]+'.d'
PRIOR='implementation/p09/evidence/p09-361-bookmark-results730-product001.v1.json'
CAPTURE='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-single-page731/'
CHANGED={'crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets/result726.rs','crates/product-cli/src/reference_validation_product/source_bookmark_results727.rs','crates/product-cli/tests/bookmark_results728.rs'}
OUTPUT='implementation/p09/evidence/p09-361-single-page736-product001.v1.json'
PREP='implementation/p09/evidence/p09-361-single-page732-inspection001.v1.json'
LAYOUT='implementation/p09/evidence/p09-361-single-page732-inputs.v1.json'
def require(ok,code):
    if not ok:raise ValueError('XREF_PAGE736_'+code)
def main():
    require(sys.argv[1:]==['--existing-native-single-page-snapshots-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED736_CONDITIONAL_SINGLE_PAGE_RESULTS',steps=[],Native_started=False,
        passed730_725_721_713_Native249_replayed=False,public_output_revision_or_complete_F11_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='e7553c1ae5f0783a745a5741aabc13a6aee93fd5f280b83851a7ce166bb1384b'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1226
            and prior['phase_resources']['original_sampler_calls']==566,'EXACT730_AND_RESOURCE_CONTRACT')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CODE_PRESERVED_AND_EXACT_SOURCE_ARCHIVES')
        captured=p.codec.unpack(q.json(CAPTURE),guard.check)
        require(q.snapshots[CAPTURE]['sha256']=='63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3'
            and captured['cleanup']is True and captured['fresh_inputs']==captured['final_fresh_hashes']==1054
            and captured['semantic_product_or_render_qualified']is False,'PRIOR_NATIVE_PRODUCER_BOUND_SOURCE_NOT_PREVIOUS_SEMANTIC_ACCEPTANCE')
        prepared=p.codec.unpack(q.json(PREP),guard.check)
        require(q.snapshots[PREP]['sha256']=='6174a25e5cda3df1dde466a0584700ae864327e33c9feef0db4b0469f8f68b1b'
            and prepared['cleanup']is True and prepared['fresh_inputs']==prepared['final_fresh_hashes']==293
            and prepared['Native_started']is False,'EXACT732_EXISTING_PRODUCER_BOUND_PAGE_INVENTORY')
        for pin in prepared['source_pins']:require(q.pin(pin['path'])==pin,'CURRENT_METADATA_TOOL_AND_CAPTURE_INPUTS')
        layout=q.json(LAYOUT);require(q.pin(LAYOUT)==prepared['input_manifest']and len(layout['snapshots'])==8,'EXACT_DECLARED_EIGHT_SNAPSHOTS')
        for v in layout['snapshots']:
            for key in('snapshot','trace','page_image'):require(q.pin(v[key]['path'])==v[key],'FRESH_EXACT_SNAPSHOT_TRACE_IMAGE')
            require(v['case_index']in(1,2,7,8)and v['stage']in('initial','reopened')and v['page_count']==1 and v['page_indices']==[0]
                and v['previously_closed_native_producer_bound']is True,'NATIVE_OBSERVATION_NOT_ARBITRARY_PAGE_COUNT')
        require(len({(v['case_index'],v['stage'])for v in layout['snapshots']})==8,'NO_DUPLICATE_OR_GAP')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,MANIFEST,'tools/p09/product_result_capture735.py'}
        for name in sorted(names):q.pin(name)
        manifest=q.json(MANIFEST)
        require(q.pin(manifest['source']['path'])==manifest['source'],'CURRENT_ORIGINAL_SOURCE')
        for case in manifest['cases']:
            for item in case['stages'].values():require(q.pin(item['pin']['path'])==item['pin'],'CURRENT32_CAPTURED_INPUTS')
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(cases)==8,'EXACT_NEW8')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        def snapshot(capture,expected):
            value=r.snapshot(capture,expected);observer.phase('tests'if value.get('observed_harness_started')else'build');return value
        env=r.audit.environment();observer.phase('build');start=time.time_ns()
        r.harness.run_one('new8_conditional_layout_and_memory_bounds',
            [r.harness.CARGO,'test',*common,'--test','single_page733','--',*sorted(cases),'--exact','--test-threads=1'],
            cases,guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NEW_TESTS_CLEAN')
        observer.phase('binary_binding');images=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('single_page733-*.d'):
            if path.stat().st_mtime_ns<start:continue
            require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPS_PREBOUND')
            images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
        require(len(images)==1,'ONE_CURRENT_TEST_IMAGE');row['compiled_tests']=images
        observer.phase('build')
        r.harness.run_one('build_single_page_snapshot_reader734',[r.harness.CARGO,'build',*common,'--example','p09_single_page734'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPS_PREBOUND')
        observer.phase('readback')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--existing16-single-page-observations-only'],env,row,'actual16_new_snapshot_geometry_checks_no_native_replay')
        require(actual is not None and actual['state']=='QUALIFIED734_EXISTING_RENDER_BOUND_SINGLE_PAGE8_SAVED4_CANDIDATE4_UNRESOLVED_NOT_GENERAL_FLOW'
            and len(actual['observations'])==16 and(actual['conditional_snapshot_matches'],actual['saved_or_candidate_extent_missing'])==(8,8)
            and all(actual[k]is False for k in('Native_started','API_attests_native_or_general_flow','publication_or_revision_authority','P09_complete')),'WHOLE16_CONDITIONAL_SCOPE_NOT_GENERAL_FLOW')
        expected=[(i,manifest['cases'][i],stage)for i in(0,1,6,7)for stage in('candidate','initial','saved','reopened')]
        for observed,(index,case,stage)in zip(actual['observations'],expected,strict=True):
            require(observed['case_index']==case['case_index']and observed['stage']==stage and observed['source']==case['stages'][stage]['pin']
                and observed['API_attests_native_or_general_flow']is False,'EXACT_RECORDED_SNAPSHOT_SCOPE')
            if stage in('initial','reopened'):
                captured=next(v for v in layout['snapshots']if v['case_index']==index+1 and v['stage']==stage)
                require(observed['status']=='matches_under_observation'and observed['capture']==captured and len(observed['assessment_sha256'])==64
                    and type(observed['target_line_y'])is int and type(observed['reference_line_y'])is int
                    and observed['target_line_y']<observed['reference_line_y'],'MATCH_UNDER_EXACT_CAPTURE_EXTENT_AND_INDEPENDENT_GEOMETRY')
            else:
                require(observed['status']=='missing_snapshot_extent_kept_unresolved'and observed['layout_transfer_not_admitted']is True
                    and observed['different_payload_parts_from_initial']==(['Contents/content.hpf']if stage=='saved'else[]),'DO_NOT_NORMALIZE_AWAY_CHANGED_PACKAGE_SPINE_OR_INFER_MISSING_EXTENT')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED736_EXISTING_NATIVE_EXTENT_BOUND_SINGLE_PAGE8_SAVED4_CANDIDATE4_MISSING_NOT_GENERAL_FLOW_OR_F11',
            product=actual,new_conditions=8,conditional_render_bound_snapshot_matches=8,saved_extent_missing=4,candidate_extent_missing=4,
            native_capture_provenance_receipt=CAPTURE,Native_process_set_unchanged=True,general_document_flow_qualified=False,
            source_preparation_batch_result_memory_bound_verified=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-single-page736-product001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED736_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
