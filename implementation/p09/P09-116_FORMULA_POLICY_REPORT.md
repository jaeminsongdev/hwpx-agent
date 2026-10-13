# P09-116 — 실제 수식 필드 정책 데이터와 원래 제품 API 연결

## 구현

별도 FormulaPolicyRepository와 field-specific Evidence/media/schema를 추가했다.
원래 authenticated sealed Result/package/provenance/form graph binding을 유지하며,
actual whole field meaning graph와 모든 수식의 reference ID/begin/end anchors/typed AST SHA를 대조한다.
current/no-op field도 정책에서 빠질 수 없고 explicit deny면 요청 전체를 거부한다.
form-control 정책을 수식 허용으로 재사용하거나 외부 발급자 검증을 가정하지 않았다.

원래 공통 StoredProductRequest에 prepare_formula_with_policy를 연결했다.
policy DATA 검사 뒤 동일한 owned authentic source를 원래 formula factory/math/lowerer/compiler로 보낸다.
changed/no-op candidate 전체를 보존하며 소비 직전에도 정책 최신 상태/철회/권한/원본을 재검사한다.
원래 ungated API는 read-only unqualified preparation이고 actual route denial은 두 API에서 유지된다.
policy allow는 원래 native 보호를 무시하지 못한다. issuer/SQL/atomic lease/execution은 미완료다.

## 발견·수정과 검증 상태

첫 focused integration10개는9 PASS/1 FAIL이었다(bb3364/session40471 →a9dbb1/exit101,160.17초).
실패는 동일 policy bytes를 다른 media/kind로 같은 artifact store에 ingest한 fixture Conflict였다.
독립 실행에서도 원래 ingest Conflict를 재현했다(de5b53/exit101). 원래 dedup guard를 바꾸지 않고
각 descriptor case를 독립 store로 분리했다. 같은 focused1은 PASS(1cc74a/exit0,2.54초).
첫 strict lint는 fixture의 semicolon 한 곳을 지적했다(be9c9e/session80658 →c5104a/exit1).
semicolon 수정과 완전한 declaration-order positional object negatives 추가 뒤 strict lint PASS(7ddc50).
강화된 strict policy focused1 PASS(649400,3.19초). 실패/중간 source 및 실패 executable은 보존한다.
위 focused/failed 실행은 최종 통과 수에 중복 합산하지 않는다.

최종 Rust production/test source9개는 cc7956의 bytes/SHA로 고정했다.
최종 CLI 회귀 b8109d/session79766 →3f9bf8/exit0은 lib6 + original product10 + stored197 + form18 =231 PASS다.
package 회귀9cb221/session31041 →9b9110/exit0은 lib+11 integration suites136 PASS다.
합계367 PASS/failed0/ignored0/filtered0이며 executable+fully-qualified function pairs367개다.
새 policy integration11개는 위367에 포함하며 반복 추가하지 않는다.
stored runtime421.73초, original product14.45초, form12.43초다. 실행 중 production/test source9개는
수정하지 않았고407579의 bytes/SHA가 cc7956 전부와 일치한다. 이 시간은 performance acceptance가 아니다.
current executable19는 final test16 + 실행하지 않은 CLI copy2 + 실패 diagnostic1이며 전부 PASS가 아니다.
--list16개367 unique pairs는 f0a30c/exit0으로 확인했다. 최초 목록 관찰 f9ca71의 잘못된 PowerShell
boolean literal은 오류로 남기고 관찰만 수정했다. test 재시작/원본 변경으로 처리하지 않았다.
위 결과를 전체 P09/native/SQL/issuer/Gate PASS로 확대하지 않는다.
source preservation PASS(1fc88c, 재확인08808f), new Rust5 format/diff whitespace PASS(db20f8).
current-source conformance upstream15 PASS/green0(3e1d1c), original default matrix_drift FAIL(f6bed9)을 유지한다.

새11 tests는 original changed/current whole candidate와 redacted receipts/no publication,
complete positional root/binding/target/begin/end negatives 및 unknown/duplicate/coercion/bounds,
missing/duplicate/extra/source-anchor/AST/whole graph/version binding, wrong form media/role,
current target의 explicit deny, policy order/latest version/revocation/old-cache refusal,
callback 직전 revoke, source+policy ACL/quarantine/AEAD/head와5 provider scope 대체,
protected current/changed 및 invalid second-section 전체 거부, caller policy의 pre-read 거부를 검사했다.

## 원본과 미완료

P115 source1034 중1030 unchanged +4 whole preimages/exact inverses를 확인했다.
수정하지 않은 P115 original checker의 preimage-view 실행으로 inherited raw2114/old executable440을 보존한다.
실제 input36과 기존 fixture/scanner/compiler/ACL/protection/body/user dirty/private 원본은 그대로다.
기존 native/SQL qualification 전체를 재실행한 것은 아니다. PLANS 삭제 상태를 유지한다.

full metadata/coordinates/comment/rich source mapping/HWPX compiler, whole document import/semantics,
CLI/HTTP transport, actual durable integration, trusted field issuer/signed registry/full protection,
atomic CAS/idempotency/publication 및 actual P84 SQL cause/regression은 미완료다.
최소6 coarse groups 유지/closed0. 대화에서 나눈 최소30 완료 조건은 작업 granularity를 설명한 하한이며
전수 확정 잔여 총수/feature coverage 또는 이번 구현 후30→29 차감 근거가 아니다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, product false/no P10/full goal active다.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않았다.
