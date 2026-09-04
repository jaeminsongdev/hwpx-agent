# P15-05 artifact delivery report

- Generated: 2026-09-05
- Implementation and audited source commit: `dde79ff3fa86953c7f3e6e8e2402479eddee813e`
- Reasoning/review mode: `max` / strict authorization, credential, range and revocation audit
- Decision: `pass_scoped_current_pc_local_artifact_delivery_reference`

P15-05 connects the already-frozen `artifact_get` public contract to a bounded local artifact
delivery reference. `metadata` returns only the structured descriptor, `preview` places a
short-lived signed HTTPS URL only in client-only `_meta`, and `attachment` additionally returns one
model-visible MCP `resource_link` with an opaque `hwpx-artifact://` URI. Model-visible content never
contains a signed credential, document bytes, local path or encryption material.

This decision qualifies the current-PC reference implementation for the licensed Hangul 2020
development target. It does not qualify an HTTPS server, CDN/object store, production key custody,
transport streaming, a hosted ChatGPT/Codex client, or Hancom 2022/2024.

## Implemented behavior

- The P15-02 `artifact_get` input/output schema remains byte-identical. P15-03 still performs public
  user authentication, duplicate-key-free JSON parsing, schema validation, tenant/project policy,
  exactly one dispatch, output validation and request/resource correlation before delivery metadata
  is attached. P15-04 job metadata remains unchanged.
- Issuance requires the exact tenant/project/artifact binding and the P14 service rechecks tenant and
  authenticated-subject ACL. Preview/attachment additionally require `available` storage and
  `verified` validation state.
- The finite project binding registry is generation fenced. Revocation increments the generation;
  re-registration increments it again, so an already-issued URL cannot become valid again.
- A distinct HMAC-SHA256 reference token binds version, key ID, operation, tenant, project,
  artifact, subject digest, content SHA-256, semantic request digest, binding generation, issue time
  and expiry in one canonical order. Verification is constant time.
- TTL is restricted to the frozen public range of 30 through 900 seconds. The configured default is
  120 seconds and may be tightened but never widened above 900 seconds.
- Redemption rechecks signature, expiry, tenant, subject, current binding generation, current P14
  ACL/state and plaintext digest before returning bytes.
- Only one canonical `bytes=` range is accepted. Closed, open-ended and suffix ranges are exact;
  multiple/whitespace/noncanonical/reversed/zero-suffix ranges fail closed. Full and partial output
  are bounded to 64 MiB and partial output returns exact 206/`Content-Range` semantics.
- Signed-URL and byte owners zeroize their buffers on drop. Request, service-output and result Debug
  implementations redact credentials and content, including failure paths before a result exists.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `crates/mcp-control-plane/Cargo.toml` | 612 | `6e2c7d2b8a2a3c581114aba0c8cfbb5110c3157baaf717fb2b8748449e702bc5` |
| `crates/mcp-control-plane/src/lib.rs` | 1,085 | `8cfd804e56a7794519e7ebfe5970463ae165cd023674a74749785140534249a2` |
| `crates/mcp-control-plane/src/handler.rs` | 19,651 | `3ec5639b4508e2c891df9547ddce096dce861b339000fcbe1779d76739576133` |
| `crates/mcp-control-plane/src/artifact_delivery.rs` | 37,528 | `89865b110bd304f03ab2d9fa7c81bb074ead873f51b92b470792f46c7dc26915` |
| `crates/mcp-control-plane/tests/artifact_delivery.rs` | 23,289 | `cf7db5eb60f6511e9276162f02240ac0d43b91a25ab8246d0b0cfd2c76efe22a` |
| `implementation/p15/P15-05_ARTIFACT_DELIVERY_POLICY.md` | 4,305 | `782663db87eef1f46275f9aa8963edfb3e3bda18bba2cb0d477a1ce70f475963` |
| `implementation/p15/p15-artifact-delivery-contract-v1.json` | 7,147 | `df025b658d49991f80b392a8afa693c412ef14ad5e90c770356956405c7e42a5` |
| `tools/p15/build_artifact_delivery_contract.py` | 5,527 | `1ddf7a136061b497ece04aff15384b965ae842353a5aaae9ed43e20e6e057df3` |
| `tools/p15/validate_artifact_delivery_contract.py` | 12,138 | `c4b4e308574d4fbc86f15861931bec4e6b95b65ca2a4cdfa461bd1fb92306932` |
| `tools/p15/tests/test_artifact_delivery_contract.py` | 4,712 | `32cc6e88373523ab1c838c76cc1c2e86b2a3f9e4d97d180dd33c9b751c69c962` |

The generated P15-05 contract verifies 39 ordered source locks. The P15-04 generated contract remains
byte-identical with SHA-256
`311e9272373da0129693ad87c8a42e1e6c56b17b34ccb1312eed630b7f049c32`; its validator permits only
the exact historical P15-04 source blobs at `4c6224f6001c5daadaaaec907c0bba86db7c6c0f` when the current
P15-05 superseding validator passes.

## Validation

| Check | Result |
|---|---|
| Artifact delivery contract builder/check/validator | pass, 39 source locks, exact frozen `artifact_get` |
| Rust artifact delivery E2E/negative | pass, 13/13 on Windows and isolated Linux |
| Rust async/handler regressions | pass, 11/11 + 16/16 on Windows and isolated Linux |
| P14 artifact-service regression | pass, 21 library + 10 cleanup tests |
| All P15 Python tests | pass, 51/51 |
| Rust format/check/Clippy | pass, `-D warnings` |
| Current exact-commit full CI | pass, 5/5 lanes |
| Exact-commit independent checkout full CI | pass, 5/5 lanes; tracked changes 0 |
| Current security lane | pass, all checks exit 0; failed checks 0; SBOM 730 components |
| Independent-checkout security lane | pass, all checks exit 0; failed checks 0; SBOM 497 components |
| Offline Linux validation | pass, 13 artifact + 11 async + 16 handler tests and Clippy |
| Residual P15 containers / `Hwp.exe` | pass, 0 / 0 |

The current exact-commit security run is `4d6c6395f44945d6a5fc31988bf636f3`. Its Git-ignored report is
1,294 bytes with SHA-256 `f39486a2b2345e15e2a0b554de23f06b6b47aee4b7b74999f4cc208016aab0ca`;
the 717,264-byte SBOM SHA-256 is
`8ee6c4d9fc9d26aea6e46ee54cf938f96ee9085e410e3e46cd0726481879d0a2`.

The independent exact-commit checkout produced security run
`d859ecafee694f67823d623c84a7099b`. Its report and SBOM were copied without modification into the
main checkout's Git-ignored evidence area. The report is 1,294 bytes with SHA-256
`37d55444a93819e45c16f623efed8ffb759b5b012f5aacd70342a07b405e1499`; the 531,972-byte SBOM
SHA-256 is `e5a6caad1aa55899c6f582ade09ec718ab7a38ae5e1f0dad7659ad133eb6fd68`.

Offline validation used
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
with network disabled, read-only root/source/host Cargo registry, dropped capabilities,
`no-new-privileges`, and bounded memory/CPU/PIDs. Only bounded temporary Cargo and target filesystems
were writable, and only the target filesystem was executable. The independent checkout received
only four exact digest-matched, Git-ignored current-PC JSON records; no HWPX, PDF or user document
was copied.

## Strict review and diagnostics

- Change risk: `high`; this code carries authorization and time-limited credentials across the MCP
  response boundary.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review found that simple active/inactive project bindings could allow a revoked URL to revive after
  re-registration. The implementation now signs and rechecks a monotonically advancing binding
  generation and has an explicit revoke/re-register regression test.
- Review found that invalid URL input and an artifact delivery object rejected before result assembly
  could drop ordinary strings containing credentials. URL parsing now zeroizes before validation,
  and both the intermediate delivery object and final result zeroize the client-only URL on drop.
- Review found that the first base-URL validator admitted malformed authority/port shapes. It now
  rejects user info, nonnumeric or empty ports, query/fragment components and noncanonical path
  characters, with negative coverage.
- Two preliminary offline commands failed before compilation: the first used a login shell that did
  not retain the image Cargo path, and the second made the Rustup update directory read-only. The
  final run invoked the pinned installed toolchain directly with the host registry read-only and
  passed. Neither preliminary command is counted as validation evidence.
- No Hangul process, COM call, HWPX/PDF/user document, system setting or external delivery service was
  opened or changed for this card.

This card does not qualify production HTTP status/header adapters, streaming/positional object reads,
multi-process binding persistence, public key rotation, CDN cache policy, external URL resolution,
hosted MCP attachment behavior or production OAuth. Those remain unverified for P15-09/P16 and the
release Gates.

P15-05 may be checked. P15 remains in progress. Continue with P15-06 Error mapping at reasoning
effort `max`: freeze one stable public error catalog across auth/schema/policy/service/job/artifact
failures, prove no secret or internal detail leakage, and preserve the P15-03 through P15-05 ordering.
