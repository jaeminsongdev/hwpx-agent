# P09 폰트 이름과 선택 범위 치환 계약

`hwpx-agent.source-selector-font-replacement/v1`은 원본의 선언된 폰트 이름을 검색하고 선택한
원문 run/text 서식 축만 바꾸는 패키지 후보를 만든다. 실제 유효 서식 cascade, 시스템 폰트 가용성,
fallback, 현재 저장 권한·실행·revision 반영을 대신하지 않는다.

## 이름과 대상

`FontNameReplacementQuery`는 query/replacement, regex/case_sensitive/whole_word와 명시적인
언어 집합을 받는다. 언어는1~7개이고 중복을 거부한다. query/replacement는 각각1~4096bytes,
매핑은 최대128개다. literal substring 또는1MiB compiled/DFA 한도의 Rust Unicode regex를
사용하며 이름은 원본 선언 값 그대로 비교한다. 선택된 이름 일치가0길이면 거부한다.

replacement는 해당 언어 안에 이미 선언된 정확한 이름이어야 한다. 없는 대상, 같은 이름의
복수 대상, 일치 없음과 변경 없음은 구분한다. 첫 선언을 임의로 고르거나 파일·플랫폼에서 찾지 않는다.
일치에 포함된 대상 자체는 no-op으로 제외하며 실제 매핑은 원본 기준으로 동시에 적용한다.
이름·XML은 영수증/debug에 노출하지 않고 원본 font receipt·정렬된 언어/매핑·요청 SHA로 결속한다.

## 선택 범위와 공유 서식 보존

기존 document/section/node-set/index-bound selection과 hidden/MEMO 정책을 먼저 해석한다.
정규화 좌표는 기존 NFC index이고 편집은 원래 Unicode scalar와 XML 범위를 사용한다.
탭·줄바꿈은 치환할 폰트 텍스트로 세지 않으며 원래 제어와 서식 참조를 보존한다.

RunProperty는 직접 run 참조를 요구하고 선택 안의 t.charStyleIDRef가 있으면 우선순위를 추정하지 않고 거부한다.
TextStyle은 직접 t.charStyleIDRef를 요구하고 run/이름 스타일로 fallback하지 않는다.
해석되지 않은 상위 ctrl.charStyleIDRef도 거부한다. 현재 전체 cascade가 아니라 명시한 축의 계약이다.

기존 charPr를 수정하지 않고 필요한 원래 글자 모양별로 새 ID의 복사본을 한 번만 만든다.
복사본은 폰트 참조와 새 ID 외의 모든 서식 정보를 보존한다. 기존 정의·비선택 사용·원본 폰트 선언·
리소스는 그대로 두고 선택한 원문 범위만 새 정의로 연결한다. 부분 run/text 분할과 중첩 run 병합은
기존 renderer를 재사용하며 원래 run끼리 합치지 않는다. 새 스타일·fragment·총 bytes와 변경 scalar는
기존 reader/patch/search/writer 한도를 유지한다. 한도 초과 시 부분 후보를 반환하지 않는다.

## 원본과 출력 검증

같은 원본 객체의 whole-source reconstruction, 원 필드/리뷰/색인과 관측 보호·field cache 거부를 유지한다.
후속 [관측 추적 표시 guard](p09-font-review-tracking-guard-v1.md)는 상위 run/문단 표시가 선택된 text에
전파되지 않던 누락을 수정한다. 관측한 charTcId/paraTcId의 ID0도 표시이며 전체 보호 의미를 대신하지 않는다.
현재 원본의 폰트 바이너리 결속 검사를 재사용한다. 원본 파트/manifest 색인을 공유하며 scalar마다
파트를 전체 순회하지 않는다. writer 뒤 한 번 출력 수입을 수행하고 전체 typed character catalog,
원문 글자·제어·모든 run/text 참조, 편집한 범위 밖 바이트와 정확한 compiled bytes를 대조한다.

별도 `hwpml-2011-scoped-font-static/v11`은 기존 text-style/v9와 font-binary/v10의 명시적 합집합이다.
다른 writer나 v1~v10 규칙을 바꾸지 않으며 chart/caption-owner 규칙과 Native 자격은 추가하지 않는다.
후보·영수증은 Deserialize/실행 권위가 없고 byte 전달은 writer 무결성만 확인한다.

## 완료 경계

312의12pass/8fail을 보존했다. 선택된 charPr의 실제 폰트를 조회하도록 fixture를 고치고 서로 다른
두 원형을 바꾸는 사례는 둘 다 일치하는 명시적 regex를 사용했다. writer 오류도 정확한 Writer 거부로 강화했다.
313은 실패8+영향3=11pass·731fresh/final731이며 무관 통과9개를 보존해 고유20개를 확인했다.
현재20개 전체 단일 실행은 아니다. 기존 공유 참조/바이너리24개와 공식249는 반복하거나 이 경로로 승격하지 않았다.

현재 저장 서비스의 ACL/head/격리/AEAD와 엄격한 별도 제품 입력은 후속
[저장 폰트 제품 계약](p09-stored-scoped-font-product-v1.md)의24개 시험으로 연결했다.
이 경로는 서버 query/compiled/DFA 상한이 더 낮으면 이를 유지한다. 기본 이름 해석 API의 한도와
기존 매핑·요청 지문 의미는 그대로다. 공통 operation compiler/실행·저장 트랜잭션·게시,
style_filter/preview_only의 전체 제품 계약, 풍부한 review/field/protection 조합, 실제 폰트와 Native
match_set·semantic_diff·reopen은 남는다. SEARCH-024 전체 제품과 P09 Gate는 OPEN이다.
