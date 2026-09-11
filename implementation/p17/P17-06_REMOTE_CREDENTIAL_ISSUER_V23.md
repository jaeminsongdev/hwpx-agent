# P17-06 independently controlled credential issuer service v23

Date: 2026-09-11

Decision: **current-PC issuer-service component PASS; P17-06 remains open**

`remote-credential-issuer` implements the issuer side of the existing private lifecycle and wire
contracts. It accepts only canonical bounded lifecycle requests authenticated by a canonical Ed25519
client assertion. The assertion has an explicit type, exact key ID, issuer, subject, audience and
`credential.manage` scope; its `iat`/`nbf`/`exp`, lifetime, clock skew, JTI and exact request SHA-256
are verified before the request is admitted. A JTI may authorize only one request digest.

Issue, refresh, rotate and revoke share one state machine that is cross-checked against
`remote-credential-lifecycle`. Invalid generation, key-generation, prior-credential or terminal
state transitions are rejected before the token signer runs. The signer is an operator-supplied
boundary bound to one exact key ID; every returned Ed25519 signature is verified with the pinned
public key before a response can be emitted. Access and revocation JWS types, identities, scope,
operation, request digest and generations are exact.

Every accepted assertion is represented in an append-only canonical JSON log before its response
returns. The log binds the complete issuer policy, sequence, predecessor record digest, request
summary, before/after state, response digest and signing key ID digest while excluding the raw
assertion, operation ID, access token and revocation receipt. Same-assertion retries do not append;
fresh-assertion retries append a replay record and must reconstruct the byte-exact response.

The file store writes and syncs a same-directory temporary file, then publishes through a
no-overwrite hard link to one fixed sequence-only slot. This is important: a digest-bearing final
name would let two concurrent writers publish different records for the same sequence. A 32-writer
test now proves exactly one winner and 31 conflicts. Sequence, canonical encoding, predecessor,
policy, state transition, response and replay drift fail closed. The model covers ordinary process
restart and abandoned bounded temporary files; it does not claim directory-fsync or power-loss
durability, hostile administrator rewrite resistance, or a cross-system transaction.

`IssuerTlsServerConfig` can only construct TLS 1.3 server state from one bounded certificate chain
and key pair and exposes only the leaf SHA-256 needed for out-of-band pinning. The independently
bound listener distinguishes an explicit deployment endpoint from an isolated loopback
qualification endpoint, redacts endpoint/certificate/key details in `Debug`, and serves one
credential frame per accepted connection. A real `PinnedCredentialIssuerTlsTransport` completed a
synthetic loopback TLS 1.3 issue against this server and the existing lifecycle verifier accepted
the returned access token.

Focused locked/offline validation passed 17/17 Rust tests and Clippy with `-D warnings`. The tests
cover all four operations, exact and fresh assertion retry, JTI/request collision, authentication,
time, canonical JSON, policy/state drift, signer and append failures, durable reopen, history
tamper, abandoned-temporary bounds, concurrent publication, wire outcomes, TLS
configuration/bind rejection, pinned TLS
interoperation, bounds and redacted debug output.

Evidence is at
`implementation/p17/evidence/credential-issuer/p17-remote-credential-issuer.current-20260911.v1.json`.
The private contract, explicit migration, validator and mutation tests bind the exact source
markers, dependency versions, test inventory and nonclaims.

No externally operated process, deployment package, DNS name, CA certificate, real client
assertion, real service credential, external signer/HSM/KMS, external network, registered host,
power-loss run or operations review was available. The deployment qualification is therefore
`not_run`; external issuer, production, P17-06 completion and product completion remain false.
