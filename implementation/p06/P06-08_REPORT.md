# P06-08 Table Inspect/Select Completion Report

- Generated: 2026-09-08
- Exact implementation commit: `293053e2c756d145fea6caf899dd636a6978757b`
- Audit mode: `STRICT`; reasoning recommendation: `max`
- Overall state: `pass_scoped_current_pc_local_pure_ir`
- Next task: `P06-09 Direct/automation differential`

P06-08은 하나의 검증된 `DocumentGraph` revision에서 모든 top-level 및 nested table을
재귀적으로 색인하고, revision·graph·구조 경로·logical ID·fingerprint에 결합된 stable
table/cell selector와 metadata-only snapshot을 구현했다. 병합 span의 covered coordinate는
요청 좌표를 보존하면서 동일한 canonical master cell로 해석된다. 이 작업은 순수 IR
component이며 HWPX selector adapter, 한글 cursor/COM, save/reopen/render 또는 다른 PC/버전을
증명하지 않는다.

## Completion criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| Stable table selector | `pass` | logical table ID, exact typed structural path, complete table fingerprint를 모두 일치시켜 해석 | HWPX/native object 대응은 미검증 |
| Stable cell selector | `pass` | requested coordinate, canonical master-cell ID와 fingerprint를 결합하고 stale drift를 typed error로 거부 | 한글 cursor 이동은 미검증 |
| Merged-cell selection | `pass` | covered coordinate가 동일 master로 해석되며 요청 좌표는 결과에 그대로 보존 | native merged-cell selection은 미검증 |
| Nested-table inspection | `pass` | cell/drawing flow와 note root를 재귀 색인하고 direct child table만 별도 열거 | arbitrary HWPX nesting corpus는 미검증 |
| Metadata-only snapshot | `pass` | canonical order의 ID/path/span/digest만 직렬화하며 cell body는 출력·Debug에서 제외 | private data side-channel 전체 평가는 후속 security Gate |
| Finite deterministic execution | `pass` | table/cell/depth/path/output hard limits와 streaming SHA-256 적용 | production workload benchmark는 미실행 |
| Negative and regression tests | `pass` | Rust 11/11, contract/tamper 4/4, primary P06 Python 74/74 | ignored runtime evidence가 없는 clean checkout의 전체 P06 suite는 미통과 |

## Contract and implementation

- Contract: `hwpx-agent.table-inspection/v1`; private record:
  `protocol/private/p06-table-inspection-v1.json`.
- Migration: `protocol/migrations/p06-table-inspection-v0-to-v1.md`.
- Public implementation: `crates/domain-ir/src/table_inspector.rs`, re-exported by
  `crates/domain-ir/src/lib.rs`.
- `TableInspectionSnapshot`은 `RevisionId`와 canonical `DocumentGraph` SHA-256에 결합된다.
  selector 해석은 revision/graph mismatch, missing ID, path/fingerprint drift, invalid grid 또는
  out-of-range coordinate를 구분된 stable public error code로 fail closed 처리한다.
- Snapshot은 stable table-ID 및 canonical master-cell order로 생성된다. Cell body, equation,
  private properties는 원문을 반환하지 않고 fingerprint에만 반영한다.
- 기본 제한은 table 100,000개, master cell 1,000,000개, path step 64개, nesting 64단계,
  metadata 32 MiB이며 hard ceiling도 유한하다. Fingerprint는 전체 JSON buffer를 만들지 않고
  bounded streaming SHA-256으로 계산한다.

## Validation evidence

- Exact implementation commit의 primary workspace에서 `cargo fmt --all -- --check`,
  `cargo test --locked -p domain-ir --all-targets`, 그리고
  `cargo clippy --locked -p domain-ir --all-targets -- -D warnings`가 통과했다. P06-08 Rust
  boundary tests는 11/11이다.
- Primary P06 Python suite는 74/74, P06-08 contract validator와 source-lock 검증은 PASS,
  tamper/negative tests는 4/4다. Contract는 source lock 4개와 implementation file 4개를
  정확히 결합한다.
- Primary FULL 실행에서 linux-core 61.404 s, windows-worker 65.813 s, widget 7.293 s가
  PASS했고 widget은 144/144였다. Docs lane은 19.330 s에 기존 P14 v1 validator가 현재
  `crates/artifact-service/Cargo.toml`을 다시 읽어 historical source lock과 비교하는
  forward-stability 결함으로 FAIL했다. P06-08 회귀가 아니며 FULL 5/5 PASS로 계산하지 않는다.
- 별도 security lane은 22.337 s에 PASS했다. Run `dc97188c938543a2af4bf3047475a9b3`은
  failed checks와 forbidden licenses 0, 1,057 components를 기록했다. Report SHA-256은
  `35cd43401c894af21e86ab6f875a0342ffd59bf439afd1bf9d22f95611fa59fa`, SBOM SHA-256은
  `771c95d9bac216fd913b38c51dbd05f7e0a07d14e63d9dc7d943d457143b3440`이다.
- 동일 exact commit의 disposable clean worktree에서 linux-core가 80.665 s에 PASS했다.
  Windows worker는 추적되지 않는 current-host baseline
  `implementation/p00/evidence/current-host-baseline.20260901.json`이 clean checkout에 없어
  runtime-probe 단계에서 중단됐으며 제품 실패나 PASS로 재분류하지 않는다.
- Clean worktree에서 P06-08 contract/tamper tests 4/4, contract validator PASS, Rust
  `table_inspector` 11/11을 독립 재현했다. 전체 P06 Python suite는 ignored current-PC
  source/fixture/evidence가 없는 상태라 8 failures/25 errors였고 clean FULL 또는 전체 P06
  PASS로 주장하지 않는다. Tracked 변경이 없음을 확인한 뒤 exact disposable worktree만
  제거했으며 main worktree 하나만 남겼다.

## Strict review and remediation

- Change risk: `high`; selector identity가 후속 read/edit plan과 conformance evidence의 기반이다.
- Verdict: `approve_scoped_current_pc_local_pure_ir`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- 자체검토에서 cell resolve가 불필요하게 전체 table summary를 할당하던 경로를 제거했다.
- Fingerprint 계산의 temporary JSON allocation을 bounded streaming SHA-256으로 교체했다.
- Drawing-contained nested table과 note-root table path 회귀를 추가해 재귀 색인 범위를
  명시적으로 고정했다.
- 검증 기준은 약화하지 않았다. Historical P14 hash를 현재 값으로 덮어쓰지 않았고,
  forward-stability 수리는 immutable commit blob 기준으로 final Gate 전에 별도 수행한다.

## Preserved boundaries

- P06-07 corrected target v2의 licensed Hangul 2020 boundary-page/repeated-header/caption/PDF
  renderer oracle는 계속 `NOT_RUN`이다.
- P06-08은 HWPX adapter, 한글 2020 cursor/readback/render, automation binding, 임의 사용자 문서,
  다른 PC 또는 한글 2022/2024를 검증하지 않았다.
- P06-09 required 61-capability matrix, P06 phase, production과 전체 제품은 완료되지 않았다.
- 사용자 원본 설계 ZIP과 기존 HWPX source는 수정·이동·삭제하지 않았다.

## Task decision and next exact task

P06-08은 scoped pure-IR inspect/select component에 한해 완료다. 다음 exact task는
`P06-09 Direct/automation differential`이며 권장 추론 수준은 `max`다. 61개 table capability를
current-PC Hangul 2020 target binding, 실제 구현·검증 증거와 대조해 required matrix를
fail-closed로 생성한다. P06-07의 renderer evidence가 비어 있는 행은 green으로 승격하지 않는다.
