"""Fixed006 code/real Windows lease models only, never Hancom, claims or Native.

The consumed005 receipt stays failed. Read sharing is NOT relaxed. The new
source guard must precede the unchanged original Open and close on failure.
"""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch006 as entry
import crossref_external006_runtime as runtime
import crossref_inline_receipt567 as layout
import search_sql_receipt as probe_layout

SELF='tools/p09/verify_capture006_entry588.py'
AUDIT='implementation/p09/evidence/p09-361-capture006-entry-code588-audit010.v1.json'
RETAINED='implementation/p09/evidence/p09-361-capture006-entry-code588-audit001.v1.json'
PROBE='implementation/p09/evidence/p09-361-capture006-namespace586.v1.json'
OLD='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run005.v1.json'
OLD_SHA='05f1d0e2c5d38a9aa41fc358e2d9cbef8b584d7f08c1ace0d244651297b3e1db'
TESTS=('test_crossref_generation006_entry','test_crossref_generation006_publication','test_crossref_capture006_worker')
PS_TESTS=('test-crossref-capture006-source-guard.ps1','test-crossref-capture006-namespace.ps1')

def run_ps_models(path,expected,guard,row):
    # Cargo's helper intentionally refuses PowerShell. This separate, narrowly
    # allowlisted model Job owns only PS: no Hancom admission or COM activation.
    ps=runtime.original.candidate.original.SHELL;owned=capture=None;started=time.monotonic()
    step=dict(stage=path,cleanup=False);row['steps'].append(step)
    try:
        call="try { & '"+str(r.c.ROOT/path)+"' -ModelsOnly } catch { if ($_.Exception.Message -cmatch '^(P09_XREF_[A-Z_]+|P58_[A-Z_]+)$') {[Console]::Error.WriteLine($_.Exception.Message)};[Console]::Error.WriteLine('P588_MODEL_RUNTIME_'+$_.Exception.GetType().Name+'_LINE_'+$_.InvocationInfo.ScriptLineNumber);exit 1 }"
        args=[ps,'-NoLogo','-NoProfile','-NonInteractive','-STA','-Command',call]
        env=r.audit.environment()
        # Sanitized Cargo environment omits SystemRoot/PSModulePath. Models use
        # only this exact Windows PowerShell's inbox modules, never PS7/user modules.
        env.update(SystemRoot=str(Path(ps).parents[3]),PSModulePath=str(Path(ps).parent/'Modules'))
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[ps],
            cwd=r.c.ROOT,checkpoint=guard.check,env=env)
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<30,'P588_MODELS_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        found=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',out)
        step.update(exit_code=owned.returncode,tests=found,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            closed_model_errors=re.findall(r'P09_XREF_BIND_[A-Z_]+',err)[:4],
            model_runtime_errors=re.findall(r'P588_MODEL_RUNTIME_[A-Za-z0-9]+_LINE_[0-9]{1,6}',err)[:4],
            guard_diagnostic=re.findall(r'P588_GUARD_DIAGNOSTIC_[A-Za-z0-9_,.+-]{1,220}',err)[:4],
            safe_runtime_locations=re.findall(r'test-crossref-capture006-[a-z-]+\.ps1:[0-9]{1,6}',err)[:4])
        r.c.require(owned.returncode==0 and not err and len(found)==len(expected)and {n for n,s in found}==expected
            and all(s=='ok'for n,s in found),'P588_ALL_EXACT_WINDOWS_MODELS_NO_SKIPS')
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--code-models-only'],'P588_MODELS_ONLY')
    c.require(not(c.ROOT/AUDIT).exists()and not(c.ROOT/entry.NAMES['code']).exists(),'P588_IMMUTABLE_CODE_PROOF')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=shell=None;passed=False;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE006_ENTRY_CODE_MODELS',generation=6,steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,native_startup_qualified=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,consumed005_replayed=False,
        source_write_sharing_relaxed=False,external006_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=layout.unpack(q.json(OLD));probe=probe_layout.unpack(q.json(PROBE))
        c.require(q.snapshots[OLD]['sha256']==OLD_SHA and old['state']=='FAILED_EXTERNAL_QUALIFIED_ENTRY'
            and old['cleanup']is True and old['fixed_eight_executed']is False
            and old['fixed_worker']['result']['case_failure']['error_code']=='P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_SHARING_VIOLATION',
            'P588_CONSUMED005_FAILURE_NOT_REINTERPRETED')
        c.require(probe['cleanup']is True and probe['fresh_inputs']==probe['final_fresh_hashes']>0
            and probe['contracts']==dict(run=5,errors=0,failures=0,skipped=0),'P588_RETAIN_CURRENT586_WITHOUT_RUST_OR_PATH_MODEL_REPLAY')
        for pin in probe['source_pins']:
            if pin['path']in('crates/product-cli/examples/p09_crossref_discovery_probe.rs',
                'crates/product-cli/examples/p09_crossref_capture006_probe.rs','tools/p09/crossref_capture006_namespace.py'):
                c.require(q.pin(pin['path'])==pin,'P588_CURRENT_COMPILED_SOURCE')
        c.require(q.pin(runtime.capture.namespace.PROBE)==probe['compiled_probe'],'P588_CURRENT_ACTUAL_COMPILED_PROBE')
        paths=entry.loaded_paths(exclude=(SELF,))|runtime.CASE_PATHS|set(runtime.fixed_input_pins())|{entry.SELF,runtime.SELF}
        names=paths|{SELF,PROBE,OLD,*['tools/p09/tests/'+n+'.py'for n in TESTS],
            *['implementation/p09/tools/'+n for n in PS_TESTS],
            'tools/p09/run_external_crossref_fixed_batch005.py','tools/p09/crossref_external005_runtime.py',
            'tools/p09/crossref_capture005_worker.py','tools/p09/crossref_generation005_publication.py'}
        for name in sorted(names):q.pin(name)
        oldpins={p['path']:p for p in old['source_pins']}
        for name in('tools/p09/run_external_crossref_fixed_batch005.py','tools/p09/crossref_external005_runtime.py',
            'tools/p09/crossref_capture005_worker.py','tools/p09/crossref_generation005_publication.py'):
            c.require(q.pin(name)==oldpins[name],'P588_CONSUMED005_CODE_UNCHANGED')
        current=q.text(runtime.SELF).replace('\r\n','\n').replace('006','005')
        prior=q.text('tools/p09/crossref_external005_runtime.py').replace('\r\n','\n')
        c.require(current==prior,'P588_WHOLE16_SESSIONS40_ARTIFACTS_AND_CASE_SOURCE_BOUNDARIES_INVERSE')
        for name,(size,sha)in runtime.fixed_input_pins().items():
            pin=q.pin(name);c.require((pin['bytes'],pin['sha256'])==(size,sha),'P588_FIXED_INPUTS')
        before={name:(c.ROOT/name).exists()for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['preflight'],entry.publication.SPOOL)}
        c.require(not any(before.values()),'P588_UNUSED006_NAMESPACE')
        retained=layout.unpack(q.json(RETAINED))
        c.require(q.snapshots[RETAINED]['sha256']=='3bb8718ff818d828efc811ee93bdccedb5b480840e79b20259125057ecd024a4'
            and retained['state']=='FAILED_CAPTURE006_ENTRY_CODE_MODELS'
            and retained['error_code']=='OWNED_SQL_EXECUTABLE_NOT_ALLOWLISTED'
            and retained['contracts']==dict(run=50,errors=0,failures=0,skipped=0)
            and retained['final_fresh_hashes']==0,'P588_ORIGINAL_FAILED_AUDIT_50_BODY_PASSES_NOT_A_WHOLE_PASS')
        archive='implementation/p09/source-archive/p361-capture006-entry588/verifier001.py'
        preimages={SELF:archive,'implementation/p09/tools/test-crossref-capture006-source-guard.ps1':
            'implementation/p09/source-archive/p361-capture006-entry588/guard-models002.ps1',
            'implementation/p09/tools/crossref-capture006-source-guard.ps1':
            'implementation/p09/source-archive/p361-capture006-entry588/guard-before-diagnostics.ps1',
            'implementation/p09/tools/test-crossref-capture006-namespace.ps1':
            'implementation/p09/source-archive/p361-capture006-entry588/namespace-models008.ps1'}
        for pin in retained['source_pins']:
            actual=q.pin(preimages.get(pin['path'],pin['path']))
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P588_RETAIN50_UNCHANGED_BODY_INPUTS_OR_DECLARED_EXACT_DRIVER_PREIMAGE')
        row.update(contracts=retained['contracts'],failed_contract_names=[],retained50_models_reexecuted=False,
            original_failed_audit_preserved=RETAINED,original_failed_cleanup_not_promoted=True)
        shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        row['external_shell_pins']=[shell.pin(Path(runtime.original.candidate.original.SHELL).name)]
        env=r.audit.environment();env['PYTHONDONTWRITEBYTECODE']='1'
        guard_prior_path='implementation/p09/evidence/p09-361-capture006-entry-code588-audit008.v1.json'
        guard_prior=layout.unpack(q.json(guard_prior_path));guard_step=guard_prior['steps'][0]
        c.require(q.snapshots[guard_prior_path]['sha256']=='93930ca82572acc0135f068597cfeabdc15fdd8b512e182dd2fbdaf31ff7e94e'
            and guard_prior['state']=='FAILED_CAPTURE006_ENTRY_CODE_MODELS'and guard_prior['cleanup']is True
            and guard_prior['final_fresh_hashes']==0 and guard_step['exit_code']==0 and guard_step['cleanup']is True
            and guard_step['stderr_bytes']==0 and len(guard_step['tests'])==6 and all(s=='ok'for n,s in guard_step['tests']),
            'P588_RETAIN_SIX_GUARD_BODY_PASSES_NOT_FAILED_WHOLE_AUDIT')
        guard_pins={p['path']:p for p in guard_prior['source_pins']}
        for name in paths|{'implementation/p09/tools/'+PS_TESTS[0]}:
            c.require(q.pin(name)==guard_pins[name],'P588_CURRENT_RETAINED_GUARD_RUNTIME_INPUTS')
        c.require(row['external_shell_pins']==guard_prior['external_shell_pins'],'P588_CURRENT_RETAINED_GUARD_PS_IMAGE')
        row['retained_six_guard_models']=dict(receipt=q.snapshots[guard_prior_path],cases=guard_step['tests'],reexecuted=False)
        for name in PS_TESTS:
            path='implementation/p09/tools/'+name;text=q.text(path)
            expected=set(re.findall(r"test ([a-z0-9_:]+) \.\.\. ok",text))
            c.require(len(expected)==(6 if 'source-guard'in name else 5),'P588_CLOSED_REAL_WINDOWS_MODEL_SET')
            if 'source-guard'in name:
                c.require({n for n,s in guard_step['tests']}==expected,'P588_RETAIN_EXACT_SIX_GUARD_NAMES');continue
            run_ps_models(path,expected,guard,row)
        c.require(all(not(c.ROOT/name).exists()for name in before),'P588_NO_NATIVE_EXECUTION_ARTIFACT_CREATED_BY_MODELS')
        runtime.absent_attempts();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.CODE_STATE,entry_dependency_paths=sorted(paths),external_shell_final_hashes=shell.final_fresh_hashes,
            preserved005_receipt_sha256=OLD_SHA,retained_probe_receipt_sha256=q.snapshots[PROBE]['sha256'],
            real_windows_models=11,original_source_lease_acquired_before_original_open=True,
            original_guarded_Hancom_open_compatibility='NOT_RUN',active_SaveAs_artifact_lease_compatibility='NOT_RUN');passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,RecursionError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P588_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        audit=shared.publisher.publish(c.ROOT,AUDIT,layout.pack(row),NS(require=c.require,exact=a.exact));canonical=None
        if passed and row['cleanup']:canonical=shared.publisher.publish(c.ROOT,entry.NAMES['code'],layout.pack(dict(row,code_audit_receipt=audit)),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s.get('cleanup'))for s in row['steps']],
            'audit':audit,'canonical_code_proof':canonical}),flush=True)
    return 0 if passed and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
