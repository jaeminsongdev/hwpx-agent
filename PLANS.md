# HWPX Agent implementation ledger

- Updated: 2026-09-06
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only.
- Active: P05-07 layout identity and P17-04 local MCP/plugin installation.
- Recommended reasoning: max for preservation, authorization and Gate review; high for routine work.
- UI status: v3 attempt 21 passed open/save/reopen/text/PDF export; layout acceptance failed.
  Session 13431 terminal exit 0; normal quit, residual zero. No additional click or automatic relaunch.

## Objective and boundaries

Complete P00–P20 without weakening Gates. Preserve user documents, source ZIPs, private evidence and
secrets. Use only named disposable fixtures for actual tests. Computer Use is screenshot-only;
the user performs all UI input. Later Hangul versions/other PCs are deferred until available.
Production/provider/server/VM/customer distribution and commercial licensing require separate Gates.
Raw XML, COM/HAction identifiers, arbitrary paths and unverified routes never enter public/LLM actions.
Synthetic/component evidence is not actual render, save, cross-version or production proof.

## Phase snapshot

| Phase | State | Authoritative evidence / dependency |
|---|---|---|
| P00–P04 | scoped current-PC local PASS | implementation/p00/ through p04/, phase Gate reports |
| P05 | in progress | 01–05 pass; 06 orientation reopened; 07 saved-output/PDF checks fail; 08–09 pending |
| P06–P09 | blocked by P05 | table, equation, graphics, fields engines |
| P10 | in progress | 01–04,07,09,10 scoped pass; 05/06 actual dependencies; 08 dedicated controls unqualified |
| P11 | blocked by P06–P10 | advanced desktop features |
| P12 | blocked by P11 | surgical edit and cross-backend normalization |
| P13 | blocked by P10 | validation/oracle/render |
| P14 | scoped local reference/disposable PostgreSQL PASS | implementation/p14/P14_GATE_REPORT.md |
| P15 | scoped local MCP reference/Inspector staging PASS | implementation/p15/P15_GATE_REPORT.md |
| P16 | in progress | 01,03,04 pass; 02 actual app pending; 05 local pass; 06 dedicated local host v14 PASS |
| P17 | in progress | 03 bounded local daemon PASS; 01/02 and 04–09 pending |
| P18 | blocked by P12/P13/P16/P17 | quality/security/performance/DR |
| P19 | blocked by P18 | production/license/submission |
| P20 | post-GA | parity and Rust-native expansion |

## Active tasks and current evidence

| ID | Task | State / next check |
|---|---|---|
| P-0045–0048 | P05-06–09 | Orientation FULL/Linux pass; diagnostics 205 pass; both FULL fail source-lock qualification |
| P-0082 | P16-02 registration | Local bundle ready; actual registered app/host receipt absent |
| P-0085 | P16-05 continuity | Local bridge/component evidence closed at fae5bc0; dedicated local host v14 PASS; actual Codex app pending |
| P-0086 | P16-06 Plan/diff UI | Source v11, durable plan v12, renderer/evidence v13 and dedicated local host v14 PASS; actual app/Hangul open |
| P-0087 | P16-06 registered renderer | PASS for dedicated local one-tool MCP host: run d22e85581cd44d06a016f3460a43de12, exact v14 qualification; actual Codex app installation remains open |
| P-0088 | P17-03 local daemon | PASS: run 4b1c023ca40c4a02b6dc25ac77ca656b, canonical LF receipt, 11/11; private auth/config/workspace sandbox and binary smoke |
| P-0089 | P17-04 local MCP config | In progress: one-tool stdio bridge and actual MCP acceptance, then personal plugin composition/fresh-install smoke; persistent secrets excluded |

- P05-07 v2 fixture 9096502 has two linear sections and one break in product inspection.
  Attempt17 read only the first marker. Earlier timeouts/failures remain preserved in their reports.
- The v2 generator omitted updating header secCnt from one to two. The repair adds preserving
  count updates and header/sequence correlation, with failing-before/passing-after evidence.
  Fresh v3 differs only in that count; old v2 now fails product inspection as intended.
  Offline Linux package all-target tests/Clippy pass with source/registry read-only and no network.
  Current and exact clean-checkout full CI both pass 5/5. V3 attempt 18 timed out before
  readback, with unchanged input and no output/PDF. See P05-07_ATTEMPT18_DIAGNOSTIC.md and count report.
- P16-05 implementation 118928b, closure fae5bc0: TS/React 41/41, local bridge calls 3/3,
  P16 Python 77/77, current/independent CI 5/5 and offline Linux evidence are recorded in its report.
- P16 branch `62542b0` is merged into MAIN as exact two-parent commit `0512883`. Immutable predecessor
  locks remain intact; explicit six-path integration and 21-source actual-DB successors pass closed.
- Current/independent: P14 132, P15 84, P16 144, widget 126, plan policy 16, five-call bridge and all
  five CI lanes PASS. Actual PostgreSQL 25/25 passes in both; owned containers/volumes are removed.
- PostgreSQL v11 now rechecks active tenant/project, ACL, exact default head, verified source,
  service seal/receipt and immutable graph digest. Final run b4ad5c05 passed 29/29 and cleaned.
- Canonical compiled-plan restore now rechecks byte form, target paths, unit receipts and DAG order.
  PostgreSQL v12 encrypts plans, supports key rotation/restart and bounded expiry purge. Final run
  1828b246 passed 39/39 and cleaned.
- Receipt-bound renderer v13 reauthenticates through volatile/PostgreSQL plan stores before loading
  evidence, then binds the exact 2020 build/x86 route, diff, dry-run, signature and caller policy.
  Its tenant-isolated AES-256-GCM evidence repository passed 19/19 in disposable PostgreSQL run
  2b01ce0ff66045f29a32c67d217aa9bd, including restart, rotation, tamper, RLS and cleanup. Workspace
  tests/Clippy and widget 126/126 pass. Dedicated local host v14 registers exactly one
  `render_plan_review_widget` tool and one immutable resource outside the P15 catalog. Clean run
  d22e85581cd44d06a016f3460a43de12 passed 14/14 with exact restart snapshot, network rejection,
  ciphertext-tamper rejection and cleanup. Actual Codex app installation and Hangul execution remain
  open. The immutable predecessor plan-review contract is intentionally stale for successor sources.
- Attempt21 saved/reopened both sections and exported portrait PDF; actual landscape acceptance failed.
  Orientation v1 reversed the tokens; v2 corrects them and invalidates the earlier landscape interpretation.
  Spine checking now uses the graph and blocks comment decoys. Read P05-07_ORIENTATION_SPINE_REPAIR.md.

## Open risks and holds

- R-0001: Diagnostic FULL fails Cargo.lock source binding; column IDs and actual landscape render remain open.
- R-0002: Source, durable plan, in-process renderer, durable evidence and dedicated local MCP host PASS;
  actual Codex app installation and registered-app E2E remain open.
- R-0003: One independent worker timeout smoke failed; unchanged retries pass 3/3, root cause not proven.
- R-0004: Broad P16 Python discovery remains red on immutable predecessor source locks, the absent
  ignored widget bundle and legacy preview digest; v12 targeted qualification remains PASS.
- R-0005: P17-03 daemon has no persistent credential provider or PostgreSQL lifecycle; P17-04 must
  expose no secret/path and must fail closed when those later services are unavailable.
- HOLD-0001: P16-02 actual Codex app installation and P16-05/06 registered-app E2E remain unverified.
- HOLD-0002: P10-05 registered path-security module and P10-06 production COM execution remain open.
- HOLD-0003: P10-08 dedicated production isolation and later-version PCs remain unqualified.
- Do not infer PASS from CURRENT_STATE.md introductory prose; per-card/phase reports and evidence
  are authoritative. That introductory summary lags the P15/P16 work.

## Exact next actions and validation policy

1. Resolve diagnostic Cargo.lock source binding; read P05-07_DIAGNOSTIC_AUDIT_STATUS.md.
   Main 92ce629/independent 3827c21: 205/Clippy PASS, both FULL exit 1; security not run. No Hancom wait.
2. Implement P17-04 stdio MCP startup/auth and a separate local-companion plugin package, then run
   a personal-marketplace fresh-install health smoke. Do not place credentials in `.mcp.json`.
3. Connect the qualified `render_plan_review_widget` host only after a local secret/PostgreSQL
   lifecycle exists; keep remote Developer mode registration independently open.
4. Run target tests, relevant regressions, current checkout FULL, exact clean-checkout FULL,
   applicable offline Linux checks, security and STRICT review before any implementation closure.
5. Close P05 only with save/reopen, semantic inspection, PDF verification and visual evidence.
6. Keep actual-registration, production and other-PC claims open until their own evidence exists.

## Context Pack and archive references

- Root: D:\개발\hwpx-agent; count-repair e82cf95; P16 baseline 9360c47. Count FULL 5232/68068: 5/5 PASS.
  Independent checkout D:\개발\hwpx-agent-audit-p05-count-e82cf95, artifacts/p05-count-repair/full-ci.log.
- P05 repair 9f493a5: FULL 84430/81116 terminal 5/5 PASS; Linux 57646 terminal 193/Clippy PASS.
  First 71568 failed; smoke 42848 passed. Diagnostic FULL 76659/40541 terminal FAIL; Linux 96358 PASS.
- P16 integrated source: D:\개발\hwpx-agent at clean merge `0512883`; implementation parent `62542b0`.
  Detached audit: D:\개발\hwpx-agent-audit-main-0512883; exact source and 5/5 CI PASS, tree clean.
  Current/independent DB runs 20dff2d03ef04bb39abce731d9331565/827b7df672264573a69f80993db50921,
  both 25/25 PASS and cleaned. Read implementation/p16/P16-06_MAIN_INTEGRATION_AUDIT.md.
- P16 source v11 worktree: D:\개발\hwpx-agent-work-p16-durable-plan-renderer; actual DB run
  b4ad5c050f0d42509da56f072ba5d6fa passed 29/29. Durable v12 run 1828b246e92746789fa5d6501e7f1ac2
  passed 39/39. Renderer/evidence v13 run 2b01ce0ff66045f29a32c67d217aa9bd passed
  19/19. Dedicated local host v14 run d22e85581cd44d06a016f3460a43de12 passed 14/14; all resources
  cleaned. Actual Codex app installation, Hangul execution and phase completion remain open.
- P16 host v14 detached audit: D:\개발\hwpx-agent-audit-p16-host-06494a9 at `06494a9`;
  frozen offline dependency restore, Node format/typecheck/build/135 tests, Python 10, exact
  qualification verification, Rust workspace tests and Clippy `-D warnings` PASS; tracked tree clean.
- P17-03 repair `ca1a332`; qualifying local daemon run 4b1c023ca40c4a02b6dc25ac77ca656b
  passed 11/11 and cleaned with canonical LF receipt. Earlier run 23cfab98b711491aacb2940ca7cf32a8
  remains non-qualifying because its receipt used CRLF. Rust target 10/10, full workspace and Clippy
  PASS. Detached audit at `05ad6bb` reverified the qualification, full workspace, Clippy and P01
  security regressions from a clean checkout; no Hangul/network/plugin.
- External QA: Codex workspace p16-response-contract-20260905/inspection.md and run-03/receipt.json.
  Thirteen captures automated, six directly reviewed; exact HTML/script hashes bound, no user browser profile.
- First reads: this ledger; P05 audit status/column-ID admission plan and attempt21; P16 MAIN audit/policy.
- First checks: MAIN/audit status; saved attempt21 HWPX/PDF; durable PlanSource/renderer boundaries.
- Attempt21 trace/progress: fixtures/target-build/p05-07-current-2020-20260905-v3/
  p05-07-hancom-2020-trace-attempt21.json[.progress.jsonl]. Former worker 31488/Hwp 43524 exited normally.
  P16 actual runs 5a68a12751804d6f84df2b42ebed2f11/a06f2d898dd943e89ab6353e0a6f331b PASS; DBs cleaned.
- Do not touch user originals, earlier failed evidence, predecessor contract locks or unrelated processes.
- Detailed completed task history through P-0085 remains in Git fae5bc0:PLANS.md, plus individual
  reports under implementation/p00/–implementation/p16/; this ledger is a bounded snapshot.
- No broad cleanup, new deployment, security-prompt bypass or external account changes are authorized
  by a local test. The full product goal remains active, not complete or globally blocked.
