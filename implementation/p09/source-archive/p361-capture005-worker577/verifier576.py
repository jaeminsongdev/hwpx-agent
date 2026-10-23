"""New005 worker composition: six Python + eight PS models + actual missing-mode denial. No Native."""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_capture005_worker as worker
import verify_crossref_generation004551 as original_models
import search_sql_receipt as layout
SELF='tools/p09/verify_capture005_worker575.py'
OUTPUT='implementation/p09/evidence/p09-361-capture005-worker575.v1.json'
BASE='implementation/p09/evidence/p09-361-capture005-namespace574.v1.json'
ENTRY='tools/p09/run_external_crossref_fixed_batch.py'
CODE='implementation/p09/evidence/p09-361-capture004-entry-code559.v1.json'
PYTEST='tools/p09/tests/test_crossref_capture005_worker.py'
FILES=('crossref-capture005-namespace.ps1','crossref-capture005-worker-program.ps1','run-crossref-capture005-worker.ps1',
    'test-crossref-capture005-namespace.ps1','test-crossref-capture005-worker-program.ps1')
PS=original_models.PS

def inverse(text):
    for old,new in(('capture004','capture005'),('Capture004','Capture005'),('fixed004','fixed005'),('Fixed004','Fixed005'),('g004','g005'),('FOUR','FIVE'),
        ('5149696','5150720'),('e64128bec14686aaecde8bafaf34458b59a4c694fe2b0a54f411d013b0a01551','9c07898c40bb95ce1ed60b42d10481152bda8aaf7bb68e9c453fffef736756d9')):
        text=text.replace(new,old)
    return text

def closed_mode(guard,row):
    owned=capture=None;started=time.monotonic();step=dict(stage='actual005_missing_flag_denial',cleanup=False);row['steps'].append(step)
    try:
        args=[PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/worker.TARGET)]
        owned=r.shared.OwnedSQLJobProcess(args,windows=guard.windows,allowed_executables=[PS],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<30,'P575_CLOSED_MODE_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        result=json.loads(out);step.update(exit_code=owned.returncode,closed_mode_result=result,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest())
        r.c.require(owned.returncode==2 and not err and result['phase']=='closed_mode'
            and result['error_code']=='P09_XREF_BIND_CAPTURE_FIVE_FIXED_MODE_REQUIRED'and result['completed_callback_cases']==0
            and result['retained_live_or_uncertain_owners']==0 and result['probe_lease_closed']is True and result['native_execution_authorized']is False,
            'P575_MISSING_FLAG_DENIED_BEFORE_PROGRAM_IMPORT_OR_NATIVE')
    finally:
        if owned is not None:
            # This model Job owns PowerShell only. No Hancom or Native worker is admitted.
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;after575=sys.argv[1:]==['--after575-final-newline-only']
    c.require(after575 or sys.argv[1:]==['--worker-models-and-closed-mode-only'],'P575_NO_NATIVE_MODE')
    output=OUTPUT.replace('575.v1','576.v1')if after575 else OUTPUT
    c.require(not(c.ROOT/output).exists(),'P575_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=shell=None
    row=dict(state='FAILED_CAPTURE005_WORKER_MODELS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_Native_SQL_or_product_started=False,old_cases_or_249_or_passed_test_bodies_replayed=False,
        capture005_runtime_entry_connected=False,capture005_session_qualified=False,new005_execution_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);worker.namespace.require_absent(c.ROOT)
        names={SELF,BASE,ENTRY,CODE,PYTEST,'tools/p09/crossref_capture005_worker.py','tools/p09/crossref_capture005_namespace.py'}|set(worker.SOURCES)
        if after575:names|={OUTPUT,'implementation/p09/source-archive/p361-capture005-worker576/verifier575.py'}|{'implementation/p09/source-archive/p361-capture005-worker576/'+name for name in FILES}
        for name in FILES:names|={'implementation/p09/tools/'+name,'implementation/p09/tools/'+name.replace('capture005','capture004')}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(names):q.pin(name)
        if after575:
            previous=layout.unpack(q.json(OUTPUT))
            c.require(q.snapshots[OUTPUT]['sha256']=='0ac35399339118d2249e34848fe3e873f721f14cce9c6fb9630a81d20c364e9f'
                and previous['cleanup']is True and previous['steps']==[]and previous['final_fresh_hashes']==0,'P576_ORIGINAL575_STATIC_FAILURE_NO_MODELS_OR_NATIVE_EXECUTED')
            for name in FILES:
                c.require(q.text('implementation/p09/source-archive/p361-capture005-worker576/'+name)==q.text('implementation/p09/tools/'+name)+'\n',
                    'P576_ONLY_ONE_EXTRA_EOF_NEWLINE_REMOVED_NO_VALIDATION_CHANGE')
            row.update(original575_failure_preserved=True,original575_models_and_Native_not_run=True)
        base=layout.unpack(q.json(BASE));c.require(q.snapshots[BASE]['sha256']=='3dd2e093d8b4d61faffe6eaca78ecf50d8de5b7cbc1a79e8756e793f095ca667'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==852,'P575_EXACT574_READONLY_PROBE_QUALIFICATION')
        c.require(q.snapshots[worker.namespace.PROBE]==base['compiled_probe']and worker.PROBE_PIN==(base['compiled_probe']['bytes'],base['compiled_probe']['sha256']),
            'P575_SAME_CURRENT_QUALIFIED005_PROBE')
        old_code=r.compact.unpack(q.json(CODE));old_pins={p['path']:p for p in old_code['source_pins']}
        c.require(q.snapshots[ENTRY]==old_pins[ENTRY],'P575_CONSUMED001_TO004_ENTRY_BYTE_EXACT_UNCHANGED')
        for name in FILES:
            current='implementation/p09/tools/'+name;old='implementation/p09/tools/'+name.replace('capture005','capture004')
            r.audit.inverse(inverse(q.text(current)),q.snapshots[old],'P575_ONLY_FIXED_NAMESPACE_PROBE_BYTES_AND_CLOSED_GENERATION_CODES_CHANGED')
        for name in(SELF,PYTEST,'tools/p09/crossref_capture005_worker.py'):ast.parse(q.text(name))
        spec=importlib.util.spec_from_file_location('capture005_worker_models',c.ROOT/PYTEST);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=6,errors=0,failures=0,skipped=0),'P575_SIX_NEW_PYTHON_WORKER_CASES')
        shell=a.AcceptanceReader(Path(PS).parent,guard.check);row['external_shell_pins']=[shell.pin(Path(PS).name)]
        for name,count in(('test-crossref-capture005-namespace.ps1',5),('test-crossref-capture005-worker-program.ps1',3)):
            script='implementation/p09/tools/'+name;expected=set(re.findall(r"WriteLine\('test ([A-Za-z0-9_:]+) \.\.\. ok'\)",q.text(script)))
            c.require(len(expected)==count,'P575_EXACT_NEW_PS_EXPECTED_CASE_COUNT')
            original_models.child(script,True,expected,guard,row)
        closed_mode(guard,row);worker.namespace.require_absent(c.ROOT)
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CAPTURE005_WORKER_SIX_PYTHON_EIGHT_PS_AND_ACTUAL_MISSING_MODE_DENIAL_NOT_NATIVE_OR_ENTRY',
            PS_models=8,actual_closed_mode_before_native_import=True,external_shell_final_fresh_hashes=shell.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P575_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        proof=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],closed_model_errors=s.get('closed_model_errors',[]))for s in row['steps']],'receipt':proof}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
