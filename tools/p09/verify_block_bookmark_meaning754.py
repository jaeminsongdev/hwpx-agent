"""Common BOOKMARK meaning migration: new9, affected legacy4, actual40; no Native."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture753 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_bookmark_meaning754.py'
TEST='crates/product-cli/tests/block_bookmark_meaning751.rs'
EXAMPLE='crates/product-cli/examples/p09_block_bookmark_meaning752.rs'
EXE='target/debug/examples/p09_block_bookmark_meaning752.exe'
DEP=EXE[:-4]+'.d'
PRIOR='implementation/p09/evidence/p09-361-bookmark-navigation748-product003.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
RENAMED='implementation/p09/evidence/p09-361-bookmark-navigation743-inputs.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-block-bookmark-meaning749/'
CHANGED={'crates/hwpx-package/src/document_import/fields/bookmark_crossref.rs',
    'crates/hwpx-package/src/document_import/fields/semantics.rs','crates/hwpx-package/src/document_import/fields/semantics/source_index.rs',
    'crates/product-cli/src/reference_validation_product/source_field_semantics.rs','crates/product-cli/src/reference_validation_product/source.rs'}
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-meaning754-product003.v1.json'
FAILED2='implementation/p09/evidence/p09-361-block-bookmark-meaning754-product002.v1.json'
CORRECTION2='implementation/p09/source-archive/p361-block-bookmark-meaning754-002/'
FAILED='implementation/p09/evidence/p09-361-block-bookmark-meaning754-product001.v1.json'
CORRECTION='implementation/p09/source-archive/p361-block-bookmark-meaning754-001/'

def require(ok,code):
    if not ok:raise ValueError('XREF_BLOCKMEANING754_'+code)

def main():
    require(sys.argv[1:]==['--common-block-meaning-migration-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED754_COMMON_BLOCK_BOOKMARK_MEANING',steps=[],Native_started=False,
        passed748_742_736_730_725_721_713_Native249_replayed=False,native_cursor_or_complete_F11_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='20492ea412646ab337ebec810ff07dc2ac8269a147451798d42ed59090c7d008'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1282
            and prior['phase_resources']['original_sampler_calls']==510 and prior['artifact_final_fresh_hashes']==4,'EXACT748_AND_RESOURCE_CONTRACT')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CODE_PRESERVED_AND_EXACT_MIGRATION_ARCHIVES')
        failed=p.codec.unpack(q.json(FAILED),guard.check);tests=failed['steps'][0]['tests']
        require(q.snapshots[FAILED]['sha256']=='a9fb0e84212c094a418dd9ff1964636d76785d3b90a09ee50b523d056665312b'
            and failed['cleanup']is True and failed['steps'][0]['exit_code']==0 and len(tests)==13 and all(v=='ok'for _,v in tests)
            and len(failed['steps'][0]['bounded_output_observation']['safe_warning_locations'])==2
            and not failed['steps'][0]['bounded_output_observation']['rust_error_codes'],'RETAIN13_OBSERVATIONS_AND_NAMING_WARNINGS_NOT_WHOLE_BUNDLE')
        for pin in failed['source_pins']:
            name=CORRECTION+pin['path']if pin['path']in(SELF,TEST)else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_WARNED_BUILD_INPUTS_AND_TEST_ARCHIVES')
        previous=q.text(CORRECTION+TEST)
        for old,new in(('source_and_field_API_versions_migrate_only_admitted_block_documents','source_and_field_api_versions_migrate_only_admitted_block_documents'),
            ('unknown_bookmark_prop_and_DATE_keep_legacy_profiles_and_explicit_unsupported','unknown_bookmark_prop_and_date_keep_legacy_profiles_and_explicit_unsupported')):
            require(previous.count('fn '+old+'(')==1,'ONE_EXPECTED_NAME');previous=previous.replace('fn '+old+'(','fn '+new+'(')
        inclusion='#[path="reference_field_semantics_product.rs"]mod legacy;'
        require(previous.count(inclusion)==1,'ONE_LEGACY_TEST_MODULE')
        previous=previous.replace(inclusion,'#[cfg(test)]'+inclusion)
        require(q.text(TEST)==previous,'TEST_BODIES_UNCHANGED_TWO_FN_NAMES_AND_TEST_ONLY_MODULE_GUARD')
        row['retained_thirteen_execution_observations']=dict(receipt=FAILED,tests=tests,current_replayed=False,
            whole_prior_bundle_qualified=False,source_final_hashes_in_prior_bundle=failed['final_fresh_hashes'])
        failed2=p.codec.unpack(q.json(FAILED2),guard.check)
        require(q.snapshots[FAILED2]['sha256']=='04334d002abd319814e298d1c72bf441cf7486544c41b569ada8b2dcc7d396ac'
            and failed2['cleanup']is True and len(failed2['steps'])==2 and failed2['steps'][0]['exit_code']==0
            and not failed2['steps'][0]['tests']and not failed2['steps'][0]['diagnostics']
            and failed2['steps'][1]['exit_code']==101,'EXACT_CLEAN_TEST_BUILD_AND_GENERAL_BUILD_ENV_MACRO_FAILURE')
        for pin in failed2['source_pins']:
            name=CORRECTION2+pin['path']if pin['path']in(SELF,TEST)else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_FAILED002_INPUTS_AND_TEST_MODULE_GUARD_ARCHIVES')
        require(q.text(TEST)==q.text(CORRECTION2+TEST).replace(inclusion,'#[cfg(test)]'+inclusion),'ONLY_GENERAL_EXAMPLE_LEGACY_TEST_MODULE_GUARD_CHANGED')
        row['retained_general_build_failure']=dict(receipt=FAILED2,test_image_bound=True,tests_replayed=False,general_example_executed=False)
        parser='crates/hwpx-package/src/document_import/fields/bookmark_crossref.rs'
        start='        let config = limits.config();';end='    /// Refuses excessive output without truncating or returning private strings.'
        def body(text):return text.split(start,1)[1].split(end,1)[0]
        require(body(q.text(ARCHIVE+parser))==body(q.text(parser)).replace('Ok((result,blocks))','Ok(result)'),
            'STRICT_BOOKMARK_COMMAND_PARSER_BODY_UNCHANGED_RETAIN_INVENTORY_ONLY')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,MANIFEST,RENAMED,'tools/p09/product_result_capture753.py'}
        for name in sorted(names):q.pin(name)
        require('.semantic_value('not in q.text(TEST)and '.source_text('not in q.text(TEST),'PUBLIC_FIXTURE_TOKEN_API_ONLY')
        manifest=q.json(MANIFEST);renamed=q.json(RENAMED)
        require(len(manifest['cases'])==len(renamed['cases'])==8,'FIXED_EIGHT_PROFILES')
        require(q.pin(manifest['source']['path'])==manifest['source'],'ORIGINAL_BOOKMARK_SOURCE')
        for c,n in zip(manifest['cases'],renamed['cases'],strict=True):
            require(c['case_index']==n['case_index']and c['stages']['reopened']['pin']==n['original'],'EXACT_ORIGINAL_RENAMED_CASE_RELATION')
            for v in c['stages'].values():require(q.pin(v['pin']['path'])==v['pin'],'CURRENT32')
            require(q.pin(n['renamed']['path'])==n['renamed'],'CURRENT_RENAMED8')
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));require(len(cases)==9,'EXACT_NEW9')
        affected={'legacy::actual_captured_field_meanings_join_exact_source_without_uri_or_native_approval',
            'legacy::selection_binds_document_package_and_meaning_and_main_v14_includes_it',
            'legacy::output_exact_bound_unknown_meanings_and_field_coverage_are_not_success_defaults',
            'legacy::actual_sixteen_table_sources_keep_formula_asts_and_unverified_caches'}
        expected=cases|affected
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        def snapshot(capture,expected):
            value=r.snapshot(capture,expected);observer.phase('tests'if value.get('observed_harness_started')else'build');return value
        env=r.audit.environment();observer.phase('build');start_ns=time.time_ns()
        require(len(expected)==13,'RETAINED9_PLUS_AFFECTED4')
        r.harness.run_one('current_clean_test_build_only_retained13_not_replayed',
            [r.harness.CARGO,'test',*common,'--test','block_bookmark_meaning751','--no-run'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NEW_AND_IMPACT_TESTS_CLEAN')
        observer.phase('binary_binding');images=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('block_bookmark_meaning751-*.d'):
            if path.stat().st_mtime_ns<start_ns:continue
            require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPS_PREBOUND')
            images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
        require(len(images)==1,'ONE_CURRENT_TEST_IMAGE');row['compiled_tests']=images
        observer.phase('build')
        r.harness.run_one('build_common_block_meaning40_example752',[r.harness.CARGO,'build',*common,'--example','p09_block_bookmark_meaning752'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPS_PREBOUND')
        observer.phase('readback')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--current-block-meanings-forty-no-native'],env,row,'actual40_new_meaning_profiles_common_graph_and_source_no_native')
        require(actual is not None and actual['state']=='QUALIFIED752_BLOCK_BOOKMARK_MEANINGS_EXISTING40_COMMON_API_GRAPH_AND_SOURCE_STILL_INCOMPLETE'
            and len(actual['observations'])==40 and actual['block_meanings_per_source']==8 and actual['unsupported_per_source']==0
            and actual['crossrefs_per_source']==1 and actual['all_graph_round_trips_whole_reconstructions_and_independent_API_parity']is True
            and actual['main_status']=='incomplete'
            and all(actual[k]is False for k in('Native_started','old_Native_or_249_tests_replayed','main_validation_report_present','full_F11_or_P09_qualified')),'WHOLE40_TYPED_BLOCK_MEANING_NOT_NATIVE_OR_GATE')
        observations=[(c,n,stage)for c,n in zip(manifest['cases'],renamed['cases'],strict=True)for stage in('candidate','initial','saved','reopened','renamed')]
        for seen,(c,n,stage)in zip(actual['observations'],observations,strict=True):
            pin=n['renamed']if stage=='renamed'else c['stages'][stage]['pin']
            require(seen['case_index']==c['case_index']and seen['stage']==stage and seen['source']==pin and seen['source_unchanged']is True
                and seen['main_schema']==('hwpx-agent.product.reference-source-assessment/v18'if stage=='candidate'else'hwpx-agent.product.reference-source-assessment/v17')
                and re.fullmatch('[a-f0-9]{64}',seen['readback_sha256'])is not None,'CURRENT40_IDENTITY_PROFILE_AND_READBACK_DIGEST')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED754_COMMON_BLOCK_BOOKMARK_MEANING_RETAINED13_CLEAN_BUILD_EXISTING40_STILL_INCOMPLETE_NOT_NATIVE_OR_F11',
            product=actual,retained_new_test_observations=9,retained_directly_affected_legacy_test_observations=4,current_test_build_only=True,
            current_tests_executed=0,actual_source_variants=40,typed_block_meanings_per_document=8,
            unsupported_meanings_per_document=0,original_sources_unchanged=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-meaning754-product003-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED754_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
