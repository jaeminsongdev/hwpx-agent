# P09-97 기존 댓글·숨은 설명 문단 본문 출력 결과

기존 실제 source review의 선택된 subList 안 문단 전체를 original TextFlowWriter로 생성해
원래 ID/patch/writer/field/body reader로 검증하는 HWPX 출력 경로를 구현했다. 원래 저장된
원본의 fresh 인증 경로에도 연결했다. 이는 댓글 본문 출력에 필요한 문단 교체 분기이며
새 댓글 삽입·작성자·시간·표시·해결·삭제·전체 rich Flow/컴파일러/제품 실행의 완료가 아니다.

## 구현과 검증

- original generic patch에 ReplaceElementContent를 추가했다. 기존 source selector와
  SafeXml/fragment/overlap/ID/preservation 검사를 재사용한다. 자식 수와 전체 fragment
  byte 합을 먼저 제한하고, 기존 wrapper tags/속성/inherited namespace 문맥은 그대로 둔다.
- 기존 ImportedDocumentReviewBodies의 실제 marker를 선택하고 모든 target 문단을 원래
  TextFlowWriter로 생성한다. 원래 paired-field/body importer로 HWPX 출력 전체를 재열고
  요청의 paragraph/run/text/tab/lineBreak 모델 전체를 비교한다. 선택된 content 앞뒤의
  section bytes와 다른 expanded parts는 exact다. unknown wrapper attrs, parameters,
  uninterpreted metaTag, field markers, main body와 다른 review는 그대로다.
- 기존 StoredImportedReviewBodies의 prepare_body/cached callback은 원래 fresh
  ACL/AEAD/quarantine/head/scope/whole-review 검증과 full lowering replay를 사용한다.
  권한 회수·재부여, 암호문 변조, head advance를 검사했다. 결과를 새로 ingest/commit/
  publish하지 않으며 require_current_product_route는 계속 RouteUnqualified다.
- Rust269 named PASS, failed/ignored0: package113 + product156이다. package는 lib42,
  ID8, 원래 patch6, text_flow12, review15, assembly_review3, metadata8, memo catalog6,
  P96 style4, 새 content patch4, 새 body5다. product는 comment8 + stored provider132 +
  stored comment16이다. 새 기능11개(4+5+2)는269 안에 포함하며 재실행을 더하지 않았다.
- Python 감사8 PASS: inherited raw/preimage4 + mock manifest coverage/rebinding/promotion4.
  mock scope checks는 실제 raw byte 감사나 native acceptance로 재집계하지 않는다.
- package/lib/new tests 및 product/lib/stored provider strict clippy PASS. 신규 Rust5개와
  제한된 patch 추가의 format, git diff --check PASS. 기존 component current-source15 PASS,
  green0/P09 OPEN. 기본 conformance는 FAIL:matrix_drift를 다시 확인해 유지했다.

양성 출력은 기존 builder/fixture를 재사용한 synthetic native-format package다. source marker
선택, 완전한 XML range inverse, 여러 target 문단/run, Unicode/entity/tab/lineBreak, 전체 part
count/bytes 및 opaque metadata 지문을 확인했다. 원래 실제 캡처의 zero-review를 native 양성으로
만들지 않았다. historical actual36은 원래 회귀에서 보존·검사했으나 새 native capture가 아니다.
original service AES-GCM/ACL/head 코드는 실행했지만 repositories/actor/scanner/keys는 fixture다.

## 실패와 보존

초기 compile은 새 patch 코드가 없는 self.limits 필드를 참조해 실패했다. 실제 원래
patch_limits로 고쳤다. 첫 새 package3/stored2 검사는 새 탭 예제의 필수 width/leader/type
누락으로 실패했으며 원래 parser를 바꾸지 않고 예제를 수정했다. 새 content test의 private
with_source_bytes 호출 compile 실패는 원래 reader에서 읽은 원문 bytes 비교로 수정했다.
새 content positive의 중복 paragraph ID는 원래 strict ID 검사가 거부했다(3 PASS/1 FAIL).
서로 다른 명시적 ID로 고쳤으며 duplicate guard를 유지했다. 새 opaque negative 예제는 원래
typed reader의 최소 run 요구를 위반해 전체 package run에서 4 PASS/1 FAIL이었다. 실제 typed
run과 opaque child를 함께 가진 예제로 바꿨다. 새 test lint2는 이름/nested if를 수정했고
allow/skip을 넣지 않았다. 각 실패 당시 관련 파일 전체와 실패 식별을 보관했다.

P96 whole checkpoint12,952 bytes/4aebe074bef35ecca8e5a322b308837f15228f48046a2d3381f1ee8966dc0f13와
P95~P96 raw pin1,222개를 현재 bytes 또는 정확한 whole archives로 확인했다. 이전 현재 source815
중811개는 같고 부모4개는 전체 preimage가 일치한다. 추가4블록/module declarations의 전체
inverse도 exact다. 과거 실행 파일71개는 덮어쓰지 않았다. 실패한 이번 새 테스트의 실행 파일은
수정 빌드로 교체됐으므로 모든 실패 binary까지 보관·재실행했다고 주장하지 않는다. 실패 source와
run 결과는 남겼다. 최초 source1551 전체나 모든 역사 qualification의 재실행을 주장하지 않는다.

## 남은 실제 제품 경계

기존 native-format 문단 본문 교체와 P96 스타일 출력은 각각 구현됐지만 full typed native
comment state/원래 compiler 연결, metadata/좌표/보호, 새 table/drawing/opaque Flow 출력,
insertion/show/resolve/delete lowering, 신뢰된 issuer/durable/atomic execution/publication은
미완료다. 나머지 field/Date/external 의미, P84 SQL 원인, 실제 한글 저장·재열기/render/
differential과 P09 Gate도 남는다. 최소6 큰 잔여 묶음 중 하나 전체를 완료했다고 차감하지 않는다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; full native34 NOT_RUN; green0.
full_comment_product_acceptance=false, native_author_time_state_binding=false,
full_typed_comment_compiler_route_connected=false, product_complete=false,
P10_new_implementation=false, goal_status=active. 한글/COM/UI/접근허용/실제 SQL/운영·trust DB/
설치·설정/commit/push/삭제·이동 없음. root PLANS.md는 삭제 상태를 유지했다.

정책: P09-97_REVIEW_BODY_OUTPUT_POLICY.md. 증거: evidence/p09-97-review-body-output.*.v1.json.
읽기 전용 감사: tools/p09/verify_review_body_output_progress.py 및 --current.
