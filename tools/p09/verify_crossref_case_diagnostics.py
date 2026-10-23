"""483: closed first-case failure projection, pure Python6/PS6 + affected release10; never Native."""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout

SELF='tools/p09/verify_crossref_case_diagnostics.py'
OUTPUT='implementation/p09/evidence/p09-361-crossref-case-diagnostics483.v1.json'
ROOT='implementation/p09/tools/'
ARCHIVE='implementation/p09/source-archive/p361-crossref-case-diagnostics483/'
RUN002='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run002.v1.json'
PS='C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe'

def names(text,prefix):return set(re.findall(r'test ('+prefix+r'[A-Za-z0-9_:]+) \.\.\. ok',text))

def ps_models(filename,prefix,expected,guard,row):
    # Same original explicitly allowlisted owned PS mechanism used by code411, not the Cargo-only helper.
    r.c.require(filename in('test-crossref-case-failure-projection.ps1','test-crossref-qualified-fixed-worker.ps1'),'FIXED_DIAGNOSTIC_MODEL_SCRIPT')
    owned=capture=None;started=time.monotonic();step=dict(stage=prefix.rstrip(':'),cleanup=False);row['steps'].append(step)
    try:
        command=[PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/ROOT/filename),'-ModelsOnly']
        owned=r.shared.OwnedSQLJobProcess(command,windows=guard.windows,allowed_executables=[PS],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<90,'STOP_CASE_DIAGNOSTIC_MODEL_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
        r.c.require(owned.returncode==0 and not stderr and {n for n,s in tests}==expected and len(tests)==len(expected)
            and all(s=='ok'for n,s in tests),'EXACT_CLOSED_PS_DIAGNOSTIC_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;recover=sys.argv[1:]==['--after-launcher483']
    c.require(sys.argv[1:]in([],['--after-launcher483']),'CASE_DIAGNOSTIC_CLOSED_MODE')
    output='implementation/p09/evidence/p09-361-crossref-case-diagnostics484.v1.json'if recover else OUTPUT
    c.require(not(c.ROOT/output).exists(),'CASE_DIAGNOSTIC_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;started=time.monotonic()
    row=dict(state='FAILED_CLOSED_CASE_FAILURE_DIAGNOSTICS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,fixed_eight_replayed=False,official249_replayed=False,run002_failure_preserved=True,
        original_source_bind_admission_weakened=False,source_bind_runtime_root_cause_confirmed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        nameset={SELF,ROOT+'crossref-fixed-batch.ps1',ROOT+'run-crossref-qualified-fixed-worker.ps1',ROOT+'crossref-owned-active-source.ps1',
            ROOT+'crossref-case-flow.ps1',ROOT+'crossref-host-channel.ps1',ROOT+'crossref-preassigned-host-channel.ps1',
            ROOT+'test-crossref-case-failure-projection.ps1',ROOT+'test-crossref-qualified-fixed-worker.ps1',
            'tools/p09/crossref_native_worker_io.py','tools/p09/tests/test_crossref_case_failure_projection.py',RUN002}
        nameset|={ARCHIVE+n for n in('fixed-batch.ps1','fixed-worker.ps1','worker-io.py')}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':nameset.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(nameset):q.pin(path)
        original=r.compact.unpack(q.json(RUN002))
        c.require(q.snapshots[RUN002]['sha256']=='937f7e344845513faf0316e581a52657d803fce026ab6ae05f175dad353fe7da'
            and original['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'and original['cleanup']is True,'EXACT_USER_COMPLETED_RUN002_FAILURE_NOT_PASS')
        first=original['qualification_worker'];fixed=original['fixed_worker'];scope=fixed['handler_summary']['protocol']['scope']
        c.require(first['exit_code']==0 and first['cleanup']is True and first['result']['COM_owner_observed']is True
            and original['qualification_boundary']['closed']is True and original['same_invocation_handoff_consumed']is True,
            'CURRENT_LIFECYCLE_AND_CLOSED_BOUNDARY_ADVANCED_NOT_WHOLE_NATIVE_QUALIFICATION')
        c.require(fixed['exit_code']==2 and fixed['cleanup']is True and fixed['result']['completed_callback_cases']==0
            and fixed['result']['stopped_case_index']==1 and fixed['result']['host_messages']==6
            and scope['next_step_index']==4 and len(scope['retired_sessions'])==1
            and scope['retired_sessions'][0]['startup_profile']['cleanup_confirmed']is True,
            'OBSERVED_FIRST_CASE_SOURCE_BIND_PREFIX_NO_SAVED_OUTPUT_OR_RETRY')
        frozen={p['path']:p for p in original['source_pins']}
        for old,new in[('crossref-fixed-batch.ps1','fixed-batch.ps1'),('run-crossref-qualified-fixed-worker.ps1','fixed-worker.ps1')]:
            pin=q.snapshots[ARCHIVE+new];expected=frozen[ROOT+old]
            c.require((pin['bytes'],pin['sha256'])==(expected['bytes'],expected['sha256']),'EXACT_RUN002_WORKER_SOURCE_ARCHIVES')
        pin=q.snapshots[ARCHIVE+'worker-io.py'];expected=frozen['tools/p09/crossref_native_worker_io.py']
        c.require((pin['bytes'],pin['sha256'])==(expected['bytes'],expected['sha256']),'EXACT_RUN002_TRANSPORT_SOURCE_ARCHIVE')
        c.require(q.pin(ROOT+'crossref-owned-active-source.ps1')==frozen[ROOT+'crossref-owned-active-source.ps1'],
            'ORIGINAL_COM_SOURCE_BIND_CHECKS_AND_REJECTION_RULES_UNCHANGED')
        testpath='tools/p09/tests/test_crossref_case_failure_projection.py'
        spec=importlib.util.spec_from_file_location('closed_case_failure_models',str(c.ROOT/testpath));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        if recover:
            failed=layout.unpack(q.json(OUTPUT))
            c.require(q.snapshots[OUTPUT]['sha256']=='564556565f52dbbe13702b6f647b8b25f6146340d629cb123a758958724c9bdf'
                and failed['state']=='FAILED_CLOSED_CASE_FAILURE_DIAGNOSTICS'and failed['error_code']=='OWNED_SQL_EXECUTABLE_NOT_ALLOWLISTED'
                and len(failed['steps'])==1 and failed['steps'][0].get('exit_code')is None,'ORIGINAL483_PS_PROCESS_CREATION_DENIAL_PRESERVED')
            for pin in failed['source_pins']:
                if pin['path']!=SELF:c.require(q.pin(pin['path'])==pin,'ALL_ORIGINAL_SIX_PYTHON_MODEL_INPUTS_UNCHANGED')
            row['contracts']=failed['contracts'];row['failed_contract_names']=failed['failed_contract_names']
            row.update(retained_python6_from_failed483_with_current_input_closure=True,python_models_replayed=False,
                original483_cleanup_false_and_missing_final_fresh_preserved=True)
        else:
            suite=unittest.defaultTestLoader.loadTestsFromModule(module);result=unittest.TestResult();suite.run(result)
            row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
            row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=6,errors=0,failures=0,skipped=0),'CASE_DIAGNOSTIC_NEW_PYTHON6')
        for path in(SELF,'tools/p09/crossref_native_worker_io.py',testpath):ast.parse(q.text(path))
        shell=a.AcceptanceReader(Path(PS).parent,guard.check);shell.pin(Path(PS).name)
        configs=[('test-crossref-case-failure-projection.ps1','case_failure::',6),('test-crossref-qualified-fixed-worker.ps1','qualified_fixed_worker::',10)]
        for filename,prefix,count in configs:
            expected=names(q.text(ROOT+filename),prefix);c.require(len(expected)==count,'EXACT_CLOSED_POWERSHELL_MODELS')
            ps_models(filename,prefix,expected,guard,row)
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CLOSED_CASE_FAILURE_PROJECTION_PY6_PS6_AFFECTED_RELEASE10_NOT_NATIVE_OR_GATE',
            exact_failed_step_runtime_observation='source_bind_entered_after_original_open_returned_not_exact_property_failure',
            runtime_replay_or_new_generation_authorized=False,external_shell_final_fresh_hashes=shell.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CASE_DIAGNOSTIC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cases=len(s.get('tests',[])),cleanup=s['cleanup'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
