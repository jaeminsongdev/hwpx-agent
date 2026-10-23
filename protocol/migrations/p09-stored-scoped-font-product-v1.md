# P09 선택 범위 폰트 저장 제품 요청

별도 `hwpx-agent.product-scoped-font-replacement-request/v1`은 현재 저장된 원본에서 폰트 이름과
명시적 선택 범위의 run/text 축 치환 후보를 준비한다. 후보는 공통 operation compiler/dispatcher,
실제 실행·새 revision commit·게시 권한을 부여하지 않는다.

## 엄격한 요청

root 필수 필드는 schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector, operation이다.
selector는 기존 revision-bound document/section/node_set/selection의 엄격한 형태를 따른다.
selection 좌표는 현재 NFC index 지문과 원본 문단/블록/scalar에 결속한다.

operation의 kind는 replace_fonts다. query/replacement, regex/case_sensitive/whole_word,
중복 없는1~7개 languages, run_property 또는 text_style인 axis, max_changed_scalars와
두 Boolean을 명시한 review_policy가 모두 필요하다. 언어는 hangul/latin/hanja/japanese/other/
symbol/user 문자열만 받는다. enum의 object 표현, 누락·중복/escape 중복·미지 필드·다른 schema,
부적합 selector와16KiB 초과 JSON을 거부한다. style_filter/preview_only는 이 프로필에서 거부한다.

query/replacement는 각각1~4096bytes이고 요청 변경 상한은1~10000이다. 실제 변경 상한은 요청과
검증된 서버 검색 한도의 최솟값이다. 서버 query byte 한도를 넘으면 artifact 읽기 전에 거부한다.
regex 문법과 compiled/DFA 한도는 현재 권한이 확인된 원본 이름 해석 안에서 검사하며 더 낮은
서버 한도를 유지한다. writer 출력 상한도 그대로 전달하며 초과 시 부분 성공 후보를 내지 않는다.

## 현재 원본과 보관 후보

StoredImportedDocumentForms의 prepare_font_candidate와 into_font_candidate는 document.write,
현재 provider scope/head·원본·ACL/격리/AEAD 및 whole-source reconstruction을 거친다.
같은 proof로 원본 이름 검색과 선택 범위 lowering을 한 번 수행한 뒤 최종 head를 확인한다.
into 경로는 원래 source 객체를 이동하며 clone이나 추가 폰트 검색·lowering을 수행하지 않는다.

보관 후보의 verify/with_verified_bytes는 매번 현재 접근·원본/head와 writer 무결성을 다시 확인한다.
이름 검색·치환을 재실행하지 않으며 byte consumer 직전 writer callback 안에서 마지막 head를 확인한다.
이 확인은 원자적 CAS나 전달 후 권한 회수 기능이 아니다. byte 접근의 우회 경로는 제공하지 않는다.

기존 선언 중 정확하고 유일한 replacement, 공유 charPr 복제, 선택 밖 보존과 전체 출력 readback은
[원본 선택 범위 계약](p09-scoped-font-name-replacement-v1.md)을 따른다. 플랫폼 폰트 탐색이나
미해결 서식 축의 우선순위·fallback은 추정하지 않는다. 필드 캐시와 보호 신호 거부도 유지한다.

## 영수증과 실행 경계

저장 영수증은 stored-scoped-font-candidate/v1, 제품 영수증은
product-scoped-font-replacement-preparation/v1이며 capability_id는 search.replace_fonts다.
raw/canonical/scoped 요청 지문, 원 저장 receipt와 kernel 출력 receipt를 결속한다. 요청 원문·
폰트 이름·본문·XML은 영수증/debug에 노출하지 않는다. candidate/receipt는 Deserialize하지 않는다.
idempotency_key_claimed와 실행/게시 권위는 false이며 key/plan 지문은 영속 멱등 실행 허가가 아니다.
require_current_product_route는 fresh 검증 후 RouteUnqualified를 반환한다.

폰트는 후속 [공통 준비와 계획](p09-compiled-font-resources-v1.md)의19번째 family에도 연결했다.
본문 편집의 [실제 inventory](p09-font-edit-inventory-v1.md)와 두 헤더 자원 효과를 함께 결속한다.
독립 API의 현재 접근/receipt/route 거부는 그대로이며 공통 계획도 실행 권한을 부여하지 않는다.
빈 계획이나 가상 문단을 사용해 이 경계를 통과시키지 않는다.

## 검증 범위와 다음 작업

독립 scoped_font_product 바이너리의 신규24개 시험은 네 selector/두 축·부분 선택·원 공유 정의 보존과
실제 출력 폰트, borrowed/owned/제품 동일성, JSON/지문/한도, read scope/외부5scope·ACL·격리·AEAD·
prepare/verify/최종 consumer head 경합, 필드 캐시 거부와 비노출/원본 불변을 확인했다.
316은24pass·739fresh/final739·진단/경고없음·cleanupTrue다.315의 시험 콜백 컴파일 실패는 보존했다.
기존 원본20/바이너리24와 공식249는 다시 실행하지 않았다.

후속 inventory의 현재 전달은 신규12+영향 제품24pass이며 기존 원본9개 결과를 별도로 보존했다.
공통 compiler/준비 연결은 후속 폰트16+영향 기존4개 시험으로 확인했다. 풍부한 review/field/protection 조합,
전체 옵션·cascade/fallback·실제 유효 폰트·저장/게시·Native 검증은 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10 미시작을 유지한다.
