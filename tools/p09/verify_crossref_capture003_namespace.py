"""488: build fixed003 readonly probe and prove fixed namespace without Native execution."""
import ast,hashlib,importlib.util,json,os,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import character_detail_receipt as layout
import crossref_capture003_namespace as ns

SELF='tools/p09/verify_crossref_capture003_namespace.py'
OUTPUT='implementation/p09/evidence/p09-361-capture003-namespace488.v1.json'
SOURCE='crates/product-cli/examples/p09_crossref_discovery_probe.rs'
WRAPPER='crates/product-cli/examples/p09_crossref_capture003_probe.rs'
ARCHIVE='implementation/p09/source-archive/p361-capture003-namespace488/probe-original.rs'
PYTEST='tools/p09/tests/test_crossref_capture003_namespace.py'
CORPUS='implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/'
ORIGINAL_PROBE='target/p09-149-conservative/debug/examples/p09_crossref_discovery_probe.exe'
RUN002='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run002.v1.json'
FAILED_CASE='implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261017-r01-c01-attempt01/'
EXAMPLE='p09_crossref_capture003_probe'

def restore_original(text):
    begin=text.index('#[derive(Clone, Copy)]\nenum CaptureNamespace')
    end=text.index('fn run_for_namespace(request: &Request, namespace: CaptureNamespace) -> Result<Value> {',begin)
    text=text[:begin]+'fn run(request: &Request) -> Result<Value> {'+text[end+len('fn run_for_namespace(request: &Request, namespace: CaptureNamespace) -> Result<Value> {'):]
    text=text.replace('    let path = namespace.path(request, &root);','    let path = request.path(&root);')
    begin=text.index('fn main() {');end=text.index('fn entry(namespace: CaptureNamespace) {',begin)
    text=text[:begin]+'fn main() {'+text[end+len('fn entry(namespace: CaptureNamespace) {'):]
    text=text.replace('''        .and_then(|request| match namespace {
            CaptureNamespace::Original => run(&request),
            CaptureNamespace::Fixed003 => run_for_namespace(&request, namespace),
        });''','        .and_then(|request| run(&request));')
    begin=text.index('#[cfg(test)]\nmod capture003_tests {');end=text.index('#[cfg(test)]\nmod tests {',begin)
    return text[:begin]+text[end:]

def inventory(guard):
    # Current compiled source trees only; no unrelated test corpus, history, Git or target walk.
    result={'Cargo.toml','Cargo.lock','rust-toolchain.toml',SOURCE,WRAPPER,SELF,PYTEST,ARCHIVE,
        'tools/p09/crossref_capture003_namespace.py',RUN002,ORIGINAL_PROBE,
        FAILED_CASE+'target-trace.json',FAILED_CASE+'owner-identities.json',
        'crates/hwpx-package/src/hancom_2020_minimal_header.xml'}
    result|={CORPUS+n for n in('source-input-manifest.v1.json','prepared-sdk-batch.v1.json','source-with-bookmark.hwpx')}
    for package in r.shared.PACKAGES:
        result.add(f'crates/{package}/Cargo.toml');root=r.c.ROOT/f'crates/{package}/src'
        r.c.require(root.is_dir()and not root.is_symlink()and not root.is_junction(),'CAPTURE003_REGULAR_COMPILED_SOURCE_ROOT')
        for directory,dirs,files in os.walk(root,followlinks=False):
            guard.check()
            for name in dirs:
                child=Path(directory)/name;r.c.require(not child.is_symlink()and not child.is_junction(),'CAPTURE003_COMPILED_SOURCE_LINK')
            for name in files:
                if name.endswith('.rs'):result.add((Path(directory)/name).relative_to(r.c.ROOT).as_posix())
                r.c.require(len(result)<=2048,'CAPTURE003_SOURCE_INVENTORY_BOUND')
    for module in tuple(sys.modules.values()):
        value=getattr(module,'__file__',None)
        if value:
            path=Path(value).absolute()
            if path.is_relative_to(r.c.ROOT/'tools/p09')and path.suffix=='.py':result.add(path.relative_to(r.c.ROOT).as_posix())
    return result

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'CAPTURE003_NAMESPACE488_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_CAPTURE003_NAMESPACE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,official249_replayed=False,original_attempts_replayed_moved_or_deleted=False,
        new_native_generation_authorized=False,external003_entry_wired_or_ready=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        ns.require_absent(c.ROOT);c.require(not(c.ROOT/ns.PROBE).exists(),'NEW003_BINARY_MUST_NOT_OVERWRITE_EXISTING')
        paths=inventory(guard)
        for path in sorted(paths):q.pin(path)
        c.require(q.snapshots[RUN002]['sha256']=='937f7e344845513faf0316e581a52657d803fce026ab6ae05f175dad353fe7da','ORIGINAL002_FAILED_RECEIPT_PRESERVED')
        c.require(q.snapshots[ORIGINAL_PROBE]['sha256']=='0f9c727afa18d1c0145a21cbc63f947c48922873f6dbe97cd2860e76355491bb','ORIGINAL_PROBE_NOT_OVERWRITTEN')
        r.audit.inverse(restore_original(q.text(SOURCE)),q.snapshots[ARCHIVE],'WHOLE_ORIGINAL_READ_PINS_PREPARATION_PARSE_SUMMARY_AND_FINAL_REREADS_UNCHANGED')
        rust=q.text(SOURCE);block=rust[rust.index('mod capture003_tests {'):rust.index('#[cfg(test)]\nmod tests {')]
        expected={'original::capture003_tests::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',block)}
        c.require(len(expected)==4 and '#[ignore]'not in block,'FOUR_NEW_FIXED_NAMESPACE_TESTS_ONLY')
        spec=importlib.util.spec_from_file_location('capture003_namespace_tests',str(c.ROOT/PYTEST));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'FIVE_FIXED003_NAMESPACE_CONTRACTS')
        for path in(SELF,PYTEST,'tools/p09/crossref_capture003_namespace.py'):ast.parse(q.text(path))
        guard.check(force=True);available=guard.samples[-1]['available_ram_percent'];required=11.036870455636344
        row['memory_admission']=dict(available_ram_percent=available,required_available_percent=required,global_RAM_commit_ceiling_percent=95)
        c.require(available>required,'CAPTURE003_COMPARABLE_COMPILE_RAM95_HEADROOM')
        scratch=c.ROOT/'target/p09-capture003-namespace-scratch488';c.require(not scratch.exists(),'CAPTURE003_UNIQUE_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='CAPTURE003_NAMESPACE_PREFLIGHT',inputs=len(q.snapshots),new_rust_tests=4,python_contracts=5,native_authorized=False)),flush=True)
        command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',EXAMPLE,'--message-format=short','--',*sorted(expected),'--exact','--test-threads=1']
        r.harness.run_one('capture003_probe_new4_only',command,expected,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],expected);c.require(not row['steps'][-1]['diagnostics'],'CAPTURE003_TEST_NO_WARNINGS')
        command=[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',EXAMPLE,'--message-format=short']
        r.harness.run_one('capture003_fixed_readonly_binary_build',command,set(),guard,env,row,observe_capture=r.snapshot)
        c.require(not row['steps'][-1]['diagnostics'],'CAPTURE003_BUILD_NO_WARNINGS')
        binary=artifact.pin(ns.PROBE);c.require(0<binary['bytes']<=16777216,'CAPTURE003_FIXED_BINARY_SIZE')
        dep=f'target/debug/examples/{EXAMPLE}.d';text=artifact.text(dep)
        declaration=text.split(': ',1)[1].splitlines()[0]
        actual={Path(value.replace('\\','/'))for value in declaration.split()}
        declared={p.relative_to(c.ROOT).as_posix()if p.is_absolute()else p.as_posix()for p in actual}
        c.require({SOURCE,WRAPPER}<=declared and declared<=set(q.snapshots),'CAPTURE003_ACTUAL_DEP_INFO_CLOSURE_PINNED_BEFORE_BUILD')
        row['actual_example_dependencies']=sorted(declared);row['fixed003_binary']=binary
        ns.require_absent(c.ROOT);artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_FIXED003_NAMESPACE_PY5_RUST4_AND_READONLY_BINARY_NOT_NATIVE_OR_ENTRY_READY',
            new_rust_tests=4,fixed_artifact_paths=40,original_probe_and_failed002_artifacts_preserved=True,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE003_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','fixed003_binary')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cases=len(s.get('tests',[])),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]),
                compiler_locations=s.get('bounded_output_observation',{}).get('short_error_locations',[]))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
