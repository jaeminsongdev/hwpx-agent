"""Fixed007 current code/models only. No Hancom, Native, claim or old-run replay.

New generation inputs are exercised once; no 249 queue/product bodies execute.
The former raw application pointer equality is replaced by nine owned-graph
requirements. Runtime compatibility remains NOT_RUN until external007.
"""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch007 as entry
import crossref_external007_runtime as runtime
import crossref_inline_receipt567 as layout
import search_sql_receipt as probe_layout

SELF='tools/p09/verify_capture007_entry592.py'
AUDIT='implementation/p09/evidence/p09-361-capture007-entry-code592-audit003.v1.json'
PROBE='implementation/p09/evidence/p09-361-capture007-namespace591.v1.json'
OLD='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run006.v1.json'
OLD_SHA='33455bc9d69b95ce2940f494383d0ed4aa749d5991f029ced2a7f8789d98703a'
PDF='implementation/p00/source-archive/original/automation/HwpAutomation_2504.pdf'
GRAPH='implementation/p09/tools/crossref-capture007-application-binding.ps1'
TESTS=('test_crossref_generation007_entry','test_crossref_generation007_publication','test_crossref_capture007_worker')
PS_TESTS=('test-crossref-capture007-application-binding.ps1','test-crossref-capture007-source-guard.ps1','test-crossref-capture007-namespace.ps1')
GRAPH_FIELDS=('returned_application_is_com','collection_bound','document_bound','windows_bound','window_bound',
    'window_handle_matches','window_pid_matches','single_document','version_matches')

def run_ps_models(path,expected,guard,row):
    ps=runtime.original.candidate.original.SHELL;owned=capture=None;started=time.monotonic()
    step=dict(stage=path,cleanup=False);row['steps'].append(step)
    try:
        call="try { & '"+str(r.c.ROOT/path)+"' -ModelsOnly } catch { if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {[Console]::Error.WriteLine($_.Exception.Message)};[Console]::Error.WriteLine('P592_MODEL_RUNTIME_'+$_.Exception.GetType().Name+'_LINE_'+$_.InvocationInfo.ScriptLineNumber);exit 1 }"
        args=[ps,'-NoLogo','-NoProfile','-NonInteractive','-STA','-Command',call]
        env=r.audit.environment();env.update(SystemRoot=str(Path(ps).parents[3]),PSModulePath=str(Path(ps).parent/'Modules'))
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[ps],cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<30,'P592_MODELS_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        found=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',out)
        step.update(exit_code=owned.returncode,tests=found,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            closed_model_errors=re.findall(r'P09_XREF_BIND_[A-Z_]+',out+'\n'+err)[:4],
            model_runtime_errors=re.findall(r'P592_MODEL_RUNTIME_[A-Za-z0-9]+_LINE_[0-9]{1,6}',err)[:4])
        r.c.require(owned.returncode==0 and not err and len(found)==len(expected)and {n for n,s in found}==expected
            and all(s=='ok'for n,s in found),'P592_ALL_EXACT_WINDOWS_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--code-models-only'],'P592_MODELS_ONLY')
    c.require(not(c.ROOT/AUDIT).exists()and not(c.ROOT/entry.NAMES['code']).exists(),'P592_IMMUTABLE_CODE_PROOF')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;passed=False;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE007_ENTRY_CODE_MODELS',generation=7,steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,consumed001_to006_replayed=False,
        source_write_sharing_relaxed=False,external007_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=layout.unpack(q.json(OLD));probe=probe_layout.unpack(q.json(PROBE))
        c.require(q.snapshots[OLD]['sha256']==OLD_SHA and old['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'
            and old['cleanup']is True and old['fixed_eight_executed']is False
            and old['fixed_worker']['result']['case_failure']['error_code']=='P09_XREF_BIND_SOURCE_DOCUMENT_APPLICATION_IDENTITY_MISMATCH',
            'P592_CONSUMED006_FAILURE_PRESERVED_NOT_REINTERPRETED')
        c.require(probe['cleanup']is True and probe['fresh_inputs']==probe['final_fresh_hashes']>0
            and probe['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P592_CURRENT591_NO_READONLY_BODY_REPLAY')
        for pin in probe['source_pins']:
            if pin['path']in('crates/product-cli/examples/p09_crossref_discovery_probe.rs',
                'crates/product-cli/examples/p09_crossref_capture007_probe.rs','tools/p09/crossref_capture007_namespace.py'):
                c.require(q.pin(pin['path'])==pin,'P592_CURRENT_COMPILED_SOURCE')
        c.require(q.pin(runtime.capture.namespace.PROBE)==probe['compiled_probe'],'P592_CURRENT_COMPILED_PROBE')
        paths=entry.loaded_paths(exclude=(SELF,))|runtime.CASE_PATHS|set(runtime.fixed_input_pins())|{entry.SELF,runtime.SELF}
        names=paths|{SELF,PROBE,OLD,PDF,GRAPH,'target/p09-capture007-documentation/application-page47.png',
            *['tools/p09/tests/'+n+'.py'for n in TESTS],*['implementation/p09/tools/'+n for n in PS_TESTS],
            'tools/p09/run_external_crossref_fixed_batch006.py','tools/p09/crossref_external006_runtime.py',
            'tools/p09/crossref_capture006_worker.py','tools/p09/crossref_generation006_publication.py',
            'implementation/p09/tools/crossref-capture006-source-guard.ps1'}
        for name in sorted(names):q.pin(name)
        c.require(q.snapshots[PDF]['sha256']=='917142de2704ae037b0132f5a344ce5331b1fd96cc19dd574666aaacfbf0268c','P592_OFFICIAL_PDF_VISUALLY_REVIEWED_PAGE47')
        oldpins={p['path']:p for p in old['source_pins']}
        for name in('tools/p09/run_external_crossref_fixed_batch006.py','tools/p09/crossref_external006_runtime.py',
            'tools/p09/crossref_capture006_worker.py','tools/p09/crossref_generation006_publication.py',
            'implementation/p09/tools/crossref-capture006-source-guard.ps1'):
            c.require(q.pin(name)==oldpins[name],'P592_CONSUMED006_CODE_UNCHANGED')
        current=q.text(runtime.SELF).replace('\r\n','\n').replace('007','006')
        c.require(current==q.text('tools/p09/crossref_external006_runtime.py').replace('\r\n','\n'),
            'P592_WHOLE16_SESSIONS40_ARTIFACTS_AND_CASE_SOURCE_BOUNDARIES_INVERSE')
        for name,(size,sha)in runtime.fixed_input_pins().items():
            pin=q.pin(name);c.require((pin['bytes'],pin['sha256'])==(size,sha),'P592_FIXED_INPUTS')
        for name in('implementation/p09/tools/crossref-capture007-namespace.ps1',
            'implementation/p09/tools/test-crossref-capture007-namespace.ps1','tools/p09/tests/test_crossref_capture007_worker.py'):
            c.require(runtime.capture.PROBE_PIN[1]in q.text(name),'P592_ACTUAL_PROBE_HASH_IN_ALL_NEW_LANGUAGE_BINDINGS')
        before={name:(c.ROOT/name).exists()for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['preflight'],entry.publication.SPOOL)}
        c.require(not any(before.values()),'P592_UNUSED007_NAMESPACE')
        shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        row['external_shell_pins']=[shell.pin(Path(runtime.original.candidate.original.SHELL).name)]
        retained_path='implementation/p09/evidence/p09-361-capture007-entry-code592-audit001.v1.json'
        retained=layout.unpack(q.json(retained_path));priorpins={p['path']:p for p in retained['source_pins']}
        c.require(q.snapshots[retained_path]['sha256']=='38bf4851aa509cc74fa8764c938d21b69db625c8dd52152ffb7326a78ad7de21'
            and retained['state']=='FAILED_CAPTURE007_ENTRY_CODE_MODELS'and retained['cleanup']is True
            and retained['final_fresh_hashes']==0 and retained.get('contracts')is None,'P592_ORIGINAL_FAILED_WHOLE_AUDIT_NOT_PROMOTED')
        archive='implementation/p09/source-archive/p361-capture007-entry592/verifier001.py';archived=q.pin(archive)
        c.require((archived['bytes'],archived['sha256'])==(priorpins[SELF]['bytes'],priorpins[SELF]['sha256']),'P592_EXACT_PREVIOUS_EXECUTOR_SOURCE')
        def executor_body(text):
            tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run_ps_models')
            return ast.get_source_segment(text,node)
        c.require(executor_body(q.text(SELF))==executor_body(q.text(archive)),'P592_SAME_OWNED_PS_EXECUTOR_AND_RESOURCE_ENVIRONMENT')
        c.require(row['external_shell_pins']==retained['external_shell_pins'],'P592_SAME_RETAINED_WINDOWS_PS_IMAGE')
        retained_dependencies={
            PS_TESTS[0]:('sdk-baseline-owned-session','crossref-owned-active-source','crossref-capture007-application-binding'),
            PS_TESTS[1]:('sdk-baseline-owned-session','crossref-owned-active-source','crossref-stage-probe','crossref-native-case-ports',
                'crossref-preassigned-owner','crossref-preassigned-case-ports','crossref-capture007-source-guard','run-hancom-2020-sdk-baseline-capture')}
        row['retained_windows_model_steps']=[]
        for name in PS_TESTS:
            path='implementation/p09/tools/'+name;text=q.text(path)
            expected=set(re.findall(r"WriteLine\('test ([a-z0-9_:]+) \.\.\. ok'\)",text))
            if 'application-binding'in name:expected|={'capture007_application::reject_false_'+v for v in GRAPH_FIELDS}
            c.require(len(expected)==(16 if 'application-binding'in name else 6 if 'source-guard'in name else 5),'P592_EXACT_NEW_PS_CASE_COUNT')
            if name in retained_dependencies:
                oldstep=next(s for s in retained['steps']if s['stage']==path)
                c.require(oldstep['exit_code']==0 and oldstep['cleanup']is True and oldstep['stderr_bytes']==0
                    and len(oldstep['tests'])==len(expected)and {n for n,s in oldstep['tests']}==expected
                    and all(s=='ok'for n,s in oldstep['tests']),'P592_EXACT_RETAINED_BODY_CASES')
                dependencies={path}|{'implementation/p09/tools/'+n+'.ps1'for n in retained_dependencies[name]}
                for dependency in dependencies:c.require(q.pin(dependency)==priorpins[dependency],'P592_FRESH_RETAINED_MODEL_DEPENDENCIES')
                row['retained_windows_model_steps'].append(dict(stage=path,cases=oldstep['tests'],
                    actual_model_dependencies=sorted(dependencies),receipt=q.snapshots[retained_path],reexecuted=False))
                continue
            run_ps_models(path,expected,guard,row)
        result=unittest.TestResult()
        for index,name in enumerate(TESTS):
            path='tools/p09/tests/'+name+'.py';ast.parse(q.text(path))
            spec=importlib.util.spec_from_file_location('capture007_models_'+str(index),c.ROOT/path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        c.require(row['contracts']==dict(run=50,errors=0,failures=0,skipped=0),'P592_ALL50_CURRENT_GENERATION_INPUT_CONTRACTS')
        c.require(all(not(c.ROOT/name).exists()for name in before),'P592_NO_NATIVE_NAMESPACE_CREATED_BY_MODELS')
        runtime.absent_attempts();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(paths),external_shell_final_hashes=shell.final_fresh_hashes,
            preserved006_receipt_sha256=OLD_SHA,retained_probe_receipt_sha256=q.snapshots[PROBE]['sha256'],real_windows_models=27,
            document_application_root_alias_assumption_replaced_by_nine_owned_graph_requirements=True,
            actual_returned_application_graph_and_Hancom_save_reopen_compatibility='NOT_RUN');passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,RecursionError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P592_FAILURE_NO_RAW_VALUES')
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
