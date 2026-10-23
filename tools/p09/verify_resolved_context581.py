"""Selected-context optimization: four new complexity/equivalence tests and 18 affected searches.

No Native, SQL, queue, trust, approval or completed historical test is replayed.
Only the resolved-context implementation changes; result schemas stay intact.
"""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_source_field_semantics as deps
import crossref_inline_receipt567 as layout
SELF='tools/p09/verify_resolved_context581.py'
OUTPUT='implementation/p09/evidence/p09-361-resolved-context581.v1.json'
CORE='crates/hwpx-package/src/document_import/search/inspection/definitions/resolved.rs'
HELPER=CORE[:-3]+'/control_contexts.rs'
BEFORE='implementation/p09/source-archive/p361-resolved-context581/resolved.rs'
TEST='crates/hwpx-package/tests/document_import_resolved_style_search.rs'
UNIT_PREFIX='document_import::search::inspection::definitions::resolved::control_contexts::tests::'
PROBES=('target/debug/examples/p09_crossref_capture005_probe.exe',
    'target/debug/examples/p09_crossref_capture004_probe.exe','target/debug/examples/p09_crossref_capture003_probe.exe',
    'target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe')


def observe(capture,expected):
    result=r.snapshot(capture,expected)
    with capture.lock:raw=bytes(capture.buffers['stderr']).decode('utf-8','replace')
    names=[]
    for name in re.findall(r'Running [^\r\n]*\(([^)\r\n]+[\\/](?:hwpx_package|document_import_resolved_style_search)-[0-9a-f]+\.exe)\)',raw):
        path=Path(name).resolve();r.c.require(path.parent==r.c.ROOT/'target/debug/deps','P581_EXACT_TEST_BINARY_DIRECTORY')
        names.append(path.relative_to(r.c.ROOT).as_posix())
    result['current_test_executables']=sorted(set(names));return result


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--selected-context-only'],'P581_CLOSED_SCOPE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P581_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifacts=None;started=time.monotonic()
    row=dict(state='FAILED_SELECTED_RESOLVED_CONTEXT_OPTIMIZATION',own_cpu_selection=selection,steps=[],
        actual_Native_COM_SQL_or_queue_started=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        new005_execution_authorized=False,full_native_cascade_or_visibility_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names=shared.source_inventory(guard.check)|{SELF,CORE,HELPER,BEFORE,TEST}|set(PROBES)
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(names):q.pin(name)
        c.require(q.snapshots[BEFORE]['sha256']=='1d4703fd6f09106df4ae68ed9670d518a8e70725869e7cd087c60f2b9ef90a3b','P581_CURRENT_PREIMAGE')
        before=q.text(BEFORE);current=q.text(CORE)
        start=before.index('            let part=source_parts.get(path)');end=before.index('\n        }\n        // Structural context',start)
        replacement='''            let part=source_parts.get(path).ok_or(E::Source)?;
            let xml=part.xml().ok_or(E::Source)?;
            uncertain.extend(control_contexts::collect(xml.elements(),&selected)?);'''
        expected=(before[:start]+replacement+before[end:]).replace('use super::*;\n','use super::*;\nmod control_contexts;\n',1)
        c.require(current==expected,'P581_ALL_OTHER_COVERAGE_AXIS_SOURCE_AND_OUTPUT_BODY_UNCHANGED')
        integration=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        unit={UNIT_PREFIX+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(HELPER))}
        c.require(len(integration)==18 and len(unit)==4,'P581_EXACT_FOUR_NEW_EIGHTEEN_AFFECTED')
        cases=integration|unit;scratch=c.ROOT/'target/p09-resolved-context581-scratch'
        c.require(not scratch.exists()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'P581_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='P581_CURRENT_CONTEXT_PREFLIGHT',fresh_inputs=len(q.snapshots),new_cases=4,affected_cases=18,
            unrelated_old_cases=0,one_cpu=True,CPU_hard_cap_percent=6.25)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--lib','--test','document_import_resolved_style_search',
            '--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('selected_context_four_new_and_eighteen_affected',args,cases,guard,env,row,observe_capture=observe)
        step=row['steps'][-1];r.tools.good_step(step,cases);c.require(not step['diagnostics'],'P581_NO_COMPILER_WARNINGS')
        actual=step['bounded_output_observation']['current_test_executables']
        c.require(len(actual)==2 and sum(Path(p).name.startswith('hwpx_package-')for p in actual)==1,'P581_TWO_ACTUAL_EXECUTED_TEST_BINARIES')
        artifacts=a.AcceptanceReader(c.ROOT,guard.check);closure=[]
        for name in actual:
            dep=Path(name).with_suffix('.d').as_posix();declared=deps.dependencies(c.ROOT/dep)
            c.require(declared<=set(q.snapshots),'P581_ALL_ACTUAL_COMPILER_DEPENDENCIES_PREPINNED')
            closure.append(dict(executable=artifacts.pin(name),dep_info=artifacts.pin(dep),dependency_count=len(declared)))
        c.require(shared.source_inventory(guard.check)<=names,'P581_NO_NEW_SOURCE_AFTER_COMPILATION')
        artifacts.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTED_RESOLVED_CONTEXT_OPTIMIZATION_NOT_NATIVE_CASCADE_OR_GATE',new_equivalence_and_complexity_cases=4,
            affected_existing_search_cases=18,unrelated_existing_cases_reexecuted=0,source_body_outside_context_lookup_unchanged=True,
            selected_two_leaf_fixture_full_xml_elements=12006,selected_two_leaf_fixture_sparse_cached_elements=6,
            dense_or_sparse_budget_exhaustion_uses_original_linear_classification=True,
            current_compile_closure=closure,compiled_artifact_final_fresh_hashes=artifacts.final_fresh_hashes,
            old003_004_and_prepared005_probe_bytes_preserved=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P581_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(exit_code=s.get('exit_code'),pass_count=sum(status=='ok'for _,status in s.get('tests',[])),
                diagnostics=s.get('diagnostics'),panic_locations=s.get('panic_locations'))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
