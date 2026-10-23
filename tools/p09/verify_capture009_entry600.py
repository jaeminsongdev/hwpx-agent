"""Generation009 current code and models only. No Hancom, COM activation or consumed-run replay.
The returned application is bound through its exact document membership; root window ownership
remains mandatory. Runtime compatibility is deliberately NOT_RUN.
"""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch009 as entry
import crossref_external009_runtime as runtime
import crossref_inline_receipt567 as layout
import search_sql_receipt as probe_layout

SELF='tools/p09/verify_capture009_entry600.py'
AUDIT='implementation/p09/evidence/p09-361-capture009-entry-code600-audit003.v1.json'
PROBE='implementation/p09/evidence/p09-361-capture009-namespace599.v1.json'
OLD='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run008.v1.json'
OLD_SHA='a16e2642e4ed5d115879f4328fdce1ba00ee6e130e71b0bb8106823c6903ecc8'
TESTS=('test_crossref_generation009_entry','test_crossref_generation009_publication','test_crossref_capture009_worker')
PS_TESTS=('test-crossref-capture009-artifact-guard.ps1','test-crossref-capture009-source-guard.ps1','test-crossref-capture009-namespace.ps1')
GRAPH_FIELDS=('returned_application_is_com','collection_bound','document_bound','windows_bound','window_bound',
    'window_handle_matches','window_pid_matches','single_document','version_matches')
def run_ps_models(path,expected,guard,row):
    ps=runtime.original.candidate.original.SHELL;owned=capture=None;started=time.monotonic()
    step=dict(stage=path,cleanup=False);row['steps'].append(step)
    try:
        call="try { & '"+str(r.c.ROOT/path)+"' -ModelsOnly } catch { if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {[Console]::Error.WriteLine($_.Exception.Message)};[Console]::Error.WriteLine('P600_MODEL_RUNTIME_'+$_.Exception.GetType().Name+'_LINE_'+$_.InvocationInfo.ScriptLineNumber);exit 1 }"
        args=[ps,'-NoLogo','-NoProfile','-NonInteractive','-STA','-Command',call]
        env=r.audit.environment();env.update(SystemRoot=str(Path(ps).parents[3]),PSModulePath=str(Path(ps).parent/'Modules'))
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[ps],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<30,'P600_MODELS_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        found=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',out)
        step.update(exit_code=owned.returncode,tests=found,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            closed_model_errors=re.findall(r'P09_XREF_BIND_[A-Z_]+',out+'\n'+err)[:4],
            model_runtime_errors=re.findall(r'P600_MODEL_RUNTIME_[A-Za-z0-9]+_LINE_[0-9]{1,6}',err)[:4])
        r.c.require(owned.returncode==0 and not err and len(found)==len(expected)and {n for n,s in found}==expected
            and all(s=='ok'for n,s in found),'P600_ALL_EXACT_WINDOWS_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-models-only'],'P600_MODELS_ONLY')
    c.require(not(c.ROOT/AUDIT).exists()and not(c.ROOT/entry.NAMES['code']).exists(),'P600_IMMUTABLE_CODE_PROOF')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;passed=False;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE009_ENTRY_CODE_MODELS',generation=9,steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,consumed001_to007_replayed=False,
        source_write_sharing_relaxed=False,external009_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=layout.unpack(q.json(OLD));probe=probe_layout.unpack(q.json(PROBE))
        c.require(q.snapshots[OLD]['sha256']==OLD_SHA and old['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'
            and old['cleanup']is True and old['fixed_eight_executed']is False
            and old['fixed_worker']['result']['completed_callback_cases']==0
            and old['fixed_worker']['result']['case_failure']['error_code']=='P09_XREF_BIND_ARTIFACT_FAILED_NO_RAW_VALUES',
            'P600_CONSUMED007_FAILURE_PRESERVED')
        c.require(probe['cleanup']is True and probe['fresh_inputs']==probe['final_fresh_hashes']>0
            and probe['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P600_CURRENT595_WITHOUT_BODY_REPLAY')
        for pin in probe['source_pins']:
            if pin['path']in('crates/product-cli/examples/p09_crossref_discovery_probe.rs',
                'crates/product-cli/examples/p09_crossref_capture009_probe.rs','tools/p09/crossref_capture009_namespace.py'):
                c.require(q.pin(pin['path'])==pin,'P600_CURRENT_COMPILED_SOURCE')
        c.require(q.pin(runtime.capture.namespace.PROBE)==probe['compiled_probe'],'P600_CURRENT_COMPILED_PROBE')
        paths=entry.loaded_paths(exclude=(SELF,))|runtime.CASE_PATHS|set(runtime.fixed_input_pins())|{entry.SELF,runtime.SELF}
        old_files=('tools/p09/run_external_crossref_fixed_batch008.py','tools/p09/crossref_external008_runtime.py',
            'tools/p09/crossref_capture008_worker.py','tools/p09/crossref_generation008_publication.py',
            'implementation/p09/tools/crossref-capture008-source-guard.ps1',
            'implementation/p09/tools/crossref-capture008-application-binding.ps1')
        names=paths|{SELF,PROBE,OLD,*old_files,
            *['tools/p09/tests/'+n+'.py'for n in TESTS],*['implementation/p09/tools/'+n for n in PS_TESTS]}
        for name in sorted(names):q.pin(name)
        oldpins={p['path']:p for p in old['source_pins']}
        for name in old_files:c.require(q.pin(name)==oldpins[name],'P600_CONSUMED007_INPUTS_BYTE_EXACT')
        c.require(q.text(runtime.SELF).replace('009','008')==q.text('tools/p09/crossref_external008_runtime.py'),
            'P600_WHOLE16_SESSIONS40_ARTIFACTS_AND_CASE_BOUNDARIES_INVERSE')
        for name,(size,sha)in runtime.fixed_input_pins().items():
            pin=q.pin(name);c.require((pin['bytes'],pin['sha256'])==(size,sha),'P600_FIXED_INPUTS')
        shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        row['external_shell_pins']=[shell.pin(Path(runtime.original.candidate.original.SHELL).name)]
        before={name:(c.ROOT/name).exists()for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['preflight'],entry.publication.SPOOL)}
        c.require(not any(before.values()),'P600_UNUSED009_NAMESPACE')
        prior_name='implementation/p09/evidence/p09-361-capture008-entry-code596.v1.json'
        prior=layout.unpack(q.json(prior_name));prior_pins={p['path']:p for p in prior['source_pins']}
        c.require(q.snapshots[prior_name]['sha256']=='09162bfc8d056c3d245ac1ff51f15e1d5a9c5b045cc7986078052f49d9530a04'
            and prior['cleanup']is True and prior['state']=='PASS_CAPTURE008_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE',
            'P600_VERIFIED008_APPLICATION_MODELS_NOT_NATIVE_OR_GATE')
        app_test='implementation/p09/tools/test-crossref-capture008-application-binding.ps1'
        app=next(s for s in prior['retained_windows_model_steps']if s['stage']==app_test)
        c.require(len(app['cases'])==19 and all(status=='ok'for name,status in app['cases']),'P600_EXACT19_RETAINED_APPLICATION_MODELS')
        for name in(app_test,'implementation/p09/tools/sdk-baseline-owned-session.ps1',
                'implementation/p09/tools/crossref-owned-active-source.ps1',
                'implementation/p09/tools/crossref-capture008-application-binding.ps1'):
            c.require(q.pin(name)==prior_pins[name],'P600_RETAINED_APPLICATION_MODEL_INPUT_UNCHANGED')
        c.require(row['external_shell_pins']==prior['external_shell_pins'],'P600_RETAINED_APPLICATION_WINDOWS_IMAGE')
        row['retained_windows_model_steps']=[dict(stage=app_test,cases=app['cases'],receipt=q.snapshots[prior_name],reexecuted=False)]
        for name in PS_TESTS:
            path='implementation/p09/tools/'+name;text=q.text(path)
            expected=set(re.findall(r"WriteLine\('test ([a-z0-9_:]+) \.\.\. ok'\)",text))
            
            c.require(len(expected)==(10 if 'artifact-guard'in name else 6 if 'source-guard'in name else 5),'P600_EXACT_WINDOWS_MODEL_COUNT')
            run_ps_models(path,expected,guard,row)
        result=unittest.TestResult()
        for index,name in enumerate(TESTS):
            path='tools/p09/tests/'+name+'.py';ast.parse(q.text(path))
            spec=importlib.util.spec_from_file_location('capture009_models_'+str(index),c.ROOT/path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=50,errors=0,failures=0,skipped=0),'P600_ALL50_CURRENT_GENERATION_CONTRACTS')
        c.require(all(not(c.ROOT/name).exists()for name in before),'P600_NO_NATIVE_NAMESPACE_CREATED_BY_MODELS')
        runtime.absent_attempts();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(paths),external_shell_final_hashes=shell.final_fresh_hashes,
            preserved008_receipt_sha256=OLD_SHA,retained_probe_receipt_sha256=q.snapshots[PROBE]['sha256'],real_windows_models=40,
            returned_document_membership_and_owned_root_windows_required=True,saved_read_lease_before_original_fresh_open_required=True,
            actual_returned_application_graph_and_Hancom_save_reopen_compatibility='NOT_RUN');passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,RecursionError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P600_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        audit=shared.publisher.publish(c.ROOT,AUDIT,layout.pack(row),NS(require=c.require,exact=a.exact));canonical=None
        if passed and row['cleanup']:canonical=shared.publisher.publish(c.ROOT,entry.NAMES['code'],layout.pack(dict(row,code_audit_receipt=audit)),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s.get('cleanup'),closed_model_errors=s.get('closed_model_errors'),model_runtime_errors=s.get('model_runtime_errors'))for s in row['steps']],
            'audit':audit,'canonical_code_proof':canonical}),flush=True)
    return 0 if passed and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
