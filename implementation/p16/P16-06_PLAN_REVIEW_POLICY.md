# P16-06 plan-review policy

## Authority

The render tool is read-only and requires `project.read`. Interactive `capability_check` is
read-only. Both dry-run and execution calls use the existing `document_edit` contract with its exact
`artifact.read`, `artifact.write`, `job.submit`, `project.read` and `project.write` scopes;
execution additionally requires user consent, host confirmation and fresh server authorization.
The browser never upgrades its own permission or treats hidden component state as authority.

## Fail-closed rules

- Strict schema and exact-key parsing applies to render input, render result and all interactive
  results.
- Model input identifies a plan; only matching server structured content may render it.
- Any partial/unsupported/unverified route, blocking warning, unknown signature effect or unverified dry-run
  sets `execution_allowed=false`.
- An otherwise valid server denial remains false; client checks never grant execution permission.
- Revalidation is atomic from the UI perspective. Capability disagreement stops before dry-run;
  dry-run disagreement stops before execution.
- Execution requires separate review, acknowledgement and final click. A final click always repeats
  the checks; earlier successful revalidation is not cached as authority.
- Raw server errors, warnings, summaries, constraints and unverified reasons are parsed for bounds
  but never rendered or logged. A newly observed warning code, constraint or unverified reason that
  was not represented by the approved snapshot stops the flow.
- Before a write is sent, reserve its project/base-revision/plan identity as `unconfirmed`.
  Lost, malformed, mismatched or newly warned replies never restore permission to resend it.
  Locale/client-surface changes, cancellation and repeated render notifications do not erase that
  record. A late reply may update its own record but cannot clear or replace a newer plan view.
- Session-local dispatched-plan records have a hard limit of 128 with no eviction. Request IDs
  and idempotency keys are independently unique and limited to 1024 each. Exhaustion fails closed.
  These records are an in-widget safety guard, not durable server idempotency or authorization;
  recreating the widget does not prove reconciliation or permit the server to execute again.
- Submitted, committed and unknown-result plans disable both review/revalidation and confirmation
  controls. Unknown results use explicit verification-needed copy, not a claim of no external effect.
- Capability identifiers are limited to the public contract's 160 characters before regex parsing.
- Plan identifiers obey the P15 total maximum of 124 characters, including the `plan_` prefix.
- `document_edit` artifact metadata is accepted only with the exact four public fields and their
  existing bounds. It is copied into a bounded projection; no URL, path, filename or download is added.
  A verified dry-run or queued acceptance still requires a null artifact. A committed revision may
  carry an artifact, but must differ from the immutable source revision.
- Parsing public `partial` and `unverified` outcomes is not permission to execute or claim success.
  A committed response that is not both `succeeded` and `verified` is `committed_unverified`:
  show a localized amber alert, retain the dispatch binding through cancellation and refresh, and
  disable repeat execution. Malformed or uncorrelated responses remain `unconfirmed`.
- Public summary, warning and capability-detail lengths use Unicode code points as JSON Schema
  specifies. They remain bounded and are neither displayed nor logged.

The response-contract repair is implementation-in-progress. The predecessor P15/P16-05 records and
the P16-06 visual/source contract still qualify their pinned checkpoint, not the later changes.
Current external captures do not silently replace those locks. Refresh the formal evidence after
the stored-plan integration and rerun current/independent full checks before closing this card.

## Prohibited input and effects

No raw XML, HAction, COM identifier, document body, file path, URL, credential, account data,
arbitrary backend, best-effort edit or signature-invalidating edit is accepted. The resource has a
closed CSP and uses no browser storage, cookies, network API, external asset or nested frame.

## Evidence classification

Local TypeScript, Python, browser, visual and CI checks prove only the component boundary on this
PC. Actual registered-host confirmation and server-side document execution remain unverified until
a later explicit account/UI session. No Hangul process or COM call belongs to this card.
