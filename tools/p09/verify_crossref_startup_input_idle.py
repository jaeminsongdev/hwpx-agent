"""Pure startup-wait delta and two affected original contracts. Never launches/waits on Hancom."""
import ast,hashlib,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
DRIVER='tools/p09/verify_crossref_startup_input_idle.py'
OUTPUT='implementation/p09/evidence/p09-361-crossref-startup-input-idle476.v1.json'
PARENT='tools/p09/crossref_native_startup.py'
LEAF='tools/p09/crossref_startup_input_idle.py'
TEST='tools/p09/tests/test_crossref_startup_input_idle.py'
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,r.c.ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--pure-models-only'],'INPUT_IDLE_PURE_MODELS_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'INPUT_IDLE_IMMUTABLE_RESULT_NO_REPLAY')
    new=load(TEST,'p09_input_idle_models');prior=load('tools/p09/tests/test_crossref_native_startup.py','p09_input_idle_original_contracts')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STARTUP_INPUT_IDLE_MODELS',own_cpu_selection=selection,
        actual_Hancom_or_COM_or_ROT_or_process_wait_started=False,new_session_or_fixed_eight_or_Native011_executed=False,
        original_failure_and_claim_preserved=True,execution_inputs_changed_requalification_required=True,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names={DRIVER,PARENT,LEAF,TEST,'tools/p09/tests/test_crossref_native_startup.py',
            'tools/p09/crossref_session_qualification.py','tools/p09/crossref_preassigned_session_scope.py',
            'implementation/p09/source-archive/p361-startup-input-idle476/native-startup.py',
            'implementation/p09/tools/crossref-existing-owner.cs','tools/p09/crossref_native_host_limits.py'}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):q.pin(path)
        before=q.text('implementation/p09/source-archive/p361-startup-input-idle476/native-startup.py')
        current=q.text(PARENT);c.require(current.replace('import crossref_startup_input_idle as input_idle\n','').replace('            input_idle.wait(self)\n','')==before,
            'ONLY_NEW_IMPORT_AND_ONE_WAIT_AFTER_ORIGINAL_SINGLE_RESUME')
        c.require(q.snapshots['implementation/p09/tools/crossref-existing-owner.cs']['sha256']=='92143ee252cb7c132bc819e24044e5b6dc0e9a17b9d3777575ab6b1ba8732733','ORIGINAL_EXACT_OWNER_AND_NO_ACTIVATION_POLICY_UNCHANGED')
        cases=unittest.defaultTestLoader.loadTestsFromTestCase(new.Tests)
        c.require(cases.countTestCases()==10,'TEN_NEW_PURE_WAIT_MODELS')
        for name in('test_03_native_backend_has_no_cli_com_activation_kill_or_late_assign','test_06_model_failed_resume_and_freshness_check_latch_without_retry'):
            cases.addTest(prior.NativeStartupContracts(name))
        result=unittest.TestResult();cases.run(result)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=12,errors=0,failures=0,skipped=0),'ALL_NEW10_AFFECTED2_PURE_MODELS')
        for path in(DRIVER,PARENT,LEAF,TEST):ast.parse(q.text(path))
        q.finish();guard.check(force=True);row['state']='PASS_BOUNDED_STARTUP_INPUT_IDLE_NEW10_AFFECTED2_MODELS_NOT_NATIVE_READINESS_OR_GATE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'INPUT_IDLE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact));print(json.dumps({**{k:v for k,v in row.items()if k not in('source_pins','resource_samples')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
