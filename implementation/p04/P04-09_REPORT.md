# P04-09 VS-0 core CLI report

- Generated: 2026-09-03
- Implementation commit: `e42666ccc78d6a70fc142ccc1d9d86e4bc5aed3b`
- Audited source commit: `6cc11f05d7d80314c6c56169a8cf37f7419a0d33`
- State: `pass_current_pc_local_vs0`
- Reasoning/review mode: `max / vertical execution, artifact publication and actual desktop evidence`

The product CLI now connects `DocumentGraph` → exact selector/compiler → signed direct-HWPX route →
workspace transaction → idempotency/revision CAS → deterministic HWPX build and bounded reopen. The
generated artifact is one A4 portrait section, one paragraph and one default style, with no personal
metadata. Actual evidence was collected only from the licensed exact Hangul 2020 installation on this
PC and a disposable generated fixture.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Versioned bounded request | `pass` | exact-field serde boundary, identifier/text limits, control/noncharacter/multiline rejection |
| Typed plan | `pass` | create target resolved and compiled through P04 selector/OperationPlan contracts |
| Verified route | `pass` | Ed25519-pinned `document.create_vs0` / `direct-hwpx-vs0`, exact 2020 build |
| Package closure | `pass` | deterministic 11 parts, stored mimetype/version, A4 1 section/paragraph/style, graph/ID reopen |
| Transaction | `pass` | private staging, complete validation, checksum identity, no overwrite, revision CAS |
| Idempotent retry | `pass` | same engine returns identical terminal result; second file/revision 0 |
| Actual Hangul 2020 | `pass` | exact x86 STA build, input identity, open/readback/close/quit all pass |
| Privacy/safety | `pass` | digest-only public evidence; input mutation/save/network/settings changes all false |

## Validation evidence

- Windows Rust 1.96.0: VS-0 package `3/3`, CLI library/integration `3/3`, workspace regressions and
  Clippy `-D warnings` passed.
- Independent actual-bundle verifier: positive plus artifact tamper, trace semantic drift, unknown
  request field and duplicate request field `5/5` passed. It additionally bounds archive/JSON sizes,
  expanded bytes, exact entry order/encoding, XML and preview semantics, metadata and progress.
- Actual exact Hangul 2020 run 6: target `hancom-hangul-2020-secondary`, build `11.0.0.9136`, STA;
  eight phases from input identity through `Quit()` all passed. Artifact SHA-256
  `57bfe1ce3b2b89fedbc5ffaf56e92cffb980afd368b7f83e05c0a13e8eccff06`, 7,431 bytes;
  readback SHA-256 `60333d94695ae286d18d5a50e0d4f32df87b85da80613efbdb4c81d8ebb957b7`,
  UTF-8 length 48. Bundle correlation SHA-256
  `b16a24fdbb8480b190607e1df320edcdb8f1cb37cf4d58a81ae5a94242e57048`.
- Actual request/trace/final-progress digests are respectively
  `02e3ab68fc5c879ee829f56ea8451f327122f94af600244d8a1f854259d2edd5`,
  `aebf0802dd93042cdb74fee785d6cd1b0a7dce2d2a4016e7a6cf0c308224237e`, and
  `369338a40d56d5d50c26eab81b7a3f1b3ee7a1b50105209f9881419d1e023dc9`.
- Current checkout and exact audited-commit clean clone FULL bootstrap: each `5/5` lanes passed;
  clean clone post-run Git changes 0. Security scanned 571 files, vulnerabilities and forbidden
  licenses 0.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`, network off,
  repository/registry read-only, Cargo offline and executable tmpfs; workspace tests and Clippy
  `-D warnings` passed.
- Actual evidence/private key directories are ignored and `git ls-files implementation/p04/evidence`
  returns no tracked files. User documents opened or modified: 0.

## Strict self-review

- Change risk: `high`; this is the first product vertical that publishes an artifact and binds a
  desktop-runtime observation to it.
- A transaction error could initially continue into the success path; control flow was made terminal
  before commit. The actual verifier was strengthened for duplicate JSON keys, boolean-as-integer
  confusion, identifier limits, ZIP expansion, preview/section correlation and package-wide personal
  metadata checks.
- The CLI never accepts raw XML/action/backend/destination input. The direct route cannot be created
  from unsigned or non-exact evidence, and failure never becomes partial success.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04 idempotency storage is in-process; separate CLI processes do not yet share a durable replay log.
That is the explicit P14 boundary. This Gate proves create-new VS-0 and exact semantic open/readback,
not arbitrary-document editing, save/render/PDF equivalence or visual fidelity. Hangul 2022/2024,
another PC, production, provider, server and VM use remain deferred and unqualified.

## Next exact task

Run the P04 phase Gate at reasoning effort `max`. If it passes, start `P05-01 Text flow reader/writer`
at `max`: lock the typed run/tab/line-break/field-boundary model, bounded lifting/lowering and Unicode
run-boundary corpus without weakening P03 preservation or P04 transaction contracts.
