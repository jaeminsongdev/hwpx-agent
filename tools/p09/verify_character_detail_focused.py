"""482: focused unchanged stored v9 bodies/new5 only. No replay/promotion of unpublished core43."""
import ast,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import verify_character_detail_search as prior
import character_detail_receipt as layout
r=prior.r
SELF='tools/p09/verify_character_detail_focused.py'
OUTPUT='implementation/p09/evidence/p09-361-character-detail-focused482.v1.json'
TESTROOT='crates/product-cli/tests/character_detail_product.rs'
PARENT=prior.PRODUCT+'regex_replacement_product.rs'
FIXTURE=prior.PRODUCT+'source_search_product_fixture.rs'
BOUNDARY=prior.PRODUCT+'source_search_boundary_fixture.rs'
HOST=prior.PRODUCT+'character_detail_product_host.rs'
ARCHIVE='implementation/p09/source-archive/p361-character-detail481/'
FAILURE='implementation/p09/evidence/p09-361-character-detail-search481-publication-failure.v1.json'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'DETAIL_FOCUSED482_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_FOCUSED_CHARACTER_DETAIL_PRODUCTS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_DB_or_Native_started=False,official249_replayed=False,unpublished_core43_replayed_or_accepted=False,
        previous481_original_row_reconstructed=False,full_style_cascade_font_substitution_visibility_or_product_route_qualified=False,
        source_mutation_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        base=r.compact.unpack(q.json(prior.BASE))
        names=shared.source_inventory(guard.check)|prior.NEW|{p['path']for p in base['source_pins']if p['path'].startswith(('crates/','fixtures/'))}
        names|={SELF,TESTROOT,PARENT,FIXTURE,BOUNDARY,HOST,ARCHIVE+'runner481.py',ARCHIVE+'regex-parent481.rs',FAILURE,
            'tools/p09/character_detail_receipt.py','tools/p09/tests/test_character_detail_receipt.py',
            'crates/product-cli/tests/support/stored_source_fixture.rs','crates/hwpx-package/src/hancom_2020_minimal_header.xml'}
        for path in(c.ROOT/'target/debug/deps').glob('regex_replacement_product-*.d'):names|=prior.dependencies(path)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):q.pin(path)
        failure=q.json(FAILURE)
        c.require(failure['state']=='OBSERVED_RUN481_PUBLICATION_FAILURE_NOT_ACCEPTANCE'and failure['original_receipt_absence_verified']is True
            and failure['full_original_row_or_final_input_closure_reconstructed']is False,'ORIGINAL481_MISSING_PROOF_NOT_RECONSTRUCTED_OR_ACCEPTED')
        c.require(not(c.ROOT/prior.OUTPUT).exists(),'ORIGINAL481_FULL_RECEIPT_STILL_ABSENT')
        archive=q.snapshots[ARCHIVE+'regex-parent481.rs'];restored=q.text(PARENT).replace('include!("source_search_product_fixture.rs");',q.text(FIXTURE).rstrip('\n'))
        r.audit.inverse(restored,archive,'ENTIRE_ORIGINAL_REGEX_TEST_PARENT_RESTORED_BY_EXACT_SHARED_FIXTURE_EXPANSION')
        boundary=q.text(BOUNDARY).strip();c.require(q.text(ARCHIVE+'regex-parent481.rs').count(boundary)==1,'EXACT_ORIGINAL_HEAD_RACE_FIXTURE_NOT_NEW_SEMANTICS')
        parent=prior.PRODUCT+'resolved_style_product.rs';prefix='product_host::resolved_style_v9::'
        old_cases=prior.tests(q,parent,prefix);new_cases=prior.tests(q,prior.PRODUCT+'character_detail_product.rs',prefix+'character_details::')
        c.require(len(old_cases)==20 and len(new_cases)==5,'FOCUSED_NEW5_AFFECTED20_SAME_TEST_BODIES')
        spec=importlib.util.spec_from_file_location('detail_inline_pin_models',str(c.ROOT/'tools/p09/tests/test_character_detail_receipt.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);suite=unittest.defaultTestLoader.loadTestsFromModule(module)
        result=unittest.TestResult();suite.run(result)
        row['layout_contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_layout_contracts']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['layout_contracts']==dict(run=6,errors=0,failures=0,skipped=0),'LOSSLESS_INLINE_PIN_LAYOUT6_UNCHANGED_256K_CAP')
        for path in(SELF,'tools/p09/character_detail_receipt.py'):ast.parse(q.text(path))
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];required=5+6.036870455636344
        row['memory_admission']=dict(available_ram_percent=available,required_available_percent=required,global_RAM_commit_ceiling_percent=95)
        c.require(available>required,'FOCUSED_COMPILE_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-character-detail-focused-scratch482';c.require(not scratch.exists(),'FOCUSED_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        cases=old_cases|new_cases
        print(json.dumps(dict(state='FOCUSED_CHARACTER_DETAIL_PREFLIGHT',inputs=len(q.snapshots),new_product_cases=5,affected_product_cases=20,core43_replayed=False)),flush=True)
        command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','character_detail_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('focused_source_style_products25',command,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'FOCUSED_NO_COMPILER_WARNINGS')
        actual=[]
        for path in(c.ROOT/'target/debug/deps').glob('character_detail_product-*.d'):
            declared=prior.dependencies(path);c.require(declared<=set(q.snapshots),'FOCUSED_ACTUAL_COMPILE_INPUT_CLOSURE_PINNED_BEFORE_BUILD')
            actual.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
        c.require(bool(actual),'FOCUSED_ACTUAL_DEP_INFO_REQUIRED');row['actual_compiled_test_inputs']=actual
        artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_FOCUSED_CHARACTER_DETAIL_STORED_NEW5_AFFECTED20_NOT_FULL_STYLE_NATIVE_OR_GATE',new_product_cases=5,affected_product_cases=20,
            total_executed_product_cases=25,character_detail_predicate_families=24,original_test_parent_and_head_race_fixture_preserved=True,
            same_current_source_checks_cursor_binding_and_route_denial=True,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'FOCUSED_DETAIL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','layout_contracts','failed_layout_contracts','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','cleanup')},'cases':len(s.get('tests',[])),
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']and row['fresh_inputs']==row['final_fresh_hashes']else 2

if __name__=='__main__':raise SystemExit(main())
