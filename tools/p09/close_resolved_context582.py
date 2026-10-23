"""Close current compile inputs and same binaries; retain 581's 22 bodies, run omitted affected8.

581 remains FAILED with final_fresh_hashes=0. This new run pins its missing XML
and child test source, builds without running tests, requires identical binaries,
then runs only the eight enclosing-control cases not selected in 581.
"""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_source_field_semantics as deps
import crossref_inline_receipt567 as layout
import verify_resolved_context581 as previous
SELF='tools/p09/close_resolved_context582.py'
OUTPUT='implementation/p09/evidence/p09-361-resolved-context582.v1.json'
CONTROL='crates/hwpx-package/tests/resolved_style_control_context.rs'
HEADER='crates/hwpx-package/src/hancom_2020_minimal_header.xml'
FAILED_SHA='7fc14c8207f9c1fce9fc2a25aca5a851212f7a09938bb94d2f9fb49e0decc288'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--same-binary-closure-only'],'P582_CLOSED_RECOVERY_SCOPE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P582_IMMUTABLE_CURRENT_CLOSURE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifacts=None;started=time.monotonic()
    row=dict(state='FAILED_SELECTED_CONTEXT_CURRENT_CLOSURE',steps=[],own_cpu_selection=selection,
        original581_failed_or_missing_preflight_rewritten=False,actual_Native_COM_SQL_or_queue_started=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,new005_execution_authorized=False,
        full_native_cascade_or_visibility_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=layout.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']==FAILED_SHA and failed['state']=='FAILED_SELECTED_RESOLVED_CONTEXT_OPTIMIZATION'
            and failed['error_code']=='P581_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED'and failed['cleanup']is True
            and failed['fresh_inputs']==919 and failed['final_fresh_hashes']==0,'P582_PRESERVE581_INCOMPLETE_CLOSURE')
        step,=failed['steps'];retained={name for name,status in step['tests']if status=='ok'}
        c.require(step['exit_code']==0 and len(step['tests'])==len(retained)==22 and not step['diagnostics']
            and step['cleanup']is True and step['owned_job']['owned_tree_empty']is True,'P582_EXACT22_SUCCESSFUL_BODIES_NOT_WHOLE581_PASS')
        for pin in failed['source_pins']:c.require(q.pin(pin['path'])==pin,'P582_ALL581_OBSERVED_SOURCE_AND_PROBES_UNCHANGED')
        for name in(SELF,CONTROL,HEADER):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        actual=step['bounded_output_observation']['current_test_executables'];c.require(len(actual)==2,'P582_TWO_PREVIOUS_ACTUAL_TEST_BINARIES')
        artifacts=a.AcceptanceReader(c.ROOT,guard.check);before={};closure=[];previous_names={p['path']for p in failed['source_pins']};missing=set()
        for name in actual:
            dep=Path(name).with_suffix('.d').as_posix();declared=deps.dependencies(c.ROOT/dep);missing|=declared-previous_names
            c.require(declared<=set(q.snapshots),'P582_ALL_CURRENT_ACTUAL_INPUTS_PREPINNED_BEFORE_BUILD')
            before[name]=artifacts.pin(name);before[dep]=artifacts.pin(dep)
            closure.append(dict(executable=before[name],dep_info=before[dep],dependency_count=len(declared)))
        c.require(missing=={HEADER,CONTROL},'P582_EXACT_TWO_MISSING_INPUTS_NO_BROAD_RELAXATION')
        cases={'control_context::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(CONTROL))}
        c.require(len(cases)==8 and not(cases&retained),'P582_ONLY_EIGHT_NOT_PREVIOUSLY_EXECUTED_AFFECTED_CASES')
        scratch=c.ROOT/'target/p09-resolved-context582-scratch';c.require(not scratch.exists(),'P582_FRESH_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='P582_SAME_BINARY_CLOSURE_PREFLIGHT',fresh_inputs=len(q.snapshots),
            prior22_bodies_reexecuted=False,new_affected_cases=8,missing_inputs_now_prebound=2,CPU_hard_cap_percent=6.25)),flush=True)
        build=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--lib','--test','document_import_resolved_style_search',
            '--no-run','--message-format=short']
        r.harness.run_one('current_source_build_only_no_test_body',build,set(),guard,env,row,observe_capture=r.snapshot)
        c.require(not row['steps'][-1]['diagnostics'],'P582_NO_BUILD_WARNINGS')
        for name,pin in before.items():c.require(artifacts.fresh_pin(name)==pin,'P582_CURRENT_BUILD_SAME_EXECUTABLE_AND_DEP_INFO_BYTES')
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_resolved_style_search',
            '--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('eight_previously_unselected_control_context_cases',args,cases,guard,env,row,observe_capture=previous.observe)
        current=row['steps'][-1];r.tools.good_step(current,cases);c.require(not current['diagnostics'],'P582_NO_AFFECTED_TEST_WARNINGS')
        c.require(current['bounded_output_observation']['current_test_executables']==[name for name in actual if Path(name).name.startswith('document_import_resolved_style_search-')],
            'P582_AFFECTED_CASES_USE_SAME_CURRENT_PRODUCT_TEST_EXECUTABLE')
        for name,pin in before.items():c.require(artifacts.fresh_pin(name)==pin,'P582_ALL_BODY_RESULTS_BOUND_TO_UNCHANGED_EXECUTABLE_BYTES')
        c.require(shared.source_inventory(guard.check)<=set(q.snapshots),'P582_CURRENT_SOURCE_INVENTORY_CLOSED')
        artifacts.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_CONTEXT_CURRENT_BUILD_RETAINED22_AFFECTED8_NOT_NATIVE_OR_GATE',retained_body_result=previous.OUTPUT,
            retained_body_cases=sorted(retained),retained_body_count=22,retained_body_tests_reexecuted=False,new_affected_case_count=8,
            total_distinct_current_cases=30,missing_XML_and_child_test_source_now_prebound=True,actual_current_build_binary_and_dep_info_bytes_identical=True,
            original581_final_fresh_hashes_still_zero=True,current_compile_closure=closure,compiled_artifact_final_fresh_hashes=artifacts.final_fresh_hashes,
            selected_two_leaf_fixture_xml_elements=12006,selected_two_leaf_fixture_sparse_cached_elements=6,
            dense_or_budget_exhaustion_retains_original_linear_classification=True,old_prepared_CROSSREF_probe_bytes_preserved=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P582_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(exit_code=s.get('exit_code'),pass_count=sum(status=='ok'for _,status in s.get('tests',[])),diagnostics=s.get('diagnostics'))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
