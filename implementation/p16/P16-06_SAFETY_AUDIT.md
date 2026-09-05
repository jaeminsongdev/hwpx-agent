# P16-06 execution safety audit

- Date: 2026-09-05; review STRICT / risk HIGH; recommended reasoning `max`.
- Implementation worktree: `D:\개발\hwpx-agent-work-p16-06-safety`, base `e82cf95`.
- State: target/unit/local-browser and refreshed formal contract pass; **full audit and integration open**.
- No actual host registration, server-side document execution, Hangul/COM or other-PC proof.

## Findings repaired

1. A submitted plan could be rearmed after revalidation or another render. The controller now
   reserves the project/base-revision/plan binding before write dispatch. Locale/surface changes
   cannot grant a second write. The no-eviction cache has a hard 128-binding limit.
2. Lost, malformed, mismatched or newly warned execution replies could look like no execution.
   They now retain an `unconfirmed` record and cannot be resent within the session. Cancellation
   after dispatch preserves that uncertainty. Submitted/committed outcomes remain distinct.
3. A late rejected execution could clear a newer approved view. Stale replies now update only
   their own dispatch record; stale failures cannot mutate another current snapshot.
4. Approved host input aliased the caller's mutable object. Parsed requests now copy the validated
   primitive identity fields. Unapproved later identity changes cannot redirect the snapshot.
5. Partial routes could authorize execution. Only verified routes satisfy necessary client checks;
   an otherwise valid explicit server denial remains false. This matches the domain router's
   verified-only admission and never grants permission client-side.
6. Request and idempotency identities could be reused. Each is now unique within the controller
   session with a hard 1024-entry limit; exhaustion fails before a write, without evicting history.
7. Submitted/unknown-result controls remained enabled. React derives disabled flags directly from
   current state; no new effect or secondary authority store was introduced. Unknown results use
   amber verification-needed copy and `role=alert`, not green completion styling.
8. Capability IDs had an unbounded regex despite the public 160-character limit. Both snapshot and
   capability-result parsing now check that bound before regex evaluation.

These are client-session defenses, not durable server idempotency, reconciliation or authorization.
Widget recreation/cross-widget operation requires the unchanged server enforcement boundary.
The positive preview/bridge fixture now marks its *synthetic* routes verified, while negative tests
reject partial execution. No real capability support state or predecessor contract was promoted.

## Regression and validation evidence

- Five initial regressions failed on the earlier implementation and passed after the first repair.
- Eleven additional target failures reproduced missing uncertainty state, disabled-control checks
  and the capability length limit. All passed after repair. A further visual-role regression failed
  before the warning-role change and passed afterward. The existing acknowledgement test's weak
  alternation was replaced with an exact disabled-button assertion plus an enabled positive case.
- Current TypeScript/React package: **109/109 PASS**, zero skipped/cancelled; typecheck and build PASS.
- Plan-review source/style/bundle validator PASS; plan-review Python tests **15/15 PASS**.
- All P16 Python tests **92/92 PASS**, including predecessor contract validation.
- Selected changed-file Prettier and `git diff --check` PASS.
- Real App/AppBridge local browser flow: five calls in exact route/dry-run/recheck/dry-run/write
  order. Disabled pre-acknowledgement and post-submission buttons were exercised without extra calls.
- Ten current screenshots passed DOM/action/console checks and direct original-resolution review:
  desktop 1200x760, narrow 500x1200, minimum width 320x1600. No overlay, page error, console warning
  or horizontal clipping was observed. The 320px case does not claim short-phone viewport fit.

The successful local browser receipt is external to the repository in the Codex workspace's
`p16-06-safety-qa-20260905/retry-05/receipt.json`, SHA-256
`03e36bdeceafa66d37a5d64b5cb3ecb02dbaa8a7759fdd264ece3f85d08f274d`. Its adjacent `inspection.md`
records direct image review. Chrome 152.0.7977.76 and installed Playwright 1.60.0 ran with Chromium
sandbox enabled, HTTP(S) blocked, no user profile and a process-local temporary directory. The
runner exited 0 and the dedicated temp directory was empty afterward. No dependency was installed.
The Browser plugin/skill was absent; the documented project-E2E/Playwright fallback was used.

Earlier external helper runs are preserved as failures: one test incorrectly selected `unconfirmed`
as confirmation; later attempts completed UI checks but hung in system-temp directory cleanup after
Chrome exited. An empty-browser probe reproduced cleanup waiting. A process-local owned ASCII temp
directory resolved the observed helper cleanup. No system setting changed; this does not establish
the cause of the separate Hangul timeout or a general PC/Unicode defect.

Current rendered bundle digests:

| Bundle | SHA-256 |
|---|---|
| `plan-review-widget-v1.html` | `21a15c8562f8933d144102bf92c2f8f3dc33c6f890d7395e4e861a654c4c12ba` |
| `plan-review-preview.html` | `3e630033cbf234a126642021f67f05c318b54fb4a1f5c877797e202e20ed1b8a` |
| `plan-review-e2e-host.html` | `741e0790130ad5376724b78ff2d0c9041a2fe876189de19da5a3ee5b704b0473` |

## Open acceptance and exact next work

- The earlier `P16 plan-review contract is stale` failure is repaired. This card now binds 43
  source files and ten verified current captures, with preview-digest and coverage regressions.
  P16-05/P15 predecessor locks and seven historical captures remain unchanged. The full plan-review
  check runner exited 0 (session 49438), including deterministic bundle build, 109 widget tests,
  source/style/contract validation, real five-call local bridge E2E and 15 policy tests.
- The new source-bound semantic summary has 10 additional tests; domain all-target tests 65/65,
  package all-target Clippy, selected-file formatting and workspace format checks pass. Post-format
  Clippy found two missing semicolons and one test import placement issue; each was fixed and the
  checks rerun without suppression. See `P16-06_SOURCE_DIFF_PROJECTION.md` for limits and non-claims.
- Current and independent P05 full CI qualify e82cf95 only, not these later P16 changes.
- Current-source full CI, independent exact-checkout full CI, applicable Linux checks and final
  STRICT audit remain required before implementation closure/integration.
- `render_plan_review_widget` is currently located in the TypeScript resource descriptor; no
  matching implementation was found in the inspected MCP control-plane source/catalog. Trace the
  real plan storage and authorization boundary. The pure domain diff projector is now implemented,
  but authenticated stored-plan binding to the renderer remains absent. Synthetic fixture rendering
  and pure graph tests alone cannot satisfy that end-product requirement.
- Actual registered-host confirmation and server document execution remain independently unverified.
  Evaluate artifact-bearing and partially validated committed responses against the public contract
  as part of integration; do not silently narrow the product to artifact-null mock responses.

Overall verdict: **REQUEST_CHANGES / not closed**. The safety repairs are concrete tested progress,
but P16-06 and the P00-P20 product goal are not complete.
