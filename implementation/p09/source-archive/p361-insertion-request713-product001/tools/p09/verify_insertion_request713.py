"""Strict owned/common insertion request; new10, directly affected old3, actual8. No Native."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import product_result_capture713 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_insertion_request713.py'
TEST='crates/product-cli/tests/stored_bookmark_insertion628.rs'
CORE='crates/product-cli/tests/support/bookmark_insertion_request711.rs'
OLD='crates/product-cli/tests/stored_bookmark_command_output622.rs'
EXAMPLE='crates/product-cli/examples/p09_insertion_request712.rs'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRIOR='implementation/p09/evidence/p09-361-insertion-compiler709-product005.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-insertion-request710/'
CHANGED={TEST,'crates/product-cli/src/form_product_request/stored_operations.rs',
    'crates/product-cli/src/form_product_request/stored_operations/request.rs'}
OUTPUT='implementation/p09/evidence/p09-361-insertion-request713-product001.v1.json'
SPOOL='implementation/p09/evidence/private/p09-361-insertion-request713-product001-forensic'
EXE='target/debug/examples/p09_insertion_request712.exe'
DEP=EXE[:-4]+'.d'
def require(ok,code):
    if not ok:raise ValueError('XREF_REQUEST713_'+code)
def main():
    require(sys.argv[1:]==['--new-owned-request-common-dispatch-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=None;begin=time.monotonic()
    row=dict(state='FAILED713_INSERTION_PRODUCT_REQUEST',steps=[],Native_started=False,official249_or_prior_compiler15_replayed=False,
        registry_execution_durable_result_or_F11_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='819f6e69d09d772bbbba4ee1a8505868c7b64f4f9171012f52b72d6f6f7870f0'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1104,'EXACT709_ORIGINAL_COMPILER_PROOF')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CHANGED_SOURCES_ARCHIVED_AND_OTHER_CODE_INPUTS_UNCHANGED')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,OLD,EXAMPLE),guard)|{SELF,CORE,MANIFEST,'tools/p09/product_result_capture713.py'}
        for name in sorted(names):q.pin(name)
        for name in CHANGED:q.pin(ARCHIVE+name)
        manifest=q.json(MANIFEST);require(q.pin(manifest['source']['path'])==manifest['source'],'EXACT_ACTUAL_SOURCE')
        fresh={'request711::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(CORE))}
        old={'request624::'+name for name in(
            'standalone_and_common_dispatch_match_original_compiler_bytes_receipts_and_hash_only_diagnostics',
            'strict_shapes_unknown_duplicate_hash_boolean_display_and_size_errors_reject_before_source_reads',
            'old_https_no_repository_denial_and_unknown_schema_still_precede_head_access')}
        require(len(fresh)==10 and all('fn '+name.split('::')[1]in q.text('crates/product-cli/tests/support/stored_bookmark_request624.rs')for name in old),'EXACT_NEW10_AFFECTED_COMMON3')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check);binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        env=r.audit.environment();common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        row['compiled_tests']=[]
        for target,cases,label in(('stored_bookmark_insertion628',fresh,'new10_owned_strict_insertion_common_and_observer'),
            ('stored_bookmark_command_output622',old,'affected3_existing_common_dispatch_shapes_and_https_denial')):
            start=time.time_ns()
            r.harness.run_one(label,[r.harness.CARGO,'test',*common,'--test',target,'--',*sorted(cases),'--exact','--test-threads=1'],
                cases,guard,env,row,observe_capture=r.snapshot)
            require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'SELECTED_TESTS_CLEAN')
            images=[]
            for path in(r.c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<start:continue
                require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPENDENCIES_PREBOUND')
                images.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
            require(len(images)==1,'EXACT_CURRENT_TEST_IMAGE');row['compiled_tests']+=images
        r.harness.run_one('build_actual8_owned_common_request_reader712',[r.harness.CARGO,'build',*common,'--example','p09_insertion_request712'],
            set(),guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)];require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPENDENCIES_PREBOUND')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--actual-eight-owned-request-readonly'],env,row,'actual8_owned_strict_common_product_request')
        require(actual is not None and actual['state']=='QUALIFIED711_STRICT_OWNED_COMMON_INSERTION_ACTUAL8_NOT_EXECUTION_OR_DURABLE_BACKEND'
            and len(actual['cases'])==8 and actual['source']==manifest['source']
            and all(actual[k]is False for k in('Native_started','head_changed','result_ingested','P09_complete')),'WHOLE8_REQUEST_COMPILER_NOT_EXECUTION')
        for observed,case in zip(actual['cases'],manifest['cases'],strict=True):
            receipt=observed['receipt'];cr=receipt['compiled']
            require(observed['case_index']==case['case_index']and observed['output_sha256']==case['stages']['candidate']['pin']['sha256']
                and observed['source_and_head_unchanged']is True and observed['route_qualified']is False
                and receipt['request_schema']=='hwpx-agent.product-bookmark-insertion-request/v1'
                and receipt['idempotency_key_claimed']is False and receipt['execution_or_publication_authority']is False
                and cr['capability_id']=='ref.crossref_insert'and cr['inserted_fields']==1,'STRICT_OWNED_REQUEST_NOT_CLAIM_OR_DURABLE_RESULT')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED713_STRICT_OWNED_INSERTION_COMMON_PRODUCT_NEW10_AFFECTED3_ACTUAL8_NOT_EXECUTION_OR_F11',
            product=actual,new_conditions=10,directly_affected_common_conditions=3,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,SPOOL,row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','compiled_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED713_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
