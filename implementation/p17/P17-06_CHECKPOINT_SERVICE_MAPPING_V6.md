# P17-06 checkpoint service mapping v6

Date: 2026-09-06
Scope: current-PC private checkpoint to P15 service-input boundary
Decision: **service mapping prerequisite implemented; P17-06 remains in progress**

`local-sync` now maps an exact private v3 checkpoint request to the existing P15
`project_checkpoint` input. Project, revision, label and optional note are preserved. Both
`expected_revision` and `revision_id` bind the private expected-head revision, `client_surface` is
fixed to `codex_local`, and the host supplies a schema-checked request ID and locale. An absent note
is omitted rather than encoded as `null`.

The P15 UUID idempotency key is a stable UUIDv5 over the canonical private project, branch, mirror
and idempotency-key identity. Changing a host correlation request ID or locale does not alter this
key or the service-intent digest; changing the mirror does. The service-intent SHA-256 excludes
correlation fields but includes all mutation fields, while a separate arguments SHA-256 covers the
exact canonical P15 JSON.

Branch ID, mirror ID, expected generation and the exact private request SHA-256 remain in a private
binding object outside the public P15 arguments. Debug output redacts all identities, label, note,
idempotency keys and digests. The new tests validate the actual mapped JSON against the embedded P15
Draft 2020-12 schema, cover stable retry/cross-mirror separation and verify redaction and invalid
context rejection. The complete `local-sync` suite passes 42 tests.

The machine contract is `protocol/private/p17-checkpoint-service-mapping-v1.json`; first-version
admission and future versioning rules are recorded in
`protocol/migrations/p17-checkpoint-service-mapping-v1.md`.

This increment does not implement authenticated mirror-registry verification, credential custody,
host transport, P15 service dispatch or an actual remote transition. It therefore does not prove
P17-06 PASS. The next increment is the authenticated host boundary that rejects a cross-mirror or
stale-head request before dispatching these mapped arguments.
