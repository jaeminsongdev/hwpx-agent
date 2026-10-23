# 개인정보 선택 마스킹의 현재 저장과 제품 요청

`hwpx-agent.product-personal-info-selection-mask-request/v1`은 SEARCH-019의 현재 저장 문서에 결속한
선택 마스킹 후보 또는 출력 파일을 폐기한 미리보기를 준비한다. [원본 선택 마스킹 계약](p09-source-personal-info-selection-mask-v1.md)의
두 정책과 비선택 개인정보/Native 미자격 경계를 유지한다. 탐지 엔진이나 문서 전체 익명화 제품이 아니다.

## 엄격한 요청과 서비스 경계

루트는 schema_version, idempotency_key, plan_id, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, selector, operation을 모두 요구한다.
selector는 기존 document/section/node_set/selection과 동일 revision에 결속한다. operation은
kind=mask_selected_personal_info, mask_policy, max_changed_components, review_policy, preview_only를 모두 받는다.
mask_policy는 per_original_scalar_preserve_slots 또는 three_asterisks_per_text_group이다. preview_only에는 기본값이 없다.

16KiB 요청·고유/escaped 고유 키·문자열 enum·필수 bool/범위·양수 generation·소문자 source SHA·selector shape와
동일 revision을 읽기 전에 검사한다. 성분 상한은1..10000이며 서버 match 한도와 교집합을 사용한다.
query/replacement·regex/direction/style_filter·caller XML/graph·승인 bits는 거부한다. 이 별도 프로필을 기존
generic 카탈로그의 전체 옵션 지원으로 취급하지 않으며 원 계약도 재정의하지 않는다.

원 source-search provider scope와 document.write를 먼저 확인하고 현재 sealed Result를 읽는다. source SHA와
head를 대조한 뒤 기존 tenant/subject/project/branch/document·ACL/quarantine/AEAD·whole Form 재구성 경계를
공유한다. borrowed/owned는 같은 준비 함수를 사용하고 owner를 이동하므로 source를 복제하거나 index/mask/
writer를 다시 실행하지 않는다. 기존 source core와 공통 변경22계열은 변경하지 않았다.

## 보관 결과와 미리보기

변경 후보는 원본 owner·실제 writer artifact·source/output/selector/review/mask 지문 receipt를 보관한다.
verify/bytes/JSON 전달은 현재 source/access와 보관 receipt·writer integrity를 확인하고 최종 head 확인 뒤
consumer를 호출한다. 재검증에서 마스킹이나 writer를 반복하지 않으며 원자적 CAS를 주장하지 않는다.

into_preview는 artifact를 폐기하고 source owner와 예측 receipt만 남긴다. preview에는 bytes/compiler/inventory
API나 역변환이 없고 제품 with_verified_bytes는 consumer를 호출하지 않고 PreviewOnly를 반환한다.
preview metadata도 현재 source/access·최종 head를 확인한다. 이 미리보기는 SEARCH-019 준비이며
SEARCH-020 개인정보 탐지/읽기 전용 선택을 구현한 것이 아니다.

전체 service/product metadata는 서버 result byte 상한 안에 있어야 한다. 저장 계층은 allocation 없는 유한
계수 writer를 사용하고 제품 JSON 전달도 bounded writer를 사용한다. 원본 core 기본4MiB ceiling은 유지한다.
출력 JSON/Debug에는 원문·선택 조각·개인정보 값별 해시·key 원문을 넣지 않는다. 집계는 반환하므로
정보 이론적 비노출은 보장하지 않는다.

whole_package_personal_data_removed=false다. header·메모 저자·미리보기·첨부·비선택 개인정보가 남을 수 있다.
idempotency_key_claimed와 full_personal_info_native_cas_execution_publication_authority도 false다.
require_current_product_route는 현재 접근을 검증한 뒤 RouteUnqualified이며 실제 ingest/commit/CAS/게시를 하지 않는다.

## 검증과 다음 경계

[365](../../implementation/p09/evidence/p09-361-personal-info-mask-product365.v1.json)는 신규33+영향 기존3=36pass·
856fresh/final856·진단/경고없음·cleanupTrue다. 두 정책/네 범위·review/cache·preview 폐기·현재 권한/ACL·격리/
암호문 변조·다른 provider5종·source/scanner·정확한 요청/응답 한도·작업/writer 상한·원본 보존·비노출과
변경4종/preview3종 최종 head 경합을 확인했다. 기존 source25/전체 제품/공식249를 반복하지 않았다.

365 전체172.843초·명령51.500+7.844초·Job CPU49.172+6.516초·private최고1896.59MiB/5.9527%·
시스템CPU최고33.97%·가용RAM최저37.0531%다. 원 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·
RAM/commit95%와 두 Job active0/empty/handle closed를 유지했다. PC 프리즈 해결 증거는 아니다.

다음은 변경 전용 compiler owner·공통 dispatcher·실제 실행/저장·전체 개인정보 정책과 target의 match_set/
semantic_diff/reopen이다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·
Native011 미승인/미실행·문자 스타일6종 선택 대기를 유지한다.
