# P06-01 TableGrid Completion Report

- Generated: 2026-09-07
- Final implementation base commit: `6e49b0f6d3937d1026f3a0395e1a58bf405a148c`
- Source qualification and audited FULL commit: `823c35255bd178de167a0f50503788e1ee886000`
- Audit mode: `STRICT`; reasoning recommendation: `high`
- Overall state: `pass_scoped_current_pc_local_pure_ir`
- Next task: `P06-02 Create/insert/delete`

P06-01은 현재 PC의 개인 로컬 개발 범위에서 backend-neutral `TableGrid`와 rectangular span
invariant를 구현하고 검증했다. 이 작업은 순수 논리 모델이며 한글 2020 COM 실행, HWPX 표
XML lift/lower, 사용자 문서, 실제 표 렌더링 또는 다른 PC/버전을 증명하지 않는다.

## Completion criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| Bounded logical grid | `pass` | Nonzero rows/columns, checked slot product, finite rows/columns/slots/master/ID/serialization limits | HWPX physical table representation is not claimed |
| Slot to master mapping | `pass` | Every slot resolves to exactly one master; gap and overlap reject before publication | Nested-table routing is P06-08+ |
| Rectangular spans | `pass` | Top-left plus nonzero row/column span; explicit covered slots must form one complete axis-aligned rectangle | Merge/split content policy is P06-03 |
| Stable identity and ordering | `pass` | Unique bounded logical IDs and row/column/ID canonical ordering | Backend identity mapping is not claimed |
| Canonical serialization | `pass` | Strict v1 JSON, unknown-field rejection, deterministic canonical bytes and SHA-256 | Public wire/API exposure is not claimed |
| Property and negative tests | `pass` | Fixed-seed 256-partition corpus, bounds/gap/overlap/nonrectangular/version/JSON/allocation negatives | Arbitrary document corpus is unverified |
| Portable source locks | `pass` | Four design sources use UTF-8/LF canonical SHA-256; LF and CRLF independent checkouts pass | Semantic source changes still fail closed |

## Model and failure contract

- Contract version: `hwpx-agent.table-grid/v1`.
- Default limits: rows 10,000; columns 1,024; slots 1,000,000; master cells 1,000,000;
  identifier 256 UTF-8 bytes; canonical serialization 32 MiB.
- `CellCoordinate`, `TableCellSpan`, `TableGridDraft` and immutable `TableGrid` separate untrusted
  construction input from validated state.
- Construction rejects invalid limits/version/JSON, zero or excessive dimensions, capacity overflow,
  invalid or duplicate IDs, empty/overflowing/out-of-bounds spans, duplicate coverage,
  nonrectangular coverage, overlap, uncovered slots, out-of-bounds lookup, serialization overflow and
  allocation failure with typed errors.
- Input cell order is non-semantic. Canonical order is row, column, then logical ID.

## Source qualification

- Source successor v21 `p17.current-workspace-source.v21.20260907` composes immutable v20 contract
  SHA-256 `adca1fbccedad8b4c6dfb7dbd223f86b02a7ba5f9357c21220340b3796969d22`.
- Clean source acceptance run `70de52be98564f43b030557435682606` passed 11/11 checks and retained
  the exact 25-member Cargo successor projection. Receipt SHA-256 is
  `c44885ee42ef8e245fb6120b542474a32998ce4afe4d33d9326946dfb2b01d9d`.
- The v21 contract binds eight P06 implementation/policy/validator files and has SHA-256
  `27d25fb3c6b1ac5f0c2761b054f9c80172534c2450cb619cafdc7ee01dc4fec9`.
- Qualification verification and its negative tests passed 3/3. The local receipt remains ignored
  evidence and was not copied into the independent worktree or Git.

## Validation evidence

- Current Windows target: `cargo test --locked -p domain-ir --test table_grid` passed 7/7; the
  256-case fixed-seed partition property corpus passed; targeted Clippy with `-D warnings` passed.
- P06 contract validator passed four source locks and three implementation marker files. Its Python
  suite passed 5/5, including source tamper rejection, traversal rejection, duplicate-key rejection
  and LF/CRLF checkout equivalence.
- Offline Linux used Rust 1.96.0 image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
  with network disabled, read-only source and Cargo registry, dropped capabilities,
  no-new-privileges, bounded CPU/memory/PIDs and executable disposable tmpfs. Domain IR tests,
  including TableGrid 7/7, and Clippy `-D warnings` passed.
- Exact audited commit `823c35255bd178de167a0f50503788e1ee886000` passed the current
  workspace FULL pipeline 5/5: linux-core, windows-worker, widget, docs and security. P14 tests were
  135/135 and P15 tests were 85/85. Security run `d64def747cb547cc9b2ed40fe60f229e`
  reported failed checks, vulnerabilities and forbidden licenses 0; report SHA-256 is
  `0a96e3494c4e81665bfc7179ab3e0e890b9e1a1ce8a6f0d6f7e62956f887d7e3`.
- A clean independent worktree detached at the same exact commit passed FULL 5/5 and the P06
  validator 5/5. Security run `ee80707dcfd841648f879e1fe98a5716` reported the same zero findings;
  report SHA-256 is
  `3ba9522dbf959f527675ca0edebef94a6af4a1c344e69a0122ef6e71381e0f54`.
- Final residual checks found `Hwp.exe` count 0 and P06 offline container count 0.

## Strict review and remediation

- Change risk: `high`; later table mutation, merge/split, formula, pagination and selector work
  depends directly on this invariant.
- Verdict: `approve_scoped_current_pc_local_pure_ir`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Initial explicit-slot construction used the first sorted coordinate's column as the rectangle's
  minimum column. A diagonal two-slot set could therefore be misclassified. Row and column minima
  are now computed independently and the diagonal regression is locked.
- The first FULL attempt detected that registering P06 checks by rewriting immutable P15's
  `run_ci.py` source lock caused generated-contract drift. P06 checks were separated from that
  immutable lane; P15 85/85 and dual FULL then passed without rewriting predecessor contracts.
- The first independent P06 validator detected raw-byte drift between CRLF and LF checkouts of the
  same tracked roadmap. Source hashes now canonicalize UTF-8 line endings to LF, and a two-form
  regression proves both checkouts while actual content tampering still fails.
- New Rust/test sources contain 0 `unwrap`, `expect`, `panic`, `unsafe`, `TODO` or `FIXME` sites;
  `git diff --check` passed.

## Preserved failures and scope boundary

- The first offline Linux attempt failed before compilation because the isolated container lacked
  the Cargo registry cache. The second failed because its target tmpfs was mounted `noexec`. Both
  remain diagnostic failures; the passing retry mounted only the registry read-only and used an
  executable disposable target without enabling network or weakening the read-only source boundary.
- The generated-contract drift and independent raw-byte source-lock failure remain recorded as
  pre-Gate defects; neither was relabeled as a pass.
- No user document or original design ZIP was opened, modified, moved or deleted. No HWPX table was
  generated and no Hangul process was launched for P06-01.
- Actual current-PC Hangul 2020 table lift/lower, save/reopen/readback/render evidence belongs to
  later P06 tasks. Hangul 2022/2024, other PCs, production, server/VM and distribution remain
  deferred and unqualified.

## Task decision and next exact task

P06-01 is complete only for the scoped pure logical-grid invariant. P06 as a phase remains in
progress and none of P06-02 through P06-09 is implied complete.

Start `P06-02 Create/insert/delete` at reasoning effort `high`. Implement deterministic table, row
and column creation/insertion/deletion over validated `TableGrid`; define master-cell identity and
index remapping, span-boundary behavior, empty/overflow/last-row-or-column policies and atomic
failure semantics; then prove boundary/index/property tests before P06-03 merge/split.
