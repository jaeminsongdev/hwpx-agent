# P09 폰트 공통 준비와 계획 컴파일러

엄격한 product-scoped-font-replacement-request/v1은 공통 SearchMutation 표의19번째 Font family다.
기존 원 요청·후보·receipt를 이동하며 별도 원본 clone/reimport·폰트 검색/lowering을 추가하지 않는다.
StoredProductRequest.prepare_compiled_search_json과 준비된 SearchMutation.compile은 기존
SelectorSnapshot/OperationPlanCompiler로 실제 본문 소유자에 결속한다. 실제 실행기는 별도다.

## 본문 대상과 헤더 자원

source_edit_domain은 final_font_body_splices_with_header_resources다. source_edit_index는
inventory.body_splices의0기반 index이며 전체 edits index와 구분한다. 각 본문 최종 splice의 실제
anchor/outer span을 검증하고 기존 owner resolver로 가장 가까운 실제 구조 소유 node를 찾는다.
소유자는 문맥이며 편집 범위를 문단 전체로 확대하지 않는다. 헤더에 가상 본문 node를 만들지 않는다.

기존 잠금 인자12개에 다음 필수 Text 인자3개를 추가한다. 모두 서버의 private candidate에서만 만든다.

- source_font_header_count_effect_json은 실제 header charProperties/itemCnt의 count 효과다.
- source_font_header_append_effect_json은 실제 마지막 기존 charPr 뒤 append 효과다.
- source_font_resource_binding_profile은 exact_header_effects_once_per_inventory_with_actual_body_owner/v1이다.

두 JSON은 source-font-edit-inventory/v1의 정확한 typed row이며 XML/폰트 이름을 포함하지 않는다.
현재 원본 anchor와 part·속성 index/byte 범위·원/출력 정의 수·추가 수·치환 지문을 대조한다.
모든 본문 operation은 같은 edit_inventory_sha256과 같은 두 자원을 가진다. 헤더 자원은 별도
Operation이나 depends_on이 아니라 그 inventory 그룹의 필수 인자다. 후속 실행기는 후보 전체
단위로 두 효과를1회 적용해야 하며 본문 operation마다 반복해서 적용하면 안 된다.

CompiledSearchReceipt.source_edit_operations는 본문 operation 수다. 전체 원본 편집 수는 inventory.edits에
기록한 헤더2개+본문 수이며 receipt.edit_inventory_sha256은 그 전체 목록을 결속한다.
원 compiled receipt JSON/권위는 바꾸지 않았고 execution_authority는 false다.

## 한도와 현재 접근

기존18개 family는 원12개 인자를 유지하고 폰트만15개를 요구한다. 각 인자는2048byte, 전체 인자8MiB,
plan16MiB와 원본 편집4096개 상한을 유지한다. 두 헤더 JSON은 bounded hash로 크기를 확인한 뒤
한 번 직렬화하고 여러 본문 operation에 공유한다. 복제 전 추가 인자 총량도 검사한다.
caller가 header 인자나 승인 필드를 넣으면 원 엄격한 parser가 원본 읽기 전에 거부한다.

compile은 현재 write/scope/head·ACL/격리/AEAD·원본/출력 무결성 안에서 수행하며 compiler 직후 head도
확인한다. 보관 검증/전달은 원 현재 접근과 plan/metadata 무결성·최종 consumer head를 유지하고
검색·owner map·snapshot·OperationPlanCompiler를 반복하지 않는다. RouteUnqualified는 유지한다.

## 검증과 남은 경계

323 입력 원장 실패는 Cargo 전에 발생했다.249의 기존18종 스키마 시험 pin을 추가한324는
신규 폰트16+영향 기존4=20pass·753fresh/final753·진단/경고없음·cleanupTrue다. 실제 두 번째 문단 owner,
양 축·NFC/공유 원형·자원 그룹·15개 인자·지문/비노출·현재 권한·격리/AEAD·세 단계 head 경합과
서버 한도를 확인했다. 기존 width/style/regex/sort는12개 인자이며 직전36개·공식249는 반복하지 않았다.
대형 과거 시험 모듈은 기대 schema 수와 새 구성원만 수정했고 본체는 실행하지 않았다.

이 계획은 신뢰된 registry/실행 허가·실제 저장/commit/CAS·영속 멱등 실행·게시·Native 자격이 아니다.
전체 옵션/review·field·protection 조합·유효 서식/fallback도 남는다. 공식158/249·잔여91·next165·
P09/A12/A13 OPEN·P10 미시작·Native011 미승인/미실행을 유지한다.
