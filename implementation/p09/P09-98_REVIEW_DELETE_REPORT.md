# P09-98 기존 메모·숨은 설명 삭제 출력 결과

기존 원본 MEMO의 paired begin/end ctrl과 hiddenComment의 삭제 출력 및 원래 인증 저장소의
fresh 검증 연결을 구현했다. 선택 본문과 다른 모든 XML bytes/parts를 그대로 유지하고
원래 전체 importer로 결과를 다시 읽는다. 이것은 실제 한글/P09 Gate/전체 메모 제품의
완료 판정이 아니다.

## 변경

package review/delete_output.rs에 existing-anchor 삭제, 원래 patch/ID/writer 출력,
전체 section 비삭제 구간 exact readback과 종류별 field/review 감소를 연결했다.
product review/delete_output.rs에는 원래 ACL/AEAD/quarantine/head/scope/source 검사 전후
prepare/replay/verified callback을 연결했다. 원래 연결 부모3개에는 module 선언만 추가했다.

대상 source overwrite, 실제 파일 삭제·이동, 새 ingest/revision commit, raw XML public API,
native metadata defaults, 보호 해제, reader/ID/validator 완화는 없다. 원래 public
review.comment_delete 계약은 P11 그대로이고, 이번 내부 출력은 지원 승인과 구분한다.

## 실행한 검증

- Rust277 PASS /0 FAIL /0 ignored: package119 +product158.
  package는 원래 lib42/ID8/patch6/text_flow12/review15/assembly_review3/metadata8/
  memo catalog6/style4/content patch4/body output5와 새 deletion6이다.
  product는 원래 comment_operation8/stored_comment_provider16 및 stored provider134다.
  새 deletion8(package6/stored2)은277에 포함되며 별도로 합산하지 않는다.
- 새 Python8 PASS: live inheritance1, verifier rejection3, mocked current manifest4.
  mock 결과를 실제 native/raw byte 검증으로 주장하지 않는다. 실제 inheritance 및 최종
  current manifest는 별도 CLI로 전체 raw bytes를 검사한다.
- package/lib/new deletion test와 product/lib/stored provider strict clippy PASS.
  신규 Rust4개의 format check, git diff --check PASS. 원래 파일 전체 formatter sweep은 없다.
- 원래 current-source conformance의15 하위 검사 PASS. green0/P09 OPEN 유지.
  원래 기본 conformance는 FAIL:matrix_drift이며 수정·필터·승격하지 않았다.
- 저장소 회귀134는 같은 실제 실행 handle로 끝까지 확인했다(246.71초). timeout을
  terminal로 취급하거나 중복 실행하지 않았다. 전체 과거 qualification 재실행은 아니다.

## 실패와 수정

초기 새 fixture의 ctrl unknown attribute 때문에 원래 field stack이 mismatch로0 PASS/6 FAIL했다.
이를 fieldBegin으로 옮긴 예제도 원래 reader가 unsupported shape로0 PASS/6 FAIL했다.
unknown attribute를 원래 지원되는 subList에 두었다. 원래 검사는 수정하지 않았다.

다음 run은5 PASS/1 FAIL: nested hidden review를 positive source처럼 만들었으나 원래
importer가 text_flow_invalid_field로 거부했다. 새 test를 원래 정확한 typed error를 확인하는
negative로 수정했다. nested reader 금지를 해제하거나 deletion 방어 guard를 제거하지 않았다.

초기 strict lint는 새 함수172/100, 두 번째111/100을 지적했다. readback/paired target/
nested guard를 역할별로 분리했다. 세 번째 유사 변수명 지적은 이름만 수정했다. allow/skip은 없다.
각 실패 당시 관련 파일 전체와 run 식별을 initial-failures 및 whole archives에 보존했다.
package/product의 lint 실패 뒤 full regression은 실행되지 않았으며 NOT_RUN으로 기록한다.

## 보존과 남은 경계

P09-97 whole checkpoint15,167 bytes/50bffa80aaa68b112d325ba60087161a484377fce59b522e2fc9c5c5e798cd96,
P95~P97 declared raw pins1,269개, 원래 source828(825 exact/부모3 whole preimage)을 확인했다.
부모 module 추가의 전체 inverse도 exact다. 이전 실행 파일85개는 보존했다. 이번 수정 빌드가
새 실패 binary를 대체했으므로 모든 실패 binary 보존이나 재실행을 주장하지 않는다.

메모 삭제 출력은 기존 style/body 출력과 함께 연결됐지만 전체 typed native state/원래compiler,
author/time/상태/좌표/보호, insertion/show/resolve, 새 rich Flow, trusted issuer/durable/atomic
execution/publication, 나머지 field/Date/external 의미와 P84 SQL 진단은 남는다.
이 최소6개 큰 잔여 묶음 중 하나 전체를 완료했다고 차감하지 않는다. native34는 별도 NOT_RUN이다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; green0. full_comment_product_acceptance=false,
full_typed_comment_compiler_route_connected=false, P11_capability_qualified=false,
product_complete=false, P10_new_implementation=false, goal_status=active.

한글/COM/UI/접근허용/실제SQL/운영·trust DB/설치·설정/commit/push/원본 삭제·이동은 하지 않았다.
root PLANS.md는 삭제 상태다. 자세한 범위는 P09-98_REVIEW_DELETE_POLICY.md,
현재 원장은 evidence/p09-98-review-delete.*.v1.json이다.
