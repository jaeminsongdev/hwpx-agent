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

## Prohibited input and effects

No raw XML, HAction, COM identifier, document body, file path, URL, credential, account data,
arbitrary backend, best-effort edit or signature-invalidating edit is accepted. The resource has a
closed CSP and uses no browser storage, cookies, network API, external asset or nested frame.

## Evidence classification

Local TypeScript, Python, browser, visual and CI checks prove only the component boundary on this
PC. Actual registered-host confirmation and server-side document execution remain unverified until
a later explicit account/UI session. No Hangul process or COM call belongs to this card.
