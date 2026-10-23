"""404: new pure12/gate8 plus actual non-killing worker1% closed successor flow; no Native."""
import hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_preassigned_preparation as subject
import crossref_preassigned_preparation_io as live

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-preparation404.v1.json'
DRIVER='tools/p09/run_crossref_preassigned_preparation.py'
PREVIOUS='implementation/p09/evidence/p09-361-crossref-preassigned-owner-parameters402.v1.json'
PYTEST='tools/p09/tests/test_crossref_preassigned_preparation.py'
PSTEST='implementation/p09/tools/test-crossref-preassigned-preparation-gate.ps1'
SHELL=Path(subject.original.SHELL)
GATES={'exact_denial_passthrough','positive_first_never_reaches_controller','old_version_rejected','wrong_sequence_rejected',
    'escaped_duplicate_rejected','extra_field_rejected','true_native_authority_rejected','character_and_utf8_byte_bounds'}


def run_gate_models(guard,env,row):
    c=r.c;owned=capture=None;started=time.monotonic();step=dict(stage='new_preparation_gate_models8',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(c.ROOT/PSTEST),'-GateModelsOnly'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();c.require(time.monotonic()-started<90,'STOP_PREPARATION_GATE_READONLY_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'(?m)^Error: (P09_XREF_[A-Z0-9_]{1,120})\r?$',stderr),
            summary_observed='8 passed; 0 failed; 0 ignored; reader_only_not_Native'in stdout)
        c.require(step['exit_code']==0 and len(tests)==8 and {n for n,s in tests}=={'preparation_gate::'+n for n in GATES}
            and all(s=='ok'for n,s in tests)and not stderr and step['summary_observed'],'EXACT8_NEW_PREPARATION_GATE_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_PREPARATION404_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_PREPARATION404',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,readonly_worker_only=True,actual_native7_job_started=False,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        old_successful_tests_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);previous=r.compact.unpack(q.json(PREVIOUS))
        c.require(q.snapshots[PREVIOUS]['sha256']=='00b62de60e3619e1726452762e2073315681653b3caf2cf5b5229523347bc67d'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==217,
            'EXACT402_PREASSIGNED_OWNER_CURRENT21_NOT_REEXECUTED')
        old={p['path']:p for p in previous['source_pins']}
        for path in subject.SOURCE_FILES:
            pin=q.pin(path)
            if path in old:c.require(pin==old[path],'PREVIOUS_OWNER_NATIVE_PORTS_ADAPTER_AND_LIMITS_UNCHANGED')
        for path in(DRIVER,PYTEST,PSTEST,'tools/p09/crossref_preassigned_preparation.py','tools/p09/crossref_preassigned_preparation_io.py'):q.pin(path)
        spec=importlib.util.spec_from_file_location('p09_preparation_contracts',c.ROOT/PYTEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':
                    relative=path.relative_to(c.ROOT).as_posix();pin=q.pin(relative)
                    if relative in old:c.require(pin==old[relative],'UNCHANGED_ACTUAL_GUARD_PROTOCOL_AND_NATIVE_DEPENDENCIES')
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        result=GuardedResult();unittest.defaultTestLoader.loadTestsFromModule(models).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=12,errors=0,failures=0,skipped=0),'EXACT12_NEW_PREPARATION_COMMAND_AND_DENIAL_CONTRACTS')
        image=a.AcceptanceReader(SHELL.parent,guard.check);image.pin(SHELL.name)
        scratch=c.ROOT/'target/p09-crossref-preassigned-preparation-scratch-404'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PREPARATION404_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='PREPARATION404_PREFLIGHT',inputs=len(q.snapshots),new_python_models=12,new_gate_models=8,actual_worker_share_percent=1,actual_native=False)),flush=True)
        run_gate_models(guard,env,row);live.run(guard,q,env,row)
        entries=list(scratch.iterdir());c.require(len(entries)<=32,'PREPARATION404_BOUNDED_SCRATCH');row['retained_compiler_scratch_entries']=len(entries)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_PREPARATION12_GATE8_ACTUAL_NON_KILLING_WORKER1_CONTROLLER_DENIAL_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='independent_current_source_closure_then_external_jobless_native_worker_session_qualification_before_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREPARATION404_FAILURE_NO_RAW_VALUES')
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
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup','requests')},'cases':len(s.get('tests',[])),
                'result':s.get('result')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
