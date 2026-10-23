# P09-103 review table source context v0 → partial v1

기존 공개 table create contract/schema/profile은 변경하지 않는다. 새 source-only API는
ImportedDocumentReviewBodies::prepare_table_creation, ReviewTableTemplate,
ReviewTableCreationContext::{receipt,native_context,verify_source}다.
입력은 immutable imported template/actual anchors/fresh packages/finite limits다.

ReviewTableCreationContext는 deserializable wire command가 아니다. 원래 native2×2
template guards를 재사용하지만 context profile은
hwpx-agent.review-table-create-source-context/partial-v1이며 insertion digest domain은
hwpx-agent.review-table-insertion-context/v1이다. 기존 최상위 create request로
이 readback을 해석하거나 replay하지 않는다. 해당 partial profile의 placeholder field는
source XML index이며 native caret 또는 최상위 문단 순번이 아니다.

header_binding=exact_shared_original_header는 전체 native header의 실제 byte equality다.
observed graph digests는 complete Flow hash 대신 사용할 수 없다.
new_table_inserted/full_document_flow_bound/full_comment_product_acceptance=false를 유지한다.
출력/전체 ID closure/서식 재조정/full compiler/stored access/execution/publication은
후속 구현과 실제 검증이 필요하다. native/SQL/P09 Gate 상태를 승격하지 않는다.
