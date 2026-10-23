"""399: v2 protocol/model/actual-pipe evidence and surgical docs; no test/Native replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-preassigned-host-sync399.v1.json'
DRIVER='tools/p09/sync_crossref_preassigned_host.py'
RUNTIME='implementation/p09/evidence/p09-361-crossref-preassigned-host398.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-existing-owner-sync397.v1.json'
STATE='CURRENT_STATE.md';READY='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
OWNER='implementation/p09/P09_CROSSREF_EXISTING_OWNER_PROGRESS.md'
SCOPE='implementation/p09/P09_CROSSREF_PREASSIGNED_SESSION_PROGRESS.md'
NEW='implementation/p09/P09_CROSSREF_PREASSIGNED_HOST_PROGRESS.md'
SOURCES={'tools/p09/crossref_preassigned_host_protocol.py','tools/p09/tests/test_crossref_preassigned_host_protocol.py',
    'tools/p09/run_crossref_preassigned_host_protocol.py','implementation/p09/tools/crossref-preassigned-host-channel.ps1',
    'implementation/p09/tools/test-crossref-preassigned-host-channel.ps1','tools/p09/crossref_preassigned_session_scope.py',
    'tools/p09/crossref_native_host_channel.py','tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py',
    'implementation/p09/tools/crossref-existing-owner.cs','implementation/p09/tools/sdk-baseline-owned-session.ps1',
    'implementation/p09/tools/crossref-native-case-ports.ps1','implementation/p09/tools/crossref-owned-active-source.ps1',
    'implementation/p09/tools/crossref-host-channel.ps1','implementation/p09/tools/crossref-case-flow.ps1'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'V2_HOST_DOC_SYNC399_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_V2_HOST_DOC_SYNC399',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);run=r.compact.unpack(q.json(RUNTIME));base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[RUNTIME]['sha256']=='93e045b3f74cf3e555d356a54cb265922c13e1ad0be02bc10fec09ddf0dd84f1'
            and run['state']=='PASS_V2_SCOPE16_X86_MODELS8_ACTUAL_PIPE152_MODEL_OWNERS_NOT_NATIVE_OR_GATE'
            and run['cleanup']and run['fresh_inputs']==run['final_fresh_hashes']==205 and run['external_shell_final_hashes']==1
            and run['contracts']==dict(run=16,errors=0,failures=0,skipped=0)and not run['failed_contract_names']
            and not run['actual_Hangul_ROT_COM_or_native_started']and not run['old_tests_replayed'],'EXACT398_NEW25_TESTS_NOT_NATIVE_OR_OLD_TEST_REPLAY')
        c.require(len(run['steps'])==2,'EXACT_TWO_READONLY_X86_WORKERS')
        for step,count in zip(run['steps'],(8,1)):
            c.require(step['exit_code']==0 and len(step['tests'])==count and len({n for n,s in step['tests']})==count
                and all(status=='ok'for name,status in step['tests'])and not step['safe_error_codes']and step['stderr_bytes']==0
                and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed']
                and step['owned_job']['last_job_accounting']['active_processes']==0,'ALL_NEW_WORKER_MARKERS_AND_OWNED_CLEANUP')
        wire=run['steps'][1];modeled=wire['modeled_host_summary']
        c.require(wire['requests']==152 and wire['admissions']==16 and wire['io_threads_joined']and wire['stream_error']is None
            and modeled['protocol']['all_eight_callback_cases_returned']and modeled['scope']['all_eight_callback_cases_returned']
            and len(modeled['scope']['retired_sessions'])==16 and modeled['scope']['closed']and not modeled['native_execution_authorized'],
            'ACTUAL152_PIPES16_MODEL_ADMISSIONS_NOT_FIXED_EIGHT_NATIVE_EXECUTION')
        c.require(q.snapshots[BASE]['sha256']=='d3c75a7b5d794d3455cb1eb1f7935930fcafc31178cab0984177a67c57430fda'
            and base['cleanup']and base['fresh_inputs']==base['final_fresh_hashes']==17,'EXACT397_PREVIOUS_DOCS_BASELINE')
        pins={p['path']:p for p in run['source_pins']};old={p['path']:p for p in base['source_pins']}
        for path in sorted(SOURCES):c.require(q.pin(path)==pins[path],'ALL_VERIFIED_NEW_PROTOCOL_MODELS_AND_ORIGINAL_NATIVE_INPUTS_UNCHANGED')
        state=q.text(STATE);marker='> 2026-10-21 P09 ACTIVE 기존 ROT 객체 연결부 컴파일 검증'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 사전배정 소유자 통신 연결'),'ONE_CURRENT_V2_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_PREVIOUS_EXTERNAL001_FAILURES_AND_USER_STATE_HISTORY_PRESERVED')
        ready=q.text(READY);start=ready.index('## 사전배정 소유자 통신');end=ready.index('## 현재 확인 결과',start)
        r.audit.inverse(ready[:start]+ready[end:],old[READY],'ONLY_NEW_V2_READINESS_SECTION_ADDED')
        owner=q.text(OWNER)
        after='[사전배정 소유자 통신](P09_CROSSREF_PREASSIGNED_HOST_PROGRESS.md)은 원 세션 scope의 descriptor를\n새 private v2로 전달하고 canonical pending owner를 대조한다.398에서 신규 Python16·PowerShell8·실제 파이프1,\n8사례/152메시지/16모의 owner admission이 통과했다. 실제 ROT/한글은 실행하지 않았고 원 adapter는 그대로다.\n다음은 제한된 worker가 정확한 기존 객체를 가져오도록 연결하고 lease의 RCW와 원 FinalRelease가 중복되지 않는\n정리 경계를 구현하는 것이다. 이어서\n'
        before='[사전배정 세션 scope](P09_CROSSREF_PREASSIGNED_SESSION_PROGRESS.md)의 현재 owner descriptor를 새 private\nhost protocol로 전달하고 제한된 worker가 정확한 기존 객체를 가져오도록 연결해야 한다. 이어서\n'
        c.require(owner.count(after)==1,'ONE_OWNER_FACTORY_NEXT_BOUNDARY_UPDATE');r.audit.inverse(owner.replace(after,before),old[OWNER],'ALL_PREVIOUS_ADAPTER_RESULTS_AND_FAILURES_PRESERVED')
        scope=q.text(SCOPE)
        after='parser3을 검증했지만 실제 ROT/한글 COM은 조회하지 않았다. [새 private v2 통신](P09_CROSSREF_PREASSIGNED_HOST_PROGRESS.md)은\n398에서 Python16·PowerShell8·실제 파이프1과8사례/152메시지/16모의 admission을 통과했다.\n다음은 기존 객체 lease의 참조 소유권/정리와 worker1% 자원 Job·owner factory의'
        before='parser3을 검증했지만 실제 ROT/한글 COM은 조회하지 않았다. 다음은 이 연결부와 worker1% 자원 Job·새 private host protocol/owner factory의'
        c.require(scope.count(after)==1,'ONE_SCOPE_V2_STATUS_UPDATE');r.audit.inverse(scope.replace(after,before),old[SCOPE],'ORIGINAL_SCOPE_AND_EXTERNAL001_NO_NEW_NATIVE_AUTHORITY')
        progress=q.text(NEW);q.pin(DRIVER)
        for text in(progress,state[:state.index(marker)]):
            for token in('205fresh/final205','152','16','CROSSREF8종 NOT_RUN','Native011 미승인/미실행','공식158/249',
                '잔여91','P09/A12/A13 OPEN','목표ACTIVE','P10 미시작','40.266초','70.91MiB','64.29%','22.2985%'):
                c.require(token in text,'NEW_V2_EVIDENCE_COUNTS_RESOURCES_AND_UNCHANGED_GATES_MATCH')
        for token in('Python 신규16','PowerShell 신규8','파이프 검사1','4096bytes','152요청','queue8','32768bytes',
            'readonly90초','FinalRelease','Native7%/worker1%','검사001은 재실행하지 않으며'):
            c.require(token in progress,'MODEL_REAL_PIPE_AND_NEXT_NATIVE_OWNERSHIP_BOUNDARIES_EXPLICIT')
        allowed={'https://forum.developer.hancom.com/t/topic/564','https://forum.developer.hancom.com/t/rot/1701',
            'https://learn.microsoft.com/en-us/windows/win32/api/objidl/nf-objidl-irunningobjecttable-getobject'}
        for path,text in((NEW,progress),(READY,ready),(OWNER,owner),(SCOPE,scope)):
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith('https://'):c.require(link in allowed,'ONLY_PREVIOUSLY_REVIEWED_PRIMARY_REFERENCES');continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'ALL_CURRENT_SOURCE_EVIDENCE_AND_HISTORY_LINKS_EXIST')
        q.finish();guard.check(force=True);row.update(state='PASS_V2_PROTOCOL25_MODELED_OWNERS_ACTUAL_PIPE152_DOC_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='lease_RCW_ownership_cleanup_and_successor_factory_worker_integration_then_actual_session_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'V2_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
