# 문단 정렬의 현재 저장과 제품 요청

StoredParagraphSortProductRequest::prepare_json은 hwpx-agent.product-paragraph-sort-request/v1 요청을
현재 저장된 sealed Result 원본과 실제 원본 정렬 후보에 연결한다. SEARCH-021의 단일 형제 그룹 경로이며
공통 dispatcher/compiler·실제 실행/ingest/commit/CAS·영속 멱등/게시는 별도다.

## 닫힌 요청

기존 project/document/base_revision·expected_head_generation·expected_source_package_sha256·plan_id·
idempotency_key와 네 종류 selector를 사용한다. operation.kind는 sort_sibling_paragraphs이며 sort_spec의
direction·comparison·max_comparison_bytes와 review_policy를 필수로 받는다. 정렬 기준은 원본 계약의
NfcUnicodeScalarLexicographic이고 비교 byte 상한은 1 이상32MiB 이하이다. query/filter/locale나 승인 flags를
암묵적으로 무시하지 않고 거부한다. 이 schema를 카탈로그 전체 정렬 계약으로 승격하지 않는다.

요청은 최대16KiB이며 중복/escaped 중복·미지 필드·배열 envelope·trailing JSON·부적합 selector 형태·
revision 불일치를 원본 읽기 전에 거부한다. raw/canonical/scoped SHA는 요청·key/plan/spec/policy와 현재
서비스 scope를 결속한다. 정확한16KiB에서 허용된 whitespace는 raw SHA만 바꾸고 canonical/scoped SHA는 유지한다.

## 현재 원본과 보관 후보

StoredImportedDocumentForms::prepare_paragraph_sort_candidate는 현재 document.write·scope/head/ACL/
quarantine/AEAD와 전체 Form 재구성을 확인하고 같은 proof로 lower_selector_paragraph_sort_candidate를 호출한다.
기존 source comparator·선택 범위·보호·필드·순열 patch·writer·독립 readback은 변경하지 않는다.
borrowed 후보와 into_paragraph_sort_candidate의 owned 후보는 같은 원본을 사용하며 clone/reimport/재정렬로
다른 결과를 만들지 않는다. 원본 소유자를 이동한 뒤에도 요청을 버리고 결과를 검증할 수 있다.

보관된 후보의 verify/byte 전달은 현재 document.write와 동일한 원본 접근을 다시 확인하며, 원본/출력/receipt/
프로필·순열·작업량·비권한 flags의 결속을 확인한다. byte consumer 직전 마지막 head 확인은 writer 검증 내부에 있다.
현재 source 검증이 필요하다는 이유로 원본 정렬을 다시 실행하지 않는다. 외부 document/branch/project/subject/
tenant나 회수된 ACL·격리·변조된 암호문·마지막 head 경합은 소비자를 호출하지 못한다.

StoredParagraphSortReceipt와 ParagraphSortProductReceipt는 원문/정렬 키/비밀 요청 key를 노출하지 않는다.
capability_id는 search.sort_text지만 idempotency_key_claimed=false와 full_sort_native_cas_execution_publication_authority=false다.
현재 후보의 무결성은 현재 실행 허가가 아니므로 require_current_product_route는 RouteUnqualified를 유지한다.

## 검증 결과

components235 신규 제품20pass·802fresh/final802·진단/경고없음·cleanupTrue다. 실제 정렬/원문 보존·borrowed/
owned/JSON 일치·NFC 양방향 안정성·네 selector·부분/오래된 선택 거부·닫힌/중복/escaped JSON·정확한16KiB·
key/plan/spec/policy 결속·현재 write/외부5scope·ACL 회수/재부여·격리/AEAD·prepare/verify/전달의 마지막 head 경합·
보호/필드·한도·무변경·비노출/미게시·128문단·숨김 정책을 확인했다. 원 source 정렬19·patch18·공식249는 반복하지 않았다.
기존 제품/시험 본문은 root별 module child와 시험 child를 제거하면 전체 역변환된다.
근거는 implementation/p09/evidence/p09-361-paragraph-sort-product-components235.v1.json이다.

235 전체152.296초·명령49.090초·시험6.90초·Job CPU46.734초다. 시스템CPU 최고25.00%·private 최고1801.05MiB/5.65285%·
가용RAM 최저26.7660%이며 Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·
private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했다. OS 변경이나 PC 프리즈 해결을 주장하지 않는다.

## 남은 제품 경계

공통 dispatcher/compiler·실제 실행/ingest/commit/CAS·영속 멱등/게시·다중/중첩 그룹·구조적 키·locale/target/Native와
전체 SEARCH-021 계약은 미완료다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·
P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
