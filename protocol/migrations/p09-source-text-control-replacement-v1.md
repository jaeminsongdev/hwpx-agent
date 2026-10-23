# 실제 원본 탭 줄바꿈 제어의 검색 치환

`hwpx-agent.source-selector-text-control-replacement/v1`은 SEARCH-009의 실제 원본 Tab/LineBreak
검색 결과를 일반 Text·typed 제어·명시적 삭제로 바꾸는 source candidate다. 문서·구역·노드 집합·
index-bound 선택 범위와 review 정책을 사용한다. 현재 저장과 엄격한 제품 요청은 별도
[제품 준비 프로필](p09-text-control-product-request-v1.md)에 연결했다. 다른 제어 종류·전체 검색
계약·실제 저장 커밋·Native 실행은 미완료다. 표·필드·각주·개체 등은 UnsupportedKind이며 검색됐다는 이유로
임의 XML 교체나 자동 fallback을 실행하지 않는다.

## 입력과 선택 증명

원본 Form proof, SourceIndexScopeSelector, 명시적 SourceReviewTextPolicy, SourceControlKind,
유한 max_results와 TextAtom 출력 벡터를 받는다. caller가 control anchor·XML byte offset·원본
그래프나 검증 완료 flag를 제공하는 경로는 없다. 출력 Text는 기존 reader의 문자 조건을 따르며
empty Text/raw 제어 문자와 reader가 금지한 noncharacter를 거부한다. Tab/LineBreak는 typed 출력으로 지정하고
빈 출력 벡터로 실제 선택 control만 삭제한다. 원래 Text는 편집하지 않는다.

원 control 검색은 actual control START의 half-open 범위 포함을 판정한다. 편집은 그 결과만
믿지 않고 같은 selector의 원 windows 안에 전체 원본 단일 control unit과 atom이 대응하는지
확인한다. 해당 unit은 한 원본 기여자·scalar0·단일 usage 위치여야 한다. 빈/인접 글자 선택을
control로 넓히거나 NFC 재정렬 경계를 XML 위치로 추측하지 않는다. 일반 control subtree 전체가
선택됐다는 주장은 하지 않으며 이 증명은 현재 qualified Tab/LineBreak에 한정한다.

공개 find_control 응답과 의미는 유지하고 본문을 find_control_with_windows로 기계적 추출했다.
원 selector·geometry·review/cap 순서·hash·result 본문은 반환 windows 처리만 제거하면 전체
역변환된다. 상위 compiler가 같은 windows를 받아 scope/catalog와 두 endpoint를 다시 만들지
않는다. review 제외는 기존처럼 cap보다 먼저 적용한다.

## 보호와 원본 보존

한 원본 proof·field/review/index·control matcher와 한 scope 해석을 사용한다. 선택된 부모/종류의
unit만 보관하며 부모마다 qualified TextSpan과 original control map을 한 번 구성하고 part마다
기존 관측 잠금·상위 추적 guard3N을 공유한다. no-op도 보호와 field cache 검사 후에만 제거한다.
기존 ReviewWriteContext가 증명한 정확한 MEMO 본문만 예외이며 바깥 field가 덮으면 차단한다.
opaque 부모 안의 control이 검색되더라도 그 부모가 qualified reader를 통과하지 못하면 거부한다.
전체 Native 잠금/숨김/서식 의미를 검증했다는 뜻은 아니다.

일반 글자·선택 밖 control/entity·paragraph/run/t shell·서식/참조와 다른 ZIP entry를 보존한다.
새 ID·참조 대상을 만들거나 기존 참조를 재결속하지 않는다. no-op control은 paired tag의 공백/
따옴표 등 원본 바이트도 유지한다. 변화 목록은 원본 검색/spine 순서로 결속하며 local ID가 같은
다른 part를 혼동하지 않는다. 변경 없는 원본과 현재 저장 문서를 in-place 수정하지 않는다.

기존 text-style/v9·Hangul2020PreviewTextV2 writer와 sparse lexical byte verifier를 공유한다.
원본 control outer range와 독립 expected encoding을 사용해 모든 선택 밖 바이트를 대조하고
안정적인 t container 순서와 출력 TextSpan을 확인한다. 출력 Form/field/review도 다시 import한다.
기존 readback 본문은 가시성만 넓혔으며 element 개수/slot 불변의 옛 readback도 완화하지 않았다.

## 비용과 출력 상한

출력 문자 validation과 semantic hash는 호출당 한 번이다. 같은 namespace의 독립 expected
encoding을 공유하며 각 control 복제 전에 실제 escaped byte·typed atom 수·누적 출력·원 reader
크기 한도를 확인한다. 큰 출력을 많은 control에 무제한 복제한 뒤 실패시키지 않는다. 실제 patch는
[typed text-control patch](p09-text-control-atom-patch-v1.md)를 사용한다.

선택 control 수는 검색 cap과4096 patch 상한을 따르고 출력 원문/escaped 값·fragment·응답·
writer의 유한 한도를 적용한다. 실패는 부분 후보를 전달하지 않는다. 2천 control은 한 부모의
TextSpan/control map과 part 보호3N을 공유한다. 이것은 코드 비용 경계이며 Native 성능 benchmark는 아니다.

## 검증 결과와 다음 작업

components192는 신규 원본24+영향 선택 범위12=36pass·712fresh/final712·진단/경고없음·cleanupTrue다.
네 selector/완전한 atomic 선택·NFC 경계·review/MEMO/cache·잠금/추적/no-op·opaque 거부·
Unicode/typed 출력·namespace/entity/서식/참조·충돌 local ID의2개 part·stale proof/scope·한도/
복제 전 큰 출력 거부·2천 control/한 부모 map·비노출/지문을 확인했다. 변경 없는 patch18·
whitespace 원본24·제품242·공식249는 반복하지 않았다. 실제 사용자 문서나 한글 실물 수용으로
올리지 않는다.

전체124.156초·명령33초/시험6.34초·Job CPU31.578초·private최고1765.96MiB/5.5427%·
시스템CPU최고53.32%·가용RAM최저28.6169%다. 소유 Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. OS/다른 앱 변경이나 PC 프리즈 해결·benchmark 주장은 없다. 근거는
implementation/p09/evidence/p09-361-control-source-components192.v1.json이다.

현재 저장 서비스·엄격한 제품 JSON 연결은 별도 components194 신규 제품24pass·716fresh/final716으로
검증했다. 불변 검증 입력 wrapper만 추가했으며 위 compiler/공개 API 본문은 그대로다. 다음은
SEARCH-009 다른 제어 종류의 지원 조건과 참조/ID 보존이다. 다른 제어 종류·전체 query/
selector/filter/유효 서식·참조 의미/ID 보존·target match_set/semantic_diff/reopen·dispatcher/
DB/commit/CAS/영속 멱등 실행/게시·Native/Gate는 미완료다. source API v12 incomplete/미해결4/
report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·
고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
