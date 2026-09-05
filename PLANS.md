# HWPX Agent implementation ledger

- Updated: 2026-09-05
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only.
- Active: P05-07 header-count repair verification and P16-06 Plan/diff UI audit.
- Recommended reasoning: max for preservation, authorization and Gate review; high for routine work.
- UI status: attempt 17 terminated; no live Hwp process or access prompt. Do not relaunch unchanged.

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
| P05 | in progress | 01–06 pass; 07 actual readback mismatch; 08–09 actual rendering pending |
| P06–P09 | blocked by P05 | table, equation, graphics, fields engines |
| P10 | in progress | 01–04,07,09,10 scoped pass; 05/06 actual dependencies; 08 dedicated controls unqualified |
| P11 | blocked by P06–P10 | advanced desktop features |
| P12 | blocked by P11 | surgical edit and cross-backend normalization |
| P13 | blocked by P10 | validation/oracle/render |
| P14 | scoped local reference/disposable PostgreSQL PASS | implementation/p14/P14_GATE_REPORT.md |
| P15 | scoped local MCP reference/Inspector staging PASS | implementation/p15/P15_GATE_REPORT.md |
| P16 | in progress | 01,03,04 pass; 02 registration pending; 05 local component pass; 06 audit open |
| P17 | ready, not started | current-PC Codex companion only |
| P18 | blocked by P12/P13/P16/P17 | quality/security/performance/DR |
| P19 | blocked by P18 | production/license/submission |
| P20 | post-GA | parity and Rust-native expansion |

## Active tasks and current evidence

| ID | Task | State / next check |
|---|---|---|
| P-0046–0048 | P05-07–09 | Header secCnt mismatch repaired; 29 target tests pass, v3 actual acceptance pending |
| P-0082 | P16-02 registration | Local bundle ready; actual registered app/host receipt absent |
| P-0085 | P16-05 continuity | Local bridge/component evidence closed at fae5bc0; actual registered host pending |
| P-0086 | P16-06 Plan/diff UI | Implementation 9360c47; safety/contract audit and final verification still open |

- P05-07 v2 fixture 9096502 has two linear sections and one break in product inspection.
  Attempts 10–16 timed out at open_input; attempt 17 instead passed open and failed
  SECTION_COLUMNS_READBACK_INPUT_TEXT_MISMATCH. Its text digest matches the first marker alone.
  The input is unchanged; no output/PDF was saved; quit passed and residual Hwp count is zero.
  See implementation/p05/P05-07_ATTEMPT17_DIAGNOSTIC.md for evidence digests and limits.
- The v2 generator omitted updating header secCnt from one to two. The repair adds preserving
  count updates and header/sequence correlation, with failing-before/passing-after evidence.
  Fresh v3 differs only in that count; old v2 now fails product inspection as intended.
  Offline Linux package all-target tests/Clippy pass with source/registry read-only and no network.
  See implementation/p05/P05-07_SECTION_COUNT_REPAIR.md; full CI is running, actual v3 is NOT_RUN.
- P16-05 implementation 118928b, closure fae5bc0: TS/React 41/41, local bridge calls 3/3,
  P16 Python 77/77, current/independent CI 5/5 and offline Linux evidence are recorded in its report.
- P16-06 9360c47 has a separate versioned plan-review resource and local component/E2E artifacts.
  The interrupted full-CI run has no final all-lane receipt and is NOT PASS. Re-audit repeat-write
  prevention, stale async failures and partial-route authorization against the domain router before
  final verification. Real server diff projection and registered-host integration must be evaluated
  explicitly; fixture-driven component evidence cannot close those boundaries.

## Open risks and holds

- R-0001: Header-count defect is fixed in software; actual v3 recovery and rendering remain unproven.
- R-0002: P16-06 authorization and asynchronous state safety are not yet accepted.
- HOLD-0001: P16-02 actual registration and P16-05/06 registered-host E2E remain unverified.
- HOLD-0002: P10-05 registered path-security module and P10-06 production COM execution remain open.
- HOLD-0003: P10-08 dedicated production isolation and later-version PCs remain unqualified.
- Do not infer PASS from CURRENT_STATE.md introductory prose; per-card/phase reports and evidence
  are authoritative. That introductory summary lags the P15/P16 work.

## Exact next actions and validation policy

1. Finish P05-07 count-repair verification. On a user-present approval session, use the fresh v3
   fixture and unchanged two-section expected text; require actual save/reopen/render evidence.
2. Repair P16-06 safety defects with failing-before/passing-after regressions, then audit integration.
3. Run target tests, relevant regressions, current checkout FULL, exact clean-checkout FULL,
   applicable offline Linux checks, security and STRICT review before any implementation closure.
4. Close P05 only with save/reopen, semantic inspection, PDF verification and visual evidence.
5. Keep actual-registration, production and other-PC claims open until their own evidence exists.

## Context Pack and archive references

- Root: D:\개발\hwpx-agent; last implementation commit 9360c47.
- First reads: this ledger; P05 attempt-17 report; implementation/p16/P16-06_PLAN_REVIEW_POLICY.md.
- First checks: git status --short; named attempt-17 trace; P16 plan-review controller/model/tests.
- Do not touch user originals, earlier failed evidence, predecessor contract locks or unrelated processes.
- Detailed completed task history through P-0085 remains in Git fae5bc0:PLANS.md, plus individual
  reports under implementation/p00/–implementation/p16/; this ledger is a bounded snapshot.
- No broad cleanup, new deployment, security-prompt bypass or external account changes are authorized
  by a local test. The full product goal remains active, not complete or globally blocked.
