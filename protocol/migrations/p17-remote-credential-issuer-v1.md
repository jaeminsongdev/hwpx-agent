# P17 remote credential issuer v1 migration

This private successor adds the issuer-side service component for the existing credential lifecycle
and `HWPXCIQ1`/`HWPXCIP1` wire. It does not change any public P00-P16 protocol and does not rewrite
the broker v22 evidence.

The issuer accepts only canonical lifecycle v1 request bytes with a request-bound canonical Ed25519
client assertion. It emits the existing canonical issuer response v1, so the pinned TLS client,
broker response parser and lifecycle verifier remain the compatibility boundary. Algorithm, token
type, key ID, identity, scope, time, JTI, request digest, generation, key generation and prior
credential state are exact and fail closed.

The new issuer log is not a broker log. It begins at sequence one in a dedicated plain directory,
uses a fixed sequence-only final filename, and binds every record to the complete issuer policy and
predecessor digest. Existing directories with unknown, linked, noncanonical, duplicate, gapped or
policy-drifted entries are rejected. Raw assertions, operation IDs and issued token/receipt bytes
are never stored in this log.

Compatibility and rollback:

- Existing lifecycle, broker, vault and pinned client state is not migrated or reinterpreted.
- Rolling back leaves the issuer log and operator-owned TLS/signing keys untouched for explicit
  reconciliation; no record is deleted or rewritten automatically.
- A different issuer policy, key set or signer key ID cannot silently adopt an existing log.
- TLS configuration is TLS 1.3 only. Loopback port zero exists only for qualification; explicit
  deployment requires a non-loopback, non-unspecified, non-multicast exact interface and nonzero
  port.
- Process-restart behavior is modeled, but power-loss durability, hostile privileged rewrite
  resistance and cross-system atomicity are not claimed.

External qualification remains a separate future operation. It requires an independently operated
host, exact DNS and endpoint, CA-issued TLS chain and protected TLS key, real client-assertion public
keys and client signer, protected issuer signing service/key, dedicated state directory and access
controls, firewall policy, distributed leaf pin, registered sync host, and an approved run/cleanup
plan. None of those inputs is inferred from the synthetic current-PC test.
