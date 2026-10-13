# P09-99 원래 XML/IR 메모 위치 연결 결과

원래 문서에서 관찰한 MEMO/hiddenComment의 XML 위치를 원래 IR 문단·control ref와 연결했다.
중복 numeric ID를 위치 identity로 쓰지 않고 whole source anchor를 사용한다. 실제 문서의
작성자·시간·상태 또는 한글 cursor/render 좌표를 검증한 것은 아니다.

## 변경

package review/locations.rs는 actual source point/전체 container path와 original paragraph
control ref를 결속하고, direct section item만 original simple CommentAnchor에 투영한다.
nested scope는 None +전체 path로 남긴다. 메모 body p 개수를 section paragraph ordinal에
섞거나 table 위치를 임의로 평탄화하지 않는다. immutable receipt/locations의 whole replay를 제공한다.

product review/locations.rs는 원래 fresh scope/ACL/AEAD/quarantine/head/whole source 검사를
조회·재검증·callback에 연결한다. current product route는 계속 거부한다. 부모3개 변경은 module
선언뿐이며 원래 graph/IR schema/5개 operation compiler/reader/validator/ID/writer를 수정하지 않는다.

## 구현 검사 범위

Rust scope는 package126 +product161 =287 named tests PASS/0 FAIL/0 ignored이며 새 location10(package7/stored3)은
그 안에 포함된다. 원래 package119와 product158을 포함하고 전체 과거 검증 재실행은 아니다.
새 package7은 cross-run pair, duplicate native IDs와 memo-body p 제외, hidden direct/ctrl,
nested table path, stale/metadata-only drift/foreign document, locked captured zero location,
256 sibling 전체 ordered mapping과 replay다. stored3은 direct comparison/no writes,
fresh ciphertext/ACL/head 거부, document/branch/project/subject/tenant5 scope substitution이다.

Python8은 live prior-view/raw/inverse1, view-routing/root-restoration/preimage rejection3,
mock current manifest4다. mock 결과는 native 또는 실제 raw byte 증거가 아니다.
별도 current CLI가 전체 선언 바이트를 읽어 확인한다. strict package/product 검사는
warnings를 허용하지 않으며 새 Rust4개 format와 git diff 검사를 수행한다.

원래 current-source conformance의15 하위 검사는 PASS이며 green0/P09 OPEN이다.
기본 conformance의 FAIL:matrix_drift는 그대로 남아 있다. 세부 실행 terminal과 결과는
source-regression.v1.json 및 final-audit.v1.json이 권위 있는 현재 원장이다.

## 최초 실패와 수정

처음 check 및 새 test compile에서 Sha256::new에 필요한 Digest trait import 누락으로
E0599가 발생했다. check/test가 종료된 뒤 관련 새 package source 전체를 보존하고 필요한
trait import만 추가했다. 새 tests는 당시 compile failure로 NOT_RUN이었다. 기존 검사/원본은
수정하거나 약화하지 않았다. 이후 위치 테스트와 strict 검사를 실행했다.

## 원본 보존과 미완료 경계

P09-98 snapshot 전체를 고정하고 raw pins1,310개 및 원래 source840 중837 exact/부모3 whole
preimage를 검증했다. current 모듈 추가의 전체 inverse가 exact이며, 수정하지 않은 P98 audit도
정확한 prior parent view에서 통과한다. 이전 실행 파일100개는 현재 bytes로 보존한다.
current source852는 파일 수이며 작업 수나 제품 완료율이 아니다.

원본 파일 수정·삭제·이동, 새 ingest/revision commit/publication, 메모 입력·보호 해제·작성자나
시간 defaults, native metadata 증거 승격은 없다. 한글/COM/UI/접근허용/실제SQL/운영·trust DB/
설치·설정/commit/push를 실행하지 않았다. root PLANS.md는 삭제 상태를 유지한다.

native caret/visual 좌표와 author/time/visibility/resolution/state/protection, 전체 native
CommentState/원래 compiler 연결, insertion/show/resolve/rich Flow, trusted issuer/durable/
atomic execution/publication, 나머지 field/Date/external 의미 및 P84 SQL 원인은 남는다.
최소6개 큰 잔여 묶음 중 하나 전체가 닫혔다고 차감하지 않는다. native34는 별도 NOT_RUN이다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; green0; product_complete=false;
full_comment_product_acceptance=false; full_typed_comment_compiler_route_connected=false;
P10_new_implementation=false; goal_status=active.

정책: P09-99_REVIEW_LOCATIONS_POLICY.md. Migration: protocol/migrations/p09-review-locations-v0-to-v1.md.
현재 증거: evidence/p09-99-review-locations.*.v1.json.
