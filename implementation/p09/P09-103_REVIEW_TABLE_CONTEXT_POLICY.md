# P09-103: 실제 메모 위치와 원본 표 생성 템플릿 결속

## 목적과 범위

원래 TableCreateHwpxReader는 최상위 빈 문단을 요구한다. 메모 내부 삽입을 위해
실제 MEMO/hiddenComment의 빈 문단과 원본 2×2 표 템플릿을 연결하는 immutable
ReviewTableCreationContext를 추가한다. 기존 공개 reader/builder/lowerer는 바꾸지 않는다.
새 표 출력이나 전체 document Flow를 임의 값으로 대신하는 구현이 아니다.

입력은 실제 review marker/paragraph source anchor, 원래 ImportedDocumentForms로
읽은 template package/table anchor, 두 fresh whole package와 finite limits뿐이다.
호출자 XML, offset, native numeric ID, 물리 치수, cell ID, 임의 graph/Flow hash를 받지 않는다.

## 기존 구현 재사용

선택된 문단은 같은 part의 실제 review body 아래, qualified p이며 direct parent는
qualified subList여야 한다. 다른 review/본문/foreign/stale/nonempty 입력은 거부한다.
기존 descendant_path와 observed ancestor table/cell protection 검사를 재사용한다.
누락된 보호값은 0으로 만들거나 전체 보호 검증으로 승격하지 않는다.
UNKNOWN boolean은 기존 native importer 단계에서 정확한 기존 오류로 거부된다.

원래 실제 table mapper의 TableNode/cell source-derived logical IDs와 원래
TableLayoutHwpxReader의 native row/column/span/width/height를 대조한다.
지원 템플릿은 exact unmerged2×2이며 각 열 너비/행 높이가 native 관측 전체에서
일치해야 한다. checked sums가 실제 표 폭/높이와 같아야 하며 임의 치수를 채우지 않는다.
빈 scaffold paragraph의 graph ID는 payload block으로 꾸미지 않는다. 원래
TableRulingHwpxReader, pagination, template-profile, native-wrapper와 insertion-wrapper
검사가 blank/payload0/formula0/서식/page 조건을 그대로 검증한다.

현재 단계는 원본 destination/template header의 전체 bytes가 같은 경우만 지원한다.
동일 ID가 동일 서식이라는 추정이나 임의 style-ID 재매핑은 하지 않는다.
header reconciliation은 실제 lowering에 필요한 별도 미완료 항목이다.
템플릿 native table ID가 destination의 해당 section에 이미 있으면 원래 collision
검사를 통해 거부한다. 다른 section까지의 ID closure는 아직 검증되지 않았다.

## 불변성과 사용 경계

context는 private fields와 원래 importer references를 보관하고 Deserialize하지 않는다.
verify_source는 두 전체 archive를 fresh 검증한 뒤 실제 선택/원래 native guards/receipt를
재실행하여 전체 readback equality를 확인한다. opaque part만 달라도 거부한다.
native_context는 캐시된 관측 getter이지 fresh stored access 또는 실행 권한이 아니다.
새 context profile/digest domain은 기존 top-level create profile과 다르다.
placeholder_paragraph_ordinal은 이 partial profile에서 XML element index이며
native caret/쪽 좌표로 사용하거나 기존 top-level ordinal로 해석할 수 없다.

partial review/template graph digests는 diagnostic binding일 뿐 full document Flow가 아니다.
new_table_inserted/full_document_flow_bound/full_comment_product_acceptance는 false다.
실제 새 표 lowering, whole-package ID validation, rich Flow와 full compiler/protection,
stored service 연결, issuer/atomic execution/publication은 남아 있다.

## 보존과 검증

수정 부모4개는 전체 preimage를 보관한다. review module export, crate-private packet
export, native reader의 표시된 신규 block, 기존 test helper4개의 parent visibility 변경
밖에 원래 바이트가 변하지 않았는지 전체 역비교한다. 기존 parser/guard/assertions는
삭제·약화하지 않는다. 원래 P102 audit는 exact prior read-view에서 그대로 실행한다.
기존 890 source entries와1479 raw pins, 과거 실행 파일158개를 유지한다.

접근허용/한글/COM/UI/실제SQL/운영·trust DB/설치·설정/commit/push/삭제·이동을
실행하지 않는다. root PLANS.md 부재와 사용자 dirty changes/실패 evidence를 유지한다.
source/synthetic/component 회귀는 native 저장·재열기/render/Gate 증거가 아니다.
P09/A12/A13 OPEN, native34 NOT_RUN/green0, P26 failed_semantic_non_green,
P62/P84_SQL UNRESOLVED, INPUT_CHANGED_RE_ADMISSION_REQUIRED, no P10을 유지한다.
