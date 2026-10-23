"""Close current004 preparation from changed code + public preflight + unchanged558 worker.

Does not run a worker, activate COM, start Native, replay tests or grant a new
human execution permission. The actual external caller must still pass its own
live prerequisites and one-shot session qualification before all eight cases.
"""
import json,re,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_runtime004_admission as admission

SELF='tools/p09/qualify_crossref_runtime004560.py'
NAMES=entry.generation_names(current004=True)
OUTPUT=NAMES['ready']
CODE_SHA='32d846850609e7abd31d09cf9352671c418b3b25e2d680692ba19050a2689a78'
PREFLIGHT='implementation/p09/evidence/p09-361-external-qualified-generation004-runtime559-preflight.v1.json'
PREFLIGHT_SHA='dcb3274de0d131e5494adbc843dc8bf1da62d40e5d752a4a6c878bd885f26738'
ARCHIVE='implementation/p09/source-archive/p361-runtime004-559/'
PREIMAGES={'tools/p09/run_external_crossref_fixed_batch.py':ARCHIVE+'entry-before.py',
    'tools/p09/crossref_external_batch_runtime.py':ARCHIVE+'runtime-before.py',
    'tools/p09/tests/test_crossref_generation004.py':ARCHIVE+'models-before.py'}

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--close-preparation-only'],'P560_FIXED_NON_NATIVE_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'P560_IMMUTABLE_PREPARATION_PACKAGE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    start=time.monotonic();q=images=shell=native=None
    row=dict(state='FAILED_RUNTIME004_PREPARATION',own_cpu_selection=selection,generation=4,
        actual_worker_ROT_Hancom_COM_or_test_replayed=False,native_startup_qualified=False,fixed_eight_executed=False,
        Native011_executed=False,new_native_execution_authorization_not_inferred=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(SELF)
        before=entry.installed.current_identity(guard.windows)
        code=r.compact.unpack(q.json(NAMES['code']));preflight=r.compact.unpack(q.json(PREFLIGHT));host=r.compact.unpack(q.json(admission.QUALIFICATION))
        c.require(q.snapshots[NAMES['code']]['sha256']==CODE_SHA and code['state']==entry.CODE_STATE and code['generation']==4
            and code['cleanup']is True and code['fresh_inputs']==code['final_fresh_hashes']==267
            and code['contracts']==dict(run=38,errors=0,failures=0,skipped=0)
            and code['whole_previous_source_outside004_admission_preserved']is True
            and code['retained_runtime_and_worker_components_freshly_identical']is True
            and code['old_Native_or_249_or_worker_PS_models_replayed']is False,'P560_EXACT559_NEW11_AFFECTED27_AND_UNCHANGED_WORKER')
        c.require(q.snapshots[PREFLIGHT]['sha256']==PREFLIGHT_SHA
            and preflight['state']=='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'
            and preflight['generation']==4 and preflight['cleanup']is True
            and preflight['fresh_inputs']==preflight['final_fresh_hashes']==232
            and preflight['external_native_final_hashes']==preflight['external_shell_final_hashes']==1
            and preflight['external_runtime_final_hashes']==2 and preflight['native_claim_created']is False
            and preflight['fixed_eight_executed']is False,'P560_ACTUAL_CURRENT_PUBLIC_PREFLIGHT_CLOSED_NO_NATIVE_OR_CLAIM')
        prerequisites=preflight['prerequisites']
        c.require(prerequisites['failed_prerequisites']==['caller_lifecycle_native_safe']
            and prerequisites['closed_errors']==dict(caller_lifecycle_native_safe='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            and prerequisites['checks']['caller_lifecycle_native_safe']is False
            and all(v is True for k,v in prerequisites['checks'].items()if k!='caller_lifecycle_native_safe')
            and all(prerequisites[k]is False for k in('process_created','COM_activated','document_opened','permission_dialog_requested')),
            'P560_CODEX_PARENT_JOB_ONLY_DENIAL_NOT_EXTERNAL_SESSION_PASS')
        for proof in(code,preflight):
            for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'P560_CURRENT_PREPARATION_INPUTS_FRESHLY_IDENTICAL')
        for pin in host['source_pins']:
            current=q.pin(PREIMAGES.get(pin['path'],pin['path']))
            c.require((current['bytes'],current['sha256'])==(pin['bytes'],pin['sha256']),'P560_RETAINED558_WORKER_INPUTS_OR_EXACT_REVIEWED_PREIMAGES')
        row['runtime004_qualification']=admission.require_qualification(q)
        step,=host['steps'];summary,result,job=step['handler_summary'],step['result'],step['owned_job']
        c.require(step['stderr_bytes']==0 and summary['query_handle_closed']is True
            and summary['actual_worker_kernel_binding']['exact_live_worker_observed']is True
            and summary['actual_worker_kernel_binding']['original_one_percent_job_member']is True
            and job['job_handle_closed']is True and job['cleanup_confirmed']is True and job['last_job_accounting']['active_processes']==0
            and job['kill_on_close']is False and job['forced_termination_invoked']is False
            and result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='current_live_release'
            and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0 and result['probe_lease_closed']is True,
            'P560_SAME_ACTUAL004_READY_DENIAL_KERNEL_QUERY_IO_JOB_CLOSED_NOT_NATIVE_SUCCESS')
        images=a.AcceptanceReader(admission.profile.fixed.PYTHON.parent,guard.check)
        row['runtime004_current_images']=admission.verify_current_reader(images)
        shell=a.AcceptanceReader(Path(entry.runtime.candidate.original.SHELL).parent,guard.check)
        c.require(shell.pin(Path(entry.runtime.candidate.original.SHELL).name)==code['external_shell_pins'][0],'P560_SAME_FIXED_SHELL')
        native=a.AcceptanceReader(Path(entry.installed.native.EXECUTABLE).parent,guard.check)
        pin=native.pin(Path(entry.installed.native.EXECUTABLE).name)
        c.require((pin['bytes'],pin['sha256'])==(entry.installed.native.EXECUTABLE_BYTES,entry.installed.native.EXECUTABLE_SHA),'P560_SAME_FIXED_HANCOM_IMAGE_NO_EXECUTION')
        paths=code['entry_dependency_paths']
        c.require(len(paths)==len(set(paths))and set(paths)<=set(q.snapshots)
            and entry.loaded_paths(exclude=(SELF,))<=set(paths)
            and entry.runtime.CAPTURE004_CASE_PATHS<=set(paths)|set(entry.runtime.fixed_input_pins(capture004_scope=True)),
            'P560_COMPLETE_CURRENT_ENTRY_AND004_CASE_CLOSURE')
        entry.runtime.absent_attempts(fixed_capture004=True)
        for key in('claim','output','notice','cleanup_notice'):
            target=c.ROOT/NAMES[key];c.require(not target.exists()and not target.is_symlink(),'P560_CURRENT004_NATIVE_SCOPE_UNCONSUMED')
        failed003='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run003.v1.json'
        failed_preflight='implementation/p09/evidence/p09-361-external-qualified-generation004-preflight.v1.json'
        c.require(q.pin(failed003)['sha256']=='901374892ce5c40986b3de473a139bf4d3579b68738419bd284f95e63a8c047a'
            and q.pin(failed_preflight)['sha256']=='79f2d1668c3fcf88edded3b2e678a743cd9dd9e42891155f3ec8ebba99d06071','P560_ORIGINAL_FAILURE_BYTES_PRESERVED')
        images.finish();shell.finish();native.finish();q.finish();guard.check(force=True)
        c.require(entry.installed.current_identity(guard.windows)==before,'P560_SAME_LIVE_KERNEL_BEFORE_AFTER')
        row.update(state='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE',
            code_proof_sha256=CODE_SHA,public_preflight_sha256=PREFLIGHT_SHA,fixed_worker_denial_sha256=admission.QUALIFICATION_SHA,
            entry_dependency_paths=paths,current004_claim_unconsumed=True,original003_and_failed_preflight_preserved=True,
            live_session_qualification_still_required=True,retained558_worker_not_rerun=True,
            external_runtime_final_hashes=images.final_fresh_hashes,external_shell_final_hashes=shell.final_fresh_hashes,
            external_native_final_hashes=native.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P560_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=entry.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
