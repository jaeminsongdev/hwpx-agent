# HWPX Agent implementation ledger

- Updated: 2026-09-05
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only.
- Active: P05-07 header-count repair verification and P16-06 Plan/diff UI audit.
- Recommended reasoning: max for preservation, authorization and Gate review; high for routine work.
- UI status: v3 attempt 19 terminal timeout; two screenshots showed the input access prompt.
  Session 1788 exit 1, owned Hwp cleaned and residual zero. No automatic relaunch.

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
| P-0086 | P16-06 Plan/diff UI | 9a16c2d safety + source-bound diff; FULL live, stored-plan/host integration open |

- P05-07 v2 fixture 9096502 has two linear sections and one break in product inspection.
  Attempts 10–16 timed out at open_input; attempt 17 instead passed open and failed
  SECTION_COLUMNS_READBACK_INPUT_TEXT_MISMATCH. Its text digest matches the first marker alone.
  The input is unchanged; no output/PDF was saved; quit passed and residual Hwp count is zero.
  See implementation/p05/P05-07_ATTEMPT17_DIAGNOSTIC.md for evidence digests and limits.
- The v2 generator omitted updating header secCnt from one to two. The repair adds preserving
  count updates and header/sequence correlation, with failing-before/passing-after evidence.
  Fresh v3 differs only in that count; old v2 now fails product inspection as intended.
  Offline Linux package all-target tests/Clippy pass with source/registry read-only and no network.
  Current and exact clean-checkout full CI both pass 5/5. V3 attempt 18 timed out before
  readback, with unchanged input and no output/PDF. See P05-07_ATTEMPT18_DIAGNOSTIC.md and count report.
- P16-05 implementation 118928b, closure fae5bc0: TS/React 41/41, local bridge calls 3/3,
  P16 Python 77/77, current/independent CI 5/5 and offline Linux evidence are recorded in its report.
- P16-06 safety repairs 5079402 and source-bound diff/visual refresh 9a16c2d are isolated, not integrated.
  Widget 109/109, domain 65/65, P16 Python 92/92, five-call bridge and 43-source formal contract pass.
  Ten verified current captures are archived separately; predecessor locks/old captures preserved.
  FULL sessions 24388/68679 are live at handoff, not PASS. Authenticated plan storage, compiled-plan binding
  and registered-host execution remain missing; the pure summary is not execution authorization.

## Open risks and holds

- R-0001: Header-count defect is fixed in software; actual v3 recovery and rendering remain unproven.
- R-0002: P16 safety has target evidence; full audit and authenticated stored-plan renderer remain open.
- HOLD-0001: P16-02 actual registration and P16-05/06 registered-host E2E remain unverified.
- HOLD-0002: P10-05 registered path-security module and P10-06 production COM execution remain open.
- HOLD-0003: P10-08 dedicated production isolation and later-version PCs remain unqualified.
- Do not infer PASS from CURRENT_STATE.md introductory prose; per-card/phase reports and evidence
  are authoritative. That introductory summary lags the P15/P16 work.

## Exact next actions and validation policy

1. Attempt 19 is terminal, not PASS; read P05-07_ATTEMPT19_DIAGNOSTIC.md. Only a fresh user-present
   request may launch another attempt. Keep two-section save/reopen/render criteria unchanged.
2. Collect live FULL 24388/68679; keep 9a16c2d fixed. Next implement authenticated stored-plan binding.
3. Run target tests, relevant regressions, current checkout FULL, exact clean-checkout FULL,
   applicable offline Linux checks, security and STRICT review before any implementation closure.
4. Close P05 only with save/reopen, semantic inspection, PDF verification and visual evidence.
5. Keep actual-registration, production and other-PC claims open until their own evidence exists.

## Context Pack and archive references

- Root: D:\개발\hwpx-agent; count-repair checkpoint e82cf95; P16-06 baseline 9360c47.
- Both count-repair FULL sessions terminated exit 0, 5/5 lanes PASS: current 5232 and exact e82cf95
  detached-checkout 68068 at D:\개발\hwpx-agent-audit-p05-count-e82cf95. Do not poll those handles.
  The independent log is artifacts/p05-count-repair/full-ci.log inside that checkout. Only the four
  exact hash-pinned P10 diagnostic JSON records were hydrated; no user document or key was copied.
- P16-06 checkpoint 9a16c2d55f82a012d9b354b5df2db983b07c4060 at D:\개발\hwpx-agent-work-p16-06-safety.
  FULL log: artifacts/p16/safety-summary-full-9a16c2d/full-ci.log in that checkout; session 24388 live.
  Target runner 49438 is terminal exit 0. Four exact P10 JSON records hydrated for FULL, no user docs/keys.
  Read implementation/p16/P16-06_SAFETY_AUDIT.md and P16-06_SOURCE_DIFF_PROJECTION.md there.
- Independent FULL 68679: D:\개발\hwpx-agent-audit-p16-9a16c2d, same exact checkpoint, tracked clean.
  Linux domain tests/Clippy PASS, session 2297 exit 0. Details: P16-06_AUDIT_HANDOFF_20260905.md in main.
- New external visual receipt/inspection: Codex workspace p16-06-safety-qa-20260905/retry-05/.
  The helper used process-local TEMP/TMP after system-temp cleanup hung; no system settings changed.
- First reads: this ledger; P05 attempt-17 report; implementation/p16/P16-06_PLAN_REVIEW_POLICY.md.
- First checks: git status --short; named attempt-17 trace; P16 plan-review controller/model/tests.
- Attempt 18 trace/progress: fixtures/target-build/p05-07-current-2020-20260905-v3/
  p05-07-hancom-2020-trace-attempt18.json[.progress.jsonl]; former Hwp 23600/worker 7832 are stopped.
- Attempt 19 uses the same v3 directory, new attempt19 output/trace/PDF names and unchanged wrapper
  implementation/p05/tools/run-hancom-2020-section-columns-readback.ps1, 600-second watchdog.
  Former worker 38380/Hwp 9872 are stopped; last event open_input/running, two captures showed prompt.
- Do not touch user originals, earlier failed evidence, predecessor contract locks or unrelated processes.
- Detailed completed task history through P-0085 remains in Git fae5bc0:PLANS.md, plus individual
  reports under implementation/p00/–implementation/p16/; this ledger is a bounded snapshot.
- No broad cleanup, new deployment, security-prompt bypass or external account changes are authorized
  by a local test. The full product goal remains active, not complete or globally blocked.
