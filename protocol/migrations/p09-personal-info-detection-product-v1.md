# 개인정보 형식 탐지의 저장과 읽기 전용 제품 요청

[탐지 source 코어](p09-source-personal-info-detection-v1.md)를 현재 저장 서비스와 엄격한 JSON 제품 준비에
연결한다. SEARCH-020의 read_only 결과이며 파일 변경·preview·실제 실행·익명화 권한과 구분한다.

## 현재 저장과 원본 소유권

StoredImportedDocumentForms::into_personal_info_detection은 원 owner를 이동한다. 현재 document.write와
scope/head/ACL/quarantine/AEAD,whole 원본 Form 재구성을 유지하고 proof의 review 인덱스와 결합 검색을1회
사용한다. service receipt는 source/index/scope·전체 정책/요청/결과 지문·명시적 review 정책·일치 수를 결속한다.
형식별/일치별 XML/ZIP 재수입을 하지 않는다. 보관 verify/전달은 원 현재 source 재구성·결과 지문을 재확인하며
정규식 컴파일·인덱스 생성·검색은 반복하지 않는다.

PreparedStoredPersonalInfoDetection은 원본과 읽기 전용 결과를 보관한다. 공개 출력은 현재 접근을 검사한
JSON뿐이고 unchecked result/bytes/compiler/inventory getter나 mutation으로의 역변환은 없다.
제품 계층의 내부 projection도 전체 JSON을 유한하게 직렬화한 뒤 마지막 head를 확인하고 consumer를1회 호출한다.
metadata의 streaming count/hash와 JSON writer에 서버 result byte 상한을 적용한다. 결과만 한도에 맞고
receipt를 더한 outer envelope가 넘는 경우도 거부한다.

## 엄격한 탐지 요청

schema_version은 hwpx-agent.product-personal-info-format-detection-request/v1이다. project/document/base_revision,
expected_head_generation/expected_source_package_sha256,idempotency_key/plan_id,selector,operation을 요구한다.
operation.kind는 find_personal_info_formats이며 rules/max_results/review_policy가 필수다.

selector는 기존 revision 결속 document/section/node_set/selection을 공유한다. 각 rule은 kind/rule_id/query와
regex/case_sensitive/whole_word를 명시하고 source profile의1~16개·질의 합계/결합식4096byte·서버 한도를 따른다.
max_results는1~10000이며 서버 match 한도와 교집합을 사용한다. body 정책은 hidden/MEMO 포함 여부를 명시한다.
16KiB 초과·중복/escaped 중복 키·배열/비객체·미지 필드/버전·enum 객체·부적합 범위/종류·누락 정책은 거부한다.
replacement/mask_policy/preview_only·승인 bits·raw XML/graph·미지원 style_filter/direction은 원본 읽기 전에 거부한다.
regex 문법/합성 및 source mapping은 기존 유한 source 엔진에서 검사하며 실패 시 후보를 부분 반환하지 않는다.

raw/canonical/provider-scope request SHA와 전체 stored receipt를 보관한다. idempotency_key와 plan_id는 요청
결속일 뿐 durable 멱등 claim이나 실행 manifest 승인이 아니다. 실제 원본 digest/head가 다르면 거부한다.

## 보관 결과의 이동과 원본 선택

next schema는 hwpx-agent.product-personal-info-format-next-request/v1이며 detection_receipt_sha256와
navigation의 direction/wrap와 선택적 cursor를 받는다. selection schema는 hwpx-agent.product-personal-info-format-selection-request/v1이며
같은 receipt SHA와 occurrence_index를 받는다. 전체 product receipt의 raw/key/plan/provider/정책/보관 결과가
결속되므로 다른 요청의 receipt나 cursor를 교체해서 사용하지 못한다. digest/좌표 자체는 접근 권한이 아니다.

metadata/next/selection의 모든 전달은 현재 write/scope/head/ACL/quarantine/AEAD·원본 재구성·결과 지문과
직렬화 뒤 consumer-final head를 유지한다. next는 보관된 일치 집합에서 앞/뒤 이동·순환하며 재검색하지 않는다.
selection은 정확한 비어 있지 않은 원본 기여 좌표만 전달한다. [기존 마스킹 제품](p09-personal-info-mask-product-v1.md)에
좌표를 넣어도 새 요청과 현재 source/보호/필드/추적 상태·writer 검사가 필요하다. read_only 준비가 자동 변경하는 경로는 없다.

응답/Debug에는 원문·질의/regex·개인정보 값별 해시·raw key/plan을 포함하지 않는다. 규칙 ID/종류와 원본 좌표·
집계는 metadata이므로 정보 이론적 비노출이나 실명 판정은 아니다. native_format_identity_or_execution_qualified·
whole_package_personal_data_removed·idempotency_key_claimed·native_identity_cas_execution_publication_authority는 false다.
require_current_product_route는 현재 접근 확인 뒤 RouteUnqualified로 거부하며 파일/컴파일/실행 API는 제공하지 않는다.

## 검증과 남은 경계

[378](../../implementation/p09/evidence/p09-361-personal-info-detection-product378.v1.json)은 신규32+영향 기존 마스킹3=35pass·
881fresh/final881·진단/경고없음·cleanupTrue다. source23/기존 제품 전체/공식249는 반복하지 않았다.
현재 source와 strict 요청·전체 metadata 상한·read-only 후속 요청·5종 provider scope·ACL 철회/복구·격리/암호문
변조·원본/ingest/head 불변과 준비/검증/metadata/next/selection의5개 consumer-final head 경합을 확인했다.
시험은 synthetic marker/scanner/키를 사용하며 실제 개인정보·native 기본 형식 정확도·운영 DB 증거가 아니다.

전체162.407초·명령45.020초·Job CPU42.891초·private최고1906.07MiB/5.98248%·시스템CPU최고41.07%·
가용RAM최저35.8555%와 Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·
RAM/commit95%를 유지했으며 PC 프리즈 원인 귀속이나 해결 증거는 아니다.

기본 형식 정책·전체 옵션·실제 변경/저장/게시·신뢰 registry·target match_set/semantic_diff/reopen·Native/Gate는 남는다.
공통 변경23계열·RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3·
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기를 유지한다. 한글/접근 허용·운영 DB·시스템/Defender/WSL 설정은 건드리지 않았다.
