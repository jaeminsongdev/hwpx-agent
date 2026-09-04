# P15-09 Inspector/Staging Report

- Generated: 2026-09-05
- Foundational implementation commit: `3ea8e6b664f0d83cd065fd8c23d5ec3ba7b68a18`
- Runtime/security repair commit: `81c1ef14f210e78df5bd6658aa6922ce528f4250`
- Audited exact acceptance and closure-contract repair commit: `7ea2f84c244fe5bbd7926ba3f176dc5acafcf624`
- Audit mode: `STRICT / max`
- Decision: `pass_scoped_current_pc_hancom_2020_local_inspector_staging`

P15-09 exposes the existing P15 public control plane through one loopback-only HTTPS Streamable HTTP
endpoint and qualifies it with the pinned MCP Inspector CLI. The current-PC acceptance preserves the
P15-01 through P15-08 authentication, schema, policy, quota, telemetry, artifact and error boundaries
instead of reimplementing them in the Node transport. A persistent Rust process owns the real
`McpControlPlane` throughout the run, while a safe synthetic gateway prevents Hangul, document,
artifact and external side effects.

## Qualified acceptance receipt

The final clean exact-commit run published
`implementation/p15/evidence/staging-runs/9a4fe4d8a8e248ecb8e0117c0652ecd3/receipt.json` only after
the temporary Inspector configuration and public certificate were deleted and both the Node server
and Rust driver exited cleanly.

| Receipt field | Qualified value |
|---|---|
| Decision / qualifying | `PASS` / `true` |
| Source commit | `7ea2f84c244fe5bbd7926ba3f176dc5acafcf624` |
| Scope | `current_pc_hancom_2020_local_inspector_staging` |
| Transport | HTTPS, `127.0.0.1`, ephemeral port, `/mcp` only |
| Protocol | Inspector `2.5.0`, SDK `2.0.0`, selected `modern` |
| Discovery | exact 18 ordered tools, schemas, annotations and metadata |
| Calls | all 18 tools succeeded through the existing Rust control plane |
| Negative probes | 8/8 exact fail-closed outcomes |
| Lifecycle | persistent driver, graceful Node/Rust shutdown |
| Secret posture | runtime-only key/token/private key; no durable secret material |
| Hangul/document/artifact effects | `false` / none |
| Receipt identity | 15,051 bytes; SHA-256 `4cb414b842b24f50a1b9b9bb7705f9d291c260742d4aad1765d27e768d85cf4a` |

The negative outcomes were missing authorization `401`, invalid authorization `401`, wrong path
`404`, hostile Host `403`, hostile Origin `403`, wrong method `405`, oversized body `413`, and
plaintext HTTP rejection. The receipt stores result and metadata digests, never arguments, result
payloads, bearers, HMAC keys, private keys, absolute paths or document data.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `protocol/mcp/p15-inspector-staging-policy-v1.json` | 2,256 | `ecb285094c3f78bdb9dea3a2f9cd041431bc5960aa4d4775937c439ba7edfe1a` |
| `crates/mcp-staging-driver/Cargo.toml` | 547 | `b375e7fbe1c1cd37e6f4114dd0733e17c0df7aad77a764456a019e19781efde2` |
| `crates/mcp-staging-driver/src/main.rs` | 15,970 | `d6853d09020438baa043c4486f7363a8110bf433e1b9d9f831e564066daa3500` |
| `web/mcp-staging/package.json` | 496 | `9fc9440010f44f59d86438859fbd0319600301f155176f294914cb4ee337fd9e` |
| `web/mcp-staging/src/server.ts` | 25,166 | `52d95018609a4215abc1e48e85349ca474d8771ae727e6035bc3644e5df50cf8` |
| `web/mcp-staging/src/server.test.ts` | 1,987 | `82a32c79f781099ea3117c1584f6653e939c1e2ba59e71e37f022f6b4e073065` |
| `tools/p15/run_inspector_staging.py` | 29,123 | `30f1a35a3cf22b45beed41971400f6d9a97d6c25bbb937c81ed9dec51cd976c7` |
| `implementation/p15/P15-09_INSPECTOR_STAGING.md` | 3,916 | `f28c1db5daffb8bd8d2e827bae2d934e2aa402a7ff7221a1efb8f8389914d833` |
| `implementation/p15/p15-inspector-staging-contract-v1.json` | 6,658 | `09335ea42021c782f75010d7e873de11c36c834bb33ba8cafde529f824e3b907` |
| `tools/p15/build_inspector_staging_contract.py` | 6,422 | `f91c0c5a7fbd533dd1ac30f403168473a89c9cc54f88b4fd81a72cd60f7fe55d` |
| `tools/p15/validate_inspector_staging_contract.py` | 14,500 | `b52aa2e28ed0a6281d5df7e284169c56163994d09050ca2859888a8294734f87` |
| `tools/p15/validate_telemetry_contract.py` | 18,001 | `b4930d621a4c6cef48083ecc4ec150d614dddeeb76fe383900460ec9697b83b1` |
| `tools/p15/tests/test_inspector_staging.py` | 4,197 | `c89b49fb4a6d40fccef22bfcc0ac4088dc28fd11782b5fc650854991b3d0e7d2` |
| `tools/p15/tests/test_inspector_staging_contract.py` | 4,058 | `2777aa55d2aa8bd6997f802c97f9189675dca6dc70521f7f14ecdc74f0c79536` |

The generated contract verifies 33 ordered source locks. It pins the exact SDK/Inspector dependency
graph, transport and driver sources, the public 18-tool catalog digest
`94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001`, the P15-08 audited source
commit `9f9c6932518175906842a2cbb5915a0fb96d0d49`, and the P15-08 contract digest
`9a0e32959a6129f316f609069e87e22f22fb68b11622935c7ca32c080f44e402`.

## Validation

| Check | Result |
|---|---|
| Inspector staging policy builder/check/validator | pass, 33 ordered source locks |
| Exact clean Inspector acceptance | pass, 18/18 tools and 8/8 negative probes |
| Closure-contract roadmap regression | pass, P15 84/84 at `7ea2f84c` |
| Rust staging driver tests | pass, 3/3 on Windows and isolated Linux |
| Rust predecessor control-plane tests | pass, 61/61 on Windows and isolated Linux |
| Node staging tests | pass, 3/3; typecheck/build pass |
| All P15 Python tests | pass, 84/84 |
| P01 security regression tests | pass, 10/10 |
| P14 Python regressions | pass, 132/132 |
| Design model | pass, 16 schemas, 609 features, 609 contracts, 190 WBS tasks, 0 errors |
| Runtime/security source main checkout full CI | pass, 5/5 lanes at `81c1ef14` |
| Runtime/security source independent checkout full CI | pass, 5/5 lanes at `81c1ef14`; tracked changes 0 |
| Main security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 984 components |
| Independent security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 751 components |
| Offline Linux validation | pass, 64/64 Rust tests and Clippy |
| Residual P15 container / independent worktree / `Hwp.exe` | pass, 0 / removed / 0 |

The main exact-commit lanes passed in 13.529 seconds (`linux-core`), 84.418 seconds
(`windows-worker`), 5.588 seconds (`widget`), 1,537.594 seconds (`docs`) and 15.929 seconds
(`security`). Its security run is `3444d0c2bdc84ddab07f057a650075c5`. The 1,294-byte report SHA-256
is `e0689b696191dbe364c19613e2249666d6cf03fef84fc88b3b7711902cdf94e2`; the 1,021,008-byte SBOM
SHA-256 is `af920b7d22c051140a81bf0c22efac56802ba28ca8fbdf0b3c5c30a774033408`.

The independent exact-commit lanes passed in 58.914 seconds (`linux-core`), 65.131 seconds
(`windows-worker`), 5.650 seconds (`widget`), 1,521.979 seconds (`docs`) and 12.229 seconds
(`security`). Its security run is `fb950275eabc4112bb8cf655f231e486`; its report and SBOM were copied
without modification into the main Git-ignored evidence area. The 1,294-byte report SHA-256 is
`b25d8d1d4c3e1dd03136f029a636ffff6a5e467dd67f3a6bb0a9ec3934f62788`; the 835,716-byte SBOM
SHA-256 is `23ab693e1addb72792180b0f581f1bd33c3312dd3d1d85ffff6a16e133f87b61`.

Offline validation used
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
with networking disabled, read-only root/source/host Cargo registry, dropped capabilities,
`no-new-privileges`, and limits of 4 GB memory, 2 CPUs and 256 PIDs. Only bounded temporary Cargo,
target and system temporary filesystems were writable. The exact installed toolchain passed the 61
control-plane tests, 3 staging-driver tests and Clippy `-D warnings`.

## Strict review and diagnostics

- Change risk: `high`; this is the first network transport around all public MCP operations.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review made driver request-ID exhaustion fail closed, required clean driver exit, closed the Node
  SDK handler/server/driver in order, and prohibited receipt publication until graceful shutdown and
  temporary configuration deletion were complete.
- Request processing validates Host and Origin, exact path/method and bearer authentication before
  bounded JSON body parsing. The persistent Rust process keeps quota and telemetry state across calls;
  request/response framing, outstanding calls, bytes, timeouts, connections and lifetime are bounded.
- Dependency review pins exact SDK, transport, Inspector and certificate-library versions. Inspector
  postinstall execution is disabled. The only MPL exception is exact package/version-scoped to the
  development-only Inspector `lightningcss` transitive graph; it is not a global MPL allowance.
- The first full-CI attempt at the foundational commit reached four successful lanes but correctly
  failed security when Windows CP949 could not encode a dependency-license character. It is not
  counted as PASS. The security runner now emits cross-locale diagnostics with `backslashreplace`,
  has dedicated regressions, and the exact repaired commit passes both full CI reproductions.
- The first Gate mutation correctly exposed that P15-08 had historically locked the mutable roadmap.
  The Gate was not accepted in that state. The exact repair allows only that roadmap path to be
  superseded when the complete P15-09 contract validates, while still comparing every historical
  P15-08 source lock to its audited commit. The rebuilt 33-lock contract, all 84 P15 regressions and a
  new clean exact-commit Inspector acceptance pass at `7ea2f84c`.
- The independent checkout received only the four exact digest-pinned current-PC diagnostic JSON
  records required by the P10 runtime validator. No HWPX, PDF, key or user document was copied.
- No Hangul process, COM call, local UI, user document, artifact, external account, public endpoint or
  system setting was opened or changed for this card.

This card does not qualify public-internet deployment, production OAuth/JWKS or key custody,
distributed quota/telemetry, real backend execution, ChatGPT/Codex attachment, production submission,
or any Hangul 2022/2024 behavior. Those remain explicitly unverified.

P15-09 may be checked. P15 remains in progress until its separate phase Gate audit. Run the P15 Gate
at reasoning effort `max`, audit P15-01 through P15-09 and every common phase constraint, and authorize
only the current-PC local scope that the evidence actually proves.
