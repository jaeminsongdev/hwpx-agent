# P17 remote credential lifecycle v1 migration

## Change

The new `remote-credential-lifecycle` crate defines the fail-closed, transport-independent state
machine used to request, verify and reconcile externally issued remote-sync credentials. It adds
canonical bounded request and pending-state schemas for issue, refresh, key rotation and signed
revocation. Pending state binds the complete prior non-secret state and the complete verification
policy, including ordered key identifiers, key-material digests and every lifetime bound.

Client-credentials renewal requests a new access token and does not model or store a refresh token.
Access and revocation JWTs have distinct explicit types, use only pinned Ed25519 verification keys,
and bind issuer, subject, audience, operation ID, request digest and exact generation counters.

## Compatibility

This is a new private component and does not migrate an existing persisted credential record. Raw
tokens are held only in zeroizing memory and are absent from stable state, pending JSON, errors and
`Debug`. A trusted broker must durably store pending state before dispatch and atomically pair vault
secret changes with stable-state changes; that broker/vault adapter is not implemented by this
migration.

## Rollback and upgrade

Removing the crate restores the prior state because no product runtime consumes this component yet.
Any schema, claim, algorithm, key-set or lifetime-policy change requires a successor contract and
explicit migration. Never reinterpret a v1 pending value under a drifted policy, and never roll an
ambiguous or unavailable issuer outcome back automatically.

No external issuer, network service, real credential, Windows vault/state transaction, registered
host, production behavior, P17-06 completion or product completion is claimed.
