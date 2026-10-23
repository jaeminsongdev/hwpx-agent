"""Prepare fixed004 readonly paths/probe only. No worker, session, Native permission or old case replay."""
import ast,importlib.util,json,re,subprocess,sys,time,unittest
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import search_sql_receipt as layout
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_capture004_namespace as namespace
SELF='tools/p09/verify_crossref_capture004_namespace549.py'
OUTPUT='implementation/p09/evidence/p09-361-capture004-namespace549.v1.json'
SOURCE='crates/product-cli/examples/p09_crossref_discovery_probe.rs'
WRAPPER='crates/product-cli/examples/p09_crossref_capture004_probe.rs'
ARCHIVE='implementation/p09/source-archive/p361-capture004-549/probe-before.rs'
PYTEST='tools/p09/tests/test_crossref_capture004_namespace.py'
STARTUP='implementation/p09/evidence/p09-361-startup15-applied548.v1.json'
RUN003='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run003.v1.json'
ORIGINAL='target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
CONSUMED003='target/debug/examples/p09_crossref_capture003_probe.exe'
CAPTURE='implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/'
def restore(text):
    text=text.replace('    Fixed004,\n','')
    text=text.replace('''            (Self::Fixed004, Request::Case { index, phase, .. }) => root.join(format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g004-c{:02}-attempt01/{}.hwpx",
                index + 1,
                phase.name()
            )),
''','')
    a=text.index('#[allow(dead_code)] // A separate readonly wrapper,');b=text.index('fn entry(namespace:',a);text=text[:a]+text[b:]
    text=text.replace('            CaptureNamespace::Fixed004 => run_for_namespace(&request, namespace),\n','')
    a=text.index('#[cfg(test)]\nmod capture004_tests {');b=text.index('#[cfg(test)]\nmod capture003_tests {',a)
    return text[:a]+text[b:]
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--readonly-probe-only'],'P549_READONLY_PREPARATION_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/namespace.PROBE).exists(),'P549_FRESH_PROBE_AND_RECEIPT_NO_OVERWRITE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_CAPTURE004_NAMESPACE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,old_cases_or_249_or_003_or_SQL545_replayed=False,
        capture004_worker_or_entry_wired=False,capture004_session_qualified=False,new_native_execution_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);namespace.require_absent(c.ROOT)
        names=inventory.inventory(guard)|{SELF,SOURCE,WRAPPER,ARCHIVE,PYTEST,STARTUP,RUN003,ORIGINAL,CONSUMED003,
            'tools/p09/crossref_capture004_namespace.py','tools/p09/crossref_capture003_namespace.py','tools/p09/crossref_startup_input_idle.py',
            *[CAPTURE+n for n in('source-input-manifest.v1.json','prepared-sdk-batch.v1.json','source-with-bookmark.hwpx')]}
        names|=includes.test_inputs((WRAPPER,),guard)
        names|={p.relative_to(c.ROOT).as_posix()for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')}
        c.require(len(names)<=2048,'P549_BOUNDED_CURRENT_COMPILE_SOURCE_SET')
        for path in sorted(names):q.pin(path)
        c.require(q.snapshots[RUN003]['sha256']=='901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a','P549_ORIGINAL003_FAILED_RECEIPT_PRESERVED')
        c.require(q.snapshots[ORIGINAL]['sha256']=='0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb'
            and q.snapshots[CONSUMED003]['sha256']=='b9bc121660a649485ca6a25d6fd91a8f3e77c97019de7f35168d0db375325900','P549_ORIGINAL_AND003_BINARIES_NOT_OVERWRITTEN')
        startup=layout.unpack(q.json(STARTUP));c.require(q.snapshots[STARTUP]['sha256']=='ecf1ff8e7bda1fe15cca29605e9a8c9884e9699bc25bc8d4487faa38be18bba2'
            and startup['cleanup']is True and startup['fresh_inputs']==startup['final_fresh_hashes']==215
            and q.snapshots['tools/p09/crossref_startup_input_idle.py']['sha256']==startup['qualified_candidate']['sha256'],'P549_CURRENT_APPROVED_STARTUP15_NOT_SESSION_AUTHORITY')
        r.audit.inverse(restore(q.text(SOURCE)),q.snapshots[ARCHIVE],'P549_ORIGINAL_PARSER_READ_PINS_PREPARE_SUMMARY_AND_FINAL_REREADS_BYTE_EXACT')
        rust=q.text(SOURCE);block=rust[rust.index('mod capture004_tests {'):rust.index('#[cfg(test)]\nmod capture003_tests {')]
        expected={'original::capture004_tests::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',block)}
        c.require(len(expected)==4 and '#[ignore]'not in block,'P549_ONLY_NEW_FOUR_RUST_TESTS')
        spec=importlib.util.spec_from_file_location('capture004_namespace_models',c.ROOT/PYTEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P549_ALL_NEW_FIVE_PATH_MODELS')
        for path in(SELF,PYTEST,'tools/p09/crossref_capture004_namespace.py'):ast.parse(q.text(path))
        guard.check(force=True);scratch=c.ROOT/'target/p09-capture004-scratch549';c.require(not scratch.exists(),'P549_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);example='p09_crossref_capture004_probe'
        print(json.dumps(dict(state='CAPTURE004_READONLY_PREFLIGHT',inputs=len(q.snapshots),new_rust_tests=4,new_python_models=5,Native_authorized=False)),flush=True)
        cargo=[r.harness.CARGO,'--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',example,'--features','p09-installed-format-fixture','--message-format=short']
        r.harness.run_one('new004_readonly_probe_four_tests',[cargo[0],'test',*cargo[1:],'--',*sorted(expected),'--exact','--test-threads=1'],expected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],expected);c.require(not row['steps'][-1]['diagnostics'],'P549_RUST_TESTS_NO_WARNINGS')
        r.harness.run_one('new004_readonly_probe_build',[cargo[0],'build',*cargo[1:]],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P549_READONLY_BUILD_NO_WARNINGS')
        binary=artifact.pin(namespace.PROBE);dep='target/debug/examples/'+example+'.d';artifact.pin(dep);declared=deps.dependencies(c.ROOT/dep)
        c.require({SOURCE,WRAPPER}<=declared and declared<=set(q.snapshots),'P549_ALL_ACTUAL_COMPILED_DEPENDENCIES_PREDECLARED');row['actual_example_dependencies']=sorted(declared)
        c.require(not any(scratch.iterdir()),'P549_COMPILER_TEMP_EMPTY');namespace.require_absent(c.ROOT);artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_FIXED004_NAMESPACE_PY5_RUST4_AND_READONLY_PROBE_NOT_WORKER_ENTRY_SESSION_OR_NATIVE',
            fixed004_binary=binary,fixed_artifact_paths=40,new_rust_tests=4,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P549_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:v for k,v in row.items()if k not in('source_pins','resource_samples','steps')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
