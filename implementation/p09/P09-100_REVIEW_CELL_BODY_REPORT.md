# P09-100 기존 메모 표 셀 본문 출력 결과

실제 source에서 관찰된 MEMO/hiddenComment 안의 표 셀 내용을 typed 문단으로 편집하는
원래 package·stored source 경로를 구현했다. 원래 전체 본문 출력의 patch/ID/writer/재수입
검사를 공유하며 표 geometry·서식·다른 셀·opaque 내용·메타정보·다른 part는 보존한다.
새 표 삽입, 전체 rich Flow, native CommentState/보호/compiler 제품 경로 완료는 아니다.

## 변경과 구현 검사

package review/cell_body_output.rs는 actual tc/source anchor를 같은 selected review body에
결속하고 내부 전체 descendant path만 원래 본문 출력 경로에 넘긴다. original body_output.rs의
lower_body는 빈 경로로 같은 동작을 유지한다. outer tc/tbl/sz의 관찰된 보호 표시도 검사한다.
누락 속성이나 zero flag를 완전한 unprotected policy로 승격하지 않는다.

stored review/cell_body_output.rs는 original fresh source/scope/ACL/AEAD/quarantine/head
검사와 complete output replay를 prepare/verify/callback에 연결한다. product route는 항상
RouteUnqualified로 거부한다. 새 ingest/revision/publication이 없으며 반복 검사는 atomic lease가 아니다.

Rust package132 +product164 =296 named tests PASS/0 FAIL/0 ignored다. 새 feature9(package6,
stored3)는 그 안에 포함되며 전체 과거 검증 재실행은 아니다. package6은 MEMO/hidden multi-
paragraph/run/Unicode/tab/lineBreak 출력의 전체 section outside/content 및 다른 part exact,
foreign/other review/main/stale selection, unsafe/empty/opaque/style/budget/protection/no-op,
immutable captured no-review 및 nested table cell/outer protection을 검사한다.
stored3은 direct output/receipt 동일·no writes와 AEAD/ACL/regrant/head 및 scope5 substitution이다.
원래 body/style/delete/location/IR/comment compiler 및 원래 저장 provider 전체 회귀를 포함한다.

strict package/product 검사는 warnings를 허용하지 않는다. 새 Rust5 파일 format check와
git diff --check를 수행했다. Python10은 live prior raw/부모 변환과 shared pipeline shape/
view routing/restoration 및 mock current manifest 검사다. mock 검사는 actual raw/native 증거가
아니며 별도 current CLI가 실제 선언 바이트 전체를 확인한다.

원래 current-source component 검사15는 PASS/green0/P09 OPEN이고 기본 검사는 여전히
FAIL:matrix_drift다. 원래 실패를 고치거나 지워서 완료 수를 올리지 않았다.

## 실패 보존과 수정

최초 package 테스트는 기존 body5 PASS, 새 cell3 PASS/2 FAIL이었다. 동일 native 문단 ID의
다문단 출력은 원래 patch/ID 검사에서 거부됐다. 테스트 입력을 distinct IDs로 고쳤다.
table sz protect 표시를 놓친 경우는 실제 ancestor tc/tbl/sz 검사로 수정하고 nested outer
protection 회귀도 추가했다. 실패 소스4개 및 실패 test executable 전체를 먼저 보존했다.

수정 테스트의 id 타입을 Option으로 잘못 쓴 E0308 compile failure도 전체 테스트 소스를
보존한 뒤 원래 u32로 수정했다. strict lint 실패(format_collect/format_push_string/expect_used와
공유 original fixture duplicate_mod)는 각 fixture 소스를 보존하고 직접 String 포맷 작성 및
원래 fixture의 공유 visibility/단일 import로 수정했다. lint를 허용하거나 검사를 약화하지 않았다.
compile/lint 실패로 예정된 후속 전체 회귀가 실행되지 않은 경우 NOT_RUN으로 남겼으며,
최종 동일 live session을 terminal까지 관찰해 package/product 검사를 완료했다.

## 원본 보존과 잔여 경계

P99 전체 checkpoint를 고정하고 prior raw pins1,347개, source852개 중847 exact/부모5개
whole preimage 및 전체 선언 transform을 확인했다. 원래 P99 audit를 수정하지 않은 채 exact
prior parent view에서 통과했다. 과거 executable116개는 raw bytes 보존이며 재실행 주장이 아니다.
current source865는 파일 수이지 남은 작업 수나 제품 완료율이 아니다.

한글/COM/UI/접근허용/실제SQL/운영·trust DB/설치·설정/commit/push를 하지 않았다.
사용자 원본·이전 실패·P00~P08 및 unrelated dirty 변경을 삭제·이동·덮어쓰지 않았다.
root PLANS.md는 없는 상태를 유지한다.

새 표 삽입과 full rich Flow/native typed state/author/time/visibility/resolution/protection,
원래 compiler 연결, durable/issuer/atomic execution/publication, 나머지 field/Date/external
및 P84 SQL 원인은 남는다. 최소6개 큰 잔여 묶음을 차감하지 않는다. native34는 별도 NOT_RUN.
P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; green0; product_complete=false;
full_comment_product_acceptance=false; P10_new_implementation=false; goal_status=active.

정책: P09-100_REVIEW_CELL_BODY_POLICY.md. Migration: protocol/migrations/p09-review-cell-body-v0-to-v1.md.
실행 terminal/정확한 현재 raw pins: evidence/p09-100-review-cell-body.*.v1.json.
