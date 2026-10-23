"""491: fixed003 worker command/projection and actual closed-mode denial, no Native dispatch."""
import hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
import crossref_capture003_worker as worker

SELF='tools/p09/verify_crossref_capture003_worker.py'
OUTPUT='implementation/p09/evidence/p09-361-capture003-worker491.v1.json'
BASE='implementation/p09/evidence/p09-361-capture003-powershell490.v1.json'
ROOT='implementation/p09/tools/'
MODEL=ROOT+'test-crossref-capture003-worker-program.ps1'
PYTEST='tools/p09/tests/test_crossref_capture003_worker.py'
ARCHIVE='implementation/p09/source-archive/p361-capture003-namespace488/fixed-worker-original.py'
PS='C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe'

def child(script,models,expected,guard,row):
    owned=capture=None;started=time.monotonic();step=dict(stage='fixed003_program_models'if models else'fixed003_actual_closed_mode_denial',cleanup=False);row['steps'].append(step)
    try:
        command=[PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/script)]+(['-ModelsOnly']if models else[])
        owned=r.shared.OwnedSQLJobProcess(command,windows=guard.windows,allowed_executables=[PS],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<90,'STOP_CAPTURE003_WORKER_MODEL_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,closed_model_errors=re.findall(r'(?m)^Error: (P09_XREF_BIND_[A-Z_]+)\r?$',stdout),
            stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
        if models:
            r.c.require(owned.returncode==0 and not stderr and len(tests)==3 and {n for n,s in tests}==expected and all(s=='ok'for n,s in tests),'THREE_EXACT_PROGRAM_PROJECTION_GROUPS')
        else:
            result=json.loads(stdout)
            r.c.require(owned.returncode==2 and not stderr and result['schema_version']=='hwpx-agent.private.crossref-fixed-worker-result/v1'
                and result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='closed_mode'
                and result['error_code']=='P09_XREF_BIND_CAPTURE_THREE_FIXED_MODE_REQUIRED'and result['retained_live_or_uncertain_owners']==0
                and result['completed_callback_cases']==0 and result['probe_lease_closed']is True
                and result['native_execution_authorized']is False and result['native_startup_qualified']is False and result['p09_complete']is False,
                'ACTUAL003_TARGET_NO_FLAG_DENIED_BEFORE_IMPORT_OR_NATIVE')
            step['closed_mode_result']=result
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'CAPTURE003_WORKER491_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=shell=None
    row=dict(state='FAILED_CAPTURE003_WORKER_COMPOSITION',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,official249_replayed=False,prior_native_attempts_replayed=False,
        new_native_generation_authorized=False,external003_entry_wired_or_ready=False,compiled488_or_namespace490_tests_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);worker.namespace.require_absent(c.ROOT)
        paths=set(worker.SOURCES)|{SELF,BASE,MODEL,PYTEST,ARCHIVE,'tools/p09/crossref_capture003_worker.py','tools/p09/crossref_fixed_worker.py'}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':paths.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(paths):q.pin(path)
        c.require(q.snapshots[BASE]['sha256']=='0bb615761917ae69dea90fa0569210105e941ab8f7ea3292b8e7569f5b495ef7','EXACT_FIXED003_NAMESPACE490')
        proof=layout.unpack(q.json(BASE));frozen={p['path']:p for p in proof['source_pins']}
        for path in(worker.PROFILE,worker.namespace.PROBE):c.require(q.snapshots[path]==frozen[path],'ACCEPTED003_NAMESPACE_AND_BINARY_UNCHANGED')
        current=q.text('tools/p09/crossref_fixed_worker.py')
        declaration='    def _fixed_command(self,reader):return command(reader)\n\n'
        c.require(current.count(declaration)==1,'EXACT_ONE_PRIVATE_FIXED_COMMAND_HOOK')
        restored=current.replace(declaration,'').replace('args=self._fixed_command(reader);','args=command(reader);')
        r.audit.inverse(restored,q.snapshots[ARCHIVE],'WHOLE_ORIGINAL_WORKER_START_ASSIGNMENT_LIMITS_READBACK_IO_CLEANUP_UNCHANGED')
        spec=importlib.util.spec_from_file_location('capture003_worker_tests',str(c.ROOT/PYTEST));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=6,errors=0,failures=0,skipped=0),'SIX_FIXED003_WORKER_COMMAND_AND_LIFECYCLE_CONTRACTS')
        expected=set(re.findall(r'test (capture003_worker::[A-Za-z0-9_]+) \.\.\. ok',q.text(MODEL)))
        c.require(len(expected)==3,'THREE_NEW_WORKER_PROGRAM_GROUPS')
        shell=a.AcceptanceReader(Path(PS).parent,guard.check);shell.pin(Path(PS).name)
        child(MODEL,True,expected,guard,row);child(worker.TARGET,False,set(),guard,row)
        worker.namespace.require_absent(c.ROOT);shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_FIXED003_WORKER_PY6_PS3_ACTUAL_CLOSED_MODE_DENIAL_NOT_NATIVE_OR_ENTRY_READY',
            external_shell_final_fresh_hashes=shell.final_fresh_hashes,actual_missing_flag_denial_before_program_import=True,
            original_non_killing_worker_limits_and_full_lifecycle_preserved=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE003_WORKER_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cases=len(s.get('tests',[])),errors=s.get('closed_model_errors',[]),cleanup=s['cleanup'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
