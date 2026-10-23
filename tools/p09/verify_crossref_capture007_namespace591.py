"""Fixed007 readonly namespace/probe preparation only. No worker/Native/claim/old test replay."""
import ast,importlib.util,json,re,subprocess,sys,time,unittest
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import search_sql_receipt as layout
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as deps
import crossref_capture007_namespace as namespace
SELF='tools/p09/verify_crossref_capture007_namespace591.py'
OUTPUT='implementation/p09/evidence/p09-361-capture007-namespace591.v1.json'
SOURCE='crates/product-cli/examples/p09_crossref_discovery_probe.rs'
WRAPPER='crates/product-cli/examples/p09_crossref_capture007_probe.rs'
ARCHIVE='implementation/p09/source-archive/p361-capture007-591/probe-before.rs'
PYTEST='tools/p09/tests/test_crossref_capture007_namespace.py'
OLD003='target/debug/examples/p09_crossref_capture003_probe.exe'
OLD004='target/debug/examples/p09_crossref_capture004_probe.exe'
ORIGINAL='target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
ENTRY='tools/p09/run_external_crossref_fixed_batch.py'
CODE='implementation/p09/evidence/p09-361-capture004-entry-code559.v1.json'
CAPTURE='implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/'

def restore(text):
    text=text.replace('    Fixed007,\n','',1)
    branch='''            (Self::Fixed007, Request::Case { index, phase, .. }) => root.join(format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g007-c{:02}-attempt01/{}.hwpx",
                index + 1,
                phase.name()
            )),
'''
    r.c.require(text.count(branch)==1,'P591_EXACT_ONE_FIXED007_PATH_BRANCH');text=text.replace(branch,'',1)
    entry='''#[allow(dead_code)] // Fixed007 wrapper only; never a Native or retry selector.
pub(crate) fn main_for_capture007() {
    entry(CaptureNamespace::Fixed007);
}

'''
    r.c.require(text.count(entry)==1,'P591_ONE_SEPARATE_READONLY_ENTRY');text=text.replace(entry,'',1)
    text=text.replace('            CaptureNamespace::Fixed007 => run_for_namespace(&request, namespace),\n','',1)
    start=text.index('#[cfg(test)]\nmod capture007_tests {');end=text.index('#[cfg(test)]\nmod capture006_tests {',start)
    return (text[:start]+text[end:]).replace('    entry(CaptureNamespace::Fixed006);\n}\n\n\nfn entry', '    entry(CaptureNamespace::Fixed006);\n}\n\nfn entry')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--readonly-probe-only'],'P591_READONLY_PREPARATION_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists()and not(c.ROOT/namespace.PROBE).exists(),'P591_FRESH_PROBE_AND_RESULT_NO_OVERWRITE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_CAPTURE007_NAMESPACE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_Native_or_SQL_started=False,old_case249_or_Native_or_passed_test_bodies_replayed=False,
        capture007_worker_or_entry_connected=False,capture007_session_qualified=False,new007_execution_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);namespace.require_absent(c.ROOT)
        names=inventory.inventory(guard)|includes.test_inputs((WRAPPER,),guard)|{SELF,SOURCE,WRAPPER,ARCHIVE,PYTEST,OLD003,OLD004,ORIGINAL,ENTRY,CODE,
            'tools/p09/crossref_capture007_namespace.py','tools/p09/crossref_capture003_namespace.py','tools/p09/crossref_capture004_namespace.py',
            *[CAPTURE+n for n in('source-input-manifest.v1.json','prepared-sdk-batch.v1.json','source-with-bookmark.hwpx')]}
        for name in sorted(names):q.pin(name)
        c.require(q.snapshots[ORIGINAL]['sha256']=='0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb'
            and q.snapshots[OLD003]['sha256']=='b9bc121660a649485ca6a25d6fd91a8f3e77c97019de7f35168d0db375325900'
            and q.snapshots[OLD004]['sha256']=='e64128bec14686aaecde8bafaf34458b59a4c694fe2b0a54f411d013b0a01551','P591_ALL_CONSUMED_READONLY_IMAGES_UNCHANGED')
        proof=r.compact.unpack(q.json(CODE));oldpins={p['path']:p for p in proof['source_pins']}
        c.require(q.snapshots[ENTRY]==oldpins[ENTRY],'P591_LEGACY001_TO004_ENTRY_BYTE_EXACT_UNCHANGED')
        r.audit.inverse(restore(q.text(SOURCE)),q.snapshots[ARCHIVE],'P591_WHOLE_ORIGINAL_PARSER_READ_SOURCE_HASHES_SUMMARIES_AND_FINAL_REREADS_PRESERVED')
        text=q.text(SOURCE);block=text[text.index('mod capture007_tests {'):text.index('#[cfg(test)]\nmod capture006_tests {')]
        expected={'original::capture007_tests::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',block)}
        c.require(len(expected)==4 and '#[ignore]'not in block,'P591_ONLY_NEW_FOUR_RUST_CASES')
        spec=importlib.util.spec_from_file_location('capture007_namespace_models',c.ROOT/PYTEST);models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        outcome=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(models).run(outcome)
        row.update(contracts=dict(run=outcome.testsRun,errors=len(outcome.errors),failures=len(outcome.failures),skipped=len(outcome.skipped)),
            failed_contract_names=[test.id()for test,_ in outcome.errors+outcome.failures])
        c.require(row['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P591_ALL_NEW_FIVE_PYTHON_PATH_CASES')
        for name in(SELF,PYTEST,'tools/p09/crossref_capture007_namespace.py'):ast.parse(q.text(name))
        scratch=c.ROOT/'target/p09-capture007-scratch591';c.require(not scratch.exists(),'P591_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1');artifact=a.AcceptanceReader(c.ROOT,guard.check)
        example='p09_crossref_capture007_probe'
        cargo=[r.harness.CARGO,'--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',example,'--features','p09-installed-format-fixture','--message-format=short']
        print(json.dumps(dict(state='CAPTURE007_READONLY_PROBE_PREFLIGHT',inputs=len(q.snapshots),new_rust_cases=4,new_python_cases=5,Native_authorized=False)),flush=True)
        r.harness.run_one('new007_readonly_probe_four_tests',[cargo[0],'test',*cargo[1:],'--',*sorted(expected),'--exact','--test-threads=1'],expected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],expected);c.require(not row['steps'][-1]['diagnostics'],'P591_TESTS_NO_WARNINGS')
        r.harness.run_one('new007_readonly_probe_build',[cargo[0],'build',*cargo[1:]],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'P591_BUILD_NO_WARNINGS')
        binary=artifact.pin(namespace.PROBE);dep='target/debug/examples/'+example+'.d';artifact.pin(dep);declared=deps.dependencies(c.ROOT/dep)
        c.require({SOURCE,WRAPPER}<=declared and declared<=set(q.snapshots),'P591_ACTUAL_COMPILED_INPUTS_PREPINNED');row['actual_probe_dependencies']=sorted(declared)
        c.require(not any(scratch.iterdir()),'P591_COMPILER_TEMP_EMPTY');namespace.require_absent(c.ROOT);artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CAPTURE007_FIXED40_PATHS_FIVE_PYTHON_FOUR_READONLY_RUST_CASES_NOT_WORKER_NATIVE_OR_GATE',
            compiled_probe=binary,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes,consumed_images_not_overwritten=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P591_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        result=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','compiled_probe','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]),failed_cases=[n for n,status in s.get('tests',[])if status!='ok'])for s in row['steps']],'receipt':result}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
