# HWPX Agent implementation ledger

- Updated: 2026-09-06
- Root: `D:\개발\hwpx-agent`
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86, personal local development only.
- Active: P05-08 Hangul-authored reference comparison and actual Gate, P05-09 coordinate-aware Gate,
  P17-06/P17-07/P17-08.
- Reasoning: max for preservation, authorization and Gate work; high for routine implementation.
- UI: attempt23 sparse layout/identity and dense attempt02 automatic flow/balance passed on Hangul 2020;
  P05-08 attempts 01-02 stopped fail-closed at open without a confirmed access-click receipt;
  attempt03 and the numeric-ID v2 attempt01 also returned false; click confirmation remains absent.

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
| P05 | in progress | 01-05 pass; 06 reopened; 07 sparse plus dense current-2020 subgates pass; 08-09 pending |
| P06-P09 | blocked by P05 | table, equation, graphics and fields engines |
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
| P-0045-0048 | P05-06-09 | Sparse/dense pass; P05-08 numeric paragraph-ID defect fixed and attempts preserved, Hangul-authored reference/current lifecycle open; 09 remains |
| P-0082 | P16-02 | Local bundle ready; actual registered app/host receipt absent |
| P-0085-0087 | P16-05/06 | Dedicated local one-tool MCP host v14 14/14; actual app/Hangul open |
| P-0088 | P17-03 | Daemon qualification 11/11 at run `4b1c023ca40c4a02b6dc25ac77ca656b` |
| P-0089/0089A | P17-04 | Bridge and installed-plugin qualification PASS; main binding PASS |
| P-0090 | P17-05 | Exact-commit MCP local file/Git plan-only run 16/16 PASS |
| P-0091 | P17-06 | Durable sync/adapter/CLI component 31/31; actual host transport remains |
| P-0092 | P17-01 | Deterministic 19-entry package core 7/7; registered remote app absent |
| P-0093 | P17-08 | Widget 133/133, MCP 13/13, disposable Git 20/20, installed v0.4 prepare 18/18; visible click/effect open |
| P-0094 | P17-07 | Local rebase/branch/manual resolver and stale-head CLI surface 37/37; host/UI/concurrent evidence open |

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

- Current source successor v2 run `6cc220553ca8460281f58d5db10ac7ea` passed 11/11 at independent
  clean `54c6c14`; 14 exact replacements, 23 locked/offline Cargo members and P05 dev-edges bound.
- P05 attempt23: actual sparse landscape save/reopen/PDF PASS; exact-fixture logical rebinding
  records two removed backend IDs without calling them preserved. Dense attempt02 also passed actual
  31-paragraph zero-break save/reopen, strict semantics, two-page coordinate/balance verification
  and visual review. Attempt01's one-page expectation failure is preserved. Source successor v7
  passed 11/11 at run `ee35b31e5192420d8292c7659655311d`; it retains all v6 P05 sources and
  additionally binds the P17-07 local resolver. Current/independent FULL remain pending.
- P05-08 fixed input passed strict product inspection and the policy-locked official Hancom model
  parsed all synthetic main/header/footer markers. Actual attempts 01-02 each returned false from
  `open_input` without a positive receipt that the user completed the displayed access request;
  neither is PASS. Attempt03 likewise failed at `open_input` after 7 seconds; whether access was
  clicked is awaiting explicit user confirmation. See `implementation/p05/P05-08_ATTEMPT01_02_DIAGNOSTIC.md`.
- P05-08 nested body paragraph IDs were incorrectly emitted as strings although the official model
  uses `UINT`. The product now rejects non-numeric values and the corrected fixture uses numeric
  IDs; package clippy and all 175 tests pass. Its actual open still returned false without a click
  receipt, so the Gate remains open. See `implementation/p05/P05-08_NUMERIC_PARAGRAPH_ID_REPAIR.md`.
- P05-09 has a fresh deterministic input at SHA-256
  `acce8f8a68ea9b4b6e9f629235bf6fa018fd7cfccf45384b316d2d2401ce2c97`. Its render contract was
  strengthened from text-only v1 to coordinate-aware v2 at SHA-256
  `eec108ed9bcc0cb15c6634db9a340d944cc305cdcfe5b428a0ccf076d8f845a8`, requiring left/right
  anchors and populated columns; verifier tests pass 21/21. Actual Hangul execution remains open.
- The old independent FULL process at `285c0ce` reached later lanes and terminated, but its detached
  console exit status was unavailable. It was not promoted; the clean exact worktree was removed.
  A fresh independent FULL remains required at the final implementation successor.
- P16 merge `0512883`; durable plan PostgreSQL run `1828b246e92746789fa5d6501e7f1ac2`
  passed 39/39, renderer/evidence run `2b01ce0ff66045f29a32c67d217aa9bd` passed 19/19,
  dedicated host run `d22e85581cd44d06a016f3460a43de12` passed 14/14; resources cleaned.
- P17-04 bridge run `d1a376b7563c4654b15fccbaa98645e0` and personal-plugin run
  `273f6ccaac644836814b87679ab4eb0c` passed 12/12; actual Hangul operations remain open.
- P17-07 local conflict resolver persists exact rebase, exact-base branch and manual-merge
  transitions through one journal CAS. All 37 `local-sync` tests pass and public stale-head output
  is identity/digest/path-free. Actual host receipt, graphical UI and concurrent Web/Codex evidence
  remain open; see `implementation/p17/P17-07_LOCAL_CONFLICT_RESOLVER_V1.md`.

## Risks and holds

- R-0001: P05-07 dense attempt02 current-PC actual subgate and latest source successor v7 pass.
  P05-08 authorized open/save/reopen/render, P05-09 and final current/independent FULL remain open;
  no later-version or arbitrary-document claim.
- R-0002: P16 actual registered-app and Hangul end-to-end evidence remains open.
- R-0003: One independent worker timeout smoke failed; retries passed, root cause unproven.
- R-0004: Broad P16 discovery remains red on immutable predecessor locks and legacy assets;
  targeted successor qualification is authoritative only for its stated scope.
- R-0005: P17-03 lacks persistent credential provider/PostgreSQL lifecycle; fail closed meanwhile.
- R-0006: P17-07 local resolver is component evidence only; qualified host/UI wiring and concurrent
  Web/Codex verification remain open.
- HOLD-0002: P10-05 path-security registration and P10-06 production COM execution are open.
- HOLD-0003: P10-08 production isolation and later-version PCs are unqualified.

## Next actions and validation

1. In a freshly loaded Codex GUI task, run one disposable v0.4 prepare/confirm flow and capture
   visible user approval plus exact Git effect/replay evidence. No Hangul access prompt is needed.
2. Complete the currently open Hangul-authored minimal header/footer reference, compare its exact
   saved structure with the corrected fixture, and repair the next proven incompatibility. Then
   rerun P05-08 and P05-09 with the user present. Require lifecycle, semantic, coordinate-aware PDF
   and visual evidence and preserve every failure.
3. Wire P17-06 to a qualified host credential/transport adapter, then capture an actual remote
   pull/push/checkpoint transition without promoting the current injected component evidence.
4. Extend that host protocol with P17-07 conflict resolution, wire the bounded stale-head surface to
   the widget, and run one real concurrent Web/Codex conflict per resolution path.
5. Before closure run target tests, regressions, current and clean-checkout FULL, applicable offline
   Linux/security/STRICT checks. Close P05 only with save/reopen, semantic, PDF and visual evidence.

## Handoff pointers

- First read: this file, `implementation/p05/P05-07_DIAGNOSTIC_AUDIT_STATUS.md`,
  `implementation/p17/P17-08_TRUSTED_WIDGET_V7.md`, and P16 main integration audit.
- Attempt23 evidence: `fixtures/target-build/p05-07-current-2020-20260906-v4/`; read
  `implementation/p05/P05-07_ATTEMPT23_IDENTITY_REBINDING.md` before the dense-flow successor.
- Dense successor: read `implementation/p05/P05-07_DENSE_COLUMN_FLOW_POLICY.md`; ignored prepared
  input is `fixtures/target-build/p05-07-dense-current-2020-20260906-v1/`.
- P05-08 diagnostic: read `implementation/p05/P05-08_ATTEMPT01_02_DIAGNOSTIC.md`; ignored prepared
  input and failed attempts are under `fixtures/target-build/p05-08-current-2020-20260906-v1/`.
- P05-08 successor: read `implementation/p05/P05-08_NUMERIC_PARAGRAPH_ID_REPAIR.md`; corrected input
  and the pending Hangul-authored reference are under
  `fixtures/target-build/p05-08-current-2020-20260906-v2/`.
- P17-07 successor: read `implementation/p17/P17-07_LOCAL_CONFLICT_RESOLVER_V1.md` and
  `implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V7.md`; actual host/UI/concurrent evidence is
  intentionally absent.
- Detailed history through P-0085 remains in `fae5bc0:PLANS.md`; later evidence is in individual
  reports and Git. Never touch user originals, failed evidence, predecessor locks or unrelated processes.
- Per-card/phase reports and bound evidence are authoritative; broad introductory prose is not.
- Product goal remains active. No local test authorizes deployment, prompt bypass or external changes.
