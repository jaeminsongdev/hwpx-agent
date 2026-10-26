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
OUTPUT='implementation/p09/evidence/p09-361-local-host725-product001.v1.json'
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
        for package,target,cases,label in(('local-companion-daemon','sandbox',old,'old3_daemon_auth_protocol_and_file_workflow'),
            ('hwpx-agent-cli','stored_bookmark_insertion628',product,'host8_authenticated_current_product_private_files')):
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
        row.update(state='QUALIFIED725_AUTHENTICATED_DAEMON_WIRE_CURRENT_PRODUCT_PRIVATE_STAGE8_AFFECTED3_NOT_LIVE_INSTALL_OR_PUBLICATION_REVISION',
            new_host_conditions=8,affected_daemon_conditions=3,actual681_source_wire_cases=1,Native_process_set_unchanged=True,
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
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-local-host725-product001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED725_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
