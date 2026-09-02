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
| P03 | `in_progress_current_pc_local` | P03-01~05 PASS, P03-06 ID/reference index 시작 |
| P04~P20 | `blocked_by_dag` | 선행 phase Gate 대기; P20은 post-GA |

P00 상세 이력과 증거는 `implementation/p00/P00_GATE_REPORT.md` 및 `implementation/p00/evidence/p00-gate-audit.20260901.v10.json`이 authoritative다.

## Active Task

| ID | 단계 | 상태 | 검증 |
|---|---|---|---|
| P-0026 | P03-06 ID/reference index | `in_progress` | part-scoped typed ID/reference index, duplicate/dangling/wrong-type detection |

### P03-06 Acceptance

- `TokenStable` XML part만 대상으로 part-scoped ID namespace와 cross-part reference를 deterministic `IdIndex`로 만든다. `Opaque`, `Rejected` 또는 근거 없는 XML은 해석하지 않는다.
- 지원하는 namespace/QName별 declaration/reference 규칙과 기대 target type을 versioned profile로 고정하고 unknown attribute를 ID/reference로 추측하지 않는다.
- declaration과 reference에 canonical part path, element/token index, checked source span, ID kind/expected target kind를 기록하되 raw XML/value는 public 또는 진단에 노출하지 않는다.
- duplicate declaration, dangling reference, wrong-type target과 malformed/oversized ID를 stable non-sensitive code로 검출하고 partial-valid index나 자동 재번호화로 downgrade하지 않는다.
- cross-part target 문법은 portable package path로 정규화하고 traversal, external scheme, missing/non-token-stable target을 fail closed로 처리한다.
- ID·reference 개수와 value length에 finite checked limits를 적용하고 reserve/allocation failure를 명시적으로 처리한다.
- namespace prefix 변형, part order 변형, same-ID-in-different-part, duplicate, dangling, wrong-type, traversal/external, unknown attribute negative fixture를 Windows/Linux에서 검증한다.
- P03-05 preservation map `5/5`, P03-04 preserving XML `7/7`, P03-03 safe XML `5/5`, P03-02 PackageGraph `8/8`, P03-01 ZIP `8/8` regression을 유지하고 versioned migration/policy를 남긴다.

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

## Next

P03-06 ID/reference index는 `max`다. P03-07 preserving patch engine도 시작 시 `max`로 유지한다.
