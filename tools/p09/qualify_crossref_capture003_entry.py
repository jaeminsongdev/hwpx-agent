"""494: current003 code/preflight/actual-denial package closure, no test or Native replay."""
import json,re,sys,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch as entry
import crossref_capture003_namespace as namespace

SELF='tools/p09/qualify_crossref_capture003_entry.py'
NAMES=entry.generation_names(current003=True)
OUTPUT=NAMES['ready']
PREFLIGHT='implementation/p09/evidence/p09-361-external-qualified-generation003-preflight.v1.json'
DENIAL='implementation/p09/evidence/p09-361-capture003-worker-denial493.v1.json'

def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--close-current003-package'],'CAPTURE003_READY_CLOSED_MODE')
    c.require(not(c.ROOT/OUTPUT).exists(),'CAPTURE003_READY494_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None
    row=dict(state='FAILED_CAPTURE003_IMPLEMENTATION_READINESS',own_cpu_selection=selection,generation=3,
        actual_worker_ROT_Hancom_COM_or_test_replayed=False,native_startup_qualified=False,fixed_eight_executed=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);values={}
        for path,sha in((NAMES['code'],'a5433e8c7a73708615929614f4a5fec054dd3633d25108c977e218f1c29837dd'),
            (PREFLIGHT,'fd9c596086dec88cfc51d176f5d344f47baa4151d9dfb2b78939d5b8e0eaea91'),
            (DENIAL,'1ba33e4826b8a3c0563b760d25599d5bb439e044ec07e5dc68849fb908e245c5')):
            values[path]=r.compact.unpack(q.json(path));c.require(q.snapshots[path]['sha256']==sha,'EXACT_IMMUTABLE_CURRENT003_PREPARATION_EVIDENCE')
        code,preflight,denial=values[NAMES['code']],values[PREFLIGHT],values[DENIAL]
        c.require(code['state']==entry.CODE_STATE and code['generation']==3 and code['cleanup']is True
            and code['fresh_inputs']==code['final_fresh_hashes']==236 and code['whole_original_runtime_ast_inverse_verified']is True
            and code['contracts']==dict(run=30,errors=0,failures=0,skipped=0),'EXACT003_NEW25_AFFECTED5_CURRENT_CODE492')
        c.require(preflight['state']=='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'and preflight['generation']==3
            and preflight['cleanup']is True and preflight['fresh_inputs']==preflight['final_fresh_hashes']==229
            and all(preflight[k]==1 for k in('external_native_final_hashes','external_shell_final_hashes','external_runtime_final_hashes'))
            and preflight['native_claim_created']is False and preflight['fixed_eight_executed']is False,'ACTUAL003_PUBLIC_PREFLIGHT_NO_NATIVE_OR_CLAIM')
        prerequisites=preflight['prerequisites']
        c.require(prerequisites['failed_prerequisites']==['caller_lifecycle_native_safe']
            and prerequisites['closed_errors']==dict(caller_lifecycle_native_safe='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            and prerequisites['checks']['caller_lifecycle_native_safe']is False
            and all(v is True for k,v in prerequisites['checks'].items()if k!='caller_lifecycle_native_safe')
            and prerequisites['process_created']is False and prerequisites['COM_activated']is False and prerequisites['document_opened']is False,
            'CURRENT003_CALLER_JOB_ONLY_DENIAL_NOT_EXTERNAL_SESSION_PERMIT')
        c.require(denial['state']=='PASS_ACTUAL_FIXED_WORKER_KERNEL_READY_DENIAL_BEFORE_ALL_CASE_IO_NOT_NATIVE_OR_GATE'
            and denial['generation']==3 and denial['cleanup']is True and denial['fresh_inputs']==denial['final_fresh_hashes']==239
            and denial['external_shell_final_hashes']==1 and denial['native_constructor_trap_calls']==0
            and denial['all_eight_native_directories_absent_after']is True and len(denial['steps'])==1,'ACTUAL003_WORKER_READY_PREFIX_ONLY_NOT_NATIVE_OR_CASE_IO')
        step=denial['steps'][0];summary=step['handler_summary'];result=step['result'];job=step['owned_job']
        c.require(step['exit_code']==2 and step['requests']==1 and step['cleanup']is True and step['stderr_bytes']==0 and step['io_threads_joined']is True
            and summary['ready_denied_before_case_io']is True and summary['query_handle_closed']is True
            and summary['actual_worker_kernel_binding']['exact_live_worker_observed']is True
            and summary['actual_worker_kernel_binding']['original_one_percent_job_member']is True
            and job['owned_tree_empty']is True and job['job_handle_closed']is True and job['cleanup_confirmed']is True
            and job['last_job_accounting']['active_processes']==0 and job['kill_on_close']is False and job['forced_termination_invoked']is False,
            'CURRENT003_KERNEL_QUERY_JOB_IO_COMPLETE_CLEANUP_WITHOUT_FORCE_KILL')
        c.require(result['state']=='fixed_eight_worker_failed_or_uncertain'and result['phase']=='current_live_release'
            and result['completed_callback_cases']==0 and result['retained_live_or_uncertain_owners']==0 and result['probe_lease_closed']is True
            and result['native_startup_qualified']is False,'CURRENT003_EXPECTED_READY_DENIAL_NOT_NATIVE_SUCCESS')
        for proof in(code,preflight,denial):
            for pin in proof['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL_CURRENT003_SOURCE_AND_ACTUAL_PREPARATION_INPUTS_UNCHANGED')
        paths=code['entry_dependency_paths']
        c.require(len(paths)==len(set(paths))==224 and set(paths)<=set(q.snapshots)
            and entry.runtime.CAPTURE003_CASE_PATHS<=set(paths)|set(entry.runtime.fixed_input_pins(True)),'ALL224_ENTRY_AND_EVERY003_CASE_INPUTS_CLOSED')
        namespace.require_absent(c.ROOT)
        for key in('claim','output','notice','cleanup_notice'):
            target=c.ROOT/NAMES[key];c.require(not target.exists()and not target.is_symlink(),'CURRENT003_NATIVE_SCOPE_UNCONSUMED')
        for path,sha in(
            ('implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run001.v1.json',None),
            ('implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run002.v1.json','937f7e344845513faf0316e581a52657d803fce026ab6ae05f175dad353fe7da')):
            pin=q.pin(path)
            if sha:c.require(pin['sha256']==sha,'ORIGINAL_FAILED002_NOT_REWRITTEN')
        q.pin(SELF);q.finish();guard.check(force=True)
        row.update(state='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE',
            code_proof_sha256=q.snapshots[NAMES['code']]['sha256'],public_preflight_sha256=q.snapshots[PREFLIGHT]['sha256'],
            fixed_worker_denial_sha256=q.snapshots[DENIAL]['sha256'],entry_dependency_paths=paths,current003_claim_unconsumed=True,
            original001_002_preserved=True,live_session_qualification_still_required=True,new_native_execution_authorization_not_inferred=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE003_READINESS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
