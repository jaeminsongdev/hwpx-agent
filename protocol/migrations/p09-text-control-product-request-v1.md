# 탭 줄바꿈 치환의 현재 저장과 제품 요청

`hwpx-agent.product-text-control-replacement-request/v1`은 현재 sealed HWPX의 Tab/LineBreak를
일반 Text·typed 제어·명시적 삭제로 바꾸는 후보 준비 요청이다. 실제 원본의 네 selector와 review
정책을 [원본 compiler](p09-source-text-control-replacement-v1.md)에 연결한다. 이는 SEARCH-009의
부분 경로이며 카탈로그의 query/replacement 전체 계약이나 실제 저장 커밋·Native 실행은 아니다.

## 엄격한 요청과 출력

외부 필드는 schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector, operation이다.
원16KiB unique JSON/object parser와 selector shape 검증을 공유한다. 누락·미지·중복 필드,
잘못된 타입/범위/소문자64자리 SHA·revision 결속을 거부한다. generation은 양수여야 한다.

operation의 필수 필드는 다음과 같다.

| 필드 | 허용 값 |
|---|---|
| kind | replace_text_controls |
| control_kind | tab 또는 line_break |
| max_replacements | 1~4096 정수 |
| output | 명시적 typed atom 배열 |
| review_policy | 필수 include_hidden_explanations/include_memo_bodies Boolean |

출력 atom은 `{ "kind": "text", "value": "일반 글자" }`,
`{ "kind": "tab", "width": 0, "leader": 0, "tab_type": 0 }`,
`{ "kind": "line_break" }`만 받는다. 세 tab 속성은 각각 u32다. 빈 output 배열은 선택 control의
삭제지만 빈 Text는 허용하지 않는다. raw 제어 문자와 기존 reader가 금지한 문자를 거부하고,
XML처럼 보이는 Text도 escape한다. LineBreak를 포함해 nested 미지 필드를 거부한다.

알려진 다른 control 종류는 UnsupportedKind이며 미지 enum 값은 요청 오류다. query/replacement,
regex/case_sensitive/whole_word/style_filter/direction/preview_only/locale 등 이 v1에 없는 필드를
무시하지 않는다. 요청·제어 종류·출력 검증은 원본 데이터 읽기 전에 끝낸다. 기존 literal/regex/
서식/Unicode/대소문자/폭/공백 제품 스키마의 의미를 넓히지 않는다.

## 한 번의 출력 검증과 원본 증명

ValidatedTextControlOutput은 kind·빌린 출력 slice·limits와 한 번 계산한 semantic SHA/글자 byte
수를 묶는 불변 입력이다. source proof·현재 접근 권한·실행 승인이 아니며 caller가 이후 limits를
넓힐 수 없다. 실제 lower에서는 해당 원본 모델에 맞는 fresh reconstruction proof를 다시 요구한다.

JSON 역직렬화는 Text String을 native atom으로 이동하고 canonical 직렬화는 빌린 atom을 순차
출력한다. native 출력 벡터를 복제하지 않는다. 현재 원본 proof·원 compiler를 한 번 사용하며
Borrowed 후보를 Owned 원본으로 이동할 때 clone/reimport를 추가하지 않는다. 수령·검증 시 검색이나
치환 compiler를 다시 실행하지 않는다. 변경 anchor는 검색 결과의 한 forward iterator에서 ordered
subset으로 대조해 변경 수와 선택 수를 곱하는 반복 탐색을 피한다.

원본 compiler의 완전한 단일 control unit/atom 선택, 관측 잠금·상위 추적·field cache 검사,
정확한 MEMO 본문 예외, 출력 복제 전 유한 byte/atom 예산과 독립 sparse byte/readback을 유지한다.
새 ID나 참조를 만들거나 재결속하지 않으며 선택 밖 바이트·서식·참조를 보존한다.

## 현재 저장 경계와 닫힌 실행 경로

stored-text-control-replacement-candidate/v1과 product-text-control-replacement-preparation/v1은
현재 document.write·project/document/branch/subject/tenant scope·head·ACL·quarantine·AEAD·원본
SHA와 source/index/selector/review/검색/출력 지문을 결속한다. raw/canonical/scoped 요청 지문과
key/plan도 결속하며 JSON escape 차이는 raw 지문에만 남는다.

후보 verify/bytes마다 현재 접근과 원본·writer integrity를 확인하고 consumer 직전에 최종 head를
다시 확인한다. 유지된 receipt·key·source selector는 권한이나 CAS가 아니다. 실제 ingest/commit,
DB revision CAS·영속 멱등 key claim·dispatcher·Native·게시는 열지 않았고
require_current_product_route는 검증 후 RouteUnqualified를 반환한다.

## 검증 결과와 다음 작업

components194 신규 제품24pass·716fresh/final716·진단/경고없음·cleanupTrue다. 네 범위·Tab/LineBreak·
일반/혼합 typed 출력·삭제·no-op ordered subset·review/MEMO/cache·namespace/entity/서식/참조·
strict/nested/중복/16KiB/legacy 분리·지문·현재 write/외부5scope·ACL/격리/AEAD·세 단계 최종 head
경합·borrowed/owned/JSON 동등성·잘못된 source/head/revision/index·보호/역상/한도·비노출·닫힌
route와2천 control을 확인했다. 불변 입력의 proof 오용과 limits 교체도 거부했다.

원 source compiler·공개 API 본문, 두 product root와 기존 시험 본문은 추가 wrapper/선언 제거로
전체 역변환했다. 기존 원본36·이전 제품242·공식249는 재실행하지 않았다. 제품 고유 시험은266개지만
현재266개 단일 실행이나 공식 수용 증가로 합치지 않는다.

194 전체139.547초·명령48.234초/시험10.12초·Job CPU46.156초·private최고1776.22MiB/5.5749%·
시스템CPU최고33.14%·가용RAM최저29.1281%다. 소유 Job active0/empty/handle closed와 한 코어
affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를
유지했다. OS/다른 앱 변경이나 PC 프리즈 해결·benchmark 주장은 없다. 근거는
implementation/p09/evidence/p09-361-control-product-components194.v1.json이다.

다른 제어 종류의 지원 조건과 참조/ID 보존은 별도 SEARCH-009 작업이다.
별도 [자동번호 재시작 source 경로](p09-source-number-control-replacement-v1.md)는 실제 review 결속을
연결해67개를 통과했고 별도 [번호 제품 요청](p09-number-control-product-request-v1.md)의26개도 검증했다.
이 텍스트 제어 제품 스키마의 지원 종류를 넓히지 않으며 실제 저장/실행은 미완료다.
카탈로그 query/replacement·전체 selector/filter/유효 서식·target match_set/semantic_diff/reopen·dispatcher/DB/commit/CAS/
영속 멱등 실행/게시·Native/Gate는 미완료다. source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·
Native011 미승인/미실행을 유지한다.
