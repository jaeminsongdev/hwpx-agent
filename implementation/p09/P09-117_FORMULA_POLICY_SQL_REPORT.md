# P09-117 — 별도 수식 정책 SQL 저장소 소스와 P116 제품 소비자 연결

## 구현

별도 SQL21 formula history/revocation/register/read/revoke 및 exact schema21 artifact/revision connectors를 추가했다.
원래 schema1~20 SQL 원문, form policy namespace와 exact17/19/20 connectors는 수정하지 않았다.
revision admission은 원래 form security 검사를 whole-equivalent로 유지하고 formula security를 추가한다.
원래 subject-fixed/scoped transaction/lease/revision service를 재사용한다.
formula current read → typed scope/head/identity/row binding → PostgresFormulaPolicyProvider → P116 strict
actual source/whole field targets/artifact ACL/AEAD/latest policy 소비 경로를 연결했다.
typed server register source는 source/head/generation CAS와 same transaction whole row readback을 유지한다.
DB metadata에 plaintext policy allow값을 넣지 않는다. product source-bound registration/issuer는 다음 경계다.

## 현재 검증

첫3 libs compile0443b8/session4287 →0a8f5b/exit0(30.51초).
review에서 artifact connector에 남은 form-specific API 이름과 새 SQL21의 old form media를 발견했다.
기존 서비스 guard를 바꾸지 않고 새 source의 이름/media만 formula-specific으로 수정했으며 whole initial sources5를 보존했다.
첫 lint241815/session47445 →26b523/exit1은 새 doc의 NOT_RUN backticks 지적이었다.
새 doc만 수정했고 failure source를 보존했다. 최종 strict lint2be139/session37576 →cd94ed/exit0.
SQL/Rust static source contracts13 PASS(bcff52); actual SQL은 실행하지 않았다.
new Rust4 format/diff check PASS(daf462).
원래 P116 audit를 exact preimage view에서 실행해 inherited raw2162/old executable459를 확인했다(8c91b6).

확대 unit-test lint는 bcb90c/exit1에서 새 tests module 뒤에 production items가 있는 배치를 지적했다.
whole source와 이전6 test executables를 보존하고 새 unit-test module만 마지막으로 옮겼다.
same expanded artifact/revision --tests strict lint26b927/exit0 PASS, 새 lint suppression은 없다.
그 전 runtime47611f/session90256 →c728d8/exit0의276 PASS는 중간 결과로 보존하며 최종 수에 더하지 않는다.

최종 source Rust/SQL9개는 f7f44b의 whole bytes/SHA로 고정했다.
최종 runtime dd6d1d/session59167 →ae6acc/exit0은 artifact lib25 + CLI lib6 + product10 + stored197 + form18
및 revision lib20 =276 PASS/failed0/ignored0/filtered0다. 새 revision tests4개는20에 포함한다.
stored372.94초, product12.76초, form12.15초이며 performance acceptance 수치가 아니다.
이번에 hwpx-package suites136/전체 workspace/이전 native·SQL qualification을 재실행한 주장은 하지 않는다.
final test executables6 + 실행하지 않은 CLI copies2 + 보존된 이전 PASS diagnostic6 =current executable14다.
모든14가 현재 scope PASS인 것은 아니다. 실제 SQL admission/CAS/권한/등록/조회/철회 또는 P09 PASS는 아니다.
current-source conformance15 PASS/green0(2fc57b), original default matrix_drift FAIL(ef37a6)은 유지한다.

## 남은 경계

새 SQL21 source는 작성만 했고 어떤 DB에도 적용하지 않았다. 소스 검사/컴파일은 SQL 실행 증거가 아니다.
실제 원본에 결합된 product policy generation/registration, trusted issuer/signature와 운영 trust config,
actual SQL/migration/security/role/fencing/CAS/revocation 동시성 및 P84 간헐 원인·회귀가 남는다.
whole import/metadata/coordinates/comments/rich compiler/field-Date-external-document 의미,
atomic execution/idempotency/publication/transport/native product acceptance도 미완료다.
최소6 coarse groups 유지/closed0, 대화의 최소30 분해 조건에서 임의로 차감하지 않는다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, no P10/product false/full goal active다.
한글/COM/UI/접근허용/actual SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않았다.
HEAD/P00~P08/사용자 dirty/private/original SQL/native/failed evidence와 PLANS 삭제 상태를 보존했다.
