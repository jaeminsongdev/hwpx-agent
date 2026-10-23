"""Current closed generation002 code package, new18 + affected old5 pure models; no Native."""
import ast,contextlib,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime
import crossref_fixed_worker as fixed
import crossref_session_worker as candidate
DRIVER='tools/p09/verify_crossref_generation002.py'
TEST='tools/p09/tests/test_crossref_generation002.py'
LEGACY='tools/p09/tests/test_crossref_qualified_entry.py'
OUTPUT=entry.generation_names(True)['code']
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,r.c.ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-models-only'],'GENERATION002_CODE_MODELS_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'GENERATION002_IMMUTABLE_CODE_PROOF')
    models=load(TEST,'p09_generation002_contracts');legacy=load(LEGACY,'p09_generation002_legacy_contracts')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_GENERATION002_CODE_PACKAGE',own_cpu_selection=selection,steps=[],
        actual_Hancom_ROT_COM_or_worker_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,retained_PS10_replayed=False,retained_idle12_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        frozen={}
        for path in('implementation/p09/evidence/p09-361-crossref-failure-diagnostics-final429.v1.json',
            'implementation/p09/evidence/p09-361-crossref-startup-input-idle476.v1.json'):
            proof=r.compact.unpack(q.json(path));c.require(proof['state'].startswith('PASS_')and proof['cleanup']is True
                and proof['fresh_inputs']==proof['final_fresh_hashes'],'EXACT_ACCEPTED_CURRENT_GUARD_DIAGNOSTIC_AND_IDLE_GENERATIONS')
            frozen.update({p['path']:p for p in proof['source_pins']})
        dependencies=entry.loaded_paths(exclude=(DRIVER,))|set(candidate.SOURCES)|set(fixed.SOURCES)|runtime.CASE_PATHS
        dependencies-=set(runtime.INPUT_PINS);row['entry_dependency_paths']=sorted(dependencies)
        c.require(entry.SELF in dependencies and 'tools/p09/crossref_startup_input_idle.py'in runtime.CASE_PATHS
            and runtime.CASE_PATHS<=dependencies|set(runtime.INPUT_PINS),'CURRENT_ENTRY_AND_EACH_NATIVE_CASE_COMPLETE_IDLE_SOURCE_CLOSURE')
        changed={entry.SELF,'tools/p09/crossref_external_batch_runtime.py'}
        for path in sorted(dependencies):
            pin=q.pin(path)
            if path in frozen and path not in changed:c.require(pin==frozen[path],'ORIGINAL_NATIVE_GUARD_IDENTITY_HOST_TRANSPORT_INPUTS_UNCHANGED')
        archive='implementation/p09/source-archive/p361-crossref-generation478/'
        original=q.text(archive+'batch-runtime.py');current=q.text('tools/p09/crossref_external_batch_runtime.py')
        c.require(current.replace("'crossref_native_startup','crossref_startup_input_idle','crossref_native_host_limits'","'crossref_native_startup','crossref_native_host_limits'")==original,
            'ONLY_CASE_INPUT_LIST_IDLE_HELPER_ADD_NO_EXECUTOR_OR_RETRY_CHANGE')
        q.pin(archive+'entry.py')
        for path in runtime.INPUT_PINS:
            pin=q.pin(path);size,sha=runtime.INPUT_PINS[path];c.require((pin['bytes'],pin['sha256'])==(size,sha),'ORIGINAL_FIXED_EIGHT_SOURCE_PACKET_AND_PROBE_BYTES_UNCHANGED')
        oldpath='implementation/p09/evidence/p09-361-crossref-qualified-entry-code411.v1.json';old=r.compact.unpack(q.json(oldpath))
        oldpins={p['path']:p for p in old['source_pins']};ps='implementation/p09/tools/test-crossref-qualified-fixed-worker.ps1'
        c.require(q.pin(ps)==oldpins[ps]and old['cleanup']is True,'PREVIOUS_PS_RELEASE10_UNCHANGED_NOT_REPLAYED')
        for path in(DRIVER,TEST,LEGACY):q.pin(path)
        for mod in tuple(sys.modules.values()):
            name=getattr(mod,'__file__',None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        new=list(unittest.defaultTestLoader.loadTestsFromTestCase(models.Tests));c.require(len(new)==18,'EXACT_EIGHTEEN_NEW_GENERATION_MODELS')
        selected=[legacy.EntryContracts(name)for name in('test_24_native_entry_has_no_retry_selector','test_25_preflight_namespace_separate_and_requires_explicit_run',
            'test_26_execution_and_preflight_cannot_be_combined','test_35_public_preflight_cannot_execute_even_if_prerequisites_pass','test_36_failed_current_prerequisites_prevent_native_claim_and_execution')]
        result=unittest.TestResult();row['contract_names']=[t.id()for t in new+selected]
        for test in new:test.run(result);guard.check(force=True)
        for test in selected:
            # Legacy entry models predate consumed001 files; isolate their fake filesystem, never rerun that entry.
            with patch.object(entry.Path,'exists',return_value=False),patch.object(entry.Path,'is_symlink',return_value=False):test.run(result)
            guard.check(force=True)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[t.id()for t,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=23,errors=0,failures=0,skipped=0),'ALL_NEW18_AFFECTED5_NO_NATIVE_MODELS')
        for path in(DRIVER,TEST,entry.SELF,'tools/p09/crossref_external_batch_runtime.py'):ast.parse(q.text(path))
        image=a.AcceptanceReader(Path(candidate.original.SHELL).parent,guard.check);image.pin(Path(candidate.original.SHELL).name)
        image.finish();q.finish();guard.check(force=True);row['state']=entry.CODE_STATE
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'GENERATION002_CODE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            external_shell_pins=[]if image is None else list(image.snapshots.values()),external_shell_final_hashes=0 if image is None else image.final_fresh_hashes,
            resource_samples=samples,elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=a.exact));print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'entry_dependencies':len(row.get('entry_dependency_paths',[])),'receipt':pin}),flush=True)
    return 0 if row['state']==entry.CODE_STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
