# P09-115 — 공통 제품 요청의 source-only 수식 재계산 및 정상 no-op

## 실제 구현

원래 form_product_request 모듈에 공통 StoredProductRequest API를 연결했다.
v1 form 요청은 원래 parser/serializer/hash/bindings/preparation을 그대로 사용한다.
v2 operation.kind=recalculate_table_formulas는 원래 authenticated sealed Result만 사용하며,
caller values/AST/IR/map/field selector/artifact/path/policy/approval/form_input을 거부한다.

actual source/ranges/meaning → 원래 evaluator → whole candidate → P114 원래 OperationPlanCompiler를
통해 변경 필드만 Atomic plan으로 준비한다. source/request/plan/candidate는 owned immutable snapshot이며
unsafe self-referential lifetime이나 caller graph는 사용하지 않는다.
source head/project/document/SHA 검사와 fresh ACL/AEAD/head/provider scope/whole source/math/plan/candidate
검사를 전후 수행한다. 새 candidate 소비는 fresh callback만 허용한다.

원래 lowerer의 exact NoChange만 별도 unchanged outcome으로 처리했다.
원본 bytes를 그대로 반환하고 compiled=None이다. 빈 plan/zero-limit 예외를 만들지 않는다.
보호/invalid numeric/empty targets/limits/readback/writer 오류를 no-op으로 바꾸지 않는다.
기존 prepare_results API의 NoChange 오류 동작은 유지하며 새 prepare_results_outcome에만 typed 구분을 추가했다.
unchanged도 native cache verification 또는 실행/저장 권한이 아니고 route는 거부한다.

## 실제 발견·수정한 결함

첫 integration9개에서8 통과/1 실패했다(8f87e1/session70889 →4fdc69/exit1).
internally tagged unit enum이 deny_unknown_fields가 있어도 operation의 추가 values 필드를 무시했다.
case-index11 단일 검사로 재현했다(b6ac11/session48856 →2e98af/exit1).
typed struct로 바꾼 뒤에도 operation 배열을 positional struct로 받아 case-index13이 실패했다
(e085ae/session20648 →de7a76/exit1).

최종 map-only visitor는 정확한 kind 하나만 받고 unknown/duplicate/sequence/coercion을 거부한다.
원래 recursive UniqueJson을 유지하며 테스트 요구조건을 바꾸지 않았다.
같은 strict 검사 최종1 PASS/c991d3/exit0(0.07초), audit read 증가0을 확인했다.
이 focused 검사를 최종 통합 실행 합계에 중복 포함하지 않는다.

새 error에 잘못 부여한 Eq/PartialEq는 원래 source error를 바꾸지 않고 새 타입에서 제거했다
(d540e5/session22170 →b16dcd/exit1).
두 큰 enum layout/doc markup lint102e56은 boxed storage와 문서로 고쳤고 suppression은 없다.
pre-outcome review에서 misplaced no-op route guard와 public Debug 누락을 발견해 callback/route를 분리하고
redacted Debug를 추가했다. 모든 단계의 source와 실패 executable3개를 보존했다.

이미 시작한 CLI 회귀에서 아직 실패하는 배열 허용을 확인해 해당 authored session만 중단했다
(9f1307/session56572 →be541b/exit1). 완료되지 않은 run이나 lib/form 부분 PASS를 최종 합계에 넣지 않는다.
관측 timeout에 따른 재시작이나 한글/외부 native 프로세스 종료가 아니다.

## 현재 소스 검증과 원본 보존

final package lib +11 integration suites136 PASS(1031ac/session92902 →5f9f83/exit0).
package source/fixtures는 실행 중 바꾸지 않았다. package 실행과 겹친 수정은 package가 의존하지 않는
CLI request code에만 있었으며 최종 CLI source는 최종 CLI 실행 전 고정했다.
최종 CLI lib6 + original product request10 + stored provider186 + form operation18 =220 PASS
(6a5397/session66738 →1b79e0/exit0; stored467.01초). package136과 합쳐356 PASS/failed0/ignored0이다.
16개 executable+fully-qualified function pairs356개이며 신규10개는 위 합계에 포함한다.
최종 strict lint는 두 package와 전체 선택 suite를 경고=오류로 검사해 PASS(fea9d7).
새 Rust5개 format/git diff --check PASS(ca1f42).

신규 integration10개는 original whole candidate/Field plan, true current no-op, empty/current 구역 혼합,
strict unknown/duplicate/coercion/limits의 pre-read 거부, wrong source/head identity,
changed/no-op ACL/AEAD/quarantine·5 provider scope 대체, protected/invalid second-section 전체 거부,
canonical retry/key/plan identity/redaction, v1 original candidate 및 kind-specific bindings를 검사한다.
--list16개에서356 executable+fully-qualified function pairs를 확인했다(5752d6/exit0).
이 목록 자체는 실행 PASS가 아니며 feature/fixture/semantic coverage 개수도 아니다.

immutable actual36 inputs는 그대로이며 helper는 원래 P114 fixture를 공유한다.
P114 parent test의 fixture visibility만 명시적으로 열었고 fixture body는 바꾸지 않았다.
P114 source1021 중1017 unchanged + 부모4 whole preimage/정확한 역변환 및
unmodified predecessor audit의 preimage-view 실행으로 inherited raw2054/old executable419를 확인했다
(7c228a/exit0). 현재 source1034/delta17/archive20/predecessor2/current executable21로 기록한다.
current executable21은 final tests16, 실행하지 않은 CLI copies2, 실패 diagnostic3이며 전부 PASS가 아니다.
이전 native qualification/executable 전체를 재실행하지 않았다.

current source conformance validators15 PASS/green0(944f02), original default matrix_drift/exit1(c854c9)은 유지한다.
PLANS 삭제 상태, P00~P08/private/reference locks/사용자 dirty 변경과 모든 failed evidence를 보존한다.

## 미완료와 다음 경계

main.rs는 여전히 create-vs0만 제공한다. 이번 것은 actual authenticated services를 사용하는 product library
API의 원래 모듈 내 dispatcher이지 CLI/HTTP transport 또는 full product execution qualification이 아니다.
full document importer, full field/date/external/document semantics, trusted field policy/issuer/signed registry,
atomic durable execution/CAS/idempotency/publication과 actual native/SQL 검증은 미완료다.
다음은 실제 source에 묶인 field policy/issuer와 full-import/transport 경계를 기존 제품 execution 경로에
연결하는 것이다. caller-owned policy나 partial graph를 full import/권한으로 승격하지 않는다.
P06 table.formula 기존 native PASS를 새 Field-result 계약에 적용하지 않는다.

metadata/coordinates, full comment/rich compiler/source mapping, durable integration,
fields/date/external/document 의미·전체 실행 연결, trusted issuer/protection/atomic publication,
actual P84 SQL 원인·회귀의 최소6 큰 묶음 유지/이번 closed0. 정확한 작업6개를 의미하지 않는다.
P09/A12/A13 OPEN, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED/product false/no P10/full goal active.
한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동은 실행하지 않았다.
