"""Private generated preview + current product callback: core6/product7/old3/actual8."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture721 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_local_stage721.py'
CORE='crates/local-workflow/tests/generated_preview717.rs'
PRODUCT='crates/product-cli/tests/stored_bookmark_insertion628.rs'
HELPER='crates/product-cli/tests/support/bookmark_local_stage719.rs'
OLD='crates/local-workflow/tests/workflow.rs'
EXAMPLE='crates/product-cli/examples/p09_local_stage720.rs'
EXE='target/debug/examples/p09_local_stage720.exe'
DEP=EXE[:-4]+'.d'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRIOR='implementation/p09/evidence/p09-361-insertion-request713-product002.v1.json'
TOOL='implementation/p09/evidence/p09-361-resource-bundle715-audit003.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-local-generated716/'
CHANGED={'Cargo.lock','crates/product-cli/Cargo.toml','crates/local-workflow/src/lib.rs',PRODUCT,
    'crates/product-cli/src/form_product_request/stored_operations/bookmark_insertion710.rs'}
OUTPUT='implementation/p09/evidence/p09-361-local-stage721-product001.v1.json'
GENERATED='implementation/p09/evidence/private/p09-361-local-stage720-generated001'
def require(ok,code):
    if not ok:raise ValueError('XREF_LOCAL721_'+code)
def main():
    require(sys.argv[1:]==['--private-current-source-stage-no-publication-native']and not(r.c.ROOT/OUTPUT).exists()
        and not(r.c.ROOT/GENERATED).exists(),'MODE_NEW_OUTPUT_AND_PRIVATE_RUN')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic()
    row=dict(state='FAILED721_CURRENT_PRIVATE_GENERATED_STAGE',steps=[],Native_started=False,
        successful713_707_or_Native249_replayed=False,public_output_revision_adoption_or_execution_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding')
        q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check);tool=p.codec.unpack(q.json(TOOL),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='862bba9d45b143b6de6f8bd52a2d85aa045606fce6262f8b0266d287f1cb0892'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1119,'EXACT713_PRODUCT_SCOPE')
        require(q.snapshots[TOOL]['sha256']=='ce7f14dd440342af0299ef50d344f7079d8376b143b83f5dda7e2714505d71fe'
            and tool['cleanup']is True and tool['phase_resources']['original_sampler_calls']==74,'EXACT715_PHASE_RESOURCE_CONTRACT')
        for baseline in(prior,tool):
            for pin in baseline['source_pins']:
                name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
                require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'UNCHANGED_PRIOR_CODE_AND_EXACT_CHANGED_SOURCE_ARCHIVES')
        names=inventory.inputs(guard.check)|includes.test_inputs((CORE,PRODUCT,OLD,EXAMPLE),guard)|{SELF,MANIFEST,'tools/p09/product_result_capture721.py'}
        for name in sorted(names):q.pin(name)
        for name in CHANGED:q.pin(ARCHIVE+name)
        manifest=q.json(MANIFEST);require(q.pin(manifest['source']['path'])==manifest['source'],'CURRENT_ACTUAL_SOURCE')
        fresh=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(CORE)))
        product={'stage719::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(HELPER))}
        old={'materialize_diff_publish_and_commit_plan_are_identity_bound','slots_and_outputs_never_overwrite','traversal_absolute_reserved_and_wrong_namespace_fail_closed'}
        require((len(fresh),len(product))==(6,7)and all('fn '+name in q.text(OLD)for name in old),'EXACT_NEW6_PRODUCT7_OLD3')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check);binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        common=['--offline','--locked','-j','1','--message-format=short']
        cli=['--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        env=r.audit.environment();row['compiled_tests']=[]
        def snapshot(capture,expected):
            value=r.snapshot(capture,expected)
            observer.phase('tests'if value.get('observed_harness_started')else'build')
            return value
        for package,target,cases,label in(('local-workflow','generated_preview717',fresh,'core6_private_generated_files'),
            ('local-workflow','workflow',old,'old3_materialize_publish_no_overwrite_paths'),
            ('hwpx-agent-cli','stored_bookmark_insertion628',product,'product7_current_source_pre_post_stage_denials')):
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
        observer.phase('build')
        r.harness.run_one('build_private_actual8_local_stage720',[r.harness.CARGO,'build',*common,'-p','hwpx-agent-cli',*cli,'--example','p09_local_stage720'],
            set(),guard,env,row,observe_capture=snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPENDENCIES_PREBOUND')
        observer.phase('readback')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--fixed-eight-private-stage-once'],env,row,'actual8_authenticated_private_disk_stage_and_reopen')
        require(actual is not None and actual['state']=='QUALIFIED719_ACTUAL8_CURRENT_SOURCE_PRIVATE_FILES_STAGED_REOPENED_NOT_PUBLICATION_OR_REVISION'
            and len(actual['cases'])==8 and actual['source']==manifest['source']
            and all(actual[k]is False for k in('Native_started','result_ingested','revision_adopted','P09_complete')),'WHOLE8_PRIVATE_DISK_EFFECT_NOT_PUBLICATION')
        row['generated_files']=[]
        for observed,case in zip(actual['cases'],manifest['cases'],strict=True):
            receipt=observed['receipt'];index=case['case_index'];directory=r.c.ROOT/GENERATED/f'c{index:02}'
            require(observed['case_index']==index and all(observed[k]is True for k in('persisted_bytes_exact','workspace_reopened','existing_public_publish_cannot_read_preview','source_and_head_unchanged'))
                and receipt['publication_execution_or_revision_adoption_authority']is False and receipt['private_preview_not_publish_candidate']is True,'QUALIFIED_PRIVATE_STAGING_SCOPE_ONLY')
            for relative,expected in(('input/source.hwpx',manifest['source']['sha256']),('.hwpx-agent/work/op_01/source.hwpx',manifest['source']['sha256']),
                ('.hwpx-agent/work/op_01/generated-preview.hwpx',case['stages']['candidate']['pin']['sha256'])):
                pin=binary.pin((directory/relative).relative_to(r.c.ROOT).as_posix());require(pin['sha256']==expected,'EXACT_GENERATED_DISK_IDENTITY');row['generated_files'].append(pin)
            require(not any((directory/'output').iterdir())and not(directory/'.hwpx-agent/work/op_01/candidate.hwpx').exists(),'NO_PUBLICATION_CANDIDATE_OR_PUBLIC_OUTPUT')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED721_CURRENT_PRODUCT_PRIVATE_GENERATED_FILES_CORE6_PRODUCT7_OLD3_ACTUAL8_NOT_PUBLICATION_OR_REVISION',
            product=actual,new_file_conditions=6,new_product_conditions=7,affected_workflow_conditions=3,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-local-stage721-product001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'resource_samples':len(guard.samples),'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED721_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
