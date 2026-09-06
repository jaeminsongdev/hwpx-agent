# P17 project continuity v1 to v2

The P16 continuity v1 request, snapshot, resource URI and render-tool descriptor remain valid for
read, refresh and checkpoint flows. They do not carry stale-head generations and cannot authorize a
conflict resolution. A v1 render request paired with a v2 snapshot, or the reverse, fails closed.

The P17 v2 successor adds one required `stale_head` member to the snapshot. It is `null` unless
`conflict_state` is `stale`. A stale value contains non-negative observed/current generations, an
exact positive `delta = current_generation - observed_generation`, a non-null current head, and one to three unique values
from `rebase_operation_plan`, `branch`, and `manual_merge`. Unknown fields, inconsistent generation
math, duplicate choices and empty choice sets are rejected.

Choosing a resolution changes no state. A second explicit confirmation calls
`project_conflict_resolve` with the exact project, displayed head revision, current generation,
selected enum and a new idempotency key. A successful response must rebind that exact revision in
addition to the request, project, generation and resolution, and is followed by
`project_open` and `project_history`; the UI does not synthesize a clean state from the mutation
reply. The resolution, open and history request IDs must all be distinct. There is no v2-to-v1
downgrade and no best-effort parsing.

The v2 UI is a local component until an authenticated host registers `project_conflict_resolve`.
An unregistered host rejects the call and the controller exposes only a bounded recovery error. The
component E2E therefore does not prove an actual remote conflict, concurrent Web/Codex operation or
P17-07 completion.
