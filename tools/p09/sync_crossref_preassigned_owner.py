"""403: current owner/successor21 evidence and surgical docs only; no worker/test replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-owner-sync403.v1.json'
DRIVER='tools/p09/sync_crossref_preassigned_owner.py'
RUNTIME='implementation/p09/evidence/p09-361-crossref-preassigned-owner-parameters402.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-preassigned-host-sync399.v1.json'
STATE='CURRENT_STATE.md';READY='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
OWNER='implementation/p09/P09_CROSSREF_EXISTING_OWNER_PROGRESS.md'
HOST='implementation/p09/P09_CROSSREF_PREASSIGNED_HOST_PROGRESS.md'
NEW='implementation/p09/P09_CROSSREF_PREASSIGNED_OWNER_PROGRESS.md'
SOURCES={'implementation/p09/tools/crossref-preassigned-owner.ps1','implementation/p09/tools/crossref-preassigned-case-ports.ps1',
    'implementation/p09/tools/test-crossref-preassigned-owner.cs','implementation/p09/tools/test-crossref-preassigned-owner.ps1',
    'implementation/p09/tools/test-crossref-preassigned-owner-recovery.ps1','tools/p09/run_crossref_preassigned_owner.py',
    'tools/p09/run_crossref_preassigned_owner_recovery.py','tools/p09/run_crossref_preassigned_owner_parameters.py',
    'implementation/p09/tools/crossref-existing-owner.cs','implementation/p09/tools/crossref-native-case-ports.ps1',
    'implementation/p09/tools/sdk-baseline-owned-session.ps1','implementation/p09/tools/crossref-dual-owner-identity.ps1',
    'tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
    'tools/p09/crossref_preassigned_host_protocol.py','implementation/p09/tools/crossref-preassigned-host-channel.ps1'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'PREASSIGNED_OWNER403_DOC_SYNC_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PREASSIGNED_OWNER_DOC_SYNC403',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=r.compact.unpack(q.json(RUNTIME));base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[RUNTIME]['sha256']=='00b62de60e3619e1726452762e2073315681653b3caf2cf5b5229523347bc67d'
            and run['state']=='PASS_PRESERVED8_REMAINING11_AFFECTED_INSTALL1_PARAMETER1_NOT_NATIVE_OR_GATE'
            and run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==217 and run['external_shell_final_hashes']==1
            and (run['current_distinct_cases'],run['preserved_successful_cases'],run['new_current_cases'])==(21,8,13)
            and not run['actual_Hangul_ROT_COM_or_native_started']and not run['unaffected_successful_tests_replayed']
            and run['affected_installation_reexecuted']and len(run['steps'])==1,'EXACT402_CURRENT_OWNER21_NOT_NATIVE_OR_UNAFFECTED_SUCCESS_REPLAY')
        step=run['steps'][0];c.require(step['exit_code']==0 and len(step['tests'])==len({n for n,s in step['tests']})==13
            and all(s=='ok'for n,s in step['tests'])and not step['safe_error_codes']and step['stderr_bytes']==0 and step['cleanup']
            and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed']
            and step['owned_job']['last_job_accounting']['active_processes']==0 and run['retained_compiler_scratch_entries']==0,
            'ACTUAL13_MARKERS_AND_COMPLETE_OWNED_WORKER_CLEANUP')
        c.require(q.snapshots[BASE]['sha256']=='6c304a6a21b829199fa43a60898e40740c90ade9bb4c4bc07690ee2bb285fb2c'
            and base['cleanup']and base['fresh_inputs']==base['final_fresh_hashes']==23,'EXACT399_PREVIOUS_DOCUMENT_BASELINE')
        pins={p['path']:p for p in run['source_pins']};old={p['path']:p for p in base['source_pins']}
        for path in sorted(SOURCES):c.require(q.pin(path)==pins[path],'ALL_CURRENT_OWNER_SUCCESSOR_MODELS_AND_ORIGINAL_NATIVE_INPUTS_UNCHANGED')
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 사전배정 소유자 통신 연결'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 사전배정 객체 연결과 종료 경로'),'ONE_CURRENT_OWNER_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_USER_STATE_EXTERNAL001_AND_FAILURE_HISTORY_PRESERVED')
        ready=q.text(READY);start=ready.index('## 사전배정 객체 factory와 종료');end=ready.index('## 현재 확인 결과',start)
        r.audit.inverse(ready[:start]+ready[end:],old[READY],'ONLY_OWNER_FACTORY_AND_CLEANUP_READINESS_SECTION_ADDED')
        host=q.text(HOST)
        after='후속 [객체 factory와 종료 경로](P09_CROSSREF_PREASSIGNED_OWNER_PROGRESS.md)는 기존 adapter의 lease를\n명시적 successor에 연결하고 원 P58/CIM 검사와 canonical identity·불명 owner 보존·단1회 참조 해제를\n구현했다.402의 현재 고유21개는 이전8보존+미실행/영향/신규13pass이며 실제 ROT/한글은 미실행이다.\n다음은 이 successor와 제한된 worker/controller의 전체 통합이다. 원 case ports/COM factory와 실물\n진입점은 그대로이며 현재 v2나 모의 결과만으로 실물 경로를 열지 않는다.\n'
        before='다음은 [기존 객체 adapter](P09_CROSSREF_EXISTING_OWNER_PROGRESS.md)의 lease를 worker의 owner factory와\ncase ports에 연결하는 명시적 successor다. 원 P58 owner/CIM 검사와 canonical kernel identity를 함께\n유지하고, adapter의 COM 참조 소유권과 원 cleanup의 FinalRelease가 중복되지 않도록 정리해야 한다.\n원 case ports는 여전히 COM 생성 뒤 admission하므로 현재 v2 연결만으로 실물 경로를 열지 않는다.\n'
        c.require(host.count(after)==1,'ONE_HOST_OWNER_FOLLOWUP_UPDATE');r.audit.inverse(host.replace(after,before),old[HOST],'ALL_ORIGINAL_V2_PIPE25_EVIDENCE_AND_EXECUTION_BOUNDARIES_PRESERVED')
        owner=q.text(OWNER)
        after='후속 [사전배정 객체 factory와 종료 경로](P09_CROSSREF_PREASSIGNED_OWNER_PROGRESS.md)는 lease의 RCW와 원\nFinalRelease가 중복되지 않는 정리·canonical identity·불명 owner 보존을 명시적 successor에 구현했다.\n402는 현재 고유21개=이전8보존+이번13pass이며 실제 ROT/COM/한글은 미실행이다. 다음은 제한된 worker와\n고정8종 controller에 이 successor를 연결하고 실제 세션 자격을 확인하는 것이다. 이어서\n'
        before='다음은 제한된 worker가 정확한 기존 객체를 가져오도록 연결하고 lease의 RCW와 원 FinalRelease가 중복되지 않는\n정리 경계를 구현하는 것이다. 이어서\n'
        c.require(owner.count(after)==1,'ONE_ADAPTER_SUCCESSOR_STATUS_UPDATE');r.audit.inverse(owner.replace(after,before),old[OWNER],'ALL_ORIGINAL_ADAPTER_RESULTS_FAILURES_AND_SOURCE_REFERENCES_PRESERVED')
        progress=q.text(NEW);q.pin(DRIVER)
        for text in(progress,state[:state.index(marker)]):
            for token in('217fresh/final217','21','13','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','공식158/249','잔여91',
                'P09/A12/A13 OPEN','목표ACTIVE','P10 미시작','31.063초','70.93MiB','23.69%','29.4358%'):
                c.require(token in text,'CURRENT_MODEL_COUNTS_RESOURCE_VALUES_AND_UNCHANGED_GATES_MATCH')
        for token in('400','401','402','CreateLease','FAILED','FinalRelease','ReleaseComObject1회','lease.Dispose1회',
            '매개변수','worker1%','재실행하거나','실제 Attach/ROT/COM/한글은 호출하지 않았다'):
            c.require(token in progress,'FAILURES_REFERENCE_OWNERSHIP_PARAMETERS_AND_REMAINING_NATIVE_SCOPE_EXPLICIT')
        allowed={'https://forum.developer.hancom.com/t/topic/564','https://forum.developer.hancom.com/t/rot/1701',
            'https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject'}
        for path,text in((NEW,progress),(READY,ready),(HOST,host),(OWNER,owner)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):c.require(link in allowed,'ONLY_PREVIOUSLY_REVIEWED_PRIMARY_REFERENCES');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_NEW_CURRENT_AND_FAILURE_EVIDENCE_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_OWNER_SUCCESSOR21_FAILURE_LINEAGE_AND_CLEANUP_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='one_percent_worker_fixed_eight_controller_then_actual_preassigned_existing_owner_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'PREASSIGNED_OWNER_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
