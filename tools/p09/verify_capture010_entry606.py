"""Fixed010 code/closed-section contracts, no Native/COM or consumed-run retry."""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch010 as entry
import crossref_external010_runtime as runtime
import crossref_inline_receipt567 as layout
import search_sql_receipt as probe_layout

SELF='tools/p09/verify_capture010_entry606.py'
AUDIT='implementation/p09/evidence/p09-361-capture010-entry-code606-audit002.v1.json'
PROBE='implementation/p09/evidence/p09-361-capture010-namespace605-validated.v1.json'
OLD='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run009.v1.json'
TESTS=('test_crossref_generation010_entry','test_crossref_generation010_main','test_crossref_section010',
    'test_crossref_runtime010_sections','test_crossref_generation010_publication','test_crossref_capture010_worker')
RETAINED=('implementation/p09/evidence/p09-361-native-worker-transport603-models.v1.json',
    'implementation/p09/evidence/p09-361-native-worker-transport604-real-pipes.v1.json')
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

def function(text,name):
    return ast.get_source_segment(text,next(n for n in ast.walk(ast.parse(text))if isinstance(n,ast.FunctionDef)and n.name==name))

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--code-models-only'],'P606_CLOSED_MODELS_ONLY')
    c.require(not(c.ROOT/AUDIT).exists()and not(c.ROOT/entry.NAMES['code']).exists(),'P606_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;passed=False;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE010_ENTRY_CODE_MODELS',generation=10,steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False,Native011_executed=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,external010_executed=False,consumed001_to009_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=layout.unpack(q.json(OLD));probe=probe_layout.unpack(q.json(PROBE))
        c.require(q.snapshots[OLD]['sha256']=='2eb9a9cb848d888ad39cfe433601e5494b3f4072eab856ef57d67f65fd7d6cef'
            and old['cleanup']is False and old['fixed_eight_executed']is False,'P606_ORIGINAL009_FAILURE_NOT_REWRITTEN')
        # Every input of the consumed invocation stays exact, not just its receipt.
        for pin in old['source_pins']:c.require(q.pin(pin['path'])==pin,'P606_CONSUMED009_SOURCE_AND_IMAGES_UNCHANGED')
        c.require(probe['cleanup']is True and probe['fresh_inputs']==probe['final_fresh_hashes']>0
            and probe['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P606_CURRENT605_PATH_MODELS_RETAINED')
        for pin in probe['source_pins']:
            if pin['path']in('crates/product-cli/examples/p09_crossref_discovery_probe.rs',
                'crates/product-cli/examples/p09_crossref_capture010_probe.rs','tools/p09/crossref_capture010_namespace.py'):
                c.require(q.pin(pin['path'])==pin,'P606_COMPILED_SOURCE_UNCHANGED')
        c.require(q.pin(runtime.capture.namespace.PROBE)==probe['compiled_probe'],'P606_CURRENT_COMPILED010_PROBE')
        row['retained_transport_proofs']=[]
        for index,name in enumerate(RETAINED):
            proof=layout.unpack(q.json(name))
            expected=('d5ae22cd52f57e920632555d15c22ab590121174e95e509c9fdcf527f9398456',
                'd263b07efd5bf29895d41f650464355a4be04aab432882175a98c65eaba2c882')[index]
            c.require(q.snapshots[name]['sha256']==expected and proof['state'].startswith('PASS_')and proof['cleanup']is True
                and proof['fresh_inputs']==proof['final_fresh_hashes']>0,'P606_RETAINED603_604_EXACT_PROOF')
            for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'P606_RETAINED_TRANSPORT_ALL_INPUTS_FRESH')
            row['retained_transport_proofs'].append(dict(receipt=q.snapshots[name],bodies_reexecuted=False))
        prior_name='implementation/p09/evidence/p09-361-capture009-entry-code600.v1.json'
        prior=layout.unpack(q.json(prior_name));prior_pins={p['path']:p for p in prior['source_pins']}
        c.require(q.snapshots[prior_name]['sha256']=='94f55799a7bbd33635cb62f59f666d9fc1a726578d94333482e20745dbf1750b'
            and prior['cleanup']is True and prior['real_windows_models']==40,'P606_RETAINED600_WINDOWS_PROOF')
        for name,pin in prior_pins.items():
            if name.endswith('.ps1')or name.endswith('capture009_probe.exe'):
                c.require(q.pin(name)==pin,'P606_REUSED_APPLICATION_SOURCE_ARTIFACT_GUARD_CLOSURE')
        row['retained_windows_models']=35
        row['retained_windows_model_receipt']=q.snapshots[prior_name]
        # Only namespace/probe and the outer program namespace change; the guards
        # are reused byte-exact. Their private009 state keys are NOT output paths.
        program='implementation/p09/tools/crossref-capture010-worker-program.ps1'
        oldprogram='implementation/p09/tools/crossref-capture009-worker-program.ps1'
        projected=q.text(oldprogram).replace('009','010').replace('NINE','TEN').replace(
            'crossref-capture010-source-guard','crossref-capture009-source-guard').replace(
            'Capture010SourceGuard','Capture009SourceGuard').replace(
            'crossref-capture010-artifact-guard','crossref-capture009-artifact-guard').replace('Capture010ArtifactGuard','Capture009ArtifactGuard')
        c.require(q.text(program).rstrip()==projected.rstrip(),'P606_PROGRAM_WHOLE_INVERSE_AND_UNCHANGED_GUARD_ORDER')
        c.require(function(q.text(runtime.SELF),'capture_artifacts')==function(q.text('tools/p09/crossref_external009_runtime.py'),'capture_artifacts'),
            'P606_ALL16_SESSIONS40_ARTIFACTS_AND_CANONICAL_OWNER_CHECKS_UNCHANGED')
        paths=entry.loaded_paths(exclude=(SELF,))|runtime.CASE_PATHS|set(runtime.fixed_input_pins())|{entry.SELF,runtime.SELF}
        tests={'tools/p09/tests/'+name+'.py'for name in TESTS}
        ps_test='implementation/p09/tools/test-crossref-capture010-namespace.ps1'
        for name in sorted(paths|tests|{SELF,ps_test}):q.pin(name)
        for name in paths:
            if name.endswith('.py'):ast.parse(q.text(name))
        for name,(size,sha)in runtime.fixed_input_pins().items():
            pin=q.pin(name);c.require((pin['bytes'],pin['sha256'])==(size,sha),'P606_FIXED_EXACT_INPUTS')
        runtime.absent_attempts()
        before={name:(c.ROOT/name).exists()for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['preflight'],entry.publication.SPOOL)}
        c.require(not any(before.values()),'P606_UNUSED010_NAMESPACE')
        shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        row['external_shell_pins']=[shell.pin(Path(runtime.original.candidate.original.SHELL).name)]
        c.require(row['external_shell_pins']==prior['external_shell_pins'],'P606_RETAINED_SAME_WINDOWS_SHELL')
        expected=set(re.findall(r"WriteLine\('test ([a-z0-9_:]+) \.\.\. ok'\)",q.text(ps_test)))
        c.require(len(expected)==5,'P606_FIVE_NEW_WINDOWS_NAMESPACE_MODELS');run_ps_models(ps_test,expected,guard,row)
        sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
        result=unittest.TestResult()
        with patch.object(runtime.original.session.startup,'PreassignedNativeStartup',side_effect=AssertionError('P606_NATIVE_TRAP'))as native,patch(
            'subprocess.Popen',side_effect=AssertionError('P606_PROCESS_TRAP'))as process:
            for index,name in enumerate(TESTS):
                path='tools/p09/tests/'+name+'.py';ast.parse(q.text(path))
                spec=importlib.util.spec_from_file_location(name,c.ROOT/path);module=importlib.util.module_from_spec(spec)
                sys.modules[name]=module;spec.loader.exec_module(module)
                unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
            row.update(native_constructor_trap_calls=native.call_count,process_constructor_trap_calls=process.call_count)
        row['contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['failed_contract_names']=[test.id()for test,_ in result.errors+result.failures]
        # Store sanitized exception TYPES/closed assertion codes, never raw canaries/logs.
        row['contract_failure_types']=[trace.splitlines()[-1].split(':')[0][:80]for _,trace in result.errors+result.failures]
        c.require(row['contracts']==dict(run=76,errors=0,failures=0,skipped=0)and native.call_count==process.call_count==0,'P606_ALL76_CLOSED_CONTRACTS')
        paths|=entry.loaded_paths(exclude=(SELF,))
        for name in sorted(paths):q.pin(name)
        c.require(all(not(c.ROOT/name).exists()for name in before),'P606_NO_MODEL_NATIVE_NAMESPACE_EFFECT')
        runtime.absent_attempts();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(paths),external_shell_final_hashes=shell.final_fresh_hashes,
            real_windows_models=40,original_Native10_and_startup15_limits_unchanged=True,
            section_policy=dict(sections=list(entry.sections.SECTIONS),section_seconds=600,whole_seconds=1800),
            transport603_wired_for_both_stages=True,actual010_Hancom_save_reopen_compatibility='NOT_RUN');passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,AssertionError,RecursionError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P606_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        audit=shared.publisher.publish(c.ROOT,AUDIT,layout.pack(row),NS(require=c.require,exact=a.exact));canonical=None
        if passed and row['cleanup']:canonical=shared.publisher.publish(c.ROOT,entry.NAMES['code'],layout.pack(dict(row,code_audit_receipt=audit)),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','contract_failure_types','fresh_inputs','final_fresh_hashes','cleanup',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'audit':audit,'code':canonical}),flush=True)
    return 0 if passed and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
