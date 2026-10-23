"""Qualify current two-image CPython for bounded local host primitives, never Native/session/product authority."""
import ast,hashlib,importlib.util,json,re,subprocess,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
import named_style_verification_runtime as r
import crossref_python_current555 as profile
import crossref_external_host_inspection as historic
import crossref_preassigned_readonly as readonly
import crossref_readonly_terminal_drain557 as drained
import crossref_session_qualification as session
import crossref_capture004_worker as fixed
import crossref_native_worker_io as io
from run_crossref_fixed_worker_denial import DenialHandler
SELF='tools/p09/qualify_crossref_python555.py'
OUTPUT='implementation/p09/evidence/p09-361-current-python-runtime557.v1.json'
PREVIOUS='implementation/p09/evidence/p09-361-current-python-runtime556.v1.json'
RECOVERY='implementation/p09/source-archive/p361-python-current557/qualifier556.py'
DRAIN_MODEL='tools/p09/tests/test_crossref_readonly_terminal_drain557.py'
PRIOR='implementation/p09/evidence/p09-361-current-python-runtime555.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-python-current556/'
CODE='implementation/p09/evidence/p09-361-capture004-entry-code551.v1.json'
MODEL='tools/p09/tests/test_crossref_python_current555.py'
PROFILE='tools/p09/crossref_python_current555.py'
SIGNATURE='implementation/p09/tools/test-current-python555-signatures.ps1'
HISTORIC='tools/p09/crossref_external_host_inspection.py'
SHELL=Path(fixed.original.prior.original.SHELL)
def signatures(guard,row):
    owned=capture=None;start=time.monotonic();step=dict(stage='current_runtime_windows_signatures',cleanup=False);row['steps'].append(step)
    try:
        owned=r.shared.OwnedSQLJobProcess([str(SHELL),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/SIGNATURE),'-VerifyCurrentRuntimeOnly'],
            windows=guard.windows,allowed_executables=[str(SHELL)],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=8192,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-start<60,'P555_SIGNATURE_OBSERVATION_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        value=json.loads(stdout);step.update(exit_code=owned.returncode,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),result=value)
        r.c.require(owned.returncode==0 and not stderr and value['state']=='PASS_CURRENT_FIXED_EXE_CORE_WINDOWS_SIGNATURES_NOT_NATIVE_QUALIFICATION'
            and value['trust_or_runtime_files_modified']is False and len(value['images'])==2,'P555_BOTH_CURRENT_VALID_SIGNATURES_REQUIRED')
        for item in value['images']:
            r.c.require(item['windows_signature']=='Valid'and item['publisher']=='OpenAI OpCo, LLC'and item['version']=='3.12.14'
                and {k:item[k]for k in('path','bytes','sha256')}==profile.specifications()[item['path']],'P555_EXACT_SIGNED_CURRENT_FILE_IDENTITIES')
        return value
    finally:
        if owned is not None:
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-start,3)
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--runtime-readonly-and-ready-denial-only'],'P555_FIXED_NON_NATIVE_SCOPE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P555_IMMUTABLE_RUNTIME_QUALIFICATION')
    spec=importlib.util.spec_from_file_location('current_python555_models',c.ROOT/MODEL);models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
    spec=importlib.util.spec_from_file_location('terminal_readonly557_models',c.ROOT/DRAIN_MODEL);drain_models=importlib.util.module_from_spec(spec);spec.loader.exec_module(drain_models)
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=runtime_image=shell=native=child=None
    row=dict(state='FAILED_CURRENT_PYTHON_HOST_PRIMITIVES',steps=[],own_cpu_selection=selection,generation=4,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_ROT_COM_or_native_started=False,fixed_eight_executed=False,native_startup_qualified=False,public_entry_profile_applied=False,
        original_guard_runtime_trust_files_modified=False,old_Native_or_cases_or_33_models_replayed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof=r.compact.unpack(q.json(CODE))
        c.require(q.snapshots[CODE]['sha256']=='f783dca3f6c9ecc755c8127544212720f9af480592bbcee5df2ce44a5d927fbc'
            and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']==245
            and proof['contracts']==dict(run=33,errors=0,failures=0,skipped=0),'P555_EXACT_CURRENT_CODE551_NO_MODEL_REPLAY')
        for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'P555_ALL_CODE551_INPUTS_UNCHANGED')
        names={SELF,MODEL,PROFILE,SIGNATURE,HISTORIC,'tools/p09/run_crossref_fixed_worker_denial.py',PRIOR,ARCHIVE+'qualifier555.py',ARCHIVE+'signatures555.ps1',
            PREVIOUS,RECOVERY,DRAIN_MODEL,'tools/p09/crossref_readonly_terminal_drain557.py','tools/p09/crossref_preassigned_preparation_drain.py'}
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):q.pin(path)
        c.require(q.snapshots[HISTORIC]['sha256']=='29bc4140b72deabfcd22dcc26aac3d60778a2dd70fedd59ab9e8cb5191ee4406','P555_HISTORICAL_RUNTIME_GATE_NOT_CHANGED')
        prior=r.compact.unpack(q.json(PRIOR))
        c.require(q.snapshots[PRIOR]['sha256']=='f9607b5e2dbd37a8eb58443a90d0b8a176f965f5daa0f47db66756593be357a1'
            and prior['contracts']==dict(run=8,errors=0,failures=0,skipped=0)and prior['cleanup']is True
            and prior['fresh_inputs']==251 and prior['final_fresh_hashes']==0 and len(prior['steps'])==1
            and prior['steps'][0]['exit_code']==2 and prior['error_code']=='P555_BOTH_CURRENT_VALID_SIGNATURES_REQUIRED','P556_PRESERVE555_MODEL_SUCCESS_AND_SIGNATURE_FAILURE')
        fixed_inputs={SELF:ARCHIVE+'qualifier555.py',SIGNATURE:ARCHIVE+'signatures555.ps1'}
        for pin in prior['source_pins']:
            actual=q.pin(fixed_inputs.get(pin['path'],pin['path']))
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P556_ALL_OTHER555_INPUTS_UNCHANGED')
        row.update(contracts=prior['contracts'],failed_contract_names=[],model_execution_repeated=False,retained_model_result_source=PRIOR,
            retained_model_source_profile_and_fixture_identical=True,prior555_failure_or_missing_final_closure_rewritten=False)
        previous=r.compact.unpack(q.json(PREVIOUS))
        c.require(q.snapshots[PREVIOUS]['sha256']=='636231cb77e07c91d41dc2d24a1a74906e2097794d01fc56428c43f9b2a24b23'
            and previous['cleanup']is False and previous['final_fresh_hashes']==0 and previous['error_code']=='XREF_PREASSIGNED_LIVE_TREE_RETAIN_JOB'
            and previous['readonly_child_cleanup_pending']['child_selfcheck_exit_code']==0 and len(previous['steps'])==1
            and previous['steps'][0]['exit_code']==0,'P557_KEEP556_PASSED_SELF_CHECK_AND_SIGNATURE_WITH_FAILED_CLEANUP')
        for pin in previous['source_pins']:
            actual=q.pin(RECOVERY if pin['path']==SELF else pin['path'])
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P557_OTHER556_INPUTS_UNCHANGED')
        cases=unittest.defaultTestLoader.loadTestsFromModule(drain_models);c.require(cases.countTestCases()==4,'P557_FOUR_NEW_TERMINAL_CLOSE_MODELS')
        result=unittest.TestResult();cases.run(result)
        row['new_terminal_drain_contracts']=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped))
        row['new_terminal_drain_failed_contract_names']=[t.id()for t,_ in result.errors+result.failures]
        c.require(row['new_terminal_drain_contracts']==dict(run=4,errors=0,failures=0,skipped=0),'P557_ALL_NEW_TERMINAL_CLOSE_MODELS')
        runtime_image=a.AcceptanceReader(profile.fixed.PYTHON.parent,guard.check)
        pins={name:runtime_image.pin(name)for name in profile.specifications()};loaded=profile.observe_loaded_images()
        c.require(list(pins.values())==prior['runtime_current_image_pins'],'P556_SAME_CURRENT_IMAGES_AS_OBSERVED_MODEL_RUN')
        row['current_runtime']=profile.validate(pins,loaded);row['loaded_image_observation']=loaded
        row['runtime_current_image_pins']=list(pins.values());before=historic.current_identity(guard.windows)
        denied=False
        try:historic.runtime_pin_matches(pins['python.exe'])
        except ValueError as e:denied=e.args==('XREF_EXTERNAL_HOST_FIXED_PYTHON_RUNTIME_BYTES',)
        c.require(denied,'P555_OLD_RUNTIME_GATE_STILL_REFUSES_DIFFERENT_BUILD')
        shell=a.AcceptanceReader(SHELL.parent,guard.check);c.require(shell.pin(SHELL.name)==proof['external_shell_pins'][0],'P555_SAME_QUALIFIED_SHELL')
        row['windows_signature_observation']=previous['windows_signature_observation'];row['signature_execution_repeated']=False;row['signature_result_retained_from']=PREVIOUS
        native=a.AcceptanceReader(Path(historic.native.EXECUTABLE).parent,guard.check)
        with patch.object(session.startup,'PreassignedNativeStartup',side_effect=ValueError('P555_NATIVE_CONSTRUCTOR_TRAP'))as trap:
            row['empty_resource_jobs']=historic.empty_resource_layout(guard.windows,guard.check,lambda:native.fresh_pin(Path(historic.native.EXECUTABLE).name))
            child=drained.DrainedReadonlyProcess(guard.windows,guard.check)
            child.create_suspended();child.resume_readonly();code=child.wait_readonly(15);c.require(code==0,'P555_CURRENT_PYTHON_PREASSIGNED_LIMIT_SELFCHECK_EXIT_ZERO')
            child.close();row['readonly_python_child']=dict(child.profile)
            c.require(child.profile['assigned_before_initial_thread']is True and child.profile['pre_run_user_cpu_100ns']==0
                and child.profile['cleanup_confirmed']is True and child.profile['force_termination_invoked']is False,'P555_CURRENT_PYTHON_ATOMIC_PREASSIGNMENT_AND_NORMAL_EXIT')
            fixed.namespace.require_absent(c.ROOT);scratch=c.ROOT/'target/p09-current-python-worker-scratch557'
            c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'P555_FRESH_WORKER_SCRATCH');scratch.mkdir()
            env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
            worker=fixed.Fixed004Worker(guard);handler=DenialHandler(worker,lambda:shell.fresh_pin(SHELL.name));attempt={};row['steps'].append(attempt)
            print(json.dumps(dict(state='CURRENT_PYTHON_QUALIFIED_PREFIX_READY_DENIAL',inputs=len(q.snapshots),python_selfcheck_exit=0,worker_CPU_cap_percent=1,Native_constructor_trapped=True)),flush=True)
            value=io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',env,
                lambda v:print(json.dumps(v),flush=True),attempt)
            row['native_constructor_trap_calls']=trap.call_count;c.require(trap.call_count==0,'P555_NATIVE_CONSTRUCTOR_NEVER_REACHED')
            c.require(attempt['exit_code']==2 and attempt['requests']==1 and handler.denied and handler.lease.closed
                and value['state']=='fixed_eight_worker_failed_or_uncertain'and value['phase']=='current_live_release'
                and value['completed_callback_cases']==0 and value['retained_live_or_uncertain_owners']==0 and value['probe_lease_closed']is True,'P555_ACTUAL004_WORKER_READY_DENIED_BEFORE_CASES')
        fixed.namespace.require_absent(c.ROOT);row['all_eight_native_directories_absent_after']=True
        after=historic.current_identity(guard.windows);c.require(after==before,'P555_SAME_LIVE_PARENT_KERNEL_LIMITS_AND_IMAGE_PATH')
        c.require(profile.observe_loaded_images()==loaded,'P555_CURRENT_LOADED_PATHS_AND_ABI_UNCHANGED')
        for path in(SELF,MODEL,PROFILE):ast.parse(q.text(path))
        native.finish();runtime_image.finish();shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_PYTHON_TWO_SIGNED_IMAGES_KERNEL_PREASSIGNED_SELFCHECK_AND004_READY_DENIAL_NOT_NATIVE_OR_GATE',
            current_kernel_identity=before,same_live_kernel_before_after=True,qualified_runtime_profile=q.snapshots[PROFILE],
            runtime_disk_image_final_fresh_hashes=runtime_image.final_fresh_hashes,external_shell_final_hashes=shell.final_fresh_hashes,
            external_native_image_final_hashes=native.final_fresh_hashes,live_session_qualification_still_required=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P555_FAILURE_NO_RAW_VALUES')
    finally:
        if child is not None and not child.closed:
            try:child.close()
            except(ValueError,OSError):row['readonly_child_cleanup_pending']=dict(child.profile)
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and 'readonly_child_cleanup_pending'not in row and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            external_shell_pins=[]if shell is None else list(shell.snapshots.values()),resource_samples=samples,elapsed_seconds=round(time.monotonic()-start,3),
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        from types import SimpleNamespace
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),SimpleNamespace(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','contracts','failed_contract_names','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','native_constructor_trap_calls')},
            'steps':[dict(exit_code=s.get('exit_code'),requests=s.get('requests'),cleanup=s.get('cleanup'))for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
