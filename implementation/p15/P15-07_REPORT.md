# P15-07 rate limit and quota report

- Generated: 2026-09-05
- Audited source commit: `e15921a59d45056c46b8ae94b6f6af778746c534`
- Foundational implementation commit: `91e84f41f99599fdbc8944ccc8355d9fed2357d8`
- Checkout-independence repair commit: `e15921a59d45056c46b8ae94b6f6af778746c534`
- Reasoning/review mode: `max` / strict quota-accounting, concurrency and leakage audit
- Decision: `pass_scoped_current_pc_hancom_2020_local_quota_reference`

P15-07 implements one digest-pinned, bounded in-memory quota service at the public MCP handler
boundary. Every admitted request is accounted across tenant, user and capability dimensions; the six
durable asynchronous tools are additionally accounted against either the standard or render job
class. Authentication, unique-key JSON parsing, input-schema validation and policy authorization
still precede quota admission, while exactly one gateway dispatch remains possible after admission.

This decision qualifies the current-PC local reference implementation for the licensed Hangul 2020
development target. It does not qualify a distributed quota store, multi-process global fairness,
production HTTP deployment, hosted MCP traffic, production telemetry, or Hancom 2022/2024.

## Implemented behavior

- The embedded policy is accepted only at its exact SHA-256 and closed schema. It fixes a 60-second
  integer token-bucket window: tenant `120/120`, user `60/60`, capability `30/30`, standard job class
  `8/8`, and render job class `2/2` capacity/refill tokens per window.
- All applicable dimensions are refilled and evaluated under one bounded mutex. A request consumes
  one token from every dimension only when all dimensions can admit it; quota rejection never
  partially charges tenant, user, capability or job-class state.
- Capability buckets use a digest of the already schema-validated `capability_id` when present and a
  digest of the frozen public tool kind otherwise. Bucket keys and token counts never enter public
  output or the service Debug representation.
- `document_create`, `document_edit`, `document_transform` and `document_validate` use the standard
  job class. `document_render` and `document_export` use the separately bounded render class. Other
  tools retain their P15-03 through P15-05 behavior without a job-class bucket.
- Exact replay of an admitted durable submission is keyed by tenant, subject, tool and idempotency
  key and is not charged again. Reusing the key with a different normalized payload is a stable
  `REQUEST_CONFLICT`; request correlation alone is excluded from the fingerprint.
- Replay state expires after 900 seconds and is bounded to 65,536 entries. Bucket state is separately
  bounded to 65,536 entries. Capacity exhaustion, poisoned state, invalid configuration and clock
  regression all fail closed without dispatch.
- Exhaustion returns the additive `QUOTA_EXCEEDED` public error at stage `quota`, with only an exact
  bounded `_meta["hwpx/retryAfterSeconds"]`. Unavailable accounting returns `QUOTA_UNAVAILABLE`.
  Every result carries `_meta["hwpx/quotaPolicySha256"]`.
- The immutable P15-06 v1 error catalog and digest remain historical evidence. The additive v2
  catalog contains exactly 16 sorted codes and is schema validated without weakening any earlier
  public mapping.
- P15-07 source locks hash the explicitly enumerated text sources after newline canonicalization.
  CRLF and LF checkouts therefore have the same identity while any semantic byte drift still fails
  closed.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `protocol/mcp/p15-quota-policy-v1.json` | 895 | `aec54a5fa7f25c91ffa86d1d3a677c41ee68b1d3c974d21c734bad59ac19fd95` |
| `protocol/mcp/p15-public-error-catalog-v2.json` | 4,557 | `ac1eaf53e79f70a7bf35ba8aafa5e8f3e684a2a0df378a02fa1194384e31e849` |
| `crates/mcp-control-plane/src/quota.rs` | 20,516 | `7e01dcb4431aa801179db48e84e7d22e88b341c0b164664f75aea454e0fa2cb4` |
| `crates/mcp-control-plane/src/handler.rs` | 22,598 | `aa9925cdc8b508980225c99d3386f1797422e974e631c8e63055326e78b97f85` |
| `crates/mcp-control-plane/src/error_catalog.rs` | 17,964 | `9f41149710b5fd3cb507969ce5c23c975bdb6eac405aecd06d5646a5d84f99e2` |
| `crates/mcp-control-plane/tests/quota_service.rs` | 16,307 | `0ec1ed30f84ac30d1be3edf15eb31f61f5e31cb6b5d26981afcc6f1f80c1856a` |
| `implementation/p15/P15-07_QUOTA_POLICY.md` | 3,847 | `17b2775ef87e72c5083eb20f42a8b1ef40160c179a6b3ded2d18205fb5caeb7c` |
| `implementation/p15/p15-quota-contract-v1.json` | 8,570 | `787f88e79b0b1aa1dff483237cf60e9a30526ab686481ec779fe04a3cd3db872` |
| `tools/p15/build_quota_contract.py` | 7,008 | `5a9a625b5ca4c1e7684e4fdca3d2787348ff51515c94e635a62d5ecb57430f8f` |
| `tools/p15/validate_quota_contract.py` | 19,645 | `3dbc9cb1f85f93f27a376d5178666d74413ce9f045c2d552d861f6d550952d2d` |
| `tools/p15/tests/test_quota_contract.py` | 6,202 | `9f6102c984041caca6d7bea12e7a2bd332b72f63c4d371bbf1a591e1c758ffdb` |

The generated P15-07 contract verifies 36 ordered source locks. It pins the quota policy digest to
`aec54a5fa7f25c91ffa86d1d3a677c41ee68b1d3c974d21c734bad59ac19fd95`, the additive v2 error
catalog digest to `ac1eaf53e79f70a7bf35ba8aafa5e8f3e684a2a0df378a02fa1194384e31e849`, and the historical P15-06
contract digest to `ae33d499350ca53f55534744036fc5830e4748efe943482b90c9e063bf54bd8b`. The P15-01 through P15-06
contracts remain historical evidence and validate only through their exact supersession chain.

## Validation

| Check | Result |
|---|---|
| Quota policy builder/check/validator | pass, 36 ordered locks, 16 error codes, 2 job classes |
| Rust quota burst/fairness/replay/E2E | pass, 8/8 on Windows and isolated Linux |
| Rust artifact/async/handler/error regressions | pass, 13/13 + 11/11 + 16/16 + 5/5 on Windows and isolated Linux |
| All P15 Python tests | pass, 65/65 |
| P15-01 through P15-07 validators | pass, historical/current supersession chain intact |
| Rust format and Clippy | pass, `-D warnings` |
| Final exact-commit main checkout full CI | pass, 5/5 lanes at `e15921a` |
| Final exact-commit independent checkout full CI | pass, 5/5 lanes at `e15921a`; tracked changes 0 |
| Main security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 730 components |
| Independent security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 497 components |
| Offline Linux validation | pass, 53/53 Rust tests and Clippy |
| Residual P15 containers / independent worktree / `Hwp.exe` | pass, 0 / removed / 0 |

The main final exact-commit CI lanes passed in 10.923 seconds (`linux-core`), 60.910 seconds
(`windows-worker`), 3.682 seconds (`widget`), 547.064 seconds (`docs`) and 14.230 seconds
(`security`). Its security run is `083484febdfe4c9da63144c9d14d51e5`. The 1,294-byte report SHA-256
is `f95259b78033c7c03577792eff48c2dba4fb474e8592ee1e3774a2e70d98d450`; the 717,264-byte SBOM
SHA-256 is `c4da0e87fb93c624793ceebaa582810b0c96ec8e80eb0e11139880457ba40488`.

The independent checkout lanes passed in 55.436 seconds (`linux-core`), 59.402 seconds
(`windows-worker`), 3.928 seconds (`widget`), 566.910 seconds (`docs`) and 10.858 seconds
(`security`). Its security run is `5d822380283a407498c5534dce26463d`; the report and SBOM were copied
without modification into the main checkout's Git-ignored evidence area. The 1,294-byte report
SHA-256 is `32bab7abafe21db617abc3a0ca02be2824bfb545535f9b4ff128d9835a37cd8b`; the 531,972-byte SBOM
SHA-256 is `2fc3b4e670fc298dcb74169b08babf65f859cff28571c7af4ce469c8a7587042`.

Offline validation used
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
with network disabled, read-only root/source/host Cargo registry, dropped capabilities,
`no-new-privileges`, and bounded 4 GB memory, 2 CPUs and 256 PIDs. Only bounded temporary and target
filesystems were writable. The exact installed toolchain passed the 53 quota and predecessor tests
plus Clippy.

## Strict review and diagnostics

- Change risk: `high`; this code controls admission, fairness and dispatch at every public tool
  boundary.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- The first compile exposed a const string-matching mistake and stopped before product execution. It
  was corrected before the foundational implementation commit.
- Initial replay handling applied to `artifact_get` and intercepted its older delivery semantics.
  Replay accounting is now limited to the six durable submissions for which the public schema
  requires an idempotency key.
- Review separated the immutable 14-code P15-06 catalog from the current additive 16-code runtime
  catalog, strengthened the capability dimension to the validated capability ID, hardened replay
  clock regression and validator missing-file handling, and covered every `QuotaError` mapping.
- A repeated-rejection regression proves that a failed render-class request does not consume shared
  tenant, user or capability tokens. Concurrency testing admits exactly two simultaneous render
  winners at a fresh bucket and rejects the rest without dispatch.
- The first exact independent checkout correctly failed because the generated source locks had
  hashed CRLF working-tree bytes. The repair canonicalizes newline bytes in both builder and
  validator, adds an explicit LF/CRLF regression, rebuilds the contract, and passes full CI in a
  newly created independent checkout at the exact repaired commit.
- The independent checkout received only the four exact policy-pinned current-PC diagnostic JSON
  records. No HWPX, PDF or user document was copied.
- No Hangul process or COM call was started, and no HWPX/PDF/user document, system setting, external
  account or product service was opened or changed for this card.

This card does not qualify cross-process or cross-host quota coordination, persistent accounting,
production SLOs, hosted trace correlation, staging HTTPS behavior or external observability. Those
remain unverified for P15-08/P15-09 and the release Gates.

P15-07 may be checked. P15 remains in progress. Continue with P15-08 Telemetry at reasoning effort
`max`: define bounded tool/job/backend/capability SLI events, trace correlation, redaction and a
complete sample trace without weakening P15-01 through P15-07.
