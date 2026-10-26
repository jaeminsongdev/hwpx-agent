"""Field API/graph integration only; preserve rejected full Source assessment."""
import json,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_source_field_semantics as dep
import product_result_capture700 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_field_apis700.py'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark696-product003.v1.json'
TEST_PROOF='implementation/p09/evidence/p09-361-block-bookmark696-product002.v1.json'
EXAMPLE='crates/product-cli/examples/p09_block_bookmark_fields699.rs'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark700-field-api002.v1.json'
EXE='target/debug/examples/p09_block_bookmark_fields699.exe'
DEP=EXE[:-4]+'.d'

def require(ok,code):
    if not ok:raise ValueError('XREF_FIELD700_'+code)

def main():
    require(sys.argv[1:]==['--qualify-field32-not-full-source']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=None;begin=time.monotonic()
    row=dict(state='FAILED700_CURRENT_FIELD_APIS',steps=[],Native_started=False,passed9_tests_replayed=False,
        full_main_Source_assessment_qualified=False,main_Source_Coverage_failure_removed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);prior=p.codec.unpack(q.json(PRIOR),guard.check)
        failed_path='implementation/p09/evidence/p09-361-block-bookmark700-field-api001.v1.json'
        failed=p.codec.unpack(q.json(failed_path),guard.check)
        require(q.snapshots[failed_path]['sha256']=='c4d972d179c4e653fcf59e2cc8e8d48cbeea0bd784a21ea0a4ff402c736d5f51'
            and failed['cleanup']is True and failed['steps'][-1]['safe_error_code']=='P699_MAIN_SOURCE_COVERAGE_REMAINS_UNQUALIFIED','PRESERVED_OVERGENERALIZED_MAIN_FAILURE_EXPECTATION')
        archive='implementation/p09/source-archive/p361-block-fields700-product001/'
        for pin in failed['source_pins']:
            path=archive+pin['path']if pin['path']in(SELF,EXAMPLE)else pin['path'];bound=q.pin(path)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'UNCHANGED_COMPONENT_CODE_AND_ARCHIVED_INITIAL_OBSERVER')
        require(q.snapshots[PRIOR]['sha256']=='aa3924eb98d3c4e5bf652dd15b5f8f7ff6da537f389d58a16f5011b14b1d8e40'
            and prior['cleanup']is True and prior['steps'][-1]['exit_code']==2
            and prior['steps'][-1]['safe_error_code']=='P695_MAIN_REFERENCE_SOURCE_TARGET_COVERAGE_REJECTED','PRESERVED_FULL_MAIN_SOURCE_FAILURE')
        for pin in prior['source_pins']:require(q.pin(pin['path'])==pin,'CURRENT_SOURCE_AND_FAILED_FULL_SCOPE_UNCHANGED')
        tests=p.codec.unpack(q.json(TEST_PROOF),guard.check)
        require(q.snapshots[TEST_PROOF]['sha256']=='ed27f639b1b8d18570fd51247744af56eb8fb7bc5472e296a5de398e9b144de9'
            and tests['cleanup']is True and [len(s['tests'])for s in tests['steps'][:2]]==[6,3]
            and all(s['exit_code']==0 and all(v=='ok'for _,v in s['tests'])for s in tests['steps'][:2]),'RETAINED9_CORE_AND_POINT_TESTS')
        manifest=q.json(MANIFEST)
        names=inventory.inputs(guard.check)|{SELF,EXAMPLE,MANIFEST,'tools/p09/product_result_capture700.py'}
        for path in sorted(names):q.pin(path)
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for group in tests['compiled_tests']:
            for pin in group.values():require(binary.pin(pin['path'])==pin,'RETAINED_QUALIFIED_TEST_ARTIFACTS')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        args=[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--features','p09-installed-format-fixture',
            '--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2',
            '--example','p09_block_bookmark_fields699','--message-format=short']
        r.harness.run_one('new_independent_field_API_reader699_only',args,set(),guard,r.audit.environment(),row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)];require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'COMPILED_SOURCE_CLOSURE_PREBOUND')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--field32-readonly-main-source-unqualified'],r.audit.environment(),row,'actual32_field_APIs_graph_with_full_Source_rejection_preserved')
        require(actual is not None and actual['state']=='QUALIFIED699_PRODUCT32_FIELD_API_CACHE_AND_GRAPH_WITH_FULL_SOURCE_LIMITATIONS_REPORTED'
            and len(actual['observations'])==32,'ALL32_FIELD_SCOPE_NOT_FULL_MAIN_SOURCE')
        expected=[(case,stage)for case in manifest['cases']for stage in('candidate','initial','saved','reopened')]
        for observed,(case,stage)in zip(actual['observations'],expected,strict=True):
            require(observed['case_index']==case['case_index']and observed['stage']==stage and observed['source']==case['stages'][stage]['pin']
                and all(observed[k]is True for k in('product_command_and_block_target_bound','field_API_typed_meaning','XML_cached_display_parity',
                    'exact_block_begin_graph_edge','original_eight_block_snapshots_preserved','graph_serialization_reopened','whole_source_reconstruction'))
                and observed['unsupported_block_meanings_preserved']==8 and observed['main_source_complete_validation_qualified']is False
                and ((observed['main_source_partial_available']is True and observed['main_source_error']is None)
                    or(observed['main_source_partial_available']is False and type(observed['main_source_error'])is str)),'ACTUAL_FIELD_PRODUCT_PROOFS_AND_PRESERVED_LIMITATIONS')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED700_FIXED32_FIELD_APIS_CACHE_GRAPH_FULL_SOURCE_LIMITATIONS_REPORTED_NOT_FULL_F11',
            product=actual,retained_core6_affected_point3_not_replayed=True,explicit_opaque_BOOKMARK_meanings_preserved=True,
            actual_current_product_documents=32,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark700-field-api002-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','compiled_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED700_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
