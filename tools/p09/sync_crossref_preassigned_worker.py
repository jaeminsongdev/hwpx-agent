"""406: independent full405 source closure + docs, no test/worker/Native replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-worker-sync406.v1.json'
DRIVER='tools/p09/sync_crossref_preassigned_worker.py'
RUNTIME='implementation/p09/evidence/p09-361-crossref-preassigned-preparation-drain405.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-owner-sync403.v1.json'
STATE='CURRENT_STATE.md';READY='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
OWNER='implementation/p09/P09_CROSSREF_PREASSIGNED_OWNER_PROGRESS.md'
NEW='implementation/p09/P09_CROSSREF_PREASSIGNED_WORKER_PROGRESS.md'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_WORKER406_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_WORKER_SOURCE_DOC_SYNC406',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=r.compact.unpack(q.json(RUNTIME));base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[RUNTIME]['sha256']=='548c544c6ac4de2fbcfdbd7d6a3e4e8e4def5af6878030d43aa4237d637dbae0'
            and run['state']=='PASS_PRESERVED20_DRAIN4_ACTUAL_WORKER1_CONTROLLER_DENIAL_COMPLETE_CLEANUP_NOT_NATIVE_OR_GATE'
            and run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==218 and run['external_shell_final_hashes']==1
            and (run['current_distinct_contracts'],run['preserved_contracts'],run['new_contracts'],run['actual_worker_integration_cases'])==(24,20,4,1)
            and run['contracts']==dict(run=4,errors=0,failures=0,skipped=0)and not run['failed_contract_names']
            and not run['actual_Hangul_ROT_COM_or_native_started']and not run['actual_native7_job_started']
            and not run['unaffected_successes_replayed']and run['affected_readonly_worker_reexecuted']and len(run['steps'])==1,
            'EXACT405_CONTRACTS24_ACTUAL_DENIAL_WORKER1_NOT_NATIVE_OR_OLD_SUCCESS_REPLAY')
        step=run['steps'][0];profile=step['owned_job'];drain=profile['post_terminal_tree_drain'];result=step['result']
        c.require(step['exit_code']==0 and step['cleanup']and step['requests']==2 and step['stderr_bytes']==0 and step['io_threads_joined']
            and profile['owned_tree_empty']and profile['job_handle_closed']and profile['last_job_accounting']['active_processes']==0
            and not profile['kill_on_close']and not profile['forced_termination_invoked']and drain['initial_active_prefix']==[1,0]
            and drain['observations']==2 and drain['elapsed_seconds']==.047 and drain['same_job_observed']and drain['final_active']==0
            and profile['limits_readback']['verified']and not profile['limits_readback']['time_limit_installed']
            and result['probe_lease_closed']and not result['native_directory_or_owner_or_trace_created']and run['retained_compiler_scratch_entries']==0,
            'ACTUAL_SAME_JOB1_TO0_BEFORE_ORIGINAL_CLOSE_ALL_THREADS_PROBE_AND_TEMP_CLEAN')
        c.require(q.snapshots[BASE]['sha256']=='bfcb10e87018bf6443bf6706d8cb85780e03087b071d647c6b8c1dd5b25e04a0'
            and base['cleanup']and base['fresh_inputs']==base['final_fresh_hashes']==24,'EXACT403_PREVIOUS_DOCUMENT_BASELINE')
        for pin in run['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL218_ACTUAL405_INPUTS_ORIGINAL_NATIVE_GUARDS_AND_FAILURE_RECORDS_UNCHANGED')
        old={p['path']:p for p in base['source_pins']}
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 사전배정 객체 연결과 종료 경로'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 제한된 worker와 고정 사례 제어 연결'),'ONE_CURRENT_PREPARATION_WORKER_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_USER_HISTORY_NATIVE_FAILURES_AND_EXTERNAL001_RESULTS_PRESERVED')
        ready=q.text(READY);start=ready.index('## 제한된 worker와 고정 사례 controller');end=ready.index('## 현재 확인 결과',start)
        r.audit.inverse(ready[:start]+ready[end:],old[READY],'ONLY_PREPARATION_WORKER_CONTROLLER_SECTION_ADDED')
        owner=q.text(OWNER)
        after='후속 [worker와 고정 사례 제어 연결](P09_CROSSREF_PREASSIGNED_WORKER_PROGRESS.md)은 준비 전용1% worker에서\n새 controller의 첫 checkpoint 거부/실패 finish/정리를 확인했다.405는 이전20보존+새 tree 배출4와\n실제 준비 통합1개가 통과했으며 한글/실물 폴더/owner/trace는0이다. 다음은 독립 입력 대조 뒤 외부\njobless Native 자격 연결/진입점과 실제 Native7% 사전배정·기존 객체/창 결속·정상 종료 검증이다.\n'
        before='다음은 새 private factory/ports를 제한된 worker1%와 고정8종 controller에 연결하고, 한글 생성 전에\nNative7% Job 배정과 정확한 기존 객체/창 결속·정상 종료까지 별도로 자격 검증하는 것이다.\n'
        c.require(owner.count(after)==1,'ONE_OWNER_WORKER_FOLLOWUP_UPDATE');r.audit.inverse(owner.replace(after,before),old[OWNER],'ALL_ORIGINAL_OWNER21_AND_FAILURE_LINEAGE_PRESERVED')
        progress=q.text(NEW);q.pin(DRIVER)
        for text in(progress,state[:state.index(marker)]):
            for token in('218fresh/final218','24','20','4','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','공식158/249','잔여91',
                'P09/A12/A13 OPEN','목표ACTIVE','P10 미시작','50.172초','75.34MiB','62.65%','31.6489%','0.047초'):
                c.require(token in text,'CURRENT_PREPARATION_SCOPE_COUNTS_RESOURCES_AND_UNCHANGED_GATE_BOUNDARIES_MATCH')
        for token in('404','FAILED','cleanupFalse','405','318.5625MiB','1%','실제 Native','진입점','RetainedStates',
            '외부 검사001','재실행하거나','정확한 v2 거부','같은 Job','최대8개'):
            c.require(token in progress,'ORIGINAL_FAILURE_LIFECYCLE_SCOPE_LIMITS_AND_REMAINING_NATIVE_ENTRY_EXPLICIT')
        allowed={'https://forum.developer.hancom.com/t/topic/564','https://forum.developer.hancom.com/t/rot/1701',
            'https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject'}
        for path,text in((NEW,progress),(READY,ready),(OWNER,owner)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):c.require(link in allowed,'ONLY_PREVIOUSLY_REVIEWED_PRIMARY_REFERENCES');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_CURRENT_SOURCE_AND_FAILURE_EVIDENCE_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_FULL218_PREPARATION_SOURCE_CLOSURE_AND_WORKER_CONTROLLER_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='external_jobless_native_session_qualification_entry_and_existing_owner_worker_connection_before_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREASSIGNED_WORKER406_SOURCE_DOC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
