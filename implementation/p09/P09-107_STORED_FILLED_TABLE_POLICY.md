# P09-107 저장 원본·템플릿의 셀 내용 포함 표 준비 정책

## 실제 경로와 입력

원래 StoredImportedReviewBodies/StoredFormProvider의 authenticated actual document와
독립 actual template import를 P09-106 실제 filled native package 출력에 연결한다.
StoredReviewFilledTableRequest는 원래 StoredReviewTableRequest의 actual template,
source-derived marker/paragraph/table anchors 및 신규 geometry와 immutable typed
ReviewNewTableCells를 받는다. raw XML/source bytes/offset/native metadata/full-Flow
hash/caller permission을 추가로 받지 않는다. 원래 P105 빈 표 경로는 그대로 유지한다.

양쪽 provider는 동일한 authenticated tenant/subject여야 한다. 각 입력의 문서·프로젝트·
branch는 원래 provider scope/ACL/head/AEAD/scanner/result kind/digest checks를
독립적으로 통과해야 한다. 같은 actor/document/generation의 다른 service result도
같은 원본으로 재결합하지 않는다. getter/캐시/receipt는 현재 권한이 아니다.

## fresh 준비·다시 검증·출력

준비 전 원래 review.verify/source.fresh_source와 template.fresh_source를 실행하고,
실제 새 context와 원래 filled output을 만든다. 이후 양쪽 원래 서비스를 다시 확인한다.
verify는 같은 fresh 절차와 전체 deterministic filled package/cell output chain을
재실행하고 immutable receipt/artifact/generations/qualification을 비교한다.
with_verified_bytes는 verify가 실패하면 consumer를 호출하지 않는다.
반복 fresh reads는 다음 callback까지 권한을 고정하는 atomic lease/CAS가 아니다.

require_current_product_route는 fresh source/template/output failures를 먼저 표시한
뒤에도 항상 원래 closed RouteUnqualified를 반환한다. 원래 actor/source/template/
output/binding/route error enum을 재사용하며 원본 path/XML/본문/실패 상세를 노출하지 않는다.
객체 Debug는 redacted이고 receipt는 두 head generations와 source package proof다.
blank_creation은 중간 빈 표 증거, final filled package digest/bytes/chain은 별도다.

## 검증 경계와 미완료

현재 true인 것은 stored_source_and_template_filled_table_authenticated source-component
뿐이다. 실제 encrypted in-memory ArtifactService/RevisionService 검사는 actual SQL
durability/운영 integration/atomic execution/publication/full rich Flow/comment compiler,
native author/time/state/caret/protection/전체 opaque ID closure/save-reopen/render 증거가 아니다.
원래 exact shared header/native blank template 및 typed cell-body 제한을 유지한다.
DATE parameter/locale/timezone을 추측하지 않는다.

최소6개 큰 잔여 묶음은 그대로이며 세부 작업 수와 완료율은 확정하지 않는다.
Native34 NOT_RUN/green0, INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED,
P09/A12/A13 OPEN, no P10/full product false다. 전체 P09~P20 목표 active.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동을
하지 않는다. 삭제된 root PLANS.md를 만들지 않는다.
