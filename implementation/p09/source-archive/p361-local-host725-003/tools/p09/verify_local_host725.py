"""Authenticated daemon wire + current provider + configured private workspace, no Native."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture721 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_local_host725.py'
DAEMON='crates/local-companion-daemon/tests/sandbox.rs'
PRODUCT='crates/product-cli/tests/stored_bookmark_insertion628.rs'
HELPER='crates/product-cli/tests/support/bookmark_local_host724.rs'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRIOR='implementation/p09/evidence/p09-361-local-stage721-product001.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-local-host722/'
CHANGED={'Cargo.lock','crates/product-cli/Cargo.toml','crates/local-companion-daemon/src/lib.rs',PRODUCT,
    'crates/product-cli/src/form_product_request/stored_operations/bookmark_insertion710.rs'}
OUTPUT='implementation/p09/evidence/p09-361-local-host725-product003.v1.json'
FAILED2='implementation/p09/evidence/p09-361-local-host725-product002.v1.json'
CORRECTION_ARCHIVE2='implementation/p09/source-archive/p361-local-host725-002/'
CORRECTED2={SELF,HELPER}
FAILED='implementation/p09/evidence/p09-361-local-host725-product001.v1.json'
CORRECTION_ARCHIVE='implementation/p09/source-archive/p361-local-host725-001/'
CORRECTED={SELF,'crates/local-companion-daemon/src/bookmark_preview722.rs',
    'crates/product-cli/src/form_product_request/stored_operations/bookmark_insertion710/local_host723.rs'}
def require(ok,code):
    if not ok:raise ValueError('XREF_LOCAL725_'+code)
def main():
    require(sys.argv[1:]==['--authenticated-local-wire-no-publication-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT_AND_PRIVATE_RUN')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED725_AUTHENTICATED_LOCAL_BOOKMARK_WIRE',steps=[],Native_started=False,
        successful713_707_or_Native249_replayed=False,public_output_revision_adoption_or_execution_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='47f1ac80035ccb8a0341caa46cf53f39711ce480caeee6b3cb631cee7e27db92'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1194
            and prior['phase_resources']['original_sampler_calls']==737,'EXACT721_PRODUCT_AND_RESOURCE_CONTRACT')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'UNCHANGED_PRIOR_CODE_AND_EXACT_CHANGED_SOURCE_ARCHIVES')
        failed=p.codec.unpack(q.json(FAILED),guard.check)
        require(q.snapshots[FAILED]['sha256']=='53bede3a00a5dcff2155a31fa915fcdb8fc530b974637104b5d663e7299c8780'
            and failed['cleanup']is True and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==0
            and len(failed['steps'][0]['tests'])==3,'RETAIN_OLD3_EXECUTION_WITH_INCOMPLETE_WARNING_BUNDLE')
        for pin in failed['source_pins']:
            name=CORRECTION_ARCHIVE+pin['path']if pin['path']in CORRECTED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'FAILED001_SOURCE_AND_EXACT_DEBUG_CORRECTION_ARCHIVES')
        row['retained_prior_daemon_test_execution']=dict(receipt=FAILED,tests=failed['steps'][0]['tests'],
            exit_code=0,whole_prior_bundle_qualified=False,current_replay=False)
        failed2=p.codec.unpack(q.json(FAILED2),guard.check)
        require(q.snapshots[FAILED2]['sha256']=='d191df1a0c9f71968998ee51e511b7628c5c031b4d217c9addfdd1177a3da0c4'
            and failed2['cleanup']is True and len(failed2['steps'])==1 and failed2['steps'][0]['exit_code']==101
            and not failed2['steps'][0]['tests'],'RETAIN_COMPILE_ONLY_FAILURE002_NO_HOST_TESTS_EXECUTED')
        for pin in failed2['source_pins']:
            name=CORRECTION_ARCHIVE2+pin['path']if pin['path']in CORRECTED2 else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'FAILED002_SOURCE_AND_EXACT_TEST_TYPE_CORRECTION_ARCHIVES')
        row['retained_compile_only_failure']=dict(receipt=FAILED2,host_test_cases_executed=0,cleanup=True)
        names=inventory.inputs(guard.check)|includes.test_inputs((DAEMON,PRODUCT),guard)|{SELF,MANIFEST,'tools/p09/product_result_capture721.py'}
        for name in sorted(names):q.pin(name)
        for name in CHANGED:q.pin(ARCHIVE+name)
        manifest=q.json(MANIFEST);require(q.pin(manifest['source']['path'])==manifest['source'],'CURRENT_ACTUAL_SOURCE')
        product={'host724::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(HELPER))}
        old={'session_and_request_shape_fail_before_any_operation','workflow_v2_is_path_free_identity_bound_and_preserves_inputs',
            'protocol_versions_and_workflow_negatives_fail_closed'}
        require(len(product)==8 and all('fn '+name in q.text(DAEMON)for name in old),'EXACT_NEW8_AFFECTED3')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check);binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--message-format=short']
        cli=['--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        env=r.audit.environment();row['compiled_tests']=[]
        def snapshot(capture,expected):
            value=r.snapshot(capture,expected)
            observer.phase('tests'if value.get('observed_harness_started')else'build')
            return value
        for package,target,cases,label in(('hwpx-agent-cli','stored_bookmark_insertion628',product,'host8_authenticated_current_product_private_files'),):
            observer.phase('build');start=time.time_ns()
            args=[r.harness.CARGO,'test',*common,'-p',package]
            if package=='hwpx-agent-cli':args+=cli
            args+=['--test',target,'--',*sorted(cases),'--exact','--test-threads=1']
            r.harness.run_one(label,args,cases,guard,env,row,observe_capture=snapshot)
            require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'SELECTED_TESTS_CLEAN')
            observer.phase('binary_binding');images=[]
            for path in(r.c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<start:continue
                require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPENDENCIES_PREBOUND')
                images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
            require(len(images)==1,'EXACT_CURRENT_TEST_IMAGE');row['compiled_tests']+=images
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED725_AUTHENTICATED_DAEMON_WIRE_CURRENT_PRODUCT_PRIVATE_STAGE8_RETAINED_PRIOR3_NOT_LIVE_INSTALL_OR_PUBLICATION_REVISION',
            new_host_conditions=8,affected_daemon_conditions_current_replayed=0,retained_prior_daemon_execution_count=3,actual681_source_wire_cases=1,Native_process_set_unchanged=True,
            live_installed_daemon_MCP_OS_ACL_tenant_or_F11_qualified=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-local-host725-product003-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED725_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
