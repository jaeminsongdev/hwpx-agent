# P15-01 authentication and tenant report

- Generated: 2026-09-04
- Audited implementation source commit: `8ac8d74a0f7795315d2dc2e0573f6b9a3a4e11e9`
- Reasoning effort: `max`
- Decision: `pass_scoped_current_pc_local_reference_resource_server`

P15-01 implements a bounded, fail-closed authentication and tenant boundary for the local reference
product. It is a resource-server middleware, not an authorization server or hosted MCP endpoint.

## Implemented contract

- `auth-middleware` accepts only exact `Authorization: Bearer` JWT input and separates public user
  tokens (`at+jwt`) from internal single-use service tokens (`hwpx-service+jwt`).
- The local deterministic adapter verifies HS256 signature, exact issuer/key binding, one exact
  audience, expiry/not-before/issued-at/lifetime, token kind, tenant hint and scopes before returning
  an authenticated context. HS256 remains explicitly non-production.
- Unknown, duplicate and multi-audience claims fail closed. External subjects are not retained; a
  length-framed digest maps the issuer/subject pair to one immutable tenant grant.
- Eight typed scopes are constrained twice: token scopes must be a subset of the registered grant,
  and handler-required scopes must be a subset of the token. Reader/editor/owner/worker roles impose
  a separate scope ceiling.
- Key, principal, revocation and replay registries have finite product maxima. Live records are not
  evicted to make a request pass; exhausted registries return a typed capacity failure.
- Revocation retains an issuer/token-ID pair for the maximum user-token lifetime plus clock skew;
  the caller cannot shorten it. Service replay is consumed only after every other check succeeds.
- Debug and error output redacts signing keys, raw bearer tokens, external subjects, tenant IDs and
  internal subject digests.
- P14-08/P14-09 historical source hashes remain unchanged. Their validators read the exact old blobs
  from their implementation commits while the current `.gitignore`, Cargo workspace and validators
  are pinned by the new P15 contract.

The design follows the official [OpenAI authentication guidance](https://developers.openai.com/plugins/build/auth):
OAuth 2.1 protected-resource metadata, exact resource/audience validation, per-request token checks
and scopes belong at the resource server; production authorization and JWKS should come from an
established identity provider.

## Source identity

- P15 contract: `implementation/p15/p15-auth-tenant-v1.json`
- Contract SHA-256: `7bae38b349e394b53636462fe19cb8e1c057a35ab68e7c23161086af6400ad99`
- Rust source SHA-256: `3381470e4a4251a444d76e09652efc5563800dff45e18b9763c8eaaf777b658d`
- Policy SHA-256: `6c6bbb5505b00a186df3da7bfca520659f0a6684e7350c1cb9b529d2c0a5b796`
- Validator SHA-256: `b46ced237b1cf73ae706c99750d012b2e30ec1e34d4c86b535a629de1661c28a`
- Locked source files: `9`

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, 9 locked sources and 8 exact scopes |
| P15 negative/contract tests | pass, 13/13 |
| Auth Rust tests on Windows | pass, 17/17 |
| Auth Clippy | pass with `-D warnings` |
| Current exact-commit CI | pass, 5/5 lanes |
| Exact-commit independent checkout bootstrap | pass, 5/5 lanes; post-run tracked changes 0 |
| Current security lane | pass, every check exit 0; secrets/vulnerabilities/forbidden licenses 0; SBOM 681 |
| Independent-checkout security lane | pass, every check exit 0; secrets/vulnerabilities/forbidden licenses 0; SBOM 448 |
| Offline Linux | pass, network disabled, source/registry read-only, Clippy and 17/17 tests |
| Residual audit containers / `Hwp.exe` | pass, 0 / 0 |

The current exact-commit security report is Git-ignored at
`implementation/p01/evidence/security-runs/3f82a202558a4c81992be3a000842304/report.json`, bytes `1294`,
SHA-256 `2d63ba0c4fb9862a954e1bd5670fb08a5e5b45838206ab58dbeea55c266d2eb3`. Its
661686-byte SBOM SHA-256 is `5f696cc732713e2eba8702452492d3b8b2b95f45e2eb4a574b699bd12e50e23a`.

The independent checkout produced run `33df7052b6654725aa0795c3bcc22ef1`; its report and SBOM were
copied without modification into the same Git-ignored run path in the main checkout. The report is
1294 bytes with SHA-256 `ef4d0f0ddc37610c653c38a1e0bcf3196330b5ef97874d40b337976fbb511a12`;
the 476394-byte SBOM SHA-256 is
`e6393a51f8cc772ccd83ccc3475dec1a2ab329cefc26fd17a3e5e643bbaa9585`.

The Linux audit used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
Networking and the root filesystem were disabled/read-only; source and Cargo registry mounts were
read-only, with only temporary Cargo metadata and build output writable. Two setup probes failed
before compilation because a login shell reset `PATH` and then rustup attempted a read-only temp
write. The corrected fixed-toolchain command passed; neither setup failure is represented as product
evidence.

## Strict review and limits

- Change risk: `high`; later public MCP handlers will trust this identity and tenant boundary.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review corrections include finite registries, conservative revocation retention, role scope
  ceilings, closed contract keys, bounded source paths and a source-locked P14 supersession chain.
- No user document, original design ZIP, Hangul process, COM automation, registry/system setting,
  production identity provider or external service was opened or changed.

This does not qualify OAuth authorization-code/PKCE execution, an authorization server, production
JWKS validation/rotation, hosted HTTPS, refresh-token propagation, multi-process replay storage,
production secret custody, mTLS or an OpenAI-hosted connection. Those claims remain unverified.

P15-01 may be checked. P15 itself remains in progress. Continue with P15-02 public tool schemas at
reasoning effort `max` and freeze all 18 tool input/output schemas, annotations and snapshots before
implementing handlers.
