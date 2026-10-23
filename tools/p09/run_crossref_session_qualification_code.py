"""407: new session protocol/kernel25 + x86 transport/source10 only, never Native/qualification worker."""
import hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_session_qualification as subject
import crossref_session_worker as worker

OUTPUT='implementation/p09/evidence/p09-361-crossref-session-qualification-code407.v1.json'
DRIVER='tools/p09/run_crossref_session_qualification_code.py'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-worker-sync406.v1.json'
PYTEST='tools/p09/tests/test_crossref_session_qualification.py'
PSTEST='implementation/p09/tools/test-crossref-session-qualification-channel.ps1'
SHELL=Path(subject.owned.SHELL)
NAMES={'ready_descriptor_data_not_authority','three_phase_transport_only','denial_allows_one_failed_finish','early_closed_rejected',
    'escaped_duplicate_rejected','qualification_flag_cannot_grant_authority','different_descriptor_context_rejected',
    'unknown_reply_key_rejected','worker_source_closed_no_document_actions','absent_owner_never_cleanup_success'}


def ps_models(guard,env,row):
    c=r.c;owned=capture=None;started=time.monotonic();step=dict(stage='new_x86_session_channel_and_worker_source_models10',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/PSTEST),'-ModelsOnly'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_SESSION_MODELS_READONLY_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'(?m)^Error: (P09_XREF_[A-Z0-9_]{1,120})\r?$',stderr),
            summary_observed='10 passed; 0 failed; 0 ignored; models_and_source_only_not_native'in stdout)
        c.require(step['exit_code']==0 and len(tests)==10 and {n for n,s in tests}=={'session_channel::'+n for n in NAMES}
            and all(s=='ok'for n,s in tests)and not stderr and step['summary_observed'],'EXACT10_NEW_SESSION_TRANSPORT_SOURCE_CASES_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'SESSION_QUALIFICATION_CODE407_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_SESSION_QUALIFICATION_CODE407',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,actual_session_qualification_worker_started=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        old_successful_tests_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[BASE]['sha256']=='2d5a5f670b5ac5d0034a64558b777bdb640ad5a92335e16ad55f721b45ba7892'
            and base['state'].startswith('PASS_')and base['cleanup']and base['fresh_inputs']==base['final_fresh_hashes']==225,'EXACT406_INDEPENDENT_PREPARATION_SOURCE_CLOSURE_NOT_REEXECUTED')
        old={p['path']:p for p in base['source_pins']}
        for path in worker.SOURCES:
            pin=q.pin(path)
            if path in old:c.require(pin==old[path],'ORIGINAL_WORKER_OWNER_NATIVE_PORTS_AND_BOOTSTRAP_UNCHANGED')
        for path in(DRIVER,PYTEST,PSTEST,'tools/p09/crossref_session_qualification.py','tools/p09/crossref_session_worker.py'):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_session_qualification_contracts',c.ROOT/PYTEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':
                    relative=path.relative_to(c.ROOT).as_posix();pin=q.pin(relative)
                    if relative in old:c.require(pin==old[relative],'ALL_ACTUAL_NATIVE_GUARD_STARTUP_AND_LOADED_DEPENDENCIES_UNCHANGED')
        original=(subject.WorkerKernelLease,subject.startup.parent_without_prompt_kill,subject.startup.PreassignedNativeStartup)
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.defaultTestLoader.loadTestsFromModule(models).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=25,errors=0,failures=0,skipped=0),'EXACT25_NEW_SESSION_LIFETIME_KERNEL_GUARD_AND_FIXED_TRANSPORT_MODELS')
        c.require((subject.WorkerKernelLease,subject.startup.parent_without_prompt_kill,subject.startup.PreassignedNativeStartup)==original,
            'ORIGINAL_KERNEL_AND_NATIVE_FUNCTIONS_RESTORED_AFTER_MODELS')
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        print(json.dumps(dict(state='SESSION_CODE407_PREFLIGHT',inputs=len(q.snapshots),new_python_contracts=25,new_x86_transport_source_contracts=10,actual_native=False)),flush=True)
        env=r.audit.environment();env['PYTHONDONTWRITEBYTECODE']='1';ps_models(guard,env,row)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_SESSION_PROTOCOL_KERNEL25_X86_TRANSPORT_SOURCE10_NOT_NATIVE_SESSION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='actual_one_percent_session_worker_kernel_binding_with_pre_native_root_denial_then_external_full_entry_integration')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SESSION_CODE407_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
