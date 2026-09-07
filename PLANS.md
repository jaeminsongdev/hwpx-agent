# HWPX Agent implementation ledger

- Updated: 2026-09-07
- Root: `D:\개발\hwpx-agent`
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only.
- Active: P06-04 actual Hangul cell-formatting Gate, P06-05 installed-font/render qualification,
  P17-06/P17-07/P17-08 and final product qualification.
- Reasoning: max for P06-04/P06-05 target-bound readback/render, preservation, authorization and
  final Gate work.
- UI: attempt23 sparse layout/identity, dense attempt02 automatic flow/balance, P05-08 v12
  odd/even/first-page header/footer/master and P05-09 v2 coordinate-aware VS-1 rendering passed on
  Hangul 2020. Computer Use performed no click or typing; the user approved the visible Hangul
  access prompts.

## Objective and boundaries

Complete P00-P20 without weakening Gates. Preserve user documents, source ZIPs, private evidence
and secrets. Use named disposable fixtures only. Computer Use is screenshot-only; the user performs
all UI input. Hangul 2022/2024 and other PCs are deferred until available. Production, provider,
server, VM, customer distribution and commercial licensing require their own Gates. Raw XML,
COM/HAction identifiers, arbitrary paths and unverified routes do not enter public/LLM actions.
Synthetic or component evidence never proves actual render, save, cross-version or production work.

## Phase snapshot

| Phase | State | Evidence or dependency |
|---|---|---|
| P00-P04 | scoped current-PC PASS | `implementation/p00/` through `implementation/p04/` |
| P05 | scoped current-PC PASS | 01-09 plus actual save/reopen/readback/PDF/visual, source v20 and dual FULL Gate |
| P06 | in progress | 01-03 scoped PASS; 04 lowerer ready/actual runtime waiting; 05 solver, HWPX adapter and current installed-font metric qualified components |
| P07-P09 | blocked in sequence | equation, graphics and fields engines follow P06 and their stated dependencies |
| P10 | in progress | 01-04,07,09,10 scoped pass; 05/06 actual dependencies; 08 unqualified |
| P11-P13 | blocked | depend on P06-P10 |
| P14 | scoped local PASS | disposable PostgreSQL reference Gate |
| P15 | scoped local PASS | local MCP/Inspector staging Gate |
| P16 | in progress | local source/plan/renderer/host pass; registered-app/Hangul open |
| P17 | in progress | package core and 03-05 implemented; 06/07 local components; 01 remote, 02, 06-09 open |
| P18-P19 | blocked | quality/security/DR then production/license/submission |
| P20 | post-GA | parity and Rust-native expansion |

## Active tasks

| ID | Task | State and next evidence |
|---|---|---|
| P-0045-0048 | P05-06-09 | Complete; authoritative scoped phase decision in `implementation/p05/P05_GATE_REPORT.md` |
| P-0049 | P06-01 | Complete: report `implementation/p06/P06-01_REPORT.md`; source v21 and dual FULL PASS |
| P-0050 | P06-02 | Complete: report `implementation/p06/P06-02_REPORT.md`; source v22 and dual FULL PASS |
| P-0051 | P06-03 | Complete: report `implementation/p06/P06-03_REPORT.md`; source v23 and dual FULL PASS |
| P-0052 | P06-04 | Runtime retry pending: attempt03 safely failed because actions targeted the initial document while a second blank document was saved; commit `8143d2c` binds/validates the active document before attempt04 |
| P-0053 | P06-05 | In progress: pure solver 15/15, HWPX adapter 12/12 and font receipt 6/6; source v29 qualified; named HWPX/Hangul semantic and PDF renderer evidence open |
| P-0082 | P16-02 | Local bundle ready; actual registered app/host receipt absent |
| P-0085-0087 | P16-05/06 | Dedicated local one-tool MCP host v14 14/14; actual app/Hangul open |
| P-0088 | P17-03 | Daemon qualification 11/11 at run `4b1c023ca40c4a02b6dc25ac77ca656b` |
| P-0089/0089A | P17-04 | Bridge and installed-plugin qualification PASS; main binding PASS |
| P-0090 | P17-05 | Exact-commit MCP local file/Git plan-only run 16/16 PASS |
| P-0091/0091A/0091B/0091C/0091D/0091E/0091F/0091G | P17-06 | Durable local sync; exact v3 mapping, authenticated host/history dispatch, bounded loopback TCP and actual PostgreSQL checkpoint process evidence pass; atomic durable mirror admission and pull/push remain |
| P-0092 | P17-01 | Deterministic 19-entry package core 7/7; registered remote app absent |
| P-0093 | P17-08 | Widget 133/133, MCP 13/13, disposable Git 20/20, installed v0.4 prepare 18/18; visible click/effect open |
| P-0094 | P17-07 | Local rebase/branch/manual resolver and stale-head CLI surface 37/37; host/UI/concurrent evidence open |
| P-0094A | P17-07 | Graphical stale-head v2 component 144/144 and local iframe E2E pass; host registration/concurrent evidence open |

## Current P17-08 evidence

- Commits: `c1358b3`, `43c391c`, `1c7d1ea`, `a42ca0f`.
- Widget: `web/plugin-widget/dist/git-approval-widget-v1.html`.
- MCP: read-only prepare tool plus app-only destructive confirm tool; 128 pending cap,
  300-second component challenge TTL, consume-before-async, current-plan revalidation and
  60-second internal HMAC confirmation. Approval key is random and process-local only.
- Actual acceptance run `2eddeec06b824857af3c546f7e32e328`: 20/20 PASS through stdio MCP,
  Node, Rust daemon and disposable Git. Exact bytes/parent/branch checked; unrelated staged data
  preserved; replay rejected. No Hangul, network, user repository or trusted UI was involved.
- Personal plugin source: `C:\Users\thdqu\plugins\hwpx-agent-local`, version
  `0.4.0+codex.20260906130036`; enabled and configured without MCP env secrets.
- Fresh Codex CLI health and prepare calls passed. They did not render trusted UI and did not
  execute Git. Canonical run `9e2a6c6e958642e6a7f72dc9dac0bf25` passed 18/18 and bound exact
  installed arguments/artifact hashes while preserving Git state and leaving no approval-state file.
- Visible confirmation requires a newly loaded Codex GUI task because this task's tool inventory
  predates plugin v0.4. Do not describe the CLI diagnostic as an actual user click.
- Disposable click fixture: `D:\개발\hwpx-agent-local-workspace`, branch `main`, HEAD
  `111ad2b6bf291f85b0e61cf537d063fdbc007d3c`, output `widget-check-01.hwpx`, SHA-256
  `a3d6a1a5749256577be7a3f13662271a048023da26b8789322cb06f69561b0ba`.

## Other current evidence

- Current source successor v20 run `7f1b1756db794407a6256398170b7bf8` passed 11/11 and binds
  implementation commit `cacbc936e4d225e1a4424efb806aa96f86965ec5`, 25 exact predecessors,
  118 implementation files and 25 locked/offline Cargo members. Receipt SHA-256 is
  `f5eafd5b3d1fef9d46c9fb7b2eb5179e9d2e1998387025470cc93484aee4c2c3`; contract SHA-256 is
  `adca1fbccedad8b4c6dfb7dbd223f86b02a7ba5f9357c21220340b3796969d22`.
- P05 attempt23: actual sparse landscape save/reopen/PDF PASS; exact-fixture logical rebinding
  records two removed backend IDs without calling them preserved. Dense attempt02 also passed actual
  31-paragraph zero-break save/reopen, strict semantics, two-page coordinate/balance verification
  and visual review. Attempt01's one-page expectation failure is preserved.
- P05-08 used Hangul-authored header/footer and master-page references to repair numeric paragraph
  IDs, the standalone unqualified `masterPage` root, manifest/root/section identity, non-spine
  publication, archive order, sublist line caches and control placement in the body run. Hangul's
  saved empty `<hp:t/>` exposed and now has a fail-closed, non-panicking zero-inline reader path.
  Earlier failed variants and the v11 marker-overlap result remain preserved and are not relabeled.
- User-authorized v12 attempt02 passed every Hangul 2020 lifecycle phase with input immutability and
  zero process residue. Saved HWPX SHA-256
  `2fd7af9efb54132160b617b7b28399804596115fb2758bf193e5b0cd830838ac` strictly read back 4 pages,
  4 definitions, 8 page fields, 1 master, first-page hiding and the locked body digest. PDF SHA-256
  `649452bdc3f755def558fbe70a6be5ad8a75e6d6e2dc9059e6fee96e82a7838a` passed its four-page
  text/forbidden-text/geometry contract; original-resolution review confirmed separated even/odd
  header, body, right-side master, footer and bottom-center number markers with no clipping or
  overlap. `hwpx-package` all-target/all-feature tests pass 217/217, warnings-denied Clippy passes
  and PDF verifier tests pass 21/21. See
  `implementation/p05/P05-08_HANCOM2020_MASTER_PAGE_REPAIR.md`.
- P05-09 v2 uses ordinary two-column flow with one explicit break and the current-target empty
  backend column ID. Actual Hangul 2020 open/save/reopen/PDF passed; strict saved inspection retained
  five paragraphs, one break, two columns and the exact visible-text digest. Coordinate verification
  passed with 24 left/17 right fragments and a 10.145 mm bottom delta; original-resolution review
  found no overlap or clipping. The previous nonempty-ID/balanced attempt and the first page-edge
  callback verification failure remain preserved. `hwpx-package` passes 218/218, six bounded
  PowerShell suites 164/164 and the PDF verifier 21/21. See
  `implementation/p05/P05-09_HANCOM2020_ACTUAL_GATE.md`.
- The old independent FULL process at `285c0ce` remains an unpromoted historical failure because its
  detached console exit status was unavailable. Exact audited commit
  `cf5475379422899ac25fecb78968802d53442b3c` subsequently passed current and clean independent FULL
  `5/5` each. Current security run `401faa204de34bd1aca467ac4491efc4` and independent run
  `5c87496e8ba3491ba93edc577e2d5e61` reported failed checks/vulnerabilities/forbidden licenses 0.
  Offline Linux P05 package tests passed 210/210 and Clippy `-D warnings` passed with network disabled
  and source/registry read-only. `implementation/p05/P05_GATE_REPORT.md` is authoritative.
- P06-01 final implementation commit `6e49b0f6d3937d1026f3a0395e1a58bf405a148c` and source/audit
  commit `823c35255bd178de167a0f50503788e1ee886000` lock the bounded `TableGrid`. Rust 7/7,
  256 property cases, P06 validator 5/5, source v21 3/3, offline Linux tests/Clippy and
  current/independent FULL 5/5 passed. Raw-byte source locks were repaired to UTF-8/LF canonical
  hashes after an independent CRLF/LF checkout failure. No Hangul runtime or user document was used.
  `implementation/p06/P06-01_REPORT.md` is authoritative.
- P06-02 implementation commit `f0f5c1e162d46993593b1f4a45fc8afd2c620a34` and source/audit
  commit `8d4ed84d89c558bfc262a923b09d988333bec41a` lock bounded table create/insert/delete,
  survivor identity/coordinate remapping, exact caller IDs, span-boundary rejection and atomic
  receipts. `domain-ir` passed 83/83, table operations 9/9, P06 Python 11/11, source v22 combined
  15/15, offline Linux tests/Clippy and current/independent FULL 5/5. Both security runs had zero
  failed checks/forbidden licenses and all vulnerability checks exited 0. No Hangul runtime or user
  document was used. `implementation/p06/P06-02_REPORT.md` is authoritative.
- P06-03 implementation commit `0bd152dd85fa42632f8f7213e96e445af44524be` and source/audit
  commit `5cfa20e54566652f0d3cd17d26996bc45379ea33` lock complete rectangular merge,
  evenly divisible split, top-left/caller-owned identity, four explicit content policies and
  deterministic transfer/discard receipts. `domain-ir` passed 95/95, merge/split 12/12, P06 Python
  17/17, source v23 4/4, offline Linux tests/Clippy and current/independent FULL 5/5. Both security
  runs had zero findings and STRICT blocker/major/minor was 0/0/0. No Hangul runtime or user
  document was used. `implementation/p06/P06-03_REPORT.md` is authoritative.
- P06-04 source attempt03 created exact disposable HWPX SHA-256
  `65c43887b4170e8ae4e09b0ba64abe6a6850692c3757a8542ce94a0549a80cb5` but failed closed at
  reopen with `HWPX_REOPEN_MARKER_MISSING`; inspection proved the saved section contained no table.
  The generator had not activated its newly added document, so eight successful `HAction` calls
  affected the initial document while `SaveAs` wrote the second blank one. Commit `8143d2c`
  explicitly binds the document and requires all four markers before save; static readback tests are
  17/17 and P06 contracts remain 33/33. attempt03 is diagnostic evidence only, never PASS.
- P06-05 current font-metric implementation commits `af3dbf0`/`42aba1c` and source qualification
  commit `742b3d2` bind exact Hangul 2020 build `11.0.0.9136` x86 and installed
  `HANBatang.ttf` without copying it. Windows PowerShell 5.1 run
  `4b9b0cac589946918140abc4a12c1be1` and PowerShell 7 run
  `cb76a3477e2c4bcdac78b6647e187acf` independently produced measurement-set SHA-256
  `96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9`; both passed 16/16,
  independent Python verification and exact Rust product consumption. Receipt tests are 6/6, P06
  contracts 33/33, all `hwpx-package` targets, full workspace tests, formatting and warning-denied
  Clippy pass. Source v29 run `99fd2af086e14d3e9d97daa2f01b6408` passed 11/11. This proves
  verified GDI+ solver input only, not Hangul layout/render equivalence or P06-05 completion.
- P16 merge `0512883`; durable plan PostgreSQL run `1828b246e92746789fa5d6501e7f1ac2`
  passed 39/39, renderer/evidence run `2b01ce0ff66045f29a32c67d217aa9bd` passed 19/19,
  dedicated host run `d22e85581cd44d06a016f3460a43de12` passed 14/14; resources cleaned.
- P17-04 bridge run `d1a376b7563c4654b15fccbaa98645e0` and personal-plugin run
  `273f6ccaac644836814b87679ab4eb0c` passed 12/12; actual Hangul operations remain open.
- P17-07 local conflict resolver persists exact rebase, exact-base branch and manual-merge
  transitions through one journal CAS. All 39 `local-sync` tests pass and public stale-head output
  is identity/digest/path-free. Actual host receipt and concurrent Web/Codex evidence remain open;
  see `implementation/p17/P17-07_LOCAL_CONFLICT_RESOLVER_V2.md`.
- P17-07 stale-head widget v2 adds checked observed/current generations, a unique server-allowed
  resolution list and a mandatory second confirmation. Selection makes zero calls; confirmation
  binds expected revision/generation and idempotency, then requires an authoritative open/history
  refresh. The plugin widget passes 144 tests, v1 regression E2E passes and v2 local iframe run
  `784ceb1476354f51b73fb5cbf40d8e1c` passes. This is graphical component evidence only:
  `project_conflict_resolve` is not registered and actual concurrent Web/Codex evidence is absent.
- P17-06 private request v3 retains exact `mirror_id` binding and adds the required checkpoint
  label/optional note. Local-mirror v5 persists the exact encoded request SHA-256 with the replay
  key, rejects same-key metadata drift before remote I/O, and never journals label/note text. The
  local suite passes 39/39; workspace build, full tests and all-target Clippy pass. This remains a
  host prerequisite. Current source successor v12 composes it with the later authenticated-host,
  TCP and PostgreSQL checkpoint sources at commit `240f270`; atomic durable mirror admission and
  actual pull/push remain absent.
- P17-06 checkpoint service mapping preserves the exact P15 project/revision/label/note input,
  derives a stable UUIDv5 idempotency key from the private project/branch/mirror/key identity, and
  retains branch, mirror, generation and private request SHA-256 outside the public arguments. The
  server decoder rejects duplicate/unknown/old-version/noncanonical requests, the mapped JSON
  validates against the actual P15 Draft 2020-12 schema, and all 43 local tests pass. Authenticated
  mirror/head verification and service dispatch remain intentionally open; see
  `implementation/p17/P17-06_CHECKPOINT_SERVICE_MAPPING_V6.md`.
- P17-06 retention-mirror admission now parses exact public mirror IDs, requires the authenticated
  tenant subject's editor role, binds the exact project/branch/mirror and admits only a clean mirror
  at the exact registered branch/observed head. Stale heads return the current head without mutation;
  aliases and missing roles disclose no identity. The target suite passes 18/18. Bearer
  authentication and dispatch remain open; see
  `implementation/p17/P17-06_AUTHORIZED_MIRROR_ADMISSION_V7.md`.
- P17-06 `remote-sync-host` now enforces bounded request/context, one-time `mirror.sync` service
  authentication, exact canonical decoding, authenticated registry admission, injected P15 argument
  dispatch and request-digest-bound response in that order. Its 6/6 tests cover replay, aliases,
  stale heads, malformed canonical bytes, denial/unavailability, invalid receipts and redaction.
  The HMAC verifier and dispatcher are local/injected references; no listener, durable credential,
  concrete P15 backend or actual remote transition is claimed. See
  `implementation/p17/P17-06_AUTHENTICATED_CHECKPOINT_HOST_V8.md`.
- P17-06 history dispatch now preserves the optional note exactly and immutably, derives stable
  request/checkpoint identities from the service idempotency UUID, and rejects label normalization
  drift. One loopback test crosses the existing local authenticated adapter, two fresh one-time
  credentials, authenticated host, exact mirror admission and concrete history service: create then
  replay returns the same checkpoint. History tests are 17/17 and host tests 7/7. The repository and
  transport remain in-memory/loopback component evidence; see
  `implementation/p17/P17-06_HISTORY_CHECKPOINT_DISPATCH_V9.md`.
- P17-06 now has one shared strict binary frame, a client and server restricted to exact loopback
  endpoints, bounded connect/read/write deadlines, trailing-byte rejection and a process-local
  single-use credential handoff that zeroizes and redacts the bearer. A real OS TCP test crosses
  authentication, exact mirror/head admission and checkpoint dispatch. `remote-sync-wire` is 3/3,
  `local-sync` is 45/45 and `remote-sync-host` is 10/10; targeted all-target Clippy is clean. This is
  still same-process component evidence with ephemeral HMAC and in-memory repositories, not a
  durable daemon or actual remote transition; see
  `implementation/p17/P17-06_LOOPBACK_TCP_TRANSPORT_V10.md`.
- P17-06 PostgreSQL checkpoint successor adds exact migration 14, optional immutable note,
  v2-only least-privilege execution, forced tenant RLS, exact migration admission and one
  serializable no-retry transaction. Current-PC run `12e4189fc3864f0faedacd6d8e8f6adf`
  launched one host and four client processes against the pinned disposable PostgreSQL image and
  passed 15/15: create, exact replay, changed-note rejection, corrupted-row replay refusal,
  immutable rows, guarded rollback, migration/privilege drift rejection and owned-resource cleanup.
  FULL security run `dc6b4f31b22946f39dc98f164b0eb5a3` also passed every lane after aligning
  the repository's existing `BSD-3-Clause` policy with `cargo-deny`; `deny.toml` is qualification-bound.
  This is actual durable checkpoint evidence only; mirror role/head admission remains process-local
  and non-atomic, while pull/push, persistent credential custody, Hangul and production remain
  unproven. See
  `implementation/p17/P17-06_POSTGRES_CHECKPOINT_HOST_V11.md` and its frozen qualification. Current
  source successor v19 composes the v12 PostgreSQL binding with the later documentation,
  Telemetry, frozen P15 context, docs/widget validation, negative-test, retention mirror and P15
  auth source bridges without expanding those claims.

## Risks and holds

- R-0001 closed for the scoped current-PC P05 Gate: actual subgates, source v20 and current/independent
  FULL pass. Later-version, other-PC and arbitrary-document claims remain explicitly deferred.
- R-0002: P16 actual registered-app and Hangul end-to-end evidence remains open.
- R-0003: One independent worker timeout smoke failed; retries passed, root cause unproven.
- R-0004: Broad P16 discovery remains red on immutable predecessor locks and legacy assets;
  targeted successor qualification is authoritative only for its stated scope.
- R-0005: P17-06 now has current-PC disposable PostgreSQL checkpoint lifecycle evidence, but lacks
  persistent credential custody, a production PostgreSQL service lifecycle and one atomic durable
  mirror role/head admission plus checkpoint transaction. Transport remains loopback-only.
- R-0006: P17-07 local resolver and graphical stale-head widget are component evidence only;
  qualified `project_conflict_resolve` host wiring and concurrent Web/Codex verification remain open.
- R-0007: P06-01/02/03 prove the pure grid and structural semantics. P06-04 adds a bounded cell-style
  lowerer and P06-05 adds a verified pure solver, preserving HWPX size adapter and exact current
  installed-font GDI+ receipt. GDI+ is not the Hangul renderer: actual Hangul 2020
  save/reopen/wrap/render, formula/pagination/inspection and the 61-row target conformance matrix
  remain open in P06-04~09.
- HOLD-0002: P10-05 path-security registration and P10-06 production COM execution are open.
- HOLD-0003: P10-08 production isolation and later-version PCs are unqualified.

## Next actions and validation

1. At reasoning `max`, source-qualify commit `8143d2c`, launch corrected P06-04 attempt04, and wait
   for the user's visible Hangul 2020 file-access approval. Require pre-save markers, exact source
   HWPX/PDF/trace, zero Hwp residue, then lower the target style and run the same bounded
   save/reopen/semantic/PDF verifier. Do not promote diagnostic attempt03.
2. Continue P06-05 at reasoning `max`: consume the qualified current-PC font receipt, feed only its
   verified metrics into the solver, lower one named HWPX fixture, and compare semantic geometry,
   wrapping and signed PDF rendering in licensed Hangul 2020. The receipt and component tests alone
   do not close the card.
3. In a freshly loaded Codex GUI task, run one disposable v0.4 prepare/confirm flow and capture
   visible user approval plus exact Git effect/replay evidence. No Hangul access prompt is needed.
4. Move mirror role/head admission into durable PostgreSQL and combine it atomically with the
   qualified checkpoint transaction, then implement and capture actual bounded pull/push
   transitions. Preserve the current separately launched PostgreSQL checkpoint run as the narrower
   predecessor; do not promote it to a full remote-sync or production PASS.
5. Extend that host protocol with the widget's bounded P17-07 `project_conflict_resolve` contract,
   register it only after authenticated transport exists, and run one real concurrent Web/Codex
   conflict per resolution path. The graphical component itself is implemented and locally tested.
6. At each phase closure run target tests, regressions, current and clean-checkout FULL, applicable
   offline Linux/security/STRICT checks without weakening the phase-specific actual evidence Gate.

## Handoff pointers

- First read: this file, `implementation/p06/P06-03_REPORT.md`, `implementation/p06/P06-02_REPORT.md`, `implementation/p06/P06-01_REPORT.md`, `implementation/p05/P05_GATE_REPORT.md`,
  `implementation/p05/P05-07_DIAGNOSTIC_AUDIT_STATUS.md`,
  `implementation/p17/P17-08_TRUSTED_WIDGET_V7.md`, and P16 main integration audit.
- Attempt23 evidence: `fixtures/target-build/p05-07-current-2020-20260906-v4/`; read
  `implementation/p05/P05-07_ATTEMPT23_IDENTITY_REBINDING.md` before the dense-flow successor.
- Dense successor: read `implementation/p05/P05-07_DENSE_COLUMN_FLOW_POLICY.md`; ignored prepared
  input is `fixtures/target-build/p05-07-dense-current-2020-20260906-v1/`.
- P05-08 diagnostic: read `implementation/p05/P05-08_ATTEMPT01_02_DIAGNOSTIC.md`; ignored prepared
  input and failed attempts are under `fixtures/target-build/p05-08-current-2020-20260906-v1/`.
- P05-08 successor: read `implementation/p05/P05-08_HANCOM2020_MASTER_PAGE_REPAIR.md`. The ignored
  current-PC PASS evidence is under `fixtures/target-build/p05-08-current-2020-20260907-v12/`;
  the Hangul-authored master reference is under
  `fixtures/target-build/p05-08-hancom-2020-master-reference-20260907-v1/`.
- P05-09 successor: read `implementation/p05/P05-09_HANCOM2020_ACTUAL_GATE.md`. The ignored
  current-PC PASS evidence is under `fixtures/target-build/p05-09-current-2020-20260907-v2/`.
- P17-07 successor: read `implementation/p17/P17-07_LOCAL_CONFLICT_RESOLVER_V1.md` and
  `implementation/p17/P17-07_STALE_HEAD_WIDGET_V2.md`, then
  `implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V8.md`; the local resolver and graphical
  component exist, while host registration/actual concurrent evidence is intentionally absent.
- P17-06 checkpoint successor: read `implementation/p17/P17-06_CHECKPOINT_INTENT_BINDING_V5.md`,
  `protocol/private/p17-remote-sync-adapter-v3.json` and both v3/v5 migration notes. The compatible
  conflict contract is `protocol/private/p17-local-conflict-resolver-v2.json`.
- P17-06 service-mapping successor: read
  `implementation/p17/P17-06_CHECKPOINT_SERVICE_MAPPING_V6.md` and
  `protocol/private/p17-checkpoint-service-mapping-v1.json`. The mapping is implemented; exact
  authenticated mirror/head verification and dispatch remain the next host task. The registry half
  is implemented in `implementation/p17/P17-06_AUTHORIZED_MIRROR_ADMISSION_V7.md` and
  `protocol/private/p17-checkpoint-host-admission-v1.json`.
- P17-06 authenticated-host successor: read
  `implementation/p17/P17-06_AUTHENTICATED_CHECKPOINT_HOST_V8.md` and
  `protocol/private/p17-checkpoint-authenticated-host-v1.json`. Authentication and admission are
  implemented as component boundaries; concrete P15 dispatch and actual transport are next.
- P17-06 concrete-dispatch successor: read
  `implementation/p17/P17-06_HISTORY_CHECKPOINT_DISPATCH_V9.md` and
  `protocol/private/p17-history-checkpoint-dispatch-v1.json`. Concrete in-memory create/replay and
  exact loopback compatibility pass; durable service state and actual transport remain next.
- P17-06 PostgreSQL checkpoint successor: read
  `implementation/p17/P17-06_POSTGRES_CHECKPOINT_HOST_V11.md`,
  `protocol/private/p17-postgres-checkpoint-host-v1.json` and
  `implementation/p17/qualification/postgres-checkpoint-host-v1-20260907/contract.json`.
  Durable checkpoint/process evidence passes; durable atomic mirror admission and pull/push are the
  next host increment.
- Detailed history through P-0085 remains in `fae5bc0:PLANS.md`; later evidence is in individual
  reports and Git. Never touch user originals, failed evidence, predecessor locks or unrelated processes.
- Per-card/phase reports and bound evidence are authoritative; broad introductory prose is not.
- Product goal remains active. No local test authorizes deployment, prompt bypass or external changes.
