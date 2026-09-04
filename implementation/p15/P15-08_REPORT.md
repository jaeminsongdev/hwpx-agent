# P15-08 bounded telemetry and dashboard report

- Generated: 2026-09-05
- Audited source and closure commit: `9f9c6932518175906842a2cbb5915a0fb96d0d49`
- Foundational implementation commit: `d492dc8badc64abc86d2d5ecb09901d58ac0d109`
- Reasoning/review mode: `max` / strict correlation, privacy, bounded-state and dispatch-order audit
- Decision: `pass_scoped_current_pc_hancom_2020_local_telemetry_reference`

P15-08 implements a digest-pinned, bounded in-memory trace collector around the public MCP handler.
Every public result commits one complete six-stage trace, and dashboard snapshots are deterministically
derived from the retained whole traces. Authentication, unique-key JSON parsing, schema validation,
policy authorization, quota admission, exactly one gateway dispatch, output validation and result
correlation preserve the P15-01 through P15-07 ordering.

This decision qualifies the current-PC local telemetry reference for the licensed Hangul 2020 target.
It does not qualify a network exporter, hosted dashboard, cross-process trace store, production SLO,
staging HTTPS transport, MCP Inspector connection, or Hancom 2022/2024 behavior.

## Implemented behavior

- The embedded policy is accepted only at its exact SHA-256 and closed shape. It fixes a maximum of
  2,048 complete traces and 128 capability routes per trace.
- Every retained trace contains the ordered hierarchy
  `mcp_request -> capability_plan -> job -> backend_execution -> validation_step -> artifact_commit`.
  Each span is explicitly `completed`, `failed` or `not_applicable`; missing work is never promoted to
  completion.
- When capacity is full, the oldest complete trace is removed before one complete replacement is
  appended. A partial trace is never retained.
- Request, job, execution, revision and artifact-evidence correlation values are process-salted
  SHA-256 digests. Capability identifiers use the same protection. The random process salt is not
  serialized, is redacted from `Debug`, changes on initialization and is zeroized on drop.
- The trace schema has no field for bearer tokens, arguments, content, tenant/project identities,
  filenames, paths, arbitrary backend strings or errors, or signed URLs. Caller classification is the
  closed current-scope enum `unattributed` or `local_reference`, not an invented production tier.
- Backend, job and validation values are reduced to closed enums. Invalid gateway output is discarded
  before telemetry observation and records a failed validation span after exactly one dispatch.
- Tool latency/count, job state, backend route, salted capability route and validation state SLIs are
  recomputed from retained traces in stable key order. Retained capacity and whole-trace evictions are
  included without a second unbounded index.
- Public results add only `_meta["hwpx/telemetryPolicySha256"]`. Internal trace identifiers and
  dashboard data do not enter public `structuredContent`, `content` or `_meta`.
- The immutable P15-07 contract remains historical evidence through an exact audited-commit and
  contract-digest supersession check. LF/CRLF checkout differences are canonicalized without accepting
  semantic source drift.

## Source identity

| Source | Bytes | SHA-256 |
|---|---:|---|
| `protocol/mcp/p15-telemetry-policy-v1.json` | 594 | `052607176a31b5bedda3210e27ddb35d92df1b5126d881219606fb8a960274d1` |
| `crates/mcp-control-plane/src/telemetry.rs` | 26,649 | `9c3f44e82b0550f5a22110d39e4835e538996614e7fdd42d4b9ce9babb5ae6a3` |
| `crates/mcp-control-plane/src/handler.rs` | 25,099 | `8ff8a1be4750b842558ea0c5047431d5cb5aa76fc8a5e0651525c3e107b9d99d` |
| `crates/mcp-control-plane/tests/telemetry.rs` | 18,897 | `45850cae105323ddb520ddf09334f714f86fa1cfb2da4c7e28f9269c64f201ca` |
| `implementation/p15/P15-08_TELEMETRY.md` | 4,305 | `3d0981904b573f596858e09751cbd2ff9d38e98879eee893ae83a22ac883a301` |
| `implementation/p15/p15-telemetry-contract-v1.json` | 7,730 | `9a0e32959a6129f316f609069e87e22f22fb68b11622935c7ca32c080f44e402` |
| `tools/p15/build_telemetry_contract.py` | 6,622 | `2e646512a2a292da42583e88fd3e7bbf693b94ab256628bf49df8e10448332ce` |
| `tools/p15/validate_telemetry_contract.py` | 16,086 | `d0d88b516307a38606a55614303fb5cf988238e1730eaac8b26e5e0bdd6bbf7a` |
| `tools/p15/tests/test_telemetry_contract.py` | 6,085 | `5224ef4f1a3ccd7abad11904d9f19a7ce55c5563bedc3b4ae9ede0d6ee26bf01` |

The generated P15-08 contract verifies 37 ordered source locks. It pins the telemetry policy digest to
`052607176a31b5bedda3210e27ddb35d92df1b5126d881219606fb8a960274d1`, the public tool catalog
digest to `94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001`, the P15-07 audited
source commit to `e15921a59d45056c46b8ae94b6f6af778746c534`, and the P15-07 contract digest to
`787f88e79b0b1aa1dff483237cf60e9a30526ab686481ec779fe04a3cd3db872`.

## Validation

| Check | Result |
|---|---|
| Telemetry policy builder/check/validator | pass, 37 ordered locks, 6 stages, 6 dashboard dimensions |
| Rust telemetry sample/privacy/bounds tests | pass, 8/8 on Windows and isolated Linux |
| Rust artifact/async/error/handler/quota regressions | pass, 13/13 + 11/11 + 5/5 + 16/16 + 8/8 on Windows and isolated Linux |
| All P15 Python tests | pass, 73/73 |
| P15-01 through P15-08 validators | pass, historical/current supersession chain intact |
| P14 Python regressions | pass, 132/132 |
| Design model | pass, 16 schemas, 609 features, 609 contracts, 190 WBS tasks, 0 errors |
| Rust format and Clippy | pass, `-D warnings` |
| Final exact-commit main checkout full CI | pass, 5/5 lanes at `d492dc8` |
| Final exact-commit independent checkout full CI | pass, 5/5 lanes at `d492dc8`; tracked changes 0 |
| Main security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 730 components |
| Independent security lane | pass, all checks exit 0; failed checks 0; forbidden licenses 0; SBOM 497 components |
| Offline Linux validation | pass, 61/61 Rust tests and Clippy |
| Residual P15 container / independent worktree / `Hwp.exe` | pass, 0 / removed / 0 |

The main exact-commit lanes passed in 12.703 seconds (`linux-core`), 73.355 seconds
(`windows-worker`), 5.090 seconds (`widget`), 988.990 seconds (`docs`) and 14.354 seconds
(`security`). Its security run is `350e011c3e7a408e917600613eb3a20c`. The 1,294-byte report SHA-256
is `e643bd6552f9c11db868e2bda26d0437f6cfb35e55c3360cacd351832ff5e9ab`; the 717,264-byte SBOM
SHA-256 is `a2479d2c40f80812f9708f4c78161f2727192bed5e2df8235b8f36a4883403e9`.

The independent checkout ran the same five lanes sequentially. Reaching its successful security lane
proves the preceding `linux-core`, `windows-worker`, `widget` and `docs` lanes completed, and the
aggregate process exited successfully. Its security run is `adb85123ef60434e8c4de2e630f91971`; the
report and SBOM were copied without modification into the main checkout's Git-ignored evidence area.
The 1,294-byte report SHA-256 is
`05c2e088090ecdcc7ba435ff0a8713d49405173687cc71aa3657bfc2b8bd7068`; the 531,972-byte SBOM
SHA-256 is `cbff3beee4c6f6d86ed9d2ab24d07a5cefaff9f391a19a221b2fba24e7207b59`.

Offline validation used
`hwpx-agent-rust-1.96-clippy:p03-08@sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`
with networking disabled, read-only root/source/host Cargo registry, dropped capabilities,
`no-new-privileges`, and limits of 4 GB memory, 2 CPUs and 256 PIDs. Only bounded temporary Cargo,
target, system temporary and Rustup temporary filesystems were writable. The exact installed
toolchain passed all 61 control-plane tests plus Clippy.

## Strict review and diagnostics

- Change risk: `high`; this code observes every public MCP request and handles internal correlation.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review corrected the initial caller classes from identity-like user/service labels to exact
  current-scope `unattributed`/`local_reference` classes, avoiding identity retention and unsupported
  production-tier claims.
- Review added zeroization for both the collector's long-lived salt and every copied per-request
  observation salt, while keeping all serialized identifiers one-way process-local digests.
- Review separated lifecycle state from result status, kept every trace structurally complete, and
  proved the invalid-output boundary records validation failure without retaining the invalid payload.
- A complete `document_create` sample proves all six ordered spans and all five correlation links.
  Negative tests cover pre-dispatch errors, public trace-ID exclusion, forbidden-value leakage,
  independently salted processes, capability routing, whole-trace eviction and strict capacity.
- The independent checkout received only the four exact policy-pinned current-PC diagnostic JSON
  records required by the existing P10 runtime validator. No HWPX, PDF, key or user document was
  copied.
- No Hangul process or COM call was started, and no HWPX/PDF/user document, system setting, external
  account or product service was opened or changed for this card.

This card does not qualify hosted retention, cross-host aggregation, percentile SLIs, alerting,
production OpenTelemetry export, staging HTTPS behavior or MCP Inspector interoperability. Those
remain unverified for P15-09 and the release Gates.

P15-08 may be checked. P15 remains in progress. Continue with P15-09 Inspector/staging at reasoning
effort `max`: implement a loopback-only authenticated HTTPS Streamable HTTP endpoint, preserve the
18-tool catalog and handler boundary, run strict MCP Inspector schema discovery and all 18 tool calls,
and retain bounded machine-readable staging evidence without promoting it to public deployment proof.
