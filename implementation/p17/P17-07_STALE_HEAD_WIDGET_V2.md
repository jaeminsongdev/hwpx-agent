# P17-07 stale-head widget v2

Date: 2026-09-06
Scope: current PC, local MCP Apps graphical component
Decision: **second bounded increment implemented; P17-07 remains in progress**

The existing P16 continuity surface now has an explicit v2 successor. V1 request and snapshot
parsers remain exact and a v1 request cannot authorize a v2 result. V2 adds a bounded stale-head
record with observed/current generations, checked delta and a unique server-allowed subset of
`rebase_operation_plan`, `branch` and `manual_merge`. A stale record requires a non-null current
head. The migration contract is
`protocol/migrations/p17-continuity-v1-to-v2.md`; the machine-readable component boundary is
`protocol/private/p17-stale-head-widget-v1.json`.

The graphical surface displays only bounded generation numbers and already-truncated project and
revision identifiers. Selecting a resolution makes zero server calls. A separate confirmation is
required before the controller sends `project_conflict_resolve` with the exact displayed revision,
current generation, selected enum and a fresh idempotency key. The response must rebind the exact
request, project, revision, generation and resolution. A matching success never fabricates the new
state: the controller immediately calls `project_open` and `project_history` and accepts only their
exact, mutually consistent result. All three request IDs must be distinct. Cancellation,
cross-version input/result pairs, unknown
fields, inconsistent generation math, duplicated choices and mismatched replies fail closed.

The plugin widget package passes 144 tests, including all three resolution paths, exact revision
response rebinding and v1 regression.
The evidence contract passes four tests and rejects injected receipt fields, run-ID/path drift,
unregistered-host promotion, source drift and bundle drift.
The local headless Chrome MCP Apps iframe E2E selected `branch`, proved zero calls before the second
click, then observed `project_conflict_resolve`, `project_open`, `project_history` in that order. Its
receipt is under `artifacts/p17/stale-head-widget-runs/`. Static rendering at 1200x900 and 390x844
had no horizontal overflow and no console warning/error; screenshots are temporary QA artifacts
outside the repository.

This is graphical component evidence only. `project_conflict_resolve` is intentionally absent from
the current P15 public catalog and no authenticated host implementation, actual remote transport,
concurrent Web/Codex conflict or Hangul operation was exercised. An unregistered call is rejected by
the host without changing local state. P17-07 stays open until the P17-06 host transport exists, the
resolution tool is registered and each path is exercised against a real concurrent conflict.
