# P15-03 public MCP handler report

- Generated: 2026-09-04
- Audited implementation source commit: `9e7ed73524be0049292fbdf45f2170df6f997fae`
- Reasoning effort: `max`
- Decision: `pass_scoped_current_pc_local_reference_handlers`

P15-03 implements one reusable, fail-closed Rust handler boundary for all 18 P15-02 public tools.
Every admitted call authenticates a public user, parses duplicate-key-free JSON, validates the exact
input schema, authorizes tenant/project access, dispatches once, validates the output schema and
checks result correlation before returning a bounded MCP-shaped result. This is an in-process
reference handler; it is not yet a hosted MCP server or a real service-adapter deployment.

## Implemented boundary

- `McpControlPlane` loads the embedded P15-02 catalog only when its exact
  `94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001` digest, all 18 tool
  names, exact OAuth scopes and all Draft 2020-12 schemas compile.
- Gross tool-name and 262,144-byte argument admission happens before authentication. For every known
  tool, public-user authentication and exact descriptor scopes are enforced before parsing JSON.
  Authentication failures include only the bounded OAuth discovery challenge.
- JSON parsing rejects duplicate keys at every nesting level. Unknown fields and every other shape
  violation are rejected by the frozen input schema before policy or service dispatch.
- `InMemoryProjectPolicy` is a finite local reference adapter: at most 4,096 projects and 16,384
  memberships, exact tenant bindings, reader/editor/owner access and indistinguishable missing,
  cross-tenant and non-member lookup behavior. State-creating tools require editor or owner access.
- `AuthorizedToolCall` contains the typed tool, authenticated context, request/project correlation,
  canonical argument digest and parsed value. Authorization headers, raw/canonical argument buffers
  use zeroizing owners; debug output redacts tokens, arguments, identifiers and digests.
- `ToolServiceGateway` is invoked at most once and only after auth/schema/policy success. It returns
  four stable categories and remains responsible for repository-level ownership of nested revision,
  artifact, job, plan and checkpoint identifiers.
- Returned structured content must satisfy the exact tool output schema. Request IDs always match;
  shared project/job/revision/release identifiers also match. Invalid or mis-correlated service
  output is discarded and replaced by a safe error.
- Success and error results have bounded MCP shapes. Error messages never reflect backend errors,
  schema diagnostics, tokens, paths or document content. P15-06 will freeze the complete public error
  catalog.
- The pinned `jsonschema 0.53.0` crate has default features disabled. Its OSI-approved `MIT-0`
  transitive license is explicit in both repository allowlists, and those policies are source-locked.
- The P15-03 contract locks 19 source/policy files. P15-01 historical Cargo/auth-validator hashes are
  preserved at commit `8ac8d74a0f7795315d2dc2e0573f6b9a3a4e11e9`; the old validator accepts current drift only when
  that historical blob and the complete P15-03 superseding contract both verify.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `crates/mcp-control-plane/Cargo.toml` | 586 | `65b597b7fe8b2900af730506cf88e0df9563288dde0f8aeebc40852ef0b0e13f` |
| `crates/mcp-control-plane/src/catalog.rs` | 7,712 | `69860323b71de2f2f1836fa90a78a41b44dd8a5016f9211a4d7f7e06373952cf` |
| `crates/mcp-control-plane/src/handler.rs` | 16,308 | `652c9d214590d60cc466769918b801eac89743a70db4a0eeef02677a3f4668ae` |
| `crates/mcp-control-plane/src/policy.rs` | 6,158 | `32513728470e18608d1eeff419e83ece628d6a9c4dd2a948c1c95012e97412ac` |
| `crates/mcp-control-plane/src/strict_json.rs` | 3,096 | `f8c4e72cb8afa4c9df37259e6b9e143dbdada228cbf9456bad8a26360ac8a882` |
| `crates/mcp-control-plane/tests/handler_contract.rs` | 24,778 | `854d15c3b906793e4c55ed636797e531c439bba921e8d3713565419c811d9714` |
| `implementation/p15/P15-03_HANDLER_POLICY.md` | 4,226 | `a7187644aec3cc9a449e86285dd3455ce0e759351b5ea25a8a813a77d3f99ba0` |
| `implementation/p15/p15-handler-contract-v1.json` | 3,739 | `f79dfeac599b11a122569e1796d428298f341f53f91d3893460c6d7c1d704f0a` |
| `tools/p15/build_handler_contract.py` | 4,126 | `3de82fb4ead944867aa997d75168950ae603300dd395a9f183f433755fbc4e88` |
| `tools/p15/validate_handler_contract.py` | 7,116 | `e0303836546d4f9b0cb9a004fece9c9c7ea2eac56b78ec0c349d8e0573c8c20f` |
| `tools/p15/tests/test_handler_contract.py` | 4,224 | `3091497208e7d44794313fd7f035f44f2fa52b6c6900d17a48a8ce90d9914683` |

The generated contract carries exact digests for the complete 19-file source set, including
workspace dependency locks, P15-01/P15-02 contracts and both dependency-license policies.

## Validation

| Check | Result |
|---|---|
| Handler contract builder and validator | pass, 19 source locks, 9 ordered boundary steps, 18 tools |
| P15-03 Python contract/negative tests | pass, 7/7 |
| All P15 Python tests | pass, 37/37 |
| Rust handler contract tests | pass, 16/16 on Windows and offline Linux |
| Rust format/check/Clippy | pass, `-D warnings` |
| Current exact-commit CI | pass, 5/5 lanes |
| Exact-commit independent checkout bootstrap | pass, 5/5 lanes; tracked changes 0 |
| Current security lane | pass, every check exit 0; secrets/vulnerabilities/forbidden licenses 0; SBOM 730 |
| Independent-checkout security lane | pass, every check exit 0; secrets/vulnerabilities/forbidden licenses 0; SBOM 497 |
| Offline Linux handler validation | pass, 16 tests plus Clippy; network disabled and source/registry read-only |
| Residual P15 containers / `Hwp.exe` | pass, 0 / 0 |

The current exact-commit security run is `b420218579c14da8abb01272b7608e46`. Its Git-ignored report is
1,294 bytes with SHA-256 `865cab8e07c6af31d4347f3560e481c06473a63399d8520c7d81a7a6aa0bf9c3`;
the 717,208-byte SBOM SHA-256 is
`0e395ba8ce4f359a93f3b695f5368983ece5af7e2ce30395228b605c79ebb7ae`.

The independent checkout produced run `26afe21148484c55bfa4ab3b05967b4a`; its report and SBOM were
copied without modification to the same Git-ignored run path in the main checkout. The report is
1,294 bytes with SHA-256 `264aa8e96bf7495185e22f4618e24666015d2cc0621a9e92e524ea49235c9cd7`;
the 531,916-byte SBOM SHA-256 is
`c6d210327270accd5c6af33c22112013ac41a9b800a762b3284bbbc30a01cfa5`.

Offline validation used local image
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
It ran with `--network none`, a read-only root, source and Cargo registry, all capabilities dropped,
`no-new-privileges` and bounded temporary Cargo/target filesystems. The independent checkout received
only four exact digest-matched, Git-ignored current-PC JSON baseline records; no HWPX, PDF or user
document was copied.

## Strict review and diagnostics

- Change risk: `high`; every public tool now shares this authorization and dispatch boundary.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- The first all-P15 run exposed legitimate P15-01 Cargo/source-lock drift. The remediation did not
  rewrite old evidence: it verifies the historical commit blobs and requires the current P15-03
  contract before accepting the explicitly superseded paths.
- The first full security run rejected unlisted `MIT-0`. Both allowlists and the source-lock set were
  updated, after which Cargo license validation and the entire security lane passed.
- Two initial offline Docker launches stopped before compilation because of Windows mount quoting and
  a login-shell/rustup update-path mismatch. The final run pinned the installed toolchain directly and
  completed tests and Clippy under the intended isolation controls. Stopped launches are diagnostics,
  not product PASS evidence.
- No user document, original design ZIP, Hangul process, COM automation, system setting, hosted
  identity provider or external service was opened or changed.

This card does not qualify Streamable HTTP, an MCP SDK adapter, real database/object-store service
wiring, long-running progress/cancellation, artifact byte delivery, production OAuth/JWKS, MCP
Inspector, ChatGPT/Codex connection or any Hancom 2022/2024 behavior. Those claims remain unverified.

P15-03 may be checked. P15 remains in progress. Continue with P15-04 Async job UX at reasoning
effort `max`: bind long-running public calls to durable job IDs, ordered progress, safe cancellation
and one terminal receipt, then prove the polling/cancel/terminal flow end to end without Hangul UI.
