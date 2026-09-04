# P15-01 authentication and tenant policy

## Scope

This card implements a bounded **resource-server authentication middleware** for the current-PC
local reference product. It does not implement an authorization server, login UI, dynamic client
registration, a production JWKS client or a hosted MCP endpoint.

## Official OpenAI source basis

- Source: [Authentication – Plugins](https://developers.openai.com/plugins/build/auth)
- Retrieved and reviewed: 2026-09-04
- Applied requirements:
  - Customer-specific data and write actions require authentication.
  - Authenticated MCP servers use OAuth 2.1 and publish protected-resource metadata.
  - The resource identifier is carried through OAuth and verified as the token audience.
  - The resource server verifies signature, issuer, audience, expiry/not-before and scopes on every
    invocation.
  - Public MCP clients use authorization-code flow with PKCE `S256`; that client-side flow is not
    implemented by this middleware.
  - ChatGPT/Codex user OAuth is separate from machine-to-machine credentials. Internal service
    tokens in this card are never accepted by the public MCP boundary.

The official guide recommends an established identity provider rather than a new authentication
server. Accordingly, the crate verifies and maps identities but does not mint production user tokens.

## Exact local contract

- Canonical resource and protected-resource metadata URLs are exact HTTPS strings. The middleware
  performs no trailing-slash, case, port or path normalization.
- Public MCP authentication accepts only `token_kind=user`, header `typ=at+jwt` and the exact
  `Authorization: Bearer <token>` shape.
- The local deterministic verifier supports only `HS256` with 32–128 byte in-memory keys. This is a
  test/reference adapter, not production OAuth evidence. Production remains disabled until an
  established IdP and asymmetric JWKS verifier pass staging.
- Claims are closed JSON objects: `iss`, `sub`, exact single `aud`, `exp`, `nbf`, `iat`, `jti`,
  `scope`, `token_kind`, `tenant_id` and optional `service_id`. Unknown, duplicate or multi-audience
  forms fail closed.
- The untrusted external `sub` is never retained. `(issuer, subject)` is length-framed and SHA-256
  mapped to the internal `SubjectDigest`, then joined to one immutable tenant grant.
- A token tenant hint must equal that registered grant. Token scopes must be a subset of registered
  scopes, and handler-required scopes must be a subset of token scopes.
- Tenant roles impose a second scope ceiling: readers are read-only, editors cannot manage retention,
  owners may receive all declared scopes, and workers receive only the internal execution subset.
- User access tokens are reusable bearer credentials until expiry or revocation, with maximum lifetime
  3600 seconds. Internal service tokens are maximum 300 seconds and single-use by `(issuer, jti)`.
- In-memory registries are capped at 64 signing keys, 4096 principals, 8192 live revocations and
  8192 live consumed service tokens. Expired revocation/replay records are pruned before capacity is
  evaluated; exhaustion fails closed without eviction of a live security record.
- Revocation stores only exact issuer/token-ID pairs and conservatively retains them for the maximum
  user-token lifetime plus clock skew; callers cannot shorten a live revocation. Diagnostics never
  contain raw bearer tokens, signing keys, external subjects, tenant IDs or subject digests.
- P15 is the authenticated successor for the `.gitignore`, workspace `Cargo.toml` and `Cargo.lock`
  changes. P14-08 and P14-09 keep their original source hashes and validate those exact historical
  blobs at implementation revisions `8d03bb6b4fb69e73f8921aa26484b400dadf941b` and
  `1d5de34121a8ba7cb9fc651cb90d63d7973db2dc`; the current files and both P14 validators are instead
  pinned by the P15 contract. This preserves evidence history without rebasing an earlier gate.

## Failure policy

Malformed header/token, unsupported algorithm, unknown/inactive key or principal, signature failure,
issuer/audience/tenant mismatch, expired/not-yet-valid/future/overlong token, invalid/insufficient
scope, revoked token, service replay, registry exhaustion and user/service boundary confusion are
typed failures. No
authenticated context is returned and no service-token replay marker is committed before every other
check passes.

P15-06 will later map these internal typed failures to the stable public error envelope. P15-02/03
will publish per-tool `securitySchemes`, protected-resource metadata and MCP authentication results.

## Explicitly unverified

- OAuth authorization-code/PKCE execution, CIMD/DCR, callback issuer validation and login UI.
- Production IdP configuration, remote JWKS retrieval/cache/rotation and asymmetric JWT algorithms.
- Hosted HTTPS, mTLS/OpenAI client identity, workspace-domain restrictions and refresh/revocation
  propagation.
- Production secret storage, multi-process replay storage, service-account lifecycle and incident
  recovery.
