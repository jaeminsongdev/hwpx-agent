"""New source result oracle8 + existing captured32, no Native or passed-suite replay."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture730 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_bookmark_results730.py'
TEST='crates/product-cli/tests/bookmark_results728.rs'
EXAMPLE='crates/product-cli/examples/p09_bookmark_results729.rs'
EXE='target/debug/examples/p09_bookmark_results729.exe'
DEP=EXE[:-4]+'.d'
PRIOR='implementation/p09/evidence/p09-361-local-host725-product004.v1.json'
CAPTURE='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-results726/'
CHANGED={'crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets.rs','crates/product-cli/src/reference_validation_product.rs'}
OUTPUT='implementation/p09/evidence/p09-361-bookmark-results730-product001.v1.json'
def require(ok,code):
    if not ok:raise ValueError('XREF_RESULT730_'+code)
def main():
    require(sys.argv[1:]==['--source-text-oracles-existing32-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED730_SOURCE_DERIVED_BOOKMARK_RESULTS',steps=[],Native_started=False,
        passed725_721_713_Native249_replayed=False,public_output_revision_or_complete_F11_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='b2bf632ecb739eb8e8add2f9ade9ec6551e873c9cb199e4f34caa991d3137e6e'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1217
            and prior['phase_resources']['original_sampler_calls']==569,'EXACT725_AND_RESOURCE_CONTRACT')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CODE_PRESERVED_AND_EXACT_SOURCE_ARCHIVES')
        captured=p.codec.unpack(q.json(CAPTURE),guard.check)
        require(q.snapshots[CAPTURE]['sha256']=='63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3'
            and captured['cleanup']is True and captured['fresh_inputs']==captured['final_fresh_hashes']==1054
            and captured['semantic_product_or_render_qualified']is False,'PRIOR_NATIVE_PRODUCER_BOUND_SOURCE_NOT_PREVIOUS_SEMANTIC_ACCEPTANCE')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,MANIFEST,'tools/p09/product_result_capture730.py'}
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
        r.harness.run_one('new8_source_result_oracle_and_fail_closed_negatives',
            [r.harness.CARGO,'test',*common,'--test','bookmark_results728','--',*sorted(cases),'--exact','--test-threads=1'],
            cases,guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NEW_TESTS_CLEAN')
        observer.phase('binary_binding');images=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('bookmark_results728-*.d'):
            if path.stat().st_mtime_ns<start:continue
            require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPS_PREBOUND')
            images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
        require(len(images)==1,'ONE_CURRENT_TEST_IMAGE');row['compiled_tests']=images
        observer.phase('build')
        r.harness.run_one('build_new_result_oracle_example729',[r.harness.CARGO,'build',*common,'--example','p09_bookmark_results729'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPS_PREBOUND')
        observer.phase('readback')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--existing32-source-result-oracles-only'],env,row,'actual32_new_source_derived_result_semantics_no_native_replay')
        require(actual is not None and actual['state']=='QUALIFIED729_SOURCE_DERIVED_NAME_CONTENT_NATIVE_CACHE12_CANDIDATE_MISMATCH4_FLOW_UNRESOLVED16'
            and len(actual['observations'])==32 and(actual['source_text_matches'],actual['candidate_text_mismatches'],actual['needs_document_flow'])==(12,4,16)
            and all(actual[k]is False for k in('Native_started','Native_producer_attested_by_this_API','publication_or_revision_authority','P09_complete')),'WHOLE32_RESULT_SCOPE_NO_PROMOTION')
        expected=[(i,case,stage)for i,case in enumerate(manifest['cases'])for stage in('candidate','initial','saved','reopened')]
        for observed,(index,case,stage)in zip(actual['observations'],expected,strict=True):
            wanted='needs_document_flow'if index//2 in(0,3)else'source_text_mismatch'if stage=='candidate'else'source_text_matches'
            require(observed['case_index']==case['case_index']and observed['stage']==stage and observed['source']==case['stages'][stage]['pin']
                and observed['status']==wanted and observed['source_target_preserved']is True and observed['native_or_layout_authority']is False
                and len(observed['assessment_sha256'])==64,'SOURCE_EXPECTATION_AND_EXACT_CAPTURE_SCOPE')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED730_PRODUCT_SOURCE_ORACLE8_EXISTING_NATIVE_CACHE12_CANDIDATE_MISMATCH4_FLOW_UNRESOLVED16_NOT_FULL_F11',
            product=actual,new_conditions=8,source_derived_native_cache_text_matches=12,candidate_text_mismatches=4,
            document_flow_unresolved=16,native_capture_provenance_receipt=CAPTURE,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-bookmark-results730-product001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED730_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
