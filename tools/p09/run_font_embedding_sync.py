"""309: current source24 and original failure stay distinct; scoped docs-only audit, no tests."""
import json,re,time
from types import SimpleNamespace as NS
import run_font_embedding_components as latest
shared,c,a,tools,compact,audit=latest.shared,latest.c,latest.a,latest.tools,latest.compact,latest.audit
OUTPUT='implementation/p09/evidence/p09-361-font-embedding-sync309.v1.json'
DRIVER='tools/p09/run_font_embedding_sync.py'
BASE='implementation/p09/evidence/p09-361-font-reference-sync307.v1.json'
PROGRESS='implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md';REPORT='implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md'
CONTRACT='protocol/migrations/p09-source-font-reference-replacement-v1.md';PROFILE='protocol/migrations/p09-font-binary-id-profile-v10.md'
OLD_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본 언어별 공유 참조 치환 고유13pass·내장 폰트1fail, 이름 검색/선택 범위·유효 내장 리소스·fallback·현재 저장/제품/target 미완료 |'
NEW_ROW='| SEARCH-024 | 폰트 일괄 대체 | 원본 언어별 공유 참조 치환과 바이너리 결속 신규10+영향14=24pass, 이름 검색/선택 범위·실제 유효 폰트·fallback·현재 저장/제품/target 미완료 |'
BEFORE='''원본 전체 바이트 일치, 관측 보호 신호 거부, 기존 shape/v6 ID 검증과 patch/writer를 유지한다.
출력은 한 번 재수입하고 기존 선언 및 전체 글자 모양의 기대값과 비교한다. 변경한 속성 값 밖의
header 바이트와 나머지 패키지 멤버를 보존한다. 내장 폰트의 binaryItemIDRef 사례는 현재 ID 검증
실패 상태이며 유효 리소스와 독립 참조 규칙이 검증되기 전 지원으로 표시하지 않는다.
'''
AFTER='''원본 전체 바이트 일치와 관측 보호 신호 거부, 기존 patch/writer를 유지한다. 별도 font-binary/v10은
shape/v6의 불변 규칙에 font/substFont 바이너리 참조만 추가하며 기존 프로필은 바꾸지 않는다.
출력은 한 번 재수입하고 기존 선언 및 전체 글자 모양의 기대값과 비교한다. 변경한 속성 값 밖의
header 바이트와 나머지 패키지 멤버를 보존한다. 선언된 바이너리 참조는 실제 manifest/비어 있지 않은
binary part와 결속해야 하며 누락·XML 또는 text/* 미디어·spine/infrastructure 대상은 거부한다.
보존용 합성 바이너리를 사용한24개 시험은 실제 폰트 유효성·설치·활성화나 Native 임베딩 지원 증거가 아니다.
[별도 ID 프로필 계약](p09-font-binary-id-profile-v10.md)을 따른다.
'''

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_BINARY_SYNC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_BINARY_SYNC',own_cpu_selection=selection,tests_build_DB_or_Hangul_replayed=False,
        document_audit_not_runtime_requalification=True,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(latest.OUTPUT));docs=q.json(BASE)
        c.require(q.snapshots[latest.OUTPUT]['sha256']=='dce90579eba99baf0e604c29dd854c7d81dece12231e1e47310d44fd85364997'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==716 and passed['total_cases']==24 and passed['steps'][0]['diagnostics']==[]
            and len(passed['steps'][0]['tests'])==24 and all(s=='ok'for _,s in passed['steps'][0]['tests']),'EXACT308_CURRENT24_SOURCE_CLOSURE_NO_IGNORES_OR_DIAGNOSTICS')
        pins={p['path']:p for p in passed['source_pins']}
        for n in latest.CHANGED|latest.NEW:
            q.pin(n);c.require(q.snapshots[n]==pins[n],'SCOPED_NEW_PROFILE_RESOURCE_GUARD_TESTS_FIXTURES_AND_OFFICIAL_SOURCE_UNCHANGED')
        j=passed['steps'][0]['owned_job'];c.require(j['owned_tree_empty']and j['cleanup_confirmed']and j['job_handle_closed']and j['last_job_accounting']['active_processes']==0,'OWNED308_JOB_TERMINAL_EMPTY_CLOSED')
        c.require(q.snapshots[BASE]['sha256']=='06d64467f124b26cc2b2c68749989cd2a010698d7fa3f3ec0432dd0da4cd1f05'and docs['cleanup'],'EXACT307_PRIOR_DOCUMENT_CLOSURE')
        old={p['path']:p for p in docs['source_pins']}
        text=q.text('CURRENT_STATE.md');marker='> 2026-10-21 P09 ACTIVE 최신 원본 폰트 참조 치환'
        c.require(text.startswith('> 2026-10-21 P09 ACTIVE 최신 폰트 바이너리 참조 결속')and text.count(marker)==1,'ONE_CURRENT_BINARY_PREFIX')
        audit.inverse(text[text.index(marker):],old['CURRENT_STATE.md'],'ALL_PREVIOUS_CURRENT_STATE_HISTORY_UNCHANGED')
        text=q.text(REPORT);start=text.index('## 바이너리 참조 결속과 보존\n');end=text.index('SEARCH-024 폰트 일괄 대체의 원본 편집 기반을 추가했다.',start)
        audit.inverse(text[:start]+text[end:],old[REPORT],'ALL_PRIOR_FAILED_AND_PARTIAL_FONT_RECORDS_PRESERVED')
        for marker in ('24개 시험','716fresh/final716','123.906초','32.109초','1807.71MiB','24.29%','41.9092%','고유 시험13개','실제 글꼴이 아니며','P09/A12/A13 OPEN'):
            c.require(marker in text,'REPORT_CURRENT_AND_HISTORICAL_SCOPE_EXACT')
        text=q.text(PROGRESS);start=text.index('별도 font-binary/v10과 현재 패키지 리소스 결속은');end=text.index('SEARCH-024의 원본 편집 기반은',start)
        c.require(text.count(NEW_ROW)==1,'ONE_CURRENT_SEARCH024_ROW')
        audit.inverse((text[:start]+text[end:]).replace(NEW_ROW,OLD_ROW),old[PROGRESS],'ALL_OTHER_SEARCH_ROWS_AND_PREVIOUS_PROGRESS_UNCHANGED')
        text=q.text(CONTRACT);c.require(text.count(AFTER)==1,'ONE_UPDATED_BINARY_BINDING_CONTRACT')
        audit.inverse(text.replace(AFTER,BEFORE),old[CONTRACT],'ALL_PRIOR_REQUEST_RECEIPT_LIMIT_AND_PERMISSION_CONTRACTS_PRESERVED')
        q.pin(PROFILE);q.pin(DRIVER);text=q.text(PROFILE)
        for marker in ('shape/v6','v1~v9','716fresh/final716','합성 opaque payload는 실제 글꼴이 아니다','binaryItemIDRef','502963997102641ca5d5393b642ed70b9a0287694c49b7dc2a0752f93b2905e4','8904c3597495f20abd00bb6fcb48841a795a125e52ffa49f8b171d4c60ccedbc'):
            c.require(marker in text,'PROFILE_PRIMARY_SOURCE_HASHES_AND_NON_NATIVE_QUALIFICATION')
        q.finish();guard.check(force=True);row.update(state='PASS_FONT_BINARY_BINDING24_AND_CURRENT_DOC_SYNC_NOT_PRODUCT_OR_NATIVE_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_component_cases=24,original_failed305_reclassified=False,official_queue_accepted=158,official_queue_total=249,
            next_work='font_name_query_and_scope_selection_without_mutating_unselected_shared_properties')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_BINARY_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','current_component_cases')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
