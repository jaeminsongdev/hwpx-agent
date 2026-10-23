"""411: new entry/handoff/batch/source36 + affected kernel6 + PS release10, no Native."""
import hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime
import crossref_fixed_worker as fixed
import crossref_session_worker as candidate

OUTPUT='implementation/p09/evidence/p09-361-crossref-qualified-entry-code411.v1.json'
DRIVER='tools/p09/run_crossref_qualified_entry_code_recovery.py'
FAILED='implementation/p09/evidence/p09-361-crossref-qualified-entry-code410.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-session-qualification-sync409.v1.json'
KERNEL='tools/p09/crossref_session_qualification.py'
PYTEST='tools/p09/tests/test_crossref_qualified_entry.py'
PSTEST='implementation/p09/tools/test-crossref-qualified-fixed-worker.ps1'
SHELL=Path(candidate.original.SHELL)
NAMES={'release_does_not_consume_case_sequence','denial_never_enters_cases','authority_flag_cannot_release','numeric_boolean_rejected',
    'escaped_duplicate_rejected','subset_or_extra_field_rejected','other_protocol_rejected','closed_fixed_eight_parameter',
    'only_fixed_controller_no_activation_or_force_kill','uncertain_owners_retained_until_host_eof'}


def original_kernel(text):
    text=text.replace("def __init__(self,worker,identity,fresh_shell_pin,expected_role='private_session_qualification_candidate'):",
        'def __init__(self,worker,identity,fresh_shell_pin):')
    added="        require(type(expected_role)is str and expected_role in('private_session_qualification_candidate','private_fixed_eight_worker'),'CLOSED_EXPECTED_WORKER_ROLE')\n"
    r.c.require(text.count(added)==1,'ONE_EXPLICIT_CLOSED_WORKER_ROLE_EXTENSION')
    text=text.replace(added,'').replace("worker.profile.get('role')==expected_role and","worker.profile.get('role')=='private_session_qualification_candidate'and")
    text=text.replace("def observe(self,refresh_image=True):\n        require(type(refresh_image)is bool,'EXACT_REFRESH_IMAGE_FLAG')",'def observe(self):')
    new="""        if refresh_image:
            pin=self.pin();require(type(pin)is dict and pin.get('path')==Path(owned.SHELL).name
                and pin.get('sha256')==identity['executable_sha256']and type(pin.get('bytes'))is int and pin['bytes']>0,'FRESH_EXACT_WORKER_IMAGE')"""
    old="""        pin=self.pin();require(type(pin)is dict and pin.get('path')==Path(owned.SHELL).name
            and pin.get('sha256')==identity['executable_sha256']and type(pin.get('bytes'))is int and pin['bytes']>0,'FRESH_EXACT_WORKER_IMAGE')"""
    r.c.require(text.count(new)==1,'ONE_EXPLICIT_CASE_BOUNDARY_IMAGE_REFRESH_MODE')
    return text.replace(new,old)


def ps_models(guard,env,row):
    c=r.c;owned=capture=None;started=time.monotonic();step=dict(stage='new_fixed_release_and_worker_source_models10',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/PSTEST),'-ModelsOnly'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_ENTRY_MODELS_READONLY_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'(?m)^Error: (P09_XREF_[A-Z0-9_]{1,120})\r?$',stderr),
            summary_observed='10 passed; 0 failed; 0 ignored; release_source_models_not_native'in stdout)
        c.require(step['exit_code']==0 and len(tests)==10 and {n for n,s in tests}=={'qualified_fixed_worker::'+n for n in NAMES}
            and all(s=='ok'for n,s in tests)and not stderr and step['summary_observed'],'EXACT10_FIXED_WORKER_RELEASE_SOURCE_MODELS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'QUALIFIED_ENTRY_CODE411_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_QUALIFIED_ENTRY_CODE410',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,actual_qualification_or_fixed_worker_started=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        unaffected_successes_replayed=False,affected_kernel_cases_reexecuted=6,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='9228f4aa1283879b3c7df80dde20f64ebe932adacd5df1ae2fce21f5213cc8dc'
            and base['cleanup']and base['fresh_inputs']==base['final_fresh_hashes']==215,'EXACT409_SESSION_CANDIDATE_SOURCE_CLOSURE')
        old={p['path']:p for p in base['source_pins']}
        failure=r.compact.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='c50364f6963ef7f487f9a7e289b7301a24b98a6343df36ce7db151bfb46d12f2'
            and failure['state']=='FAILED_QUALIFIED_ENTRY_CODE410'and failure['cleanup']
            and failure['fresh_inputs']==failure['final_fresh_hashes']==219 and failure['steps']==[]
            and failure.get('contracts')is None,'ORIGINAL410_INVERSE_WHITESPACE_PREFLIGHT_FAILURE_NO_TESTS_NOT_RELABELED_PASS')
        for pin in failure['source_pins']:
            path=pin['path']
            if path!=entry.SELF:c.require(q.pin(path)==pin,'ALL410_PREPARED_IMPLEMENTATION_INPUTS_UNCHANGED')
            else:
                text=q.text(path);r.audit.inverse(text.replace('p09-361-crossref-qualified-entry-code411.v1.json',
                    'p09-361-crossref-qualified-entry-code410.v1.json'),pin,'ONLY_VERIFIED_CODE_PROOF_REFERENCE_ADVANCED_FAILURE410_PRESERVED')
        dependencies=entry.loaded_paths(exclude=(DRIVER,))|set(candidate.SOURCES)|set(fixed.SOURCES)|runtime.CASE_PATHS
        dependencies-=set(runtime.INPUT_PINS)
        c.require(entry.SELF in dependencies and runtime.CASE_PATHS<=dependencies|set(runtime.INPUT_PINS),'ALL_ACTIVE_ENTRY_AND_CASE_INPUTS_IN_ONE_CURRENT_MANIFEST')
        row['entry_dependency_paths']=sorted(dependencies)
        for path in sorted(dependencies):
            pin=q.pin(path)
            if path in old and path!=KERNEL:c.require(pin==old[path],'ALL_ORIGINAL_NATIVE_GUARD_STARTUP_OWNER_AND_PREVIOUS_RUNTIME_INPUTS_UNCHANGED')
        r.audit.inverse(original_kernel(q.text(KERNEL)),old[KERNEL],'ONLY_CLOSED_FIXED_ROLE_AND_PER_CASE_IMAGE_REFRESH_MODE_DEFAULT_STRICT_KERNEL_AND_NATIVE_GUARDS_UNCHANGED')
        for path in runtime.INPUT_PINS:
            pin=q.pin(path);size,sha=runtime.INPUT_PINS[path];c.require((pin['bytes'],pin['sha256'])==(size,sha),'ORIGINAL_FIXED_EIGHT_SOURCE_PACKET_AND_PROBE_UNCHANGED')
        for path in(DRIVER,PYTEST,PSTEST):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_qualified_entry_contracts',c.ROOT/PYTEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        suite=unittest.defaultTestLoader.loadTestsFromModule(models)
        for name in unittest.defaultTestLoader.getTestCaseNames(models.prior_kernel.SessionContracts):
            if 20<=int(name.split('_')[1])<=25:suite.addTest(models.prior_kernel.SessionContracts(name))
        def names(value):
            if isinstance(value,unittest.TestSuite):return [n for item in value for n in names(item)]
            return [value.id()]
        row['contract_names']=names(suite)
        result=GuardedResult();suite.run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=42,errors=0,failures=0,skipped=0),'EXACT36_NEW_ENTRY_CASE_HANDOFF_SOURCE_MODELS_AND_AFFECTED6_KERNEL_MODELS')
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        print(json.dumps(dict(state='QUALIFIED_ENTRY411_PREFLIGHT',inputs=len(q.snapshots),new_contracts=36,affected_kernel_contracts=6,new_ps_release_source=10)),flush=True)
        env=r.audit.environment();env['PYTHONDONTWRITEBYTECODE']='1';ps_models(guard,env,row)
        image.finish();q.finish();guard.check(force=True);row.update(state=entry.CODE_STATE,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='actual_public_preflight_and_fixed_worker_handshake_denial_before_user_external_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'QUALIFIED_ENTRY410_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'entry_dependencies':len(row.get('entry_dependency_paths',[])),
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state']==entry.CODE_STATE and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())


