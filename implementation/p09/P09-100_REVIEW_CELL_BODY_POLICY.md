# P09-100 기존 메모 표 셀 본문 출력 정책

## 제품 요구와 이번 구현 범위

P09-04의 완전한 메모 기능에는 native metadata/state/protection, 원래 typed compiler,
삽입·표시·해결 및 전체 rich Flow가 필요하다. 이번 구현은 그중 실제 관찰된 MEMO 또는
hiddenComment 본문 안의 기존 표 셀에 typed TextFlow 문단을 출력하는 경로다.
새 표 생성·삽입이나 임의 rich object 직렬화를 구현한 것으로 대체하지 않는다.

기존 일반 문단 TableCreateHwpxLowerer는 exact 2x2 native template 및 top-level
placeholder를 요구한다. 메모 subList의 nested 문단을 그 경로에 임의로 끼워 넣거나
native ID·style·header·placement 계약을 우회하지 않는다. 새 표 삽입은 미완료다.

## 입력·선택·출력

- 입력은 원래 immutable package의 fresh bytes, actual review marker와 actual tc의
  SourceAnchorHandle, complete typed TextFlow 문단, 원래 WriterLimits다.
- caller raw XML·offset·table ordinal·numeric ID 또는 authority/evidence boolean을 받지 않는다.
- cell은 같은 part의 선택된 review body 내부여야 한다. 실제 tc/tr/tbl parent와 유일한
  direct subList를 확인한다. 다른 메모·main body·외부 문서·이전 output의 anchor는 거부한다.
- 전체 ancestor 경로에서 관찰된 tc protect, tbl lock, table sz protect의 nonzero/unknown
  값은 거부한다. 없는 속성을 unprotected로 채우지 않으며 zero flags도 전체 보호 정책
  검증으로 승격하지 않는다.
- 기존 lower_body는 빈 content path로 같은 원래 출력 경로를 사용한다. 내부 descendant
  path는 actual source에서만 도출하며 공개 입력/직렬화로 노출하지 않는다.
- 원래 TextFlowWriter, ReplaceElementContent, ID FormulaV3, PreviewTextV2 preservation,
  PreservingWriter, 전체 source/forms/fields/review 재수입 및 typed 문단 비교를 공유한다.
- selected cell subList content 외의 section prefix/suffix 전체가 exact이며 다른 part는
  raw SHA exact다. containing table geometry/다른 셀/메타정보/marker는 변경하지 않는다.
  선택 셀 안의 기존 내용은 complete replacement 대상이며 새 opaque/table 내용은 원래
  TextFlowWriter가 허용하지 않는다. 전체 rich Flow 출력 지원이라고 부르지 않는다.

## 저장된 문서 경로

prepare/verify/callback 전에 원래 stored source의 scope/ACL/AEAD/quarantine/head 및
whole import 검사를 수행하고 동일 출력과 receipt를 다시 도출한다. 실패 후 callback을
호출하지 않는다. 반복 fresh read는 held atomic execution lease가 아니다.
current product route는 검증 후에도 RouteUnqualified로 거부하며 새 ingest, revision commit,
publication, actual SQL 또는 native execution을 수행하지 않는다.

## 유한 한도·원본·검증 경계

원래 source/XML/review/paragraph/patch/writer limits와 stale/conflict/ID/style 검사를 유지한다.
empty/no-op/opaque/unresolved style/over-limit/unsafe output에는 partial artifact를 반환하지 않는다.
원본과 과거 실패/receipt는 보존한다. 부모5개 whole preimage와 명시된 변경의 전체 exact
transform을 검사하고, 수정하지 않은 P99 audit를 exact prior parent view에서 실행한다.
prior view는 current native/product acceptance가 아니다.

synthetic/native-package-builder 및 저장소 fixture 검사는 실제 한글/native caret/render/
저장·재열기/SQL 또는 full CommentState acceptance를 대신하지 않는다.
P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; native34 NOT_RUN/green0.
최소6개 큰 잔여 묶음은 유지하며 P10 새 구현이나 full goal 완료로 승격하지 않는다.

한글/COM/UI/접근허용/실제SQL/운영·trust DB/설치·설정/commit/push를 실행하지 않는다.
삭제된 root PLANS.md는 재생성하지 않는다.
