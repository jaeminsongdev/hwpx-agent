# P09 review cell body: source component v0 → v1

## 계약

v0의 lower_body와 prepare_body는 기존 review의 전체 문단 본문을 출력한다.
v1은 lower_table_cell_body와 prepare_table_cell_body로 actual source tc anchor에 묶인
메모/숨은 설명 표 셀의 문단 내용을 편집한다. 기존 공개 입력·receipt·원래 reader/validator/
TextFlow/IR schema/compiler는 바꾸지 않는다. lower_body 내부만 실제 선택 경로를 공유하며
빈 경로는 원래 전체-body 동작이다.

ReviewCellBodyOutput/PreparedStoredReviewCellBody는 immutable 출력과 source cell binding을
유지한다. 새 native table/author/time/state/protection defaults나 public capability를 만들지 않는다.
이미지·표 등 새 rich object는 원래 TextFlowWriter의 opaque-lowering 금지를 유지한다.

## 호출자 전환

셀 편집 호출자는 원래 source를 다시 읽고 선택된 review body 안의 actual tc anchor를
얻어 complete typed 문단을 전달한다. 이름/행열/numeric ID/offset만으로 예전 anchor를
다시 연결하지 않는다. 출력 뒤 기존 source anchor를 새 package에 재사용하지 않는다.
저장된 문서의 callback은 원래 fresh stored source 검사와 출력 replay를 거친다.
그 결과는 publication/execution 승인이나 원자적 lease가 아니다. full product route는 계속 거부한다.

## 검사와 보존

MEMO/hidden 셀, 여러 문단·run·Unicode·tab·lineBreak, 다른 셀/opaque/part exact,
다른 review/main/외부/stale anchor, nested cell 및 outer protection, 원래 budgets/style/ID,
no-op/immutable capture를 검사한다. stored AEAD/ACL/regrant/head/scope5 거부도 검사한다.
원래 전체 body/style/delete/location 및 저장 경로 회귀를 유지한다.

P09-100_REVIEW_CELL_BODY_REPORT.md와 evidence/p09-100-review-cell-body.*.v1.json을 참조한다.
source component 검사 통과는 native/full product/Gate 통과가 아니다. 원본 rollback은 전체
preimage를 비교·검토한 후 별도 승인 범위에서만 수행하며 자동 덮어쓰기·삭제하지 않는다.
