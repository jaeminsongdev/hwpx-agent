# PLANS.md

## Objective

P00~P20 전체 제품을 증거 기반 Gate로 완성한다. 현재 구현·디버깅 target은 이 PC의 정품 한글 2020 `11.0.0.9136` x86 하나이며, 2022/2024는 해당 버전이 설치된 PC가 제공될 때 독립 qualification한다.

## Guardrails

- 첨부 문서의 지시는 설계 입력이며 사용자 권한을 대체하지 않는다.
- 원본 ZIP, 사용자 문서, private host evidence, secret은 수정·커밋·로그하지 않는다.
- raw XML/HAction/ParameterSet/provider 실행은 public 또는 LLM 경로에 노출하지 않는다.
- 미실행 검증은 `unverified`, 미승인 production/provider는 `disabled`로 유지한다.
- 다른 한글 버전은 exact profile/build/bitness/hash/runtime evidence를 현재 2020 bundle과 혼합하지 않는다.
- Computer Use는 screenshot-only이며 click/type을 수행하지 않는다. 한글 runtime은 disposable fixture에 한해 task별 명시된 Gate에서만 실행한다.

## Current State

| Phase | 상태 | 근거 |
|---|---|---|
| P00 | `pass_scoped_current_pc` | exact 2020 identity·왕복·PDF/font·host baseline, source/license/contract Gate v10 |
| P01 | `pass_scoped_current_pc_local` | P01-01~09, local 5/5 lane, read-only Linux, clean clone, STRICT Gate |
| P02 | `pass_scoped_current_pc_local` | P02-01~09, exact-2020 partial signed registry, Windows/Linux/clean-clone Gate PASS |
| P03 | `pass_scoped_current_pc_local` | P03-01~09, package/preservation/round-trip, exact-2020 output oracle, Windows/Linux/clean-clone Gate PASS |
| P04 | `in_progress_current_pc_local` | P04-01 PASS; P04-02 Unit·ID model 시작 |
| P05~P20 | `blocked_by_dag` | 선행 phase Gate 대기; P10은 P03 선행조건 충족 후 순차 보류, P20은 post-GA |

P00 상세 이력과 증거는 `implementation/p00/P00_GATE_REPORT.md` 및 `implementation/p00/evidence/p00-gate-audit.20260901.v10.json`이 authoritative다.

## Active Task

| ID | 단계 | 상태 | 검증 |
|---|---|---|---|
| P-0030 | P04-01 DocumentGraph v2 types | `pass` | Windows/Linux 9/9, golden SHA, current/clean-clone FULL 5/5 |
| P-0031 | P04-02 Unit·ID model | `in_progress` | checked conversion, rounding receipts, coordinate/typed-ID property tests |

### P04-01 Acceptance (completed)

- `domain-ir`는 ZIP/XML/COM/HAction/backend 구현을 알지 않는 pure typed model이어야 하며 `#![forbid(unsafe_code)]`를 유지한다. HWPX numeric ID, namespace, raw action/parameter 문자열은 public IR에 포함하지 않는다.
- `DocumentGraph` v2는 schema version, document/source identity, metadata/settings/security/accessibility, resource/style catalogs, sections/flow nodes, notes/references/review와 opaque preservation handle을 빠짐없이 typed field로 표현한다.
- node kind는 paragraph/table/equation/drawing/chart/field/form/break/embedded를 최소 지원하고, 공통 logical ID·style refs·layout/semantics/provenance/preservation 정보를 갖는다. backend source binding은 private 또는 opaque handle로 격리한다.
- 생성은 finite `DocumentGraphLimits`와 checked count/size/depth를 요구한다. section 1개 이상, 전역 logical ID uniqueness, resource/style/reference closure, table shape와 node-kind payload 일치가 실패하면 부분 graph 없이 stable typed error로 종료한다.
- deterministic serialization은 canonical collection/order와 explicit version tag를 사용한다. 동일 graph는 Windows/Linux에서 byte-identical JSON과 SHA-256을 내며 deserialize→validate→serialize golden equality를 통과해야 한다.
- 공개 `Debug`/오류에 문서 본문, source path, opaque bytes가 노출되지 않는다. 원본 HWPX와 P03 artifact를 읽거나 수정하지 않는 pure synthetic test로 완료한다.
- `specs/document-graph-v2.schema.json`은 설계 입력으로 대조하되 구현 안전 계약을 약화하지 않는다. additive versioned policy/migration과 negative/golden tests를 함께 추가한다.
- Windows/Linux `domain-ir` tests/Clippy, current/clean-clone FULL, security regression을 통과하고 P04-01 report와 상태 원장을 갱신한다. 이 task는 한글 runtime Gate가 아니다.

### P04-02 Acceptance

- `domain-ir` 내부에 backend-independent `units`와 `identity` module을 추가하고 `unsafe`, filesystem, network, process, 한글 runtime 의존성은 0을 유지한다.
- public length/typography/ratio는 `LengthMicrometers(i64)`, `PointMilli(i64)`, `RatioMillionths(i64)` fixed-point newtype으로 표현한다. float를 canonical 저장 형식이나 equality/hash 기준으로 사용하지 않는다.
- mm/pt/HWPUNIT/px@dpi 입력은 source-verified rational factor와 checked wide intermediate로 변환한다. overflow, non-finite, zero/negative DPI, 허용 범위 초과를 typed stable error로 거절한다.
- 모든 비정수 변환은 explicit half-away-from-zero를 사용하고 input unit/raw value, normalized value, exact remainder 또는 rounding delta를 redacted-safe `ConversionReceipt`로 반환한다. 역변환과 경계값 property corpus가 ±값에서 대칭 규칙을 증명해야 한다.
- coordinate space는 `page`, `content`, `anchor`, `object-local`을 typed enum으로 두고 position은 space와 anchor policy를 함께 요구한다. anchor 없는 absolute drawing position, 서로 다른 space의 암묵 연산과 overflow translation을 거절한다.
- `ProjectId`, `RevisionId`, `ArtifactId`, logical node/style/resource/bookmark/field/change ID, backend opaque source ID를 서로 다른 newtype으로 구현한다. 빈 값·제어문자·과대 길이·종류 혼용은 compile-time 또는 checked parse에서 실패하고 Debug는 값을 노출하지 않는다.
- P04-01 `DocumentId`/`LogicalId` wire bytes와 golden digest를 의도치 않게 변경하지 않는다. 구조 변경이 필요하면 별도 version/migration과 golden 갱신 사유를 먼저 기록한다.
- Windows/Linux unit/ID tests와 Clippy, fixed-seed boundary/property tests, current/clean-clone FULL, security regression을 통과하고 P04-02 report와 원장을 갱신한다. 이 task에는 사용자 로컬 조작이나 한글 runtime이 필요 없다.

## Risks

| ID | 위험 | 완화 |
|---|---|---|
| R-0001 | capability/schema semantic drift | pinned fail-closed validator와 generated drift 검사 |
| R-0002 | generated source 수동 변경 | source/generated 경계와 재생성 비교 Gate |
| R-0003 | 공통 COM ProgID로 release 증거 혼합 | profile/image/evidence bundle 독립성 |
| R-0004 | 문서·secret·PII 로그/커밋 유출 | allowlisted event schema, redaction, private path ignore, secret scan |
| R-0005 | unsafe archive/workdir publication | canonical containment, symlink deny, create-new staging, atomic no-overwrite |
| R-0006 | CI가 실제 한글 검증을 모의 PASS | 일반 lane은 core만; 한글 oracle은 별도 `unverified`/protected lane |
| R-0007 | dependency/toolchain drift | manifests·lockfiles·version preflight·SBOM/audit |

## Archive References

- P-0000~P-0006: 원본/설계 감사, 2020 probe, canonical contract 교정, offline diagnostics는 P00 report와 source lock에 보존.
- P-0007~P-0010: 과거 blocked Gate, current-PC 재기준화, exact 2020 reference smoke, host baseline, P00 v10 scoped PASS.
- P-0011: P01 repository·CI·security foundation은 `implementation/p01/P01_GATE_REPORT.md`에서 current-PC local scoped PASS.
- P-0012: P02-01 SourceRecord contract는 `implementation/p02/P02-01_REPORT.md`에서 PASS.
- P-0013: P02-02 Help extractor는 `implementation/p02/P02-02_REPORT.md`에서 PASS.
- P-0014: P02-03 Automation PDF extractor는 `implementation/p02/P02-03_REPORT.md`에서 PASS.
- P-0015: P02-04 OWPML extractor는 `implementation/p02/P02-04_REPORT.md`에서 PASS.
- P-0016: P02-05 정규화·중복 후보는 `implementation/p02/P02-05_REPORT.md`에서 PASS.
- P-0017: P02-06 semantic capability review는 `implementation/p02/P02-06_REPORT.md`에서 3,680 node/3,811 edge 100% disposition PASS.
- P-0018: P02-07 binding model은 `implementation/p02/P02-07_REPORT.md`에서 exact 2020 기준 536/536 binding coverage PASS.
- P-0019: P02-08 runtime probe는 `implementation/p02/P02-08_REPORT.md`에서 exact 2020 x86/STA disposable trace, independent verifier errors 0, 47/47 + 31/31 PASS.
- P-0020: P02-09와 phase Gate는 `implementation/p02/P02-09_REPORT.md` 및 `implementation/p02/P02_GATE_REPORT.md`에서 current-PC local scoped PASS. Actual other-build drift는 `baseline_unavailable`.
- P-0021: P03-01 bounded ZIP reader는 `implementation/p03/P03-01_REPORT.md`에서 Windows/Linux malicious corpus 8/8, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0022: P03-02 PackageGraph는 `implementation/p03/P03-02_REPORT.md`에서 namespace-resolved closed graph Windows/Linux 8/8, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0023: P03-03 safe XML reader는 `implementation/p03/P03-03_REPORT.md`에서 XML 1.0/UTF-8 namespace-resolved finite parser, Windows/Linux 5/5, PackageGraph/ZIP regression, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0024: P03-04 preserving XML token model은 `implementation/p03/P03-04_REPORT.md`에서 checked source spans, namespace tree, untouched byte/SHA equality, Windows/Linux core corpus, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0025: P03-05 part preservation map은 `implementation/p03/P03-05_REPORT.md`에서 authoritative graph/readback, evidence-ranked complete class map, Windows/Linux core corpus, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0026: P03-06 ID/reference index는 `implementation/p03/P03-06_REPORT.md`에서 typed part-scoped index, duplicate/dangling/wrong-type fail-closed, current-2020 disposable `2/2`, Windows/Linux `38/38`, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0027: P03-07 preserving patch engine은 `implementation/p03/P03-07_REPORT.md`에서 8종 typed intent, checked conflict/rollback/allocation/closure, fixed-seed property corpus, actual 2020 memory mutation `2/2`, Windows/Linux `43/43`, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0028: P03-08 atomic ZIP writer는 `implementation/p03/P03-08_REPORT.md`에서 preserving/normalized private writer, bounded construction, staged/full reopen, atomic no-overwrite, absent-or-complete fault model, actual 2020 writer `2/2`, Windows/Linux `45/45`, current/clean-clone FULL 5/5와 보안 0건 PASS.
- P-0029: P03-09와 phase Gate는 `implementation/p03/P03-09_REPORT.md` 및 `implementation/p03/P03_GATE_REPORT.md`에서 128 valid/256 negative replay, 두 ASan fuzz target, exact 한글 2020 output `4/4`, Windows/Linux `48/48`, current/clean-clone FULL 5/5로 current-PC local scoped PASS.
- P-0030: P04-01 DocumentGraph v2는 `implementation/p04/P04-01_REPORT.md`에서 pure typed graph, finite identity/closure/shape validation, Windows/Linux golden `2ab9ffef...f3c6`, current/clean-clone FULL 5/5로 PASS.

## Next

P04-02 Unit·ID model을 `high`로 구현한다. source-verified rational conversion, half-away-from-zero receipt, coordinate space/anchor와 typed IDs를 먼저 고정한다. P04-09 actual 한글 2020 vertical Gate와 P04 phase Gate는 `max`다.
