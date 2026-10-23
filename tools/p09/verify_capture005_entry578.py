"""Fixed005 entry/runtime code models only. Canonical code proof published only on success.

Failed model audits remain immutable and cannot satisfy the executable entry's code gate.
No actual005 preflight/claim/final/spool, Native session or product is executed here.
"""
import ast,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch005 as entry
import crossref_external005_runtime as runtime
import crossref_inline_receipt567 as layout
import search_sql_receipt as prior_layout
SELF='tools/p09/verify_capture005_entry578.py'
AUDIT='implementation/p09/evidence/p09-361-capture005-entry-code578-audit001.v1.json'
TEST='tools/p09/tests/test_crossref_generation005_entry.py'
WORKER='implementation/p09/evidence/p09-361-capture005-worker577.v1.json'
PROBE='implementation/p09/evidence/p09-361-capture005-namespace574.v1.json'
PUBLICATION='implementation/p09/evidence/p09-361-generation005-publication573.v1.json'
OLD_CODE='implementation/p09/evidence/p09-361-capture004-entry-code559.v1.json'
LEGACY_ENTRY='tools/p09/run_external_crossref_fixed_batch.py'
LEGACY_RUNTIME='tools/p09/crossref_external_batch_runtime.py'

def check_capture_body(q):
    current=q.text(runtime.SELF);original=q.text(LEGACY_RUNTIME)
    current=current[current.index('def capture_artifacts('):current.index('\ndef execute(',current.index('def capture_artifacts('))].rstrip()
    original=original[original.index('def capture_artifacts('):original.index('\ndef execute(',original.index('def capture_artifacts('))].rstrip()
    current=current.replace('def capture_artifacts(guard,host):',
        "def capture_artifacts(guard,host,*,fixed_capture003=False,fixed_capture004=False):\n    require(type(fixed_capture003)is bool,'EXACT_CAPTURE003_SCOPE_FLAG')\n    require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')",1)
    current=current.replace('        base=capture.namespace.directory(index)',
        '        base=capture004.namespace.directory(index)if fixed_capture004 else capture003.namespace.directory(index)if fixed_capture003 else artifact_directory(index)',1)
    r.c.require(current==original,'P578_ALL_ORIGINAL16_OWNERS40_ARTIFACTS_TRACE_HASHES_AND_FINAL_FRESHNESS_CHECKS_PRESERVED')

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-models-only'],'P578_MODELS_ONLY_NO_ACTUAL_ENTRY_OR_NATIVE')
    c.require(not(c.ROOT/AUDIT).exists()and not(c.ROOT/entry.NAMES['code']).exists(),'P578_NEW_AUDIT_AND_CANONICAL_CODE_ONLY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=shell=None;passed=False
    row=dict(state='FAILED_CAPTURE005_ENTRY_CODE_MODELS',generation=5,own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,actual005_entry_preflight_or_claim_or_final_created=False,
        original001_to004_replayed=False,new005_execution_authorized=False,native_startup_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        worker=prior_layout.unpack(q.json(WORKER));probe=prior_layout.unpack(q.json(PROBE));publication=layout.unpack(q.json(PUBLICATION))
        c.require(q.snapshots[WORKER]['sha256']=='f78d108e5052e3b1a558ea8234a6fe969e3ea490c5b6b462145ca46738b216b0'
            and worker['cleanup']is True and worker['fresh_inputs']==worker['final_fresh_hashes']==256,'P578_RETAIN577_WORKER_COMPONENTS_NOT_REPLAYED')
        c.require(q.snapshots[PROBE]['sha256']=='3dd2e093d8b4d61faffe6eaca78ecf50d8de5b7cbc1a79e8756e793f095ca667'
            and probe['cleanup']is True and probe['fresh_inputs']==probe['final_fresh_hashes']==852,'P578_RETAIN574_READONLY_PROBE_NOT_REBUILT')
        c.require(q.snapshots[PUBLICATION]['sha256']=='42714fbbe0b2164205e7c82483eccfd5cb39dbb435da7aed043949676453c51f'
            and publication['cleanup']is True and publication['contracts']==dict(run=10,errors=0,failures=0,skipped=0),'P578_RETAIN573_PUBLICATION_COMPONENT_NOT_REPLAYED')
        paths=entry.loaded_paths(exclude=(SELF,))|runtime.CASE_PATHS|set(runtime.fixed_input_pins())|{entry.SELF,runtime.SELF}
        names=paths|{SELF,TEST,WORKER,PROBE,PUBLICATION,OLD_CODE,LEGACY_ENTRY,LEGACY_RUNTIME}
        names|=set(probe['actual_probe_dependencies'])
        for pin in worker['source_pins']:
            if pin['path']not in('tools/p09/verify_capture005_worker575.py',):names.add(pin['path'])
        for name in sorted(names):q.pin(name)
        for prior in(worker,publication):
            for pin in prior['source_pins']:
                path=pin['path']
                if path in paths or path in('tools/p09/crossref_generation005_publication.py','tools/p09/crossref_inline_receipt567.py'):
                    c.require(q.pin(path)==pin,'P578_RETAINED_COMPONENT_CURRENT_INPUTS_IDENTICAL')
        old=r.compact.unpack(q.json(OLD_CODE));oldpins={p['path']:p for p in old['source_pins']}
        c.require(q.snapshots[LEGACY_ENTRY]==oldpins[LEGACY_ENTRY]and q.snapshots[LEGACY_RUNTIME]==oldpins[LEGACY_RUNTIME],'P578_CONSUMED_ENTRIES_AND_RUNTIME_BYTE_EXACT_UNCHANGED')
        c.require(q.snapshots[runtime.capture.namespace.PROBE]==probe['compiled_probe'],'P578_CURRENT_FROZEN_READONLY_PROBE')
        check_capture_body(q)
        before={name:bool((c.ROOT/name).exists())for name in(entry.NAMES['preflight'],entry.NAMES['claim'],entry.NAMES['output'],entry.publication.SPOOL)}
        c.require(not any(before.values()),'P578_ACTUAL005_EXECUTION_NAMESPACE_UNUSED')
        for name in(SELF,TEST,entry.SELF,runtime.SELF):ast.parse(q.text(name))
        spec=importlib.util.spec_from_file_location('capture005_entry_models',c.ROOT/TEST);models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(models.Entry005);c.require(suite.countTestCases()==34,'P578_EXACT34_NEW_CODE_CONTRACTS')
        result=unittest.TestResult();suite.run(result)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=34,errors=0,failures=0,skipped=0),'P578_ALL34_NEW_CODE_CONTRACTS_PASS')
        c.require(all(not(c.ROOT/name).exists()for name in before),'P578_NO_ACTUAL005_PREFLIGHT_CLAIM_RESULT_OR_SPOOL_CREATED_BY_MODELS')
        runtime.absent_attempts();shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        row['external_shell_pins']=[shell.pin(Path(runtime.original.candidate.original.SHELL).name)]
        c.require(row['external_shell_pins']==worker['external_shell_pins'],'P578_SAME_CURRENT_QUALIFIED_SHELL')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(paths),external_shell_final_fresh_hashes=shell.final_fresh_hashes,
            retained_probe_worker_and_publication_components=True,original_capture_validation_body_preserved=True);passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,RecursionError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P578_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        audit=shared.publisher.publish(c.ROOT,AUDIT,layout.pack(row),NS(require=c.require,exact=a.exact));canonical=None
        if passed and row['cleanup']:
            canonical=shared.publisher.publish(c.ROOT,entry.NAMES['code'],layout.pack(dict(row,code_audit_receipt=audit)),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'audit':audit,'canonical_code_proof':canonical}),flush=True)
    return 0 if passed and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
