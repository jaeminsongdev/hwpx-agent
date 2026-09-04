# P15-06 public error mapping report

- Generated: 2026-09-05
- Implementation and audited source commit: `f36a07e988558b4481c50955a0f76bd69c516d9d`
- Foundational implementation commit: `81d0adcfd9b80ef5e597d9f677e1a60ea8858a8a`
- Reasoning/review mode: `max` / strict public-boundary, correlation and leakage audit
- Decision: `pass_scoped_current_pc_local_public_error_reference`

P15-06 freezes one digest-pinned public error catalog and maps every current Auth, Policy, Gateway,
Async-job and Artifact-delivery failure variant into a bounded `hwpx-agent.error/v2` envelope. The
public result contains only a stable code, category, safe message, retryability, stage, empty details
and one bounded recovery action. Raw internal errors, credentials, paths, tenant or subject identity,
document content and backend payloads never enter the public result or Debug output.

This decision qualifies the current-PC local reference implementation for the licensed Hangul 2020
development target. It does not qualify production HTTP status/header adapters, hosted MCP
transport, external identity infrastructure, production telemetry, or Hancom 2022/2024.

## Implemented behavior

- The alphabetically ordered 14-code catalog is loaded with duplicate-key rejection and an exact
  SHA-256 pin. Missing, malformed, duplicated, reordered or digest-mismatched catalogs fail closed.
- Every catalog entry fixes its category, retryability, allowed stage, safe message and single
  recovery action. Public failures can only be constructed through crate-owned typed mappings.
- Authentication still runs before argument parsing. Admission, authentication, parse and input
  validation failures receive a generated `req_server_<uuid>` correlation ID without reading or
  echoing an untrusted JSON request ID.
- After the frozen input schema validates, policy, dispatch, output-validation and correlation
  failures use the validated public `request_id`. The envelope and `_meta["hwpx/requestId"]` must
  match exactly.
- Client credential failures collapse to `AUTHENTICATION_FAILED`; server configuration, registry
  and capacity failures collapse to `AUTHENTICATION_UNAVAILABLE`. The public boundary therefore
  cannot be used as an authentication oracle.
- Missing and cross-tenant policy records are indistinguishable as `RESOURCE_NOT_FOUND`. Explicit
  authorization denial is `POLICY_DENIED`, while policy configuration/conflict/capacity failures
  are retryable `POLICY_UNAVAILABLE`.
- Gateway, async-job and artifact-delivery errors collapse into bounded missing, conflict,
  unavailable or rejected states. Parameterized internal values are discarded.
- Error mappings are exhaustive Rust matches. A new internal enum variant cannot compile until an
  explicit public mapping and acceptance evidence are added.
- Unknown raw tool names, bearer headers, raw arguments and server fallback correlation values are
  redacted from Debug output. The public envelope emits an empty `details` object and no trace.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `protocol/mcp/p15-public-error-catalog-v1.json` | 4,007 | `7f85fb7a5c116ba6a262a5595906ccf3abf23df28ab5a567551f6904121ee2b7` |
| `specs/error-envelope.schema.json` | 3,081 | `b360d2f581150791c9a605553f64349db0fda6686d4539ee5cece346e47a24eb` |
| `crates/mcp-control-plane/src/error_catalog.rs` | 16,474 | `1e77939f2ace14eab7b0a2b60a1aa7c3dc31181b919c28ccb1e0921b4bf23fef` |
| `crates/mcp-control-plane/src/handler.rs` | 20,037 | `5f38d16a0765998f6119f60cb2f84cf2207c6ae946784c7789f8497d50eb663c` |
| `crates/mcp-control-plane/tests/error_mapping.rs` | 7,243 | `ccc97909ca15a5ec3f124e048ef09ddb6a89a4725cf33dee6c70432290648cc1` |
| `implementation/p15/P15-06_ERROR_MAPPING_POLICY.md` | 3,256 | `35cd6db42b2154c89f79567d6d2f4bfd78dc3e75b6f92f3592ddaf71834209a8` |
| `implementation/p15/p15-error-mapping-contract-v1.json` | 6,674 | `ae33d499350ca53f55534744036fc5830e4748efe943482b90c9e063bf54bd8b` |
| `tools/p15/build_error_mapping_contract.py` | 5,835 | `4e3e3ac24dc59a56865c9a42454ffeb475b5bc85105632cc5c0c155755c83d3d` |
| `tools/p15/validate_error_mapping_contract.py` | 16,370 | `118e828955ede6deef120d525dd97fc4496c7c6d2619986f44195bad8815059f` |
| `tools/p15/tests/test_error_mapping_contract.py` | 5,286 | `e9c0f2197707b7a515718178c83d4753656fa79bee52f84ddb6391b4597aa585` |

The generated P15-06 contract verifies 32 ordered source locks. It pins the public catalog digest to
`7f85fb7a5c116ba6a262a5595906ccf3abf23df28ab5a567551f6904121ee2b7` and the compatible global
envelope schema digest to
`b360d2f581150791c9a605553f64349db0fda6686d4539ee5cece346e47a24eb`. The P15-03 through P15-05
contracts remain historical evidence and validate only through their exact supersession chain.

## Validation

| Check | Result |
|---|---|
| Error catalog builder/check/validator | pass, 14 codes and 32 ordered source locks |
| Rust error mapping negative/E2E | pass, 5/5 on Windows and isolated Linux |
| Rust artifact/async/handler regressions | pass, 13/13 + 11/11 + 16/16 on Windows and isolated Linux |
| All P15 Python tests | pass, 57/57 |
| P15-01 through P15-06 validators | pass, historical/current supersession chain intact |
| Rust format and Clippy | pass, `-D warnings` |
| Main implementation-content full CI | pass, 5/5 lanes at `81d0adc` |
| Final exact-commit independent checkout full CI | pass, 5/5 lanes at `f36a07e`; tracked changes 0 |
| Main security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 730 components |
| Final exact-commit independent security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 497 components |
| Offline Linux validation | pass, 45/45 Rust tests and Clippy |
| Residual P15 containers / independent worktree / `Hwp.exe` | pass, 0 / removed / 0 |

The main implementation-content security run is `031f1138246345bca00031ef82c938cf`. Its report is
1,294 bytes with SHA-256 `c3394a219cd41d59fd83e50e431d62a34e34760832588e34d19a4ae51da160f7`;
the 717,264-byte SBOM SHA-256 is
`cd931dbfe26eb17253752baa47d3034dbe98ea39c3bdcf00fad3beab12608814`.

The independent final exact-commit checkout produced security run
`7d153e4d01574f45999acd23c7ac85d6`. Its report and SBOM were copied without modification into the
main checkout's Git-ignored evidence area. The report is 1,294 bytes with SHA-256
`ea6504dda1101b034a80c3513030e5cde82eed05dfd9698a425cacda3c26932d`; the 531,972-byte SBOM SHA-256
is `8601408375ac29e44cbb01f0878c8a1cd902f4ac955b6d75fde9314c28343f97`.

Offline validation used
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
with network disabled, read-only root/source/host Cargo registry, dropped capabilities,
`no-new-privileges`, and bounded memory/CPU/PIDs. Only bounded temporary and target filesystems were
writable. The final commands invoked the exact installed toolchain and passed all 45 tests and
Clippy.

## Strict review and diagnostics

- Change risk: `high`; this code defines the information released at every public MCP failure
  boundary.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review found that a broadly constructible public-failure type could allow future arbitrary
  stage/code combinations. Its constructor is now crate-private and only typed mappings construct it.
- Review found that unknown raw tool names could enter Debug output. The handler now redacts them.
- Review found that malformed or empty catalog input could raise an unclassified validator
  exception. The validator now reports bounded validation errors.
- The initial P15-06 source locks included the mutable roadmap file. It was removed from the lock set
  so a card-closing checkbox cannot invalidate the immutable implementation contract; the final
  exact commit and independent checkout prove this repair.
- The independent checkout first stopped twice before tests because its Git-ignored runtime evidence
  subset was incomplete. After hydrating the four exact policy-pinned JSON records, the same exact
  commit passed all five lanes. No HWPX, PDF or user document was copied.
- Preliminary offline commands exposed a mount-quoting error, then a read-only Rustup temporary path,
  then a Rustup-proxy Clippy path. These occurred before the relevant check completed and are not
  counted as PASS. The final exact-toolchain commands passed.
- No Hangul process, COM call, HWPX/PDF/user document, system setting or external service was opened
  or changed for this card.

This card does not qualify production HTTP mapping, public trace exposure, multi-process catalog
rollout, production log retention, hosted MCP behavior or external observability. Those remain
unverified for P15-08/P15-09 and the release Gates.

P15-06 may be checked. P15 remains in progress. Continue with P15-07 Rate limit/quotas at reasoning
effort `max`: freeze tenant/user/capability/job-class limits and prove bounded burst handling,
fairness, retry guidance and fail-closed accounting without weakening P15-01 through P15-06.
