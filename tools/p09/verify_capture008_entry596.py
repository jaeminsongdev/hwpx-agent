"""Generation008 current code and models only. No Hancom, COM activation or consumed-run replay.
The returned application is bound through its exact document membership; root window ownership
remains mandatory. Runtime compatibility is deliberately NOT_RUN.
"""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch008 as entry
import crossref_external008_runtime as runtime
import crossref_inline_receipt567 as layout
import search_sql_receipt as probe_layout

SELF='tools/p09/verify_capture008_entry596.py'
AUDIT='implementation/p09/evidence/p09-361-capture008-entry-code596-audit002.v1.json'
PROBE='implementation/p09/evidence/p09-361-capture008-namespace595-validated.v1.json'
OLD='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run007.v1.json'
OLD_SHA='8d5cf7c58b6e9d8346eb1131c5403644c68a3a22087b84449d8ec7cec439d518'
TESTS=('test_crossref_generation008_entry','test_crossref_generation008_publication','test_crossref_capture008_worker')
PS_TESTS=('test-crossref-capture008-application-binding.ps1','test-crossref-capture008-source-guard.ps1','test-crossref-capture008-namespace.ps1')
GRAPH_FIELDS=('returned_application_is_com','collection_bound','document_bound','windows_bound','window_bound',
    'window_handle_matches','window_pid_matches','single_document','version_matches')
def run_ps_models(path,expected,guard,row):
    ps=runtime.original.candidate.original.SHELL;owned=capture=None;started=time.monotonic()
    step=dict(stage=path,cleanup=False);row['steps'].append(step)
    try:
        call="try { & '"+str(r.c.ROOT/path)+"' -ModelsOnly } catch { if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {[Console]::Error.WriteLine($_.Exception.Message)};[Console]::Error.WriteLine('P596_MODEL_RUNTIME_'+$_.Exception.GetType().Name+'_LINE_'+$_.InvocationInfo.ScriptLineNumber);exit 1 }"
        args=[ps,'-NoLogo','-NoProfile','-NonInteractive','-STA','-Command',call]
        env=r.audit.environment();env.update(SystemRoot=str(Path(ps).parents[3]),PSModulePath=str(Path(ps).parent/'Modules'))
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[ps],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<30,'P596_MODELS_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        found=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',out)
        step.update(exit_code=owned.returncode,tests=found,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            closed_model_errors=re.findall(r'P09_XREF_BIND_[A-Z_]+',out+'\n'+err)[:4],
            model_runtime_errors=re.findall(r'P596_MODEL_RUNTIME_[A-Za-z0-9]+_LINE_[0-9]{1,6}',err)[:4])
        r.c.require(owned.returncode==0 and not err and len(found)==len(expected)and {n for n,s in found}==expected
            and all(s=='ok'for n,s in found),'P596_ALL_EXACT_WINDOWS_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-models-only'],'P596_MODELS_ONLY')
    c.require(not(c.ROOT/AUDIT).exists()and not(c.ROOT/entry.NAMES['code']).exists(),'P596_IMMUTABLE_CODE_PROOF')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;passed=False;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE008_ENTRY_CODE_MODELS',generation=8,steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,consumed001_to007_replayed=False,
        source_write_sharing_relaxed=False,external008_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=layout.unpack(q.json(OLD));probe=probe_layout.unpack(q.json(PROBE))
        c.require(q.snapshots[OLD]['sha256']==OLD_SHA and old['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'
            and old['cleanup']is True and old['fixed_eight_executed']is False
            and old['fixed_worker']['result']['completed_callback_cases']==0
            and old['fixed_worker']['result']['case_failure']['error_code']=='P09_XREF_BIND_CAPTURE_SEVEN_APPLICATION_REAL_WINDOWS',
            'P596_CONSUMED007_FAILURE_PRESERVED')
        c.require(probe['cleanup']is True and probe['fresh_inputs']==probe['final_fresh_hashes']>0
            and probe['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P596_CURRENT595_WITHOUT_BODY_REPLAY')
        for pin in probe['source_pins']:
            if pin['path']in('crates/product-cli/examples/p09_crossref_discovery_probe.rs',
                'crates/product-cli/examples/p09_crossref_capture008_probe.rs','tools/p09/crossref_capture008_namespace.py'):
                c.require(q.pin(pin['path'])==pin,'P596_CURRENT_COMPILED_SOURCE')
        c.require(q.pin(runtime.capture.namespace.PROBE)==probe['compiled_probe'],'P596_CURRENT_COMPILED_PROBE')
        paths=entry.loaded_paths(exclude=(SELF,))|runtime.CASE_PATHS|set(runtime.fixed_input_pins())|{entry.SELF,runtime.SELF}
        old_files=('tools/p09/run_external_crossref_fixed_batch007.py','tools/p09/crossref_external007_runtime.py',
            'tools/p09/crossref_capture007_worker.py','tools/p09/crossref_generation007_publication.py',
            'implementation/p09/tools/crossref-capture007-source-guard.ps1',
            'implementation/p09/tools/crossref-capture007-application-binding.ps1')
        names=paths|{SELF,PROBE,OLD,*old_files,
            *['tools/p09/tests/'+n+'.py'for n in TESTS],*['implementation/p09/tools/'+n for n in PS_TESTS]}
        for name in sorted(names):q.pin(name)
        oldpins={p['path']:p for p in old['source_pins']}
        for name in old_files:c.require(q.pin(name)==oldpins[name],'P596_CONSUMED007_INPUTS_BYTE_EXACT')
        c.require(q.text(runtime.SELF).replace('008','007')==q.text('tools/p09/crossref_external007_runtime.py'),
            'P596_WHOLE16_SESSIONS40_ARTIFACTS_AND_CASE_BOUNDARIES_INVERSE')
        for name,(size,sha)in runtime.fixed_input_pins().items():
            pin=q.pin(name);c.require((pin['bytes'],pin['sha256'])==(size,sha),'P596_FIXED_INPUTS')
        shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        row['external_shell_pins']=[shell.pin(Path(runtime.original.candidate.original.SHELL).name)]
        before={name:(c.ROOT/name).exists()for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['preflight'],entry.publication.SPOOL)}
        c.require(not any(before.values()),'P596_UNUSED008_NAMESPACE')
        retained_name='implementation/p09/evidence/p09-361-capture008-entry-code596-audit001.v1.json'
        retained=layout.unpack(q.json(retained_name))
        c.require(q.snapshots[retained_name]['sha256']=='752b473b32d31e169e586409af3a20730f023147895fee03bed12086f87cd780'
            and retained['state']=='FAILED_CAPTURE008_ENTRY_CODE_MODELS' and retained['cleanup']is True
            and retained['contracts']==dict(run=50,errors=1,failures=0,skipped=0)
            and retained['failed_contract_names']==['capture008_models_1.Publication.test_preserved003_values_round_trip_only_in_synthetic_temporary008_namespace'],
            'P596_ORIGINAL_WHOLE_FAILED_NOT_PROMOTED')
        changed_test='tools/p09/tests/test_crossref_generation008_publication.py'
        originals={p['path']:p for p in retained['source_pins']}
        for name,pin in originals.items():
            if name not in(SELF,changed_test):c.require(q.pin(name)==pin,'P596_ALL_RETAINED_MODEL_PARENT_INPUTS_FRESH_UNCHANGED')
        for name,archive in((SELF,'implementation/p09/source-archive/p361-capture008-entry596/verifier001.py'),
                (changed_test,'implementation/p09/source-archive/p361-capture008-entry596/publication-model001.py')):
            original_text=q.text(archive).replace('\r\n','\n')
            c.require(originals[name]['sha256']in(hashlib.sha256(original_text.encode()).hexdigest(),
                hashlib.sha256(original_text.replace('\n','\r\n').encode()).hexdigest()),'P596_VERIFIED_RETAINED_SOURCE_PREIMAGE')
        prior_test=q.text('implementation/p09/source-archive/p361-capture008-entry596/publication-model001.py')
        current_test=q.text(changed_test)
        c.require(prior_test.count("value['generation']=7")==1 and current_test.replace("value['generation']=8","value['generation']=7")==prior_test,
            'P596_ONLY_FAILED_PUBLICATION_FIXTURE_GENERATION_CHANGED')
        def method(text,name):
            tree=ast.parse(text);return ast.get_source_segment(text,next(n for n in ast.walk(tree)
                if isinstance(n,ast.FunctionDef)and n.name==name))
        previous_executor=q.text('implementation/p09/source-archive/p361-capture008-entry596/verifier001.py')
        c.require(method(q.text(SELF),'run_ps_models')==method(previous_executor,'run_ps_models')
            and row['external_shell_pins']==retained['external_shell_pins'],'P596_UNCHANGED_WINDOWS_EXECUTOR_ENVIRONMENT_AND_IMAGE')
        row['retained_windows_model_steps']=[]
        for name in PS_TESTS:
            path='implementation/p09/tools/'+name;text=q.text(path)
            expected=set(re.findall(r"WriteLine\('test ([a-z0-9_:]+) \.\.\. ok'\)",text))
            if 'application-binding'in name:expected|={'capture008_application::reject_false_'+v for v in GRAPH_FIELDS}
            step=next(s for s in retained['steps']if s['stage']==path)
            c.require(step['exit_code']==0 and step['cleanup']is True and step['stderr_bytes']==0
                and len(step['tests'])==len(expected) and {n for n,s in step['tests']}==expected
                and all(s=='ok'for n,s in step['tests']),'P596_EXACT30_RETAINED_WINDOWS_MODEL_BODIES')
            row['retained_windows_model_steps'].append(dict(stage=path,cases=step['tests'],
                receipt=q.snapshots[retained_name],reexecuted=False))
        spec=importlib.util.spec_from_file_location('capture008_publication_delta',c.ROOT/changed_test)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        test_name='test_preserved003_values_round_trip_only_in_synthetic_temporary008_namespace'
        result=unittest.TestResult();module.Publication(test_name).run(result)
        delta=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['delta_contracts']=delta;row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(delta==dict(run=1,errors=0,failures=0,skipped=0),'P596_CHANGED_ONE_PUBLICATION_MODEL_PASSES')
        row.update(contracts=dict(run=50,errors=0,failures=0,skipped=0),retained_python_passes=49,
            python_test_bodies_executed_this_run=1,retained_model_receipt=q.snapshots[retained_name],
            retained_whole_failure_promoted=False,windows_model_bodies_reexecuted=False)
        c.require(all(not(c.ROOT/name).exists()for name in before),'P596_NO_NATIVE_NAMESPACE_CREATED_BY_MODELS')
        runtime.absent_attempts();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(paths),external_shell_final_hashes=shell.final_fresh_hashes,
            preserved007_receipt_sha256=OLD_SHA,retained_probe_receipt_sha256=q.snapshots[PROBE]['sha256'],real_windows_models=30,
            returned_document_membership_and_owned_root_windows_required=True,
            actual_returned_application_graph_and_Hancom_save_reopen_compatibility='NOT_RUN');passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,RecursionError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P596_FAILURE_NO_RAW_VALUES')
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
