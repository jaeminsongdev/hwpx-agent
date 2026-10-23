"""413: current source closure of code411, public preflight and actual denial412.

This implementation-readiness receipt is not a saved Native/session permit.
No worker, Hancom, COM, product or already-passing test is executed here.
"""
import json,re,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-qualified-entry-runtime-ready413.v1.json'
DRIVER='tools/p09/qualify_crossref_external_entry_runtime.py'
CODE='implementation/p09/evidence/p09-361-crossref-qualified-entry-code411.v1.json'
PREFLIGHT='implementation/p09/evidence/p09-361-external-qualified-entry-preflight001.v1.json'
DENIAL='implementation/p09/evidence/p09-361-crossref-fixed-worker-denial412.v1.json'
EXTERNAL='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run001.v1.json'
CODE_SHA='ad8b5af9d425dc56419dffaa478f7a12f46047d5d334814708b292ac9b9bc754'
PREFLIGHT_SHA='0a3f7d4b06a3a2a0084ea285ed24eec47fda715008cc818c16795f184028903a'
DENIAL_SHA='a69b6d160f063d86648a5938ae5eb734e7c06a5665357d7900f40527f087cb46'
EXTERNAL_SHA='a9598c11a234b96a602ac9d075c8af151a518e7ab2ba40d53fcab6ea93c068c7'


def current_generation002():
    c,a,shared=r.c,r.a,r.shared
    output='implementation/p09/evidence/p09-361-crossref-generation-ready479.v1.json'
    code_path='implementation/p09/evidence/p09-361-crossref-generation-code478.v1.json'
    preflight_path='implementation/p09/evidence/p09-361-external-qualified-generation002-preflight.v1.json'
    denial_path='implementation/p09/evidence/p09-361-crossref-fixed-worker-denial480.v1.json'
    c.require(not(c.ROOT/output).exists(),'GENERATION002_READY_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_GENERATION002_IMPLEMENTATION_READINESS',own_cpu_selection=selection,
        actual_worker_ROT_Hancom_COM_or_test_replayed=False,native_startup_qualified=False,fixed_eight_executed=False,Native011_executed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        code=r.compact.unpack(q.json(code_path));preflight=r.compact.unpack(q.json(preflight_path));denial=r.compact.unpack(q.json(denial_path))
        c.require(q.snapshots[code_path]['sha256']=='6982fde81a6d089fb293290b270a77c996bbca22df4cff34a139cb407b84be33'
            and code['state']=='PASS_QUALIFIED_BATCH_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE'and code['cleanup']is True
            and code['fresh_inputs']==code['final_fresh_hashes']==233 and code['contracts']==dict(run=23,errors=0,failures=0,skipped=0),'EXACT_CURRENT_CODE478_NEW18_AFFECTED5')
        c.require(q.snapshots[preflight_path]['sha256']=='6d898e59f7df2d2bb0fd897d43a2d2f56f0bc6d04a28ff3d3d686957a466b2fe'
            and preflight['state']=='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'and preflight['generation']==2
            and preflight['cleanup']is True and preflight['fresh_inputs']==preflight['final_fresh_hashes']==223
            and all(preflight[k]==1 for k in('external_native_final_hashes','external_shell_final_hashes','external_runtime_final_hashes'))
            and preflight['native_claim_created']is False and preflight['fixed_eight_executed']is False,'ACTUAL_CURRENT_GENERATION002_PUBLIC_PREFLIGHT_NO_NATIVE_OR_CLAIM')
        checks=preflight['prerequisites'];c.require(checks['failed_prerequisites']==['caller_lifecycle_native_safe']
            and checks['closed_errors']==dict(caller_lifecycle_native_safe='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            and checks['checks']['caller_lifecycle_native_safe']is False and all(v is True for k,v in checks['checks'].items()if k!='caller_lifecycle_native_safe')
            and checks['process_created']is False and checks['COM_activated']is False and checks['document_opened']is False,'CURRENT_PREFLIGHT_ONLY_ORIGINAL_PARENT_POLICY_DENIED')
        c.require(denial['state']=='PASS_ACTUAL_FIXED_WORKER_KERNEL_READY_DENIAL_BEFORE_ALL_CASE_IO_NOT_NATIVE_OR_GATE'
            and denial['cleanup']is True and denial['fresh_inputs']==denial['final_fresh_hashes']>0 and denial['external_shell_final_hashes']==1
            and denial['native_constructor_trap_calls']==0 and denial['all_eight_native_directories_absent_after']is True and len(denial['steps'])==1,
            'ACTUAL_CHANGED_IO_WORKER_PREFIX_DENIAL_NO_NATIVE_CONSTRUCTOR_OR_CASE_IO')
        step=denial['steps'][0];summary=step['handler_summary'];result=step['result'];job=step['owned_job']
        c.require(step['exit_code']==2 and step['requests']==1 and step['cleanup']is True and step['stderr_bytes']==0 and step['io_threads_joined']is True
            and summary['ready_denied_before_case_io']is True and summary['query_handle_closed']is True
            and summary['actual_worker_kernel_binding']['exact_live_worker_observed']is True
            and summary['actual_worker_kernel_binding']['original_one_percent_job_member']is True
            and job['owned_tree_empty']is True and job['job_handle_closed']is True and job['cleanup_confirmed']is True
            and job['last_job_accounting']['active_processes']==0 and job['kill_on_close']is False and job['forced_termination_invoked']is False,
            'CURRENT_WORKER_QUERY_JOB_IO_CLEANUP_WITHOUT_NATIVE_OR_FORCE_KILL')
        c.require(result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='current_live_release'
            and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0 and result['probe_lease_closed']is True
            and result['native_startup_qualified']is False,'CURRENT_WORKER_EXPECTED_DENIAL_NOT_NATIVE_SUCCESS')
        for proof in(code,preflight,denial):
            for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_CURRENT_GENERATION002_ACTIVE_CODE_AND_ACTUAL_READONLY_INPUTS_UNCHANGED')
        paths=code['entry_dependency_paths'];c.require(len(paths)==219 and len(set(paths))==219
            and 'tools/p09/crossref_startup_input_idle.py'in paths and set(paths)<=set(q.snapshots),'ALL_CURRENT_219_ENTRY_AND_IDLE_DEPENDENCIES_CLOSED')
        from crossref_external_batch_runtime import absent_attempts
        from run_external_crossref_fixed_batch import generation_names
        absent_attempts();names=generation_names(True)
        for key in('claim','output'):
            target=c.ROOT/names[key];c.require(not target.exists()and not target.is_symlink(),'CURRENT002_CLAIM_AND_RUN_UNCONSUMED')
        for path in('implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run001.v1.json',
            'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim001.v1.json',DRIVER):q.pin(path)
        compile(q.text(DRIVER),DRIVER,'exec');q.finish();guard.check(force=True)
        row.update(state='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE',code_proof_sha256=q.snapshots[code_path]['sha256'],
            public_preflight_sha256=q.snapshots[preflight_path]['sha256'],fixed_worker_denial_sha256=q.snapshots[denial_path]['sha256'],entry_dependency_paths=paths,
            generation=2,live_session_qualification_still_required=True,current002_claim_unconsumed=True,original001_preserved=True,
            new_native_execution_authorization_not_inferred=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'GENERATION002_READINESS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,r.compact.pack(row),NS(require=c.require,exact=a.exact));print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


def main():
    if sys.argv[1:]==['--generation002']:return current_generation002()
    r.c.require(not sys.argv[1:],'ENTRY_READINESS_CLOSED_MODE')
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'ENTRY_READY413_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_EXTERNAL_ENTRY_RUNTIME_READINESS413',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,native_startup_qualified=False,fixed_eight_executed=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        values={}
        for path,sha in ((CODE,CODE_SHA),(PREFLIGHT,PREFLIGHT_SHA),(DENIAL,DENIAL_SHA),(EXTERNAL,EXTERNAL_SHA)):
            values[path]=r.compact.unpack(q.json(path));c.require(q.snapshots[path]['sha256']==sha,'EXACT_IMMUTABLE_IMPLEMENTATION_AND_EXTERNAL_EVIDENCE')
        code,preflight,denial,external=(values[p]for p in(CODE,PREFLIGHT,DENIAL,EXTERNAL))
        c.require(code['state']=='PASS_QUALIFIED_BATCH_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE'
            and code['contracts']==dict(run=42,errors=0,failures=0,skipped=0)and code['cleanup']is True
            and code['fresh_inputs']==code['final_fresh_hashes']==228 and code['affected_kernel_cases_reexecuted']==6,
            'CURRENT_ENTRY42_CONTRACTS_AND_228_SOURCE_CLOSURE')
        c.require(len(code['steps'])==1 and code['steps'][0]['exit_code']==0 and code['steps'][0]['cleanup']is True
            and len(code['steps'][0]['tests'])==10 and all(test[1]=='ok'for test in code['steps'][0]['tests'])
            and code['steps'][0]['stderr_bytes']==0,'CURRENT_FIXED_RELEASE_PS10_MODELS_ALREADY_PASSED_NOT_REPLAYED')
        c.require(preflight['state']=='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'
            and preflight['mode']=='preflight_only'and preflight['cleanup']is True
            and preflight['fresh_inputs']==preflight['final_fresh_hashes']==222
            and all(preflight[k]==1 for k in('external_native_final_hashes','external_shell_final_hashes','external_runtime_final_hashes'))
            and preflight['native_claim_created']is False and preflight['fixed_eight_executed']is False
            and preflight['native_startup_qualified']is False,'ACTUAL_PUBLIC_CLI_CLOSED_ALL_THREE_EXECUTABLES_WITHOUT_NATIVE_CLAIM')
        checks=preflight['prerequisites'];c.require(checks['failed_prerequisites']==['caller_lifecycle_native_safe']
            and checks['closed_errors']==dict(caller_lifecycle_native_safe='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            and checks['checks']['caller_lifecycle_native_safe']is False
            and all(v is True for k,v in checks['checks'].items()if k!='caller_lifecycle_native_safe')
            and checks['process_created']is False and checks['COM_activated']is False and checks['document_opened']is False,
            'PUBLIC_CLI_DENIED_ONLY_ORIGINAL_CALLER_JOB_NOT_PRODUCT_FAILURE_OR_EXTERNAL_PERMIT')
        c.require(denial['state']=='PASS_ACTUAL_FIXED_WORKER_KERNEL_READY_DENIAL_BEFORE_ALL_CASE_IO_NOT_NATIVE_OR_GATE'
            and denial['cleanup']is True and denial['fresh_inputs']==denial['final_fresh_hashes']==230
            and denial['external_shell_final_hashes']==1 and denial['native_constructor_trap_calls']==0
            and denial['all_eight_native_directories_absent_after']is True and len(denial['steps'])==1,
            'ACTUAL_FULL_WORKER_READY_DENIAL_WITHOUT_NATIVE_CONSTRUCTOR_OR_CASE_IO')
        step=denial['steps'][0];summary=step['handler_summary'];result=step['result'];job=step['owned_job']
        c.require(step['exit_code']==2 and step['requests']==1 and step['cleanup']is True and step['stderr_bytes']==0
            and step['io_threads_joined']is True and summary['ready_denied_before_case_io']is True and summary['query_handle_closed']is True
            and summary['actual_worker_kernel_binding']['exact_live_worker_observed']is True
            and summary['actual_worker_kernel_binding']['original_one_percent_job_member']is True
            and job['owned_tree_empty']is True and job['job_handle_closed']is True and job['cleanup_confirmed']is True
            and job['last_job_accounting']['active_processes']==0 and job['kill_on_close']is False
            and job['forced_termination_invoked']is False,'ACTUAL_KERNEL_BINDING_QUERY_JOB_IO_CLEANUP_NO_FORCE_KILL')
        c.require(result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='current_live_release'
            and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0
            and result['probe_lease_closed']is True and result['native_startup_qualified']is False,
            'WORKER_EXIT2_PRESERVED_AS_EXPECTED_DENIAL_NOT_NATIVE_SUCCESS')
        c.require(external['state']=='OBSERVED_EXTERNAL_JOBLESS_PREREQUISITES_EMPTY_LIMITS_NOT_NATIVE_OR_SESSION'
            and external['cleanup']is True and external['fresh_inputs']==external['final_fresh_hashes']==200
            and external['fixed_eight_executed']is False and external['native_startup_qualified']is False,
            'COMPLETED_USER_INSPECTION001_OBSERVATION_PRESERVED_NOT_NEXT_SESSION_PERMIT')
        for proof in(code,preflight,denial):
            for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_IMPLEMENTATION_AND_ACTUAL_READONLY_EXECUTION_SOURCES_UNCHANGED')
        paths=code['entry_dependency_paths'];c.require(type(paths)is list and len(paths)==218 and len(set(paths))==len(paths)
            and set(paths)<=set(q.snapshots),'ALL218_CURRENT_EXTERNAL_ENTRY_DEPENDENCIES_COVERED')
        from crossref_external_batch_runtime import absent_attempts
        absent_attempts()
        for path in('implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim001.v1.json',
            'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run001.v1.json'):
            target=c.ROOT/path;c.require(not target.exists()and not target.is_symlink(),'NO_NATIVE_CLAIM_OR_RUN_OUTPUT_CONSUMED')
        compile(q.text(DRIVER),DRIVER,'exec');q.finish();guard.check(force=True)
        row.update(state='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE',
            code_proof_sha256=CODE_SHA,public_preflight_sha256=PREFLIGHT_SHA,fixed_worker_denial_sha256=DENIAL_SHA,
            completed_external_inspection001_sha256=EXTERNAL_SHA,entry_dependency_paths=paths,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            live_session_qualification_still_required=True,all_eight_attempts_absent=True,native_claim_absent=True,
            next_work='user_same_external_jobless_invocation_live_session_qualification_then_single_fixed_eight_capture')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'ENTRY_READY413_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
