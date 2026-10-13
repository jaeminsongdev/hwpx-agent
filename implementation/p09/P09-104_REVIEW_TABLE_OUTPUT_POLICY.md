# P09-104 실제 메모 빈 표 출력 정책

## 범위와 원래 제품 계약

P09-103의 immutable actual review paragraph/template context에서 실제 HWPX package를
생성한다. MEMO, hiddenComment, 그 내부 기존 표 셀의 실제 빈 문단이 대상이다.
원래 native table renderer/grid/ruling/layout/pagination, preserving patch engine,
FormulaV3 ID validation, PreviewTextV2 preservation, package writer와 original importer를
재사용한다. 별도 XML backend나 fake full-Flow hash를 만들지 않는다.

행 높이/열 너비는 명시적인 신규 표 요청 치수다. template 관측 치수로 속이지 않으며
logical IDs는 source context + 요청 치수의 domain-separated deterministic transient
builder identities다. native table ID/frame/style은 원래 template에서 상속한다.
원래 공개 TableCreateHwpxBuilder/Lowerer의 전체 Flow 결속 조건은 변경하지 않는다.
전체 Flow/compiler/product 연결은 이 source-only API의 구현과 별개로 남는다.

## 안전·보존 계약

- source/template 전체 archive fresh 재검증을 입력과 반환 전에 수행한다.
- 실제 선택된 review/paragraph 경로, ancestor protection과 원래 template guards를 유지한다.
- 현재 importer가 인정한 XML parts 전체에서 template native table ID 충돌을 거부한다.
  opaque/unknown ID domain까지 포함한 전체 package ID closure는 아직 미검증이다.
- template wrapper의 문단 ID는 실제 교체 대상 빈 문단의 native ID로 이어 쓴다.
  zero sentinel도 실제 source 값인 경우만 유지한다. 새 ID나 임의 0을 만들지 않는다.
- inherited namespace fragment는 admitted whole template로 분석한다.
  원래 wrapper/scaffold 검사와 exact selected identity span 검사 후 원래 bounded edits를 쓴다.
- original patch/ID validation이 다른 duplicate/dangling/style 참조를 계속 거부한다.
  진단은 original closed static error code만 제공하며 XML/문서/원시 로그는 노출하지 않는다.
- 완성된 package를 원래 importer로 다시 읽고 actual new grid/state/tracks/target review를 확인한다.
- 선택된 빈 문단 외 section bytes와 그 외 모든 expanded ZIP parts는 정확히 보존한다.
  header는 원래 renderer의 border-fill coordination 결과와 정확히 같아야 한다.
- Artifact는 immutable verified bytes로만 읽는다. integrity는 stored ACL/issuer/실행·발행 권한이 아니다.

## 완료로 승격하지 않는 것

source_review_blank_table_output_implemented만 이 범위에서 true다.
full_document_flow_bound/full_comment_product_acceptance/native visual acceptance/
actual SQL/root cause/whole_package_ID_closure/full protection/execution publication은 false다.
author/time/state/caret coordinates, rich comment compiler, durable integration,
남은 fields/Date/external/document semantics, trusted atomic publication, P84 SQL는 남는다.

Native34 NOT_RUN/green0, INPUT_CHANGED_RE_ADMISSION_REQUIRED, P26 failed_semantic_non_green,
P62/P84_SQL UNRESOLVED, P09/A12/A13 OPEN을 유지한다. P10 새 구현은 없다.
전체 목표는 P09~P20 그대로 active다. 최소6개 큰 잔여 묶음은 세부 작업 수가 아니다.

한글/COM/UI/접근허용, actual SQL/운영·trust DB, 설치·설정, stage/commit/push,
삭제·이동은 이 범위에서 실행하지 않는다. root PLANS.md는 재생성하지 않는다.
