# P16-06 plan and semantic-diff design specification

## Visual source and product boundary

- Concept: `implementation/p16/design/p16-06-plan-review-concept.png`.
- Final captures: `implementation/p16/visual-qa/p16-06-*.png`.
- The generated concept establishes hierarchy only. Production uses React, semantic HTML and CSS;
  it never loads the concept or capture images.

P16-06 adds a separate immutable plan-review resource. It receives only opaque project, base
revision and plan identities in model-visible input. An authoritative server result supplies a
closed capability route, bounded semantic counters, closed warning classifications and risk. The
view never accepts document text, filenames, paths, raw XML, HAction/COM names, credentials, URLs
or arbitrary warning copy.

## Information hierarchy

1. Plan-review title and closed `low`, `medium` or `high` risk badge.
2. Immutable base revision and plan prefixes only.
3. At most twelve capability routes with a closed backend and support level.
4. Added, modified and removed totals plus at most eight semantic categories.
5. At most eight locally worded warning classifications.
6. One primary and at most one secondary action.

The concept's decorative menu and close controls are omitted because the host owns container
navigation. The code-native implementation also replaces prose warnings with server code plus
local closed copy, and keeps every opaque identifier abbreviated.

## Validation and execution state machine

- Missing approved input is `approval_pending`, not an error. Tool input alone never becomes
  authoritative; the server result must strictly match project, source revision and plan identity.
- `execution_allowed=true` is accepted only when every route is supported at `verified`,
  dry-run state is `verified`, signature impact is `none`, and no warning is blocking. Server
  `execution_allowed=false` is preserved even when those necessary conditions pass.
- `계획 다시 검증` calls exact `capability_check` and then exact `document_edit` with
  `dry_run=true`, `best_effort=false`, exact base revision and signature invalidation disabled.
- `실행 검토` makes no server call. It opens a separate confirmation region. Execution remains
  disabled until the user selects the explicit risk acknowledgement.
- The final click repeats capability and dry-run validation before calling `document_edit` with
  `dry_run=false`. Dry-run and execution use distinct request and idempotency identities.
- Route/backend/support disagreement, base or plan disagreement, duplicate IDs, partial/unverified
  result, unexpected artifact, invalid lifecycle or cancellation clears authoritative state.
- Every asynchronous boundary rechecks the live approved snapshot. Cancellation or teardown during
  revalidation prevents all later dry-run and execution calls; stale results are ignored.
- In-widget consent does not replace host confirmation or server authentication, authorization,
  ownership, quota, idempotency and exact-revision checks.
- A dispatched plan is never rearmed in the same controller session. Its project/base/plan binding
  is reserved before dispatch; lost or invalid replies retain `unconfirmed` and explicit
  verification-needed copy. Valid accepted replies mean `submitted`, not document completion.
  Late replies cannot replace newer approved views. These bounded no-eviction records are not
  durable server reconciliation, and all post-dispatch primary/confirmation actions are disabled.

## Semantic diff and warning safety

- Diff data contains only integer totals and closed categories: paragraph, table, style, image,
  field, section, metadata or other. It contains no changed content or positional selector.
- Warning data contains only a bounded uppercase code, closed severity and closed category. The
  browser maps the category to local Korean/English copy and discards server prose.
- Capability IDs are constrained to the existing dotted identifier grammar. Backends are only
  `direct_hwpx`, `hancom_2020`, `hybrid` or `none`.
- The route digest is an opaque SHA-256 identity, displayed only as an eight-character prefix.

## Responsive and accessible behavior

- Desktop uses a two-column route/diff view; below 720 px it becomes one column without horizontal
  or nested scrolling.
- Controls are at least 44 px high, keyboard native and focus-visible. The acknowledgement uses a
  native checkbox. Blocking warnings use `role=alert`; revalidation and submission use
  `role=status`.
- Light and dark semantic colors retain at least 4.5:1 text contrast. Reduced-motion disables the
  only loading animation.

## Evidence boundary

The real `@modelcontextprotocol/ext-apps` `App` and `AppBridge` execute a local Chrome iframe
round-trip. The E2E asserts two-phase revalidation, explicit acknowledgement, second-click write,
distinct idempotency keys and exact base/plan routing. This is a local component E2E, not an actual
ChatGPT/Codex host, registered plugin, Developer mode, remote MCP, Hangul/COM or production proof.
