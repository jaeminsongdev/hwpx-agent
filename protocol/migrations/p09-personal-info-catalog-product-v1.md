# 전체 개인정보 카탈로그 제품 요청과 결과 전달

전체 source 카탈로그를 현재 저장 문서의 읽기 전용 탐지 제품에 연결하는 계약이다. 기존 명시적16규칙 제품은
변경하지 않는다. 새 요청/이동/선택과 실제 설치 source의 저장 통합을33개 합성·1개 설치 fixture·2개 영향
검사로 확인했다. 실제 Native matcher·전체 검색 계약·P09 Gate의 완료는 아니다.

## 현재 문서와 카탈로그 선택

schema_version은 `hwpx-agent.product-personal-info-catalog-request/v1`이다. 기존 project/document/base_revision,
expected_head_generation/expected_source_package_sha256,idempotency_key/plan_id,selector와 operation에 더해
전체 source 카탈로그의 `expected_catalog_sha256`을 요구한다. 카탈로그 SHA는 source 결속이며 vendor/Native 인증이 아니다.

operation.kind는 `find_personal_info_catalog`이며 families/max_results/review_policy가 필수다. families는
telephone/resident_registration/foreign_registration/email/account/driver_license/passport/credit_card/ip_address/
birth_date/user_defined 중1~11개의 중복 없는 문자열 배열이다. ADDRESS를 설치 형식으로 추가하지 않는다.
선택한 종류의 모든 원 패턴을 사용하며 원 파일 순서와 텍스트를 바꾸거나16개로 잘라내지 않는다.
빈 USERDEF 선택은 빈 결과이며 zero-width 패턴으로 대체하지 않는다.

selector는 revision에 결속한 document/section/node_set/selection을 사용한다. max_results는1~10000이며
서버 한도와 교집합을 적용한다. 기존 scalar/point/match·regex/DFA·전체 metadata byte 상한을 유지한다.
16KiB 초과·중복/escaped 중복 key·잘못된 schema·enum 객체·미지/누락 필드·잘못된 scope/종류/해시는
문서나 카탈로그를 읽기 전에 거부한다. patterns/rules/query·파일 경로·승인 bits·preview/mutation/raw graph는 받지 않는다.

## 현재 source와 결과 영수증

host가 `CurrentPersonalInfoCatalogSource`를 제공한다. 요청자는 config 경로나 임의 source 객체를 선택하지 않는다.
고정 설치 loader는 읽기 전용64KiB 상한을 적용하고 private 사용자 INI를 읽지 않는다. SHA/bytes/원본 section
순서와 패턴 provenance를 stored receipt에 결속하고 현재 문서의 write/scope/head/ACL/quarantine/AEAD를 유지한다.

원 sealed Result owner를 이동해 한 Form proof/review 인덱스와 결합 검색을 준비 시1회 사용한다. 제품 receipt는
raw/canonical/provider-scope 요청 SHA와 전체 stored receipt를 포함한다. key/plan은 요청 결속이며 durable
멱등 claim이 아니다. 제품 outer envelope까지 byte 상한을 확인한 뒤 카탈로그와 최종 문서 head를 다시 확인한다.
보관 verify/전달은 원본·결과·현재 config를 확인하되 regex/index/search를 반복하지 않는다.

## 결과 이동과 원본 선택

next schema는 `hwpx-agent.product-personal-info-catalog-next-request/v1`이며 `catalog_receipt_sha256`과
navigation의 direction/wrap/선택적 cursor를 받는다. selection schema는
`hwpx-agent.product-personal-info-catalog-selection-request/v1`이며 같은 receipt SHA와 occurrence_index를 받는다.
전체 제품 receipt가 raw/key/plan/provider·카탈로그/선택·정확한 보관 결과를 결속한다.
다른 요청·카탈로그·형식 선택의 receipt나 cursor는 재사용하지 못한다.

metadata/next/selection은 전체 응답을 먼저 직렬화한 뒤 현재 카탈로그를 다시 읽고 consumer 직전 최종 head를
확인한다. 원문·패턴·개인정보 값별 해시는 출력하지 않는다. 원본 선택은 정확한 비어 있지 않은 기여 좌표만
전달한다. 기존 마스킹에 좌표를 넣어도 새 요청의 현재 source·범위·보호/필드/추적 상태와 writer 검증이 필요하다.

native_format_identity_or_execution_qualified·installed_vendor_authenticity_or_native_semantics_qualified·
whole_package_personal_data_removed·idempotency_key_claimed·native_identity_cas_execution_publication_authority는 false다.
현재 접근 확인 뒤에도 실제 실행 route는 RouteUnqualified로 거부한다.

## 검증 결과와 남은 경계

[저장 서비스416](../../implementation/p09/evidence/p09-361-personal-info-catalog-stored-recovery416.v1.json)의
신규23+영향2 고유25개와415 실패 원본을 보존한다. 새 제품 검증은 합성33개·실제 설치 source opt-in1개·
영향 저장2개다. 기본 환경변수 없는1개와 명시적 feature의 나머지32개/설치1개/영향2개를 나눠 실행해 모두 통과했다.
설치 fixture는 `p09-installed-format-fixture`를 명시해야 하며 원 설치 파일이 없거나 달라지면 실패해야 한다.

[417](../../implementation/p09/evidence/p09-361-personal-info-catalog-product417.v1.json)은36pass·775fresh/final775·
설치 config1final·진단/경고없음·cleanupTrue다.17,020bytes의 원 설치 파일 SHA를 시작/종료에 결속했고
전체64개 및 전화8개 선택을 현재 저장/제품 경로로 확인했다. private 사용자 INI나 한글/COM은 사용하지 않았다.
원본 저장 서비스25개 전체·source33개·공식249·이전 Native를 반복하지 않았다.

전체141.984초·두 명령18.750/23.797초·Job CPU16.688/22.344초·private최고971.40MiB·
시스템CPU최고45.09%·가용RAM최저40.9500%다. 두 Job active0/empty/handle closed를 확인했고 한 코어/
BelowNormal·CPU cap6.25%·readonly private8%/stop7%·RAM/commit95%를 유지했다. 프리즈 해결 판정은 아니다.

실제 Native matching/상호참조 의미·전체 검색 옵션·변경/저장/게시·
신뢰 registry·P09 Gate는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작을 유지한다.
