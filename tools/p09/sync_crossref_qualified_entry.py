"""414: current implementation readiness and surgical runbook/doc closure, no replay."""
import json,re,time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r

OUTPUT='implementation/p09/evidence/p09-361-crossref-qualified-entry-sync414.v1.json'
DRIVER='tools/p09/sync_crossref_qualified_entry.py'
READY='implementation/p09/evidence/p09-361-crossref-qualified-entry-runtime-ready413.v1.json'
BASE='implementation/p09/evidence/p09-361-crossref-session-qualification-sync409.v1.json'
STATE='CURRENT_STATE.md'
READINESS='implementation/p09/P09_CROSSREF_EXECUTION_READINESS.md'
SESSION='implementation/p09/P09_CROSSREF_SESSION_QUALIFICATION_PROGRESS.md'
BOOK='implementation/p09/P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md'
NEW='implementation/p09/P09_CROSSREF_QUALIFIED_ENTRY_PROGRESS.md'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'ENTRY_SYNC414_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_QUALIFIED_ENTRY_SOURCE_DOC_SYNC414',own_cpu_selection=selection,
        actual_worker_ROT_Hangul_COM_or_test_replayed=False,native_startup_qualified=False,fixed_eight_executed=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);ready=r.compact.unpack(q.json(READY));base=r.compact.unpack(q.json(BASE))
        c.require(q.snapshots[READY]['sha256']=='9dd98eafde1218df44d63f92c5f0ff6fe17d021f7da3fc7fffbbc27135c59cc0'
            and ready['state']=='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE'
            and ready['cleanup']is True and ready['fresh_inputs']==ready['final_fresh_hashes']==234
            and ready['native_startup_qualified']is False and ready['fixed_eight_executed']is False,'EXACT413_CURRENT_IMPLEMENTATION_READINESS_NOT_NATIVE')
        for pin in ready['source_pins']:c.require(q.pin(pin['path'])==pin,'ALL234_READY_INPUTS_AND_ORIGINAL_NATIVE_SOURCES_UNCHANGED')
        c.require(q.snapshots[BASE]['sha256']=='9228f4aa1283879b3c7df80dde20f64ebe932adacd5df1ae2fce21f5213cc8dc'
            and base['cleanup']is True,'EXACT409_PRIOR_DOCUMENT_BASELINE')
        old={p['path']:p for p in base['source_pins']};texts={path:q.text(path)for path in(STATE,READINESS,SESSION,BOOK,NEW)}
        state=texts[STATE];marker='> 2026-10-21 P09 ACTIVE 세션 자격 프로토콜과 실제 worker 결속'
        c.require(state.startswith('> 2026-10-21 P09 ACTIVE 외부 세션 자격과 고정8종 단일 진입점 준비'),'CURRENT_QUALIFIED_ENTRY_PREFIX')
        r.audit.inverse(state[state.index(marker):],old[STATE],'ALL_PRIOR_USER_SOURCE_FAILURES_AND_PHASE_HISTORY_PRESERVED')
        text=texts[READINESS];start=text.index('## 외부 단일 진입점 준비 완료');end=text.index('## 외부 호스트 사전검사 준비',start)
        r.audit.inverse(text[:start]+text[end:],old[READINESS],'ONLY_CURRENT_ENTRY_READINESS_SECTION_ADDED')
        pairs=[(
            '이 파일은 private worker 진입점이며 직접 실행하지 않는다. 외부 사용자가 실행할 전체 Python 진입점은\n후속 [전체 진입점 현황](P09_CROSSREF_QUALIFIED_ENTRY_PROGRESS.md)에 연결됐고 구현 준비 검증을 완료했다.\n',
            '이 파일은 private worker 진입점이다. 외부 사용자가 실행할 Python의 전체 qualification/고정8종 진입점은\n아직 연결되지 않았으며, 이 worker만 직접 실행하도록 안내하지 않는다.\n'),(
            '후속 Python 진입점은 이 세션 candidate와 고정8종 controller를 동일한 외부 jobless 호출자에 연결한다.\n411의 Python42·PowerShell10pass, 실제 공개 preflight의 원 caller Job 거부,412의 실제 worker 첫 요청 거부와\n413의234fresh/final234 입력 대조를 완료했다. 다음은 사용자가 [외부 실행 안내](P09_EXTERNAL_CROSSREF_HOST_RUNBOOK.md)의\n전체 진입점을1회 실행하는 것이다. 실제 호출의 Native7% 사전배정·ROT/COM/window 결속·정상 종료·\nfresh source 최종 대조를 마친 뒤에만 승인된 고정8종으로 진행하며 실제 세션/8종은 아직 NOT_RUN이다.\n',
            '다음은 이 세션 candidate와 이미 준비한 고정8종 controller를 동일한 외부 jobless 호출자에 연결할\nPython 진입점과 source/실행/산출물/정리 증거 결속이다. 실제 호출의 Native7% 사전배정·ROT/COM/window\n결속·정상 종료·fresh source 최종 대조를 마친 뒤에만 승인된 고정8종으로 진행해야 한다.\n')]
        text=texts[SESSION]
        for after,before in pairs:c.require(text.count(after)==1,'ONE_EXACT_SESSION_FOLLOWUP_CHANGE');text=text.replace(after,before)
        r.audit.inverse(text,old[SESSION],'ALL_SESSION407_408_CODE_MODELS_AND_REAL_DENIAL_HISTORY_PRESERVED')
        book=texts[BOOK];marker='## 완료된 사전검사 절차 이력'
        oldbook='# 외부 CROSSREF 호스트 사전검사 실행'+book[book.index(marker)+len(marker):]
        oldbook=oldbook.replace('## 과거 사전검사 명령','## 실행 방법').replace(
            '아래는 이미 완료된 검사001에 사용한 명령이며 다시 실행할 명령이 아니다. 당시 현재 폴더는 상관없었다.',
            'Codex의 실행 패널이 아닌 별도로 연 PowerShell에서 다음 명령을 한 번 실행한다. 현재 폴더는 상관없다.').replace(
            '결과는 [검사001 영수증](evidence/p09-361-external-crossref-host-inspection-run001.v1.json)에 저장돼 있다.\n이미 존재하는 결과를 덮어쓰지 않는다. 사용자는 마지막 JSON을 전달했고 원 영수증을 독립 대조했다.',
            '결과는 [검사001 영수증](evidence/p09-361-external-crossref-host-inspection-run001.v1.json)에 새로 저장된다.\n이미 존재하는 결과를 덮어쓰지 않는다. 실행이 끝나면 채팅에 `실행 완료`라고 알려주면 된다.')
        r.audit.inverse(oldbook,dict(path=BOOK,bytes=6213,sha256='15f914d9ba68c223b1ca57c3051a599598840ce82c3db723ce8db6ee7880311c'),
            'COMPLETED_EXTERNAL001_ORIGINAL_RESULTS_AND_HISTORICAL_COMMAND_PRESERVED')
        current=state[:state.index('> 2026-10-21 P09 ACTIVE 세션 자격 프로토콜과 실제 worker 결속')]
        for text in(current,texts[NEW]):
            for token in('공식158/249','잔여91','next165','P09/A12/A13 OPEN','목표ACTIVE','P10 미시작','CROSSREF8종 NOT_RUN',
                'Native011 미승인/미실행','문자 스타일6종 선택 대기','RouteUnqualified/P02 routing_allowed=false',
                'source API v12 incomplete/미해결4/report없음/exit3'):
                c.require(token in text,'AUTHORITATIVE_QUEUE_GATES_AND_NATIVE_APPROVAL_BOUNDARIES_UNCHANGED')
        command="& (Join-Path $env:USERPROFILE '.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe') -B 'D:\\개발\\hwpx-agent\\tools\\p09\\run_external_crossref_fixed_batch.py' --execute-qualified-fixed-eight"
        c.require(book.count(command)==1 and '같은 명령을 다시 실행하지 않는다' in book and '다시 실행할 명령이 아니다' in book
            and '권한 창이 여러 번 나올 수 있다' in book and 'WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL' in book,
            'ONE_COMPLETE_EXTERNAL_COMMAND_CONDITIONAL_FIXED8_NO_RETRY_WITH_EXACT_HANDLE_CLEANUP_GUIDANCE')
        checked=0
        for path in(READINESS,SESSION,BOOK,NEW):
            for link in re.findall(r'\]\(([^)]+)\)',texts[path]):
                if link.startswith('https://'):continue
                target=((c.ROOT/path).parent/link).resolve();c.require(target.is_relative_to(c.ROOT.resolve())and target.is_file(),'CURRENT_SOURCE_AND_EVIDENCE_LINK_EXISTS');checked+=1
        from crossref_external_batch_runtime import absent_attempts
        absent_attempts()
        for name in('claim','run'):c.require(not(c.ROOT/f'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-{name}001.v1.json').exists(),'NO_NATIVE_CLAIM_OR_RUN_CONSUMED_BY_DOC_AUDIT')
        compile(q.text(DRIVER),DRIVER,'exec');q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_QUALIFIED_ENTRY_SOURCE_AND_EXTERNAL_RUNBOOK_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,checked_document_links=checked,
            implementation_readiness_sha256=q.snapshots[READY]['sha256'],
            next_work='user_external_current_session_qualification_then_conditionally_approved_fixed_eight_once')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'ENTRY_SYNC414_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=r.a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','checked_document_links','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
