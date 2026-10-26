"""New original insertion compiler, affected8 source guards and actual8 readonly; no Native."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import product_result_capture709 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_insertion_compiler709.py'
TEST='crates/product-cli/tests/stored_bookmark_insertion628.rs'
CORE='crates/product-cli/tests/support/bookmark_insertion_compiler708.rs'
PARENT='crates/product-cli/src/form_stored_provider/actual_import/bookmark_insertion_output.rs'
EXAMPLE='crates/product-cli/examples/p09_insertion_compiler708.rs'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRIOR='implementation/p09/evidence/p09-361-conditional-headings706-product002.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-insertion-compiler707/'
OUTPUT='implementation/p09/evidence/p09-361-insertion-compiler709-product002.v1.json'
EXE='target/debug/examples/p09_insertion_compiler708.exe'
DEP=EXE[:-4]+'.d'
def require(ok,code):
    if not ok:raise ValueError('XREF_INSERT709_'+code)
def main():
    require(sys.argv[1:]==['--new-compiler-and-affected-source-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=None;begin=time.monotonic()
    row=dict(state='FAILED709_INSERTION_COMPILER',steps=[],Native_started=False,official249_or_unrelated_passed_conditions_replayed=False,
        registry_execution_durable_result_or_F11_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='9da384e0e654e083f73b044139ebb64ba4cd1aa44d23d56e462d738f4fb6d1d4'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1090,'EXACT706_PRIOR_QUALIFIED_SCOPE')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in(PARENT,TEST)else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_EXACT_ARCHIVED_CHANGED_INPUTS_OTHER_SOURCES_PRESERVED')
        failed_path='implementation/p09/evidence/p09-361-insertion-compiler709-product001.v1.json'
        failed=p.codec.unpack(q.json(failed_path),guard.check)
        require(q.snapshots[failed_path]['sha256']=='c74d8c270be0f7610b638d336488db2b0147a72c900d7263ff3c2afec45e58f1'
            and failed['cleanup']is True and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101,'PRESERVED_INITIAL_TEST_FAILURE')
        require(len(failed['steps'][0]['tests'])==15 and sum(v=='ok'for _,v in failed['steps'][0]['tests'])==14
            and failed['steps'][0]['tests'][8]==['compiler708::first_insertion_plan_binds_original_plain_run_owner_target_revision_output_and_receipt','FAILED'],'EXACT14_OBSERVED_AND_ONE_FAILED_NOT_NATIVE')
        for pin in failed['source_pins']:
            name='implementation/p09/source-archive/p361-insertion-compiler709-product001/'+pin['path']if pin['path']in(CORE,SELF)else pin['path']
            bound=q.pin(name);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'INITIAL_CODE_ARCHIVED_UNCHANGED_OTHER_SOURCES_INPUTS')
        row['retained14_observed_tests_not_replayed']=failed['steps'][0]['tests'][:8]+failed['steps'][0]['tests'][9:]
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,EXAMPLE),guard)|{SELF,CORE,MANIFEST,'tools/p09/product_result_capture709.py'}
        for name in sorted(names):q.pin(name)
        for name in(PARENT,TEST):q.pin(ARCHIVE+name)
        manifest=q.json(MANIFEST);require(q.pin(manifest['source']['path'])==manifest['source'],'ACTUAL_FIXED_SOURCE')
        q.pin('implementation/p09/evidence/private/p09-361-block-bookmark670-source-document001/created.hwpx')
        fresh={'compiler708::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(CORE))}
        old=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(fresh)==7 and len(old)==8,'NEW7_AFFECTED8_ONLY')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check);binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        env=r.audit.environment();common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        selected={'compiler708::first_insertion_plan_binds_original_plain_run_owner_target_revision_output_and_receipt'}
        start=time.time_ns()
        r.harness.run_one('corrected_independent_owner_oracle_one_failed_case_only',
            [r.harness.CARGO,'test',*common,'--test','stored_bookmark_insertion628','--',*sorted(selected),'--exact','--test-threads=1'],
            selected,guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'SELECTED_TESTS_CLEAN')
        images=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('stored_bookmark_insertion628-*.d'):
            if path.stat().st_mtime_ns<start:continue
            require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPENDENCIES_PREBOUND')
            images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
        require(len(images)==1,'EXACT_CURRENT_TEST_IMAGE');row['compiled_tests']=images
        r.harness.run_one('build_actual_source8_compiler_reader708',[r.harness.CARGO,'build',*common,'--example','p09_insertion_compiler708'],
            set(),guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)];require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPENDENCIES_PREBOUND')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--actual-eight-compiler-readonly'],env,row,'actual8_current_source_original_compiler')
        require(actual is not None and actual['state']=='QUALIFIED708_ACTUAL_BLOCK_EIGHT_ORIGINAL_COMPILER_CURRENT_STORED_SOURCE_NOT_EXECUTION'
            and len(actual['cases'])==8 and actual['source']==manifest['source']
            and all(actual[k]is False for k in('Native_started','head_changed','result_ingested','P09_complete')),'WHOLE8_REAL_SOURCE_COMPILER_NOT_EXECUTION')
        for observed,case in zip(actual['cases'],manifest['cases'],strict=True):
            cr=observed['compiled_receipt']
            require(observed['case_index']==case['case_index']and observed['output_sha256']==case['stages']['candidate']['pin']['sha256']
                and observed['source_and_output_exact']is True and observed['plan_reopened']is True and observed['route_qualified']is False
                and cr['capability_id']=='ref.crossref_insert'and cr['inserted_fields']==1
                and cr['display_text_preserved_not_evaluated_or_refreshed']is True and cr['execution_or_publication_authority']is False,
                'EXACT_COMPILED_INSERTION_BINDINGS_NO_AUTHORITY')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED709_ORIGINAL_BOOKMARK_INSERTION_COMPILER_NEW7_AFFECTED8_ACTUAL8_NOT_EXECUTION_OR_F11',
            product=actual,new_conditions=7,affected_source_conditions=8,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-insertion-compiler709-product002-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','compiled_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED709_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
