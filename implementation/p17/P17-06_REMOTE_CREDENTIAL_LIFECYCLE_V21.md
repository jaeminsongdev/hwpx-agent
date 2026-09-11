# P17-06 remote credential lifecycle v21

Date: 2026-09-11

Decision: **pure credential lifecycle component PASS; P17-06 remains open**

The new independent `remote-credential-lifecycle` crate implements one exact fail-closed state
machine for an externally issued remote-sync credential. `issue` starts only from absent state;
`refresh` starts only at the due boundary while the access token is unexpired and advances only the
token generation; `rotate` advances token and key generations; `revoke` accepts active state even
after token expiry and requires a distinct signed receipt before producing a terminal state.

Every request is deterministic bounded JSON. Its digest and complete prior non-secret state are
stored in a canonical pending value that must be persisted before dispatch. The pending value binds
the exact issuer, subject, audience, scope, ordered pinned-key identifiers and key digests, all
lifetime/skew/timeout limits, expected generations, prior credential digest, operation ID and time.
Retries reproduce the same bytes until the exact deadline. Only an authenticated definitive
rejection may restore the prior state; an unavailable or ambiguous result must retain pending state.

Issuer responses are bounded canonical unpadded compact JWS values. Only EdDSA with pinned Ed25519
keys is accepted. Access and revocation responses use mutually exclusive explicit `typ` values and
deny unknown/duplicate/non-canonical claims. Exact issuer, subject, audience, scope, operation,
request and generation bindings and bounded `iat`/`nbf`/`exp` rules are checked. The previous exact
token, previous `jti` and previous operation ID cannot be reused, and generation arithmetic is
checked for overflow.

Following RFC 6749 client-credentials renewal, no refresh token is modeled or stored. Raw access
tokens exist only inside a zeroizing verified value, can be borrowed only through lexical access,
and do not enter stable metadata, pending JSON, errors or `Debug` output. The component has no file,
network, registry, credential-manager or user-document side effect.

Fifteen locked/offline Rust tests passed on this PC. They cover happy paths, due/expiry/deadline and
clock boundaries, signature/key/algorithm/type/claim/generation drift, token and identifier replay,
complete policy drift, canonical and bounded JSON/JWS, definitive versus ambiguous outcomes,
terminal revocation, overflow-sensitive operations and secret redaction. Contract, migration,
validator, direct evidence and tamper tests bind the source and nonclaims.

The current crate deliberately stops at the atomicity boundary. An external issuer transport and a
trusted Windows broker that atomically persists pending state and updates Credential Manager plus
stable metadata are still required. No external issuer or network, real service credential,
registered host, production, P17-06 completion or product completion is claimed.
