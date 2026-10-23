# 스타일 선언의 현재 저장과 제품 요청

`hwpx-agent.product-named-style-declarations-request/v1`은 현재 저장된 HWPX에서 기존 PARA/CHAR
스타일의 이름을 해석하고 원본 선언과 연결 자원 metadata를 반환한다. SEARCH-025의 준비 기반이며,
`search.replace_styles` capability의 실제 본문 변경이나 문자 스타일 적용 완료를 뜻하지 않는다.
[원본 선언 계약](p09-named-style-declaration-resolution-v1.md)의 ID domain 구분과 미자격 경계를 유지한다.

## 엄격한 요청과 범위

루트 필수 필드는 schema_version, idempotency_key, plan_id, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, operation이다. operation은 kind를
resolve_named_style_declarations로, style_kind를 paragraph/character로, name_axis를
native_name/english_name으로 명시하고 query/replacement, regex/case_sensitive/whole_word를 모두 받는다.
종류 enum은 문자열만 허용한다. 이름/대상은 원본 선언이며 대상은 같은 종류/축에서 정확하고 유일해야 한다.

요청은 최대16KiB다. 중복/escaped 중복 키·미지/누락 필드·null/배열 envelope·trailing JSON·다른 schema와
부적합 bool/enum을 거부한다. source SHA는64자리 소문자 hex, generation은 양수이며 head를 파싱한다.
서버 query byte 한도도 읽기 전에 적용한다. 본문 selector·style_filter·review/mutation 옵션·XML/graph·
승인 bits·caller 대상 ID는 지원하지 않으며 무시하지 않는다. 기존 문단 v1/v2 요청은 변경하지 않았다.

## 현재 접근과 결과 전달

제품은 원 source-search provider scope와 document.write를 먼저 확인하고 현재 sealed Result를 읽는다.
요청 source SHA와 head를 원본에 대조한다. 저장 서비스는 기존 tenant/subject/project/branch/document·
ACL/quarantine/AEAD·whole Form 재구성·consumer 최종 head를 유지한다. 기존 catalog와 이름 matcher를
준비 시 한 번만 사용하며 결과는 private owner와 결속한다.

verify/전달은 현재 원본과 접근을 다시 확인하고 보관 resolution receipt/선언/대상·전체 결과 SHA를 대조한다.
catalog import나 이름 검색을 반복하지 않는다. 최종 head 확인 뒤에만 consumer를 호출하며 원자적 CAS나
전달 후 자료 회수는 보장하지 않는다. 선언 종류/자원 ID를 이용해 본문 적용 위치를 추정하지 않는다.

응답은 원본 source receipt, resolution receipt, from 선언 ID/anchor와 대상 ID/anchor, 연결 charPr/
paraPr/nextStyle 자원 및 지문을 포함한다. 제품은 여기에 raw/canonical/scoped 요청 SHA를 결속한다.
본문·이름·질의·key 원문은 JSON/Debug에 넣지 않는다. 원본의 기본128개 mapping·4096byte 질의·regex1MiB·
응답4MiB와 서버 제한을 유지하며, 전체 service/product envelope에 결과 byte 한도를 적용한다.
저장 계층은 자체 유한 직렬화를 사용하고 private 제품 helper에 의존하지 않는다.

결과의 body_mapping_mutation_native_or_execution_qualified와 idempotency_key_claimed는 false다.
편집 artifact·compiler owner·무검사 bytes 전달·ingest/commit/CAS/멱등 claim·실행 API는 없으며,
require_current_product_route는 현재 접근을 확인한 뒤 RouteUnqualified다. 기존 공통 변경22계열은 그대로다.

## 검증과 다음 경계

[357 컴파일 실패](../../implementation/p09/evidence/p09-361-named-declarations-product357.v1.json)는
비공개 제품 helper 참조 E0603·시험0·cleanupTrue이며 종료 후 입력 재확인은 시스템CPU94.47% 표본으로
미완료다. 저장 계층 직렬화로 분리한 뒤 [358](../../implementation/p09/evidence/p09-361-named-declarations-product-recovery358.v1.json)은
기존 임시 경로 중복·시험0·840fresh/final840·cleanupTrue로 보존했다. 실행별 임시 경로와 조기 검사를 적용한
[359](../../implementation/p09/evidence/p09-361-named-declarations-product-isolated359.v1.json)는 신규26+영향 기존3=29pass·
842fresh/final842·진단/경고없음·cleanupTrue다. 권한 철회/재부여·scope5종·격리/암호문 변조·입력/출력 정확한
byte 한도·source/head·최종 경합·개인정보 비노출·원본/ingest/head 보존과 route 거부를 확인했다.
기존 선언19/제품 전체/공식249는 반복하지 않았다.

359 전체135.172초·시스템CPU최고32.16%·private최고933.64MiB/2.9304%·가용RAM최저25.9121%다.
원 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%와 두 Job 정리를 유지했다.
357 spike 귀속이나 PC 프리즈 해결의 증거는 아니다.

문자 스타일 본문 연결·전체 옵션·실제 실행/저장/게시·신뢰 registry·Native/Gate는 남는다. 고정6종 캡처는
사용자 선택 대기이며 승인/세션 자격 전 실행하지 않는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
