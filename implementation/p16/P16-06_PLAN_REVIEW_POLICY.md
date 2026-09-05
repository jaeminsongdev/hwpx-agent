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
- Any unsupported/unverified route, blocking warning, unknown signature effect or unverified dry-run
  sets `execution_allowed=false`.
- Revalidation is atomic from the UI perspective. Capability disagreement stops before dry-run;
  dry-run disagreement stops before execution.
- Execution requires separate review, acknowledgement and final click. A final click always repeats
  the checks; earlier successful revalidation is not cached as authority.
- Raw server errors, warnings, summaries, constraints and unverified reasons are parsed for bounds
  but never rendered or logged. A newly observed warning code, constraint or unverified reason that
  was not represented by the approved snapshot stops the flow.

## Prohibited input and effects

No raw XML, HAction, COM identifier, document body, file path, URL, credential, account data,
arbitrary backend, best-effort edit or signature-invalidating edit is accepted. The resource has a
closed CSP and uses no browser storage, cookies, network API, external asset or nested frame.

## Evidence classification

Local TypeScript, Python, browser, visual and CI checks prove only the component boundary on this
PC. Actual registered-host confirmation and server-side document execution remain unverified until
a later explicit account/UI session. No Hangul process or COM call belongs to this card.
