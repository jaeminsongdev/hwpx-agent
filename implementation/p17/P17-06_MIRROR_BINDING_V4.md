# P17-06 exact mirror binding v4

Date: 2026-09-06
Scope: current-PC private remote-sync request contract
Decision: **host prerequisite implemented; P17-06 remains in progress**

The private adapter now binds every pull, push and checkpoint request to the local mirror's exact
opaque `mirror_id`, in addition to its project and branch. This closes the gap between the P17
client request and the P14 server model, whose authorization and state transitions are keyed by an
exact tenant-owned mirror. The response hash covers the encoded v2 request including this field.

Request v1 is not accepted by a future v2 host and no fallback derives a mirror from project and
branch. Project, branch and mirror values remain absent from public CLI output and redacted from
Debug. The response contract remains v1 because its shape is unchanged. Migration and negative
requirements are recorded in `protocol/migrations/p17-remote-sync-request-v1-to-v2.md` and the
digest-pinned private contract is `protocol/private/p17-remote-sync-adapter-v2.json`.

This increment does not provide a credential provider, host transport, remote service, MCP tool or
production authentication. It does not claim an actual remote transition, Hangul execution or
P17-06 PASS. The next increment must implement a qualified host that authenticates `mirror.sync`,
checks the exact project/branch/mirror ownership triple, and rejects v1 and cross-mirror requests
before the CLI can stop using its fail-closed port.
