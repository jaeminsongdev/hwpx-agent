# P17-06 durable local sync CLI v2

Date: 2026-09-06
Scope: current PC, durable local-only mirror workflow
Decision: **second bounded increment implemented; P17-06 remains in progress**

The `local-sync` crate now persists its validated mirror state in a bounded immutable journal. Every
entry has a monotonic sequence, a previous-entry checksum, a full validated mirror snapshot and its
own checksum. Publication uses a fixed sequence filename with `create_new`; two stale processes
cannot overwrite each other or both publish the same next sequence. Reopen verifies the complete
contiguous chain, byte/entry limits, regular-file boundary, schema, checksum and mirror invariants.
Unexpected, missing, gapped, oversized, linked or malformed entries fail closed. No repair or
deletion is attempted automatically.

Mirror snapshot v2 stores the remote-head snapshot digest separately from the current local
snapshot digest. This prevents an `ahead` mirror from accepting a same-head remote response whose
content digest drifted. The v1 migration accepts only a structurally clean snapshot, where the one
legacy digest is unambiguous; v1 `ahead` or `conflict` data fails closed instead of guessing a base.

The `local-sync` binary implements four local-only commands:

```text
local-sync init <state-root> <project-id> <branch-id> <mirror-id> <snapshot-sha256> <offline|online> [<revision-id> <generation>]
local-sync status <state-root>
local-sync set-connectivity <state-root> <offline|online>
local-sync queue <state-root> <snapshot-sha256> <operation-plan-sha256>
```

`status` never creates a missing store. Public success output is bounded JSON containing only the
command, durable sequence, connectivity, phase, observed generation and boolean state markers. It
does not echo filesystem paths, private IDs, digests or idempotency keys. Errors are stable codes on
stderr. The CLI integration test runs the real compiled process across `init -> queue offline ->
set-connectivity online -> status` and reopens the durable state between commands.

This increment passes ten state-machine tests, five durable-store tests and two real-process CLI
tests, plus all-target Clippy with warnings denied. That is valid current-host evidence for the
local offline/online transition and storage boundary only. The authenticated remote adapter and
the actual `pull`, `push`, and `checkpoint` CLI commands are not implemented yet, so P17-06 is not
PASS and no remote-service or Hangul execution is claimed.
