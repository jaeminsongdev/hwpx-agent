# P09-121 — 원본 기반 Changed 수식 후보 및 자원 제한 회귀

## 범위와 상태

전체 stored228 회귀 b는 자원 안전장치로 중단되었다. 전체 PASS 및 P121 checkpoint 수용은 아직 하지 않는다.
이 문서는 이번 단계 기록이며 P09 Gate 또는 제품 완료 증거가 아니다.
P120 원본36/소스/증거/실행 파일, 사용자 변경, HEAD, PLANS 삭제 상태를 보존한다.
P120 corpus parent 전체를 별도 보존한 뒤 새 child module declaration 하나만 추가했다.
Production 구현/Cargo/SQL/기존 테스트 및 보호 검사는 수정하지 않는다.

## 발견과 수정

초기 build/lint는 통과했으나 targeted3 실행은 0PASS/3FAILED/225filtered였다.
안전한 단일 사례 diagnostic은 새 changed.rs line20의 Changed 조건에서 실패했다.
첫 숫자 셀은 수식 결과 셀이 아니었지만 모든 수식의 의존 입력은 아니었다.
원본 수식16은 SUM4/AVG6/PRODUCT6 형태다. 원문 수식/숫자/XML/비밀 값은 출력하지 않는다.
초기 새 Rust3, source freeze14 원장 및 당시 실행 파일 전체를 initial-targeted-failure에 보존했다.
초기 targeted/diagnostic FAIL을 이후 수정된 소스의 PASS로 대체하거나 지우지 않는다.

numeric derivative는 original importer/semantics/evaluator의 원래 AST·table identity·source binding
anchor가 가리키는 실제 참조 숫자 셀을 선택한다. 그 셀의 text content만 RAM에서 +101한다.
추가된 independent comparator는 전체 expanded part inventory/다른 part의 bytes/section의 한 leaf
치환으로 전체 section을 정확히 재구성한다. 원본 AST/형식/속성/보호 정보는 바꾸지 않는다.
실제 Changed 조건을 그대로 요구하며 사례를 빼거나 NoChange를 Changed로 승격하지 않는다.

## 실제 확인한 결과

수정 optimized build b PASS 및 strict clippy -D warnings b PASS.
targeted b: 3PASS/0failed/0ignored/225filtered/239.27초(자원 wrapper239.35초).
원본 기반 Changed16 및 각각의 fresh current NoChange16 후보를 signed consumer에 전수 통과시켰다.
독립 outside-result-leaf comparator의 populated branch16, valid allow 서명에도 protected32 거부,
candidate의 numeric input을 추가 변경한 counterexample16 거부를 확인했다.
실제 Ed25519/AEAD/ArtifactService/원래 importer/evaluator/lowerer/compiler/product callback 경로다.
issuer/key/root/clock/metadata 저장소는 synthetic RAM fixture이며 production trust/실제 SQL이 아니다.
candidate는 RAM에만 존재하며 head/Result publication을 하지 않는다.
기존 calculator는 공유하므로 independent math/native oracle 검증이 아니다.

## CPU/RAM 보호 및 근거

test worker1, affinity2 logical CPU, BelowNormal; cargo jobs1/codegen-units1/opt-level1.
debug assertions 및 overflow checks는 true로 유지한다. process-local 환경만 설정한다.
5초 샘플에서 system CPU85% 이상3연속/가용 RAM4096MiB 미만/test RAM2048MiB 초과/기간 초과면
이번 실행 소유 process tree만 중단한다. baseline 압박은 실행을 미룬다.
affinity는 엄밀한 CPU 비율 quota가 아니며 다른 앱의 자원 상태는 변경하지 않는다.
targeted b: system CPU 순간 max100% 관측, 가용 RAM min15116MiB/test RAM max20.66MiB.
연속 CPU 중단 조건에는 해당하지 않았으며 실제 terminal exit0을 확인했다.
빌드 RAM 샘플은 cargo root 측정이며 모든 rustc child의 합계로 해석하지 않는다.
raw stdout/stderr는 RAM에서 폐기하며 closed location/type/digest/count/flags만 저장한다.
자원 parser/privacy14 검사 및 whole P120 preservation audit PASS.
실제 targeted b runtime을 기반으로 receipt negative guards12개도 PASS다. ignore/Gate/product/
source·executable identity/동일 Changed bytes/중복 index/문자열 bool/보호 누락/RAM/worker 조건을
변조하면 거부한다. 전체228 PASS를 주장하는 검사가 아니며 --current 수용은 아직 하지 않는다.

원장 및 runtime receipts:

- `implementation/p09/evidence/p09-121-signed-changed-original.source-regression.v1.json`
- `target/p09-121-resource-optimized/p121-build-resources-20261005-a.json` / `-b.json`
- `target/p09-121-resource-optimized/p121-lint-resources-20261005-a.json` / `-b.json`
- `target/p09-121-resource-optimized/p121-targeted-resources-20261005-a.json` / `-b.json`
- `target/p09-121-resource-optimized/p121-diagnostic-resources-20261005-a.json`
- `target/p09-121-resource-optimized/p121-full-resources-20261005-b.json` (RAM 부족 중단, NOT_ACCEPTED)

전체 b는153.72초에 system CPU100%/가용 RAM2797MiB/test RAM18.88MiB 샘플에서
STOP_LOW_AVAILABLE_RAM으로 소유 테스트만 종료했다. summary 없음/0실패 관측을 전체 PASS로
바꾸지 않는다. source freeze14 exact/잔여 test0/Hwp0을 확인했고 당시 system CPU89%에서
재실행하지 않았다. 이후 CPU6%/가용 RAM16787.1MiB로 회복된 것을 확인했다.
이 관측만으로 외부 앱 또는 테스트가 시스템 압박의 원인이라고 단정하지 않는다.
2차 회복 확인은 CPU14%/가용 RAM16929MiB/test0이었다. 기존 b를 그대로 보존하고
새 c runtime은 source14/동일 수정 binary/감시 간격2초를 지정했지만 실행 직전 CPU100%로
DEFERRED_BASELINE_RESOURCE_PRESSURE_NOT_STARTED가 되었다. 실제 test process를 시작하지 않았다.
기존 CPU85%3연속/RAM4GiB/test2GiB/기간1800초 보호를 유지했고 전체 PASS로 채택하지 않는다.
추가 full retry는 수행하지 않는다. source/증거 정리·가벼운 검사만 진행한다.
현재 상태는 별도 `p09-121-signed-changed-original.partial-progress.v1.json`으로 고정한다.
이전 declared source1095 중 unrelated1094 및 전체 부모 inverse1을 보존하고,
current delta15/whole archives5/executables2/runtime receipts9를 전수 대조한다.
declared current source1109, inherited raw2309 및 이전 executable504를 보존한다.
이 수는 전체 repo의 파일 개수 또는 전부 재실행한 executable 수가 아니다.
source-regression 상태는 IN_PROGRESS_NOT_accepted로 유지한다.

## 유지하는 경계

한글/Hwp/COM/UI/접근허용 창/운영·trust DB/SQL/설정·설치/stage·commit·push/삭제·이동 없음.
P09/A12/A13 OPEN, product false/P10 새 구현 없음/native34 NOT_RUN 또는 재수용 필요.
P26 failed_semantic_non_green, P62/P84 SQL UNRESOLVED를 그대로 유지한다.
최소6 coarse groups/closed0, 최소30 세부 조건은 비완전 목록이며 이번 수를 차감하지 않는다.
production issuer/config/key custody/trust registry, atomic execution/idempotency/publication/transport,
whole import/metadata/coords/comment/rich compiler/field-Date-external 의미 및 native 검증은 미완료다.
사용자는 목표·구현 재개를 요청했으나 목표 도구에서 실제 조회한 등록 상태는 blocked다.
구현 작업은 재개했고 도구로 goal status를 active로 전환할 수 없으므로 완료/일시정지로 바꾸지 않는다.
