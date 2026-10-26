"""Changed graph targets6, affected point3, and fixed32 product readback only."""
import json,re,subprocess,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import verify_prepared_bookmark631 as command
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_bookmark_graph696.py'
CHANGED='crates/hwpx-package/src/document_import/fields/semantics.rs'
ARCHIVE='implementation/p09/source-archive/p361-block-graph694/'+CHANGED
CORE='crates/hwpx-package/tests/block_bookmark_graph694.rs'
POINT='crates/product-cli/tests/bookmark_reference_edges618.rs'
EXAMPLE='crates/product-cli/examples/p09_block_bookmark_readback695.rs'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark696-product002.v1.json'
EXE='target/debug/examples/p09_block_bookmark_readback695.exe'
DEP=EXE[:-4]+'.d'

def require(ok,code):
    if not ok:raise ValueError('XREF_GRAPH696_'+code)

def main():
    require(sys.argv[1:]==['--changed-graph-and-fixed32-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=None;begin=time.monotonic()
    row=dict(state='FAILED696_BLOCK_PRODUCT_GRAPH',steps=[],Native_started=False,Native_or_unrelated_pass_tests_replayed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        failed_path='implementation/p09/evidence/p09-361-block-bookmark696-product001.v1.json'
        failed=p.codec.unpack(q.json(failed_path),guard.check)
        require(q.snapshots[failed_path]['sha256']=='cb702dde025d9c73f58202dd069f488df110357f48de504c63277dcb079b0289'
            and failed['cleanup']is True and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0432'],'EXACT_INITIAL_FIXTURE_IMPORT_FAILURE_NO_TESTS_RUN')
        archive='implementation/p09/source-archive/p361-block-graph696-product001/'
        for pin in failed['source_pins']:
            path=archive+pin['path']if pin['path']in(CORE,SELF)else pin['path'];bound=q.pin(path)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'FAILED_CODE_AND_CURRENT_INPUTS_PRESERVED')
        require(q.text(CORE)==q.text(archive+CORE).replace('#[allow(dead_code)]mod fixture;\n','#[allow(dead_code)]mod fixture;\nuse fixture as base;\n',1),'ONLY_REQUIRED_EXISTING_FIXTURE_MODULE_ALIAS')
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1054 and len(prior['cases'])==8,'EXACT693_CLOSED_CAPTURES')
        for pin in prior['source_pins']:
            name=ARCHIVE if pin['path']==CHANGED else pin['path'];bound=q.pin(name)
            require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRODUCER_CODE_ARCHIVED_AND_OTHER_INPUTS_UNCHANGED')
        manifest=q.json(MANIFEST);require(q.snapshots[MANIFEST]==prior['product_inputs'],'EXACT_OBSERVED_XML_INPUT_MANIFEST')
        names=inventory.inputs(guard.check)|includes.test_inputs((CORE,POINT,EXAMPLE),guard)|{SELF,CHANGED,ARCHIVE,CORE,POINT,EXAMPLE,MANIFEST,PRIOR}
        for path in sorted(names):q.pin(path)
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(CORE)));require(len(core)==6,'EXACT_NEW_SIX')
        point={'all_eight_command_options_create_edges_only_to_original_bookmark_wrappers','missing_and_ambiguous_bookmarks_never_create_a_first_match_edge','repeated_field_edges_keep_all_bookmark_and_unrelated_reference_state'}
        require(all('fn '+name+'('in q.text(POINT)for name in point),'DIRECTLY_AFFECTED_POINT_REGRESSION_ONLY')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check);binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        env=r.audit.environment();common=['--offline','--locked','-j','1','--message-format=short']
        cli=['--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        row['compiled_tests']=[]
        for package,target,cases,label in(('hwpx-package','block_bookmark_graph694',core,'new_block_graph6'),('hwpx-agent-cli','bookmark_reference_edges618',point,'affected_point_graph3')):
            args=[r.harness.CARGO,'test',*common,'-p',package]
            if package=='hwpx-agent-cli':args+=cli
            args+=['--test',target,'--',*sorted(cases),'--exact','--test-threads=1'];start=time.time_ns()
            r.harness.run_one(label,args,cases,guard,env,row,observe_capture=r.snapshot)
            require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'CHANGED_TESTS_CLEAN')
            files=[]
            for path in(r.c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<start:continue
                require(dep.dependencies(path)<=set(q.snapshots),'TEST_DEPENDENCIES_PREBOUND')
                files.append(dict(dep_info=binary.pin(path.relative_to(r.c.ROOT).as_posix()),binary=binary.pin(path.with_suffix('.exe').relative_to(r.c.ROOT).as_posix())))
            require(len(files)==1,'EXACT_CURRENT_TEST_IMAGE');row['compiled_tests']+=files
        r.harness.run_one('build_fixed32_product_reader695',[r.harness.CARGO,'build',*common,'-p','hwpx-agent-cli',*cli,'--example','p09_block_bookmark_readback695'],set(),guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)];require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPENDENCIES_PREBOUND')
        actual=command.command(guard,[str(r.c.ROOT/EXE),'--fixed32-readonly-no-native'],env,row,'current32_actual_product_readback')
        require(actual['state']=='QUALIFIED695_PRODUCT32_BLOCK_TARGET_CACHE_MAIN_MEANING_AND_GRAPH_NOT_FULL_F11'
            and len(actual['observations'])==32 and actual['Native_started']is False,'WHOLE_CURRENT32_ACTUAL_PRODUCT')
        expected=[(case,stage)for case in manifest['cases']for stage in('candidate','initial','saved','reopened')]
        for observed,(case,stage)in zip(actual['observations'],expected,strict=True):
            require(observed['case_index']==case['case_index']and observed['stage']==stage and observed['source']==case['stages'][stage]['pin']
                and all(observed[k]is True for k in('product_command_and_block_target_bound','main_source_typed_meaning','XML_cached_display_parity','exact_block_begin_graph_edge',
                    'original_eight_block_snapshots_preserved','graph_serialization_reopened','whole_source_reconstruction'))
                and observed['unsupported_block_meanings_preserved']==8,'ALL_ACTUAL_PRODUCT_PROOFS_NOT_FULL_MEANING')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED696_BLOCK32_PRODUCT_MAIN_SOURCE_CACHE_EXACT_GRAPH_EDGES_NOT_RENDER_OR_FULL_F11',
            product=actual,new_core_conditions=6,directly_affected_point_conditions=3,original32_files_not_modified=True,
            unsupported_BOOKMARK_meanings_still_explicit=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark696-product002-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','compiled_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_variants','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED696_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
