# P17-06 checkpoint intent binding v5

Date: 2026-09-06
Scope: current-PC local-sync state, CLI and injected private adapter
Decision: **host prerequisite implemented; P17-06 remains in progress**

The checkpoint path now carries the required P15 `label` and optional `note` through the CLI,
state machine and private adapter. It uses private request v3 and keeps the exact project, branch,
mirror and expected-head binding. The optional note field is omitted when absent.

Before remote I/O, the local mirror writes the idempotency key and SHA-256 of the exact encoded v3
request into local-mirror v5. A retry must reproduce both values. Changing label, note or any other
bound request field under the same key fails locally without calling the port. The append-only
journal stores neither label nor note; public CLI and Debug output expose only bounded booleans.

Clean v1-v4 snapshots migrate to v5. A legacy pending checkpoint is rejected fail-closed because
its original metadata cannot be reconstructed. Unavailable and invalid-response outcomes retain
the pair; definitive rejection, validated conflict and validated success clear it together.

The private contract is `protocol/private/p17-remote-sync-adapter-v3.json`. Breaking remote and
local-state rules are recorded in `protocol/migrations/p17-remote-sync-request-v2-to-v3.md` and
`protocol/migrations/p17-local-mirror-v4-to-v5.md`.

This increment does not implement the credential provider, real host transport, remote service or
MCP tool registration. It does not prove an actual remote transition, Hangul execution, production
authentication or P17-06 PASS.
