"""409: full408 source closure + session candidate/actual-denial docs; no execution replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-session-qualification-sync409.v1.json'
DRIVER='tools/p09/sync_crossref_session_qualification.py'
RUNTIME='implementation/p09/evidence/p09-361-crossref-session-ready-denial408.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-worker-sync406.v1.json'
STATE='CURRENT_STATE.md';READY='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
WORKER='implementation/p09/P09_CROSSREF_PREASSIGNED_WORKER_PROGRESS.md'
NEW='implementation/p09/P09_CROSSREF_SESSION_QUALIFICATION_PROGRESS.md'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'SESSION_QUALIFICATION409_DOC_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SESSION_QUALIFICATION_SOURCE_DOC_SYNC409',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=r.compact.unpack(q.json(RUNTIME));base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[RUNTIME]['sha256']=='3f10ad6e031da18b2c113213bb5f98087ced0a15b9e137d18d977e70ef4d7458'
            and run['state']=='PASS_ACTUAL_SESSION_WORKER_KERNEL_BINDING_ORIGINAL_ROOT_DENIAL_NOT_NATIVE_OR_GATE'
            and run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==209 and run['external_shell_final_hashes']==1
            and run['original_native_guard_used']and not run['actual_Hangul_ROT_COM_or_native_started']
            and not run['old_successful_tests_replayed']and len(run['steps'])==1,'EXACT408_REAL_WORKER_AND_ORIGINAL_PARENT_DENIAL_NOT_NATIVE_SUCCESS')
        step=run['steps'][0];profile=step['owned_job'];session=step['session_summary'];result=step['result'];binding=step['actual_worker_kernel_binding']
        c.require(step['exit_code']==2 and step['cleanup']and step['requests']==2 and step['stderr_bytes']==0 and step['io_threads_joined']
            and step['native_constructor_trap_calls']==0 and binding['exact_live_worker_observed']and binding['original_one_percent_job_member']
            and session['worker_lease_closed']and session['native_backend_profile']is None and not session['lifecycle_candidate_observed']
            and session['primary_error']=='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE'
            and profile['owned_tree_empty']and profile['job_handle_closed']and profile['last_job_accounting']['active_processes']==0
            and not profile['kill_on_close']and not profile['forced_termination_invoked']and run['retained_compiler_scratch_entries']==0,
            'ACTUAL_KERNEL_JOB_BOUND_DENIAL_WITH_ALL_QUERY_IO_AND_WORKER_HANDLES_CLOSED_NO_NATIVE_CONSTRUCTOR')
        c.require(result['state']=='session_worker_failed_or_uncertain'and result['phase']=='host_ready'and not result['COM_owner_observed']
            and not result['document_opened_or_saved']and not result['fixed_eight_executed']and not result['native_startup_qualified']
            and result['cleanup']==dict(close_without_dirty_prompt_returned=False,quit_invoked=False,reference_release_returned=False,remaining_owned_process_count=-1),
            'EXIT2_NATIVE_ABSENCE_AND_UNKNOWN_NATIVE_CLEANUP_NOT_RELABELED_SESSION_PASS')
        c.require(q.snapshots[BASE]['sha256']=='2d5a5f670b5ac5d0034a64558b777bdb640ad5a92335e16ad55f721b45ba7892'
            and base['cleanup']and base['fresh_inputs']==base['final_fresh_hashes']==225,'EXACT406_PREVIOUS_SOURCE_AND_DOCUMENT_BASELINE')
        for pin in run['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL209_ACTUAL_SESSION_DENIAL_INPUTS_ORIGINAL_NATIVE_CODE_AND_407_EVIDENCE_UNCHANGED')
        old={p['path']:p for p in base['source_pins']}
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 제한된 worker와 고정 사례 제어 연결'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 세션 자격 프로토콜과 실제 worker 결속'),'ONE_CURRENT_SESSION_QUALIFICATION_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_USER_NATIVE_FAILURES_SOURCE_HISTORY_AND_EXTERNAL001_PRESERVED')
        ready=q.text(READY);start=ready.index('## 세션 자격 프로토콜과 실제 worker 결속');end=ready.index('## 현재 확인 결과',start)
        r.audit.inverse(ready[:start]+ready[end:],old[READY],'ONLY_SESSION_CANDIDATE_AND_ACTUAL_DENIAL_SECTION_ADDED')
        worker=q.text(WORKER)
        after='후속 [세션 자격 프로토콜](P09_CROSSREF_SESSION_QUALIFICATION_PROGRESS.md)은 신규 계약35개와 실제1% worker의\nkernel/Job 결속·원 caller Job 거부·정리를 검증했다. 실제 Native constructor는0회다.\n다음은 세션 candidate와 고정8종을 동일 외부 호출자에 연결할 Python 진입점과 최종 증거 결속이다.\n준비 worker의 통과는 실제 Native7% 생성 시 배정이나 기존 ROT/COM owner·\n'
        before='다음은 새 코드/원 입력의 독립 대조 뒤, 외부 jobless 호출자에서 실제 Native 세션을 자격 검증할 연결과\n진입점을 완성하는 것이다. 준비 worker의 통과는 실제 Native7% 생성 시 배정이나 기존 ROT/COM owner·\n'
        c.require(worker.count(after)==1,'ONE_PREPARATION_WORKER_SESSION_FOLLOWUP_UPDATE');r.audit.inverse(worker.replace(after,before),old[WORKER],'ALL_ORIGINAL_PREPARATION_24_AND_ACTUAL405_DRAIN_FAILURE_LINEAGE_PRESERVED')
        progress=q.text(NEW);q.pin(DRIVER)
        for text in(progress,state[:state.index(marker)]):
            for token in('209fresh/final209','35','2','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','공식158/249','잔여91',
                'P09/A12/A13 OPEN','목표ACTIVE','P10 미시작','30.234초','72.04MiB','24.65%','30.1071%'):
                c.require(token in text,'CURRENT_SESSION_CODE_DENIAL_SCOPE_COUNTS_RESOURCES_AND_UNCHANGED_GATES_MATCH')
        for token in('407','408','Python25','source10','206fresh/final206','41.610초','36.91%','28.3468%',
            'query/synchronize','100ns','1%','PARENT_LIFECYCLE_NOT_NATIVE_SAFE','trap','호출0회','remaining-1',
            '진입점','동일한 외부 jobless 호출자','재실행하지 않으며'):
            c.require(token in progress,'MODELS_ACTUAL_KERNEL_DENIAL_HANDLES_SOURCE_CLOSURE_AND_REMAINING_FULL_ENTRY_EXPLICIT')
        allowed={'https://forum.developer.hancom.com/t/topic/564','https://forum.developer.hancom.com/t/rot/1701',
            'https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject'}
        for path,text in((NEW,progress),(READY,ready),(WORKER,worker)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):c.require(link in allowed,'ONLY_PREVIOUSLY_REVIEWED_PRIMARY_REFERENCES');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_CURRENT_SESSION_SOURCE_AND_PROOF_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_FULL209_SESSION_CANDIDATE_SOURCE_AND_ACTUAL_ROOT_DENIAL_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='same_external_jobless_caller_full_qualification_and_fixed_eight_entry_with_live_source_cleanup_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SESSION_QUALIFICATION409_SOURCE_DOC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
