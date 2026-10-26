"""Conditional heading input702: new parser/API tests, affected direct cases, fixed32 readonly."""
import json,re,subprocess,sys,time
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import product_result_capture706 as result
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_conditional_headings706.py'
TEST='crates/product-cli/tests/conditional_heading702.rs'
OLD='crates/product-cli/tests/reference_source_product.rs'
OLD_CASES='crates/product-cli/tests/reference_source_product/heading_targets.rs'
EXAMPLE='crates/product-cli/examples/p09_conditional_heading_readback705.rs'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark700-field-api002.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-conditional-headings702/'
CHANGED={'crates/hwpx-package/src/document_import/reference_targets/headings.rs',
    'crates/product-cli/src/reference_validation_product/source.rs'}
OUTPUT='implementation/p09/evidence/p09-361-conditional-headings706-product001.v1.json'
EXE='target/debug/examples/p09_conditional_heading_readback705.exe'
DEP=EXE[:-4]+'.d'

def require(ok,code):
    if not ok:raise ValueError('XREF_HEADING706_'+code)

def main():
    require(sys.argv[1:]==['--new-conditional-and-affected-source-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=binary=None;begin=time.monotonic()
    row=dict(state='FAILED706_CONDITIONAL_HEADING_INPUT',steps=[],Native_started=False,official249_or_passed_field_graph_tests_replayed=False,
        branch_selection_effective_headings_or_complete_validation_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='e6a58b22e9d292f55f5ed432c57d1380bf8751e2a114053306380d4e6fe2394b'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1076,'EXACT700_QUALIFIED_FIELD_SCOPE_PRESERVED')
        for pin in prior['source_pins']:
            name=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path'];current=q.pin(name)
            require((current['bytes'],current['sha256'])==(pin['bytes'],pin['sha256']),'PRIOR_CHANGED_INPUTS_ARCHIVED_OTHER_INPUTS_UNCHANGED')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,OLD,EXAMPLE),guard)|{SELF,MANIFEST,'tools/p09/product_result_capture706.py'}
        for name in sorted(names):q.pin(name)
        manifest=q.json(MANIFEST)
        for case in manifest['cases']:
            for stage in('candidate','initial','saved','reopened'):require(q.pin(case['stages'][stage]['pin']['path'])==case['stages'][stage]['pin'],'CURRENT_EXACT32_PRODUCT_INPUTS')
        fresh=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        old={'source_heading_targets::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(OLD_CASES))}
        require(len(fresh)==9 and len(old)==13,'FOCUSED_NINE_AND_THIRTEEN')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check);binary=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        env=r.audit.environment();common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli',
            '--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2',
            '--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
        row['compiled_tests']=[]
        for target,cases,label in(('conditional_heading702',fresh,'new9_conditional_parser_API_CLI_limits_source_coverage'),
            ('reference_source_product',old,'affected13_legacy_direct_heading_API_CLI_coverage')):
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
        r.harness.run_one('build_fixed32_main_Source_reader705',[r.harness.CARGO,'build',*common,'--example','p09_conditional_heading_readback705'],
            set(),guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'NORMAL_BUILD_CLEAN')
        row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)];require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'NORMAL_DEPENDENCIES_PREBOUND')
        actual=result.command(guard,[str(r.c.ROOT/EXE),'--main-source32-readonly'],env,row,'actual32_main_Source_conditional_and_legacy_partial')
        require(actual is not None and actual['state']=='QUALIFIED705_FIXED32_MAIN_SOURCE_CONDITIONAL_UNRESOLVED_AND_LEGACY_PARTIAL'
            and len(actual['observations'])==32 and actual['Native_started']is False,'WHOLE32_MAIN_SOURCE_READBACK')
        for observed,(case,stage)in zip(actual['observations'],[(c,s)for c in manifest['cases']for s in('candidate','initial','saved','reopened')],strict=True):
            require(observed['case_index']==case['case_index']and observed['stage']==stage and observed['source']==case['stages'][stage]['pin']
                and observed['main_Source_partial_available']is True and observed['field_API_and_cache_parity']is True
                and observed['branch_selected']is False and observed['complete_validation_qualified']is False
                and observed['conditional_definitions']==(3 if stage=='candidate'else 0)
                and observed['heading_targets_unavailable']==(stage=='candidate'),'EXACT_PARTIAL_NOT_SELECTED_TARGET_OR_AUTHORITY')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED706_CONDITIONAL_HEADING_MODEL_MAIN_SOURCE32_PARTIAL_NOT_EFFECTIVE_HEADINGS_OR_FULL_F11',
            product=actual,new_conditions=9,affected_legacy_conditions=13,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-conditional-headings706-product001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','compiled_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','safe_error_code','bounded_output_observation')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED706_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
