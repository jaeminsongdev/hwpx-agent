"""426: original failure retained; pure transport/entry16 + PS diagnostics10, no Native."""
import hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
import run_external_crossref_fixed_batch as entry
import crossref_session_worker as candidate
import crossref_fixed_worker as fixed

OUTPUT='implementation/p09/evidence/p09-361-crossref-failure-diagnostics426.v1.json'
DRIVER='tools/p09/run_crossref_failure_diagnostics.py'
PYTEST='tools/p09/tests/test_crossref_failure_diagnostics.py'
PSTEST='implementation/p09/tools/test-crossref-session-failure-diagnostics.ps1'
ORIGINAL='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run001.v1.json'
CHANGED={'tools/p09/crossref_native_worker_io.py','tools/p09/run_external_crossref_fixed_batch.py',
    'implementation/p09/tools/run-crossref-session-qualification-worker.ps1'}
NAMES={'worker_syntax','pure_function_extracted_not_worker','rot_code_preserved','bind_code_preserved','com_hresult_without_message',
    'arbitrary_values_redacted','bounded_code_shape','wrapped_base_code_preserved','no_native_or_process_commands','actual_catch_no_authority'}


def ps_models(guard,env,row):
    shell=Path(candidate.original.SHELL);owned=capture=None;started=time.monotonic()
    step=dict(stage='new_pure_failure_diagnostics_PS10',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(shell),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/PSTEST),'-ModelsOnly'],
            windows=guard.windows,allowed_executables=[str(shell)],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<60,'STOP_DIAGNOSTICS_MODELS_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
            safe_error_codes=re.findall(r'P09_XREF_BIND_DIAGNOSTICS_[A-Z_]{1,100}',stderr),
            summary_observed='10 passed; 0 failed; 0 ignored; diagnostics_models_not_native'in stdout)
        r.c.require(step['exit_code']==0 and len(tests)==10 and {n for n,s in tests}=={'failure_diagnostics::'+n for n in NAMES}
            and all(s=='ok'for n,s in tests)and not stderr and step['summary_observed'],'ALL10_ACTUAL_PURE_PS_DIAGNOSTIC_MODELS')
    finally:
        if owned is not None:
            # This is ONLY the read-only model test process, never a Hancom or
            # qualification worker. Native no-kill ownership is unchanged.
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'DIAGNOSTICS426_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CROSSREF_FAILURE_DIAGNOSTICS426',steps=[],own_cpu_selection=selection,
        actual_Hangul_ROT_COM_or_native_started=False,qualification_or_fixed_worker_started=False,fixed_eight_executed=False,
        native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        original_failure_preserved=True,original_claim_consumed=True,remaining_owned_native_force_terminated=False,
        current_entry_source_requires_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=r.compact.unpack(q.json(entry.CODE));manifest={p['path']:p for p in old['source_pins']}
        original=r.compact.unpack(q.json(ORIGINAL))
        c.require(q.snapshots[ORIGINAL]['sha256']=='2dd57a5b8cd12d4da0b43f418258cede5b8122061b3c337da8aa2957158c59c1'
            and original['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'and original['cleanup']is False and original['fixed_eight_executed']is False
            and original['qualification_worker']['exit_code']==2,'EXACT_EXTERNAL_RUN001_FAILURE_RETAINED_UNCHANGED')
        row['original_failure']=dict(path=ORIGINAL,sha256=q.snapshots[ORIGINAL]['sha256'],phase=original['qualification_worker']['result']['phase'],
            error_code=original['qualification_worker']['result']['error_code'],cleanup=False,fixed_eight_executed=False)
        spec=importlib.util.spec_from_file_location('p09_failure_diagnostic_models',c.ROOT/PYTEST)
        models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
        paths=entry.loaded_paths()|set(candidate.SOURCES)|set(fixed.SOURCES)|{DRIVER,PYTEST,PSTEST,entry.CLAIM}
        for path in sorted(paths):
            pin=q.pin(path)
            if path in manifest and path not in CHANGED:c.require(pin==manifest[path],'UNCHANGED_NATIVE_OWNERSHIP_GUARD_AND_OTHER_EXECUTION_INPUTS')
        row['changed_execution_inputs']=sorted(CHANGED)
        class GuardedResult(unittest.TestResult):
            def stopTest(self,test):super().stopTest(test);guard.check(force=True)
        suite=unittest.defaultTestLoader.loadTestsFromModule(models);result=GuardedResult();suite.run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=16,errors=0,failures=0,skipped=0),'ALL16_PURE_TRANSPORT_AND_ENTRY_FAILURE_MODELS')
        shell=Path(candidate.original.SHELL);image=a.AcceptanceReader(shell.parent,guard.check);image.pin(shell.name)
        env=r.audit.environment();env['PYTHONDONTWRITEBYTECODE']='1';ps_models(guard,env,row)
        final_attempted=True;image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CROSSREF_FAILURE_DIAGNOSTICS_PY16_PS10_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        row.update(error_type=type(error).__name__,error_code=entry.runtime.io.safe_failure(error)['error_code'])
        if q is not None and not final_attempted:
            final_attempted=True
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[]))}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
