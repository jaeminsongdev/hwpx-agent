# P17-07 local conflict resolver v2

Date: 2026-09-06
Scope: mirror-v5 compatibility successor
Decision: **local component remains implemented; P17-07 remains in progress**

The existing three local stale-head resolutions are unchanged. Their private contract now points to
local-mirror v5 so a checkpoint request digest can never be detached from its pending idempotency
key. Clean v1-v4 snapshots migrate to v5; a legacy pending checkpoint remains fail-closed.

The successor contract is `protocol/private/p17-local-conflict-resolver-v2.json`. The current
`local-sync` suite passes 39 tests, including the existing exact-head, zero-change rejection,
durable CAS and real-process CLI coverage plus the checkpoint request-binding regressions.

This compatibility successor is still local component evidence. It does not provide a registered
host tool, authenticated branch receipt, or actual concurrent Web/Codex conflict run and therefore
does not close P17-07.
