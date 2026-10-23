"""Fixed004 worker/entry composition; new models and missing-flag denial only, no Native or case capture."""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_external_batch_runtime as runtime
import crossref_capture004_worker as worker
import search_sql_receipt as baseline_codec
SELF='tools/p09/verify_crossref_generation004551.py'
OUTPUT=entry.generation_names(current004=True)['code']
BASE='implementation/p09/evidence/p09-361-capture004-namespace549.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-capture004-entry551/'
ENTRY='tools/p09/run_external_crossref_fixed_batch.py'
RUNTIME='tools/p09/crossref_external_batch_runtime.py'
MODELS=('tools/p09/tests/test_crossref_generation004.py','tools/p09/tests/test_crossref_capture004_worker.py')
PSFILES=('crossref-capture004-namespace.ps1','crossref-capture004-worker-program.ps1','run-crossref-capture004-worker.ps1',
    'test-crossref-capture004-worker-program.ps1','test-crossref-capture004-namespace.ps1')
PS='C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,r.c.ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def restore_entry(text):
    text=text.replace('*,current003=False,current004=False','*,current003=False')
    a=text.index("    r.c.require(type(current004)is bool");b=text.index('    if current003:return',a);text=text[:a]+text[b:]
    text=text.replace("    group.add_argument('--preflight-generation-004',action='store_true')\n",'').replace("    group.add_argument('--execute-generation-004-fixed-eight',action='store_true')\n",'')
    a=text.index('    if args.preflight_generation_004');b=text.index('    if args.preflight_generation_003',a);text=text[:a]+text[b:]
    text=text.replace(',current_generation004=False','')
    text=text.replace(",**({'current004':True}if current_generation004 else{})",'').replace("    runtime.require(type(current_generation004)is bool,'EXACT_CAPTURE004_SCOPE_FLAG')\n",'')
    text=text.replace(",**({'capture004_scope':True}if current_generation004 else{})",'')
    text=text.replace('    current004=args.preflight_generation_004 or args.execute_generation_004_fixed_eight\n','')
    text=text.replace(' or args.preflight_generation_004','').replace(' or args.execute_generation_004_fixed_eight','')
    text=text.replace(",**({'current004':True}if current004 else{})",'').replace('generation=4 if current004 else ','generation=')
    text=text.replace('        if current004:proof,manifest,paths=load_manifest(q,require_runtime_ready=execute,current_generation004=True)\n        elif current003:', '        if current003:')
    text=text.replace('        if current004:runtime.absent_attempts(fixed_capture004=True)\n        elif current003:', '        if current003:')
    text=text.replace('            if current004:artifacts=runtime.execute(guard,manifest,paths,shell_expected,env,notify,row,fixed_capture004=True)\n            elif current003:', '            if current003:')
    return text
def restore_runtime(text):
    text=text.replace('import crossref_capture004_worker as capture004\n','')
    text=text.replace("CAPTURE004_CASE_PATHS=CASE_PATHS|set(capture004.SOURCES)|{'tools/p09/crossref_capture004_namespace.py','tools/p09/crossref_capture004_worker.py'}\n",'')
    text=text.replace('capture003_scope=False,*,capture004_scope=False','capture003_scope=False').replace(',fixed_capture004=False','')
    text=text.replace("    require(type(capture004_scope)is bool and not(capture003_scope and capture004_scope),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')\n",'')
    text=text.replace('    if capture004_scope:return {**INPUT_PINS,capture004.namespace.PROBE:capture004.PROBE_PIN}\n','')
    text=text.replace("        require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')\n",'')
    text=text.replace("    require(type(fixed_capture004)is bool and not(fixed_capture003 and fixed_capture004),'EXACT_EXCLUSIVE_CAPTURE004_SCOPE_FLAG')\n",'')
    text=text.replace('    if fixed_capture004:return capture004.namespace.require_absent(r.c.ROOT)\n','')
    text=text.replace('fixed_pins={**fixed_input_pins(True),**fixed_input_pins(capture004_scope=True)}','fixed_pins=fixed_input_pins(True)')
    text=text.replace('self.paths=CAPTURE004_CASE_PATHS if fixed_capture004 else ','self.paths=')
    text=text.replace('base=capture004.namespace.directory(index)if fixed_capture004 else ','base=')
    text=text.replace("    if fixed_capture004:require(CAPTURE004_CASE_PATHS<=set(all_paths),'COMPLETE_CAPTURE004_INPUT_CLOSURE')\n",'')
    text=text.replace('check_attempts=(lambda:absent_attempts(fixed_capture004=True))if fixed_capture004 else ','check_attempts=')
    text=text.replace(",**({'fixed_capture004':True}if fixed_capture004 else{})",'')
    text=text.replace('full=capture004.Fixed004Worker(guard)if fixed_capture004 else ','full=')
    text=text.replace("record['artifacts']=capture_artifacts(guard,host,fixed_capture004=True)if fixed_capture004 else ","record['artifacts']=")
    return text
def child(script,models,expected,guard,row):
    owned=capture=None;started=time.monotonic();step=dict(stage=script,cleanup=False);row['steps'].append(step)
    try:
        args=[PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/script)]+(['-ModelsOnly']if models else[])
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[PS],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<90,'P551_MODEL_CHILD_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            closed_model_errors=re.findall(r'(?m)^Error: (P09_XREF_BIND_[A-Z_]+)\r?$',stdout))
        if models:r.c.require(owned.returncode==0 and not stderr and {n for n,s in tests}==expected and len(tests)==len(expected)and all(s=='ok'for n,s in tests),'P551_ALL_EXACT_PS_MODELS')
        else:
            value=json.loads(stdout);r.c.require(owned.returncode==2 and not stderr and value['phase']=='closed_mode'
                and value['error_code']=='P09_XREF_BIND_CAPTURE_FOUR_FIXED_MODE_REQUIRED'and value['completed_callback_cases']==0
                and value['retained_live_or_uncertain_owners']==0 and value['probe_lease_closed']is True and value['native_execution_authorized']is False,'P551_ACTUAL004_MISSING_FLAG_DENIED_BEFORE_NATIVE_IMPORT')
            step['closed_mode_result']=value
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-and-closed-mode-only'],'P551_NO_NATIVE_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P551_IMMUTABLE_CODE_PROOF')
    modules=[load(path,'capture004_models_'+str(i))for i,path in enumerate(MODELS)]
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=shell=None
    row=dict(state='FAILED_CAPTURE004_WORKER_ENTRY_CODE',steps=[],own_cpu_selection=selection,generation=4,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,fixed_eight_executed=False,native_startup_qualified=False,new_native_execution_authorized=False,
        official249_or_003_or_Native_or_previous_models_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);worker.namespace.require_absent(c.ROOT)
        entry_paths=entry.loaded_paths(exclude=(SELF,))|set(worker.SOURCES)|runtime.CAPTURE004_CASE_PATHS
        names=entry_paths|{SELF,BASE,ENTRY,RUNTIME,*MODELS,ARCHIVE+'entry-before.py',ARCHIVE+'runtime-before.py',
            'tools/p09/crossref_capture003_worker.py','tools/p09/crossref_fixed_worker.py',
            'implementation/p09/evidence/p09-361-startup15-applied548.v1.json'}
        names|={'implementation/p09/tools/'+name for name in PSFILES}
        names|={'implementation/p09/tools/'+name.replace('004','003')for name in PSFILES}
        for path in sorted(names):q.pin(path)
        base=baseline_codec.unpack(q.json(BASE));c.require(q.snapshots[BASE]['sha256']=='0d87ed05c43b4c10402cbc9f88431db1d6aef02878f9d9b9e3a562a83258e5a8'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==848,'P551_EXACT549_READONLY_NAMESPACE_CLOSURE')
        c.require(q.snapshots[worker.namespace.PROBE]==base['fixed004_binary'],'P551_SAME_QUALIFIED004_BINARY')
        r.audit.inverse(restore_entry(q.text(ENTRY)),q.snapshots[ARCHIVE+'entry-before.py'],'P551_WHOLE_OLD_ENTRY_CLAIM_PREREQUISITES_CLOSURE_AND_FAILURE_BODY_PRESERVED')
        r.audit.inverse(restore_runtime(q.text(RUNTIME)),q.snapshots[ARCHIVE+'runtime-before.py'],'P551_WHOLE_OLD_CURRENT_SESSION_HANDOFF_CASE_LIFETIME_AND_CAPTURE_CHECKS_PRESERVED')
        for name in PSFILES:
            current=q.text('implementation/p09/tools/'+name)
            for term in('capture004','Capture004','Fixed004','fixed004'):current=current.replace(term,term.replace('004','003'))
            current=current.replace('-g004-','-g003-').replace('CAPTURE_FOUR','CAPTURE_THREE').replace('20261022-g003','20261021-g003')
            current=current.replace('5149696','5148672').replace('e64128bec14686aaecde8bafaf34458b59a4c694fe2b0a54f411d013b0a01551','b9bc121660a649485ca6a25d6fd91a8f3e77c97019de7f35168d0db375325900')
            c.require(current.rstrip()==q.text('implementation/p09/tools/'+name.replace('004','003')).rstrip(),'P551_ONLY_CLOSED_PS_NAMESPACE_BINARY_PIN_AND_NAMES_CHANGED')
        cases=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module)for module in modules);c.require(cases.countTestCases()==33,'P551_NEW_GENERATION27_WORKER6_MODELS')
        result=unittest.TestResult();cases.run(result);row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=33,errors=0,failures=0,skipped=0),'P551_ALL_NEW004_MODELS_PASS')
        for path in(SELF,ENTRY,RUNTIME,*MODELS,'tools/p09/crossref_capture004_worker.py'):ast.parse(q.text(path))
        shell=a.AcceptanceReader(Path(PS).parent,guard.check);shell.pin(Path(PS).name)
        for name,count in(('test-crossref-capture004-namespace.ps1',5),('test-crossref-capture004-worker-program.ps1',3)):
            script='implementation/p09/tools/'+name;expected=set(re.findall(r'test (capture004_[A-Za-z_:0-9]+) \.\.\. ok',q.text(script)))
            c.require(len(expected)==count,'P551_EXACT_PS_TEST_INVENTORY');child(script,True,expected,guard,row)
        child(worker.TARGET,False,set(),guard,row)
        worker.namespace.require_absent(c.ROOT);shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(entry_paths),external_shell_pins=list(shell.snapshots.values()),
            external_shell_final_fresh_hashes=shell.final_fresh_hashes,worker_namespace_PS_models=8,actual_missing_flag_denial_before_import=True,
            live_session_qualification_and_current_ready_package_still_required=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P551_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=entry.publish(OUTPUT,row);print(json.dumps({**{k:v for k,v in row.items()if k not in('source_pins','resource_samples','entry_dependency_paths','external_shell_pins','steps')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],closed_model_errors=s.get('closed_model_errors',[]))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
