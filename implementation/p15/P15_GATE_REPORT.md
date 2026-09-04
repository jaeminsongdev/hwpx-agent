# P15 Remote MCP Control Plane Gate Report

- Generated: 2026-09-05
- Audited P15-09 exact acceptance source commit: `7ea2f84c244fe5bbd7926ba3f176dc5acafcf624`
- Audited P15-09 closure report commit: `b823b32f811b9eea97931e98f832b8a4cf3fc33e`
- Audit mode: `STRICT / max`
- Overall state: `pass_scoped_current_pc_hancom_2020_local_mcp_reference_and_inspector_staging`
- P16/P17 authorization: `authorized_current_pc_local_only`

P15-01 through P15-09 form one bounded public MCP reference boundary for the current PC's licensed
Hangul 2020 target. The phase now has typed authentication and tenancy, exactly 18 public tool
contracts, ordered handlers, asynchronous job semantics, ACL-bound artifact delivery, stable public
errors, quotas, privacy-bounded telemetry and a reproducible Inspector-qualified local HTTPS staging
transport. The Gate intentionally does not convert local/in-memory/synthetic evidence into hosted,
production, real-Hangul or provider proof.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P15-01 Auth/tenant | `pass` | exact resource/audience checks, immutable tenant mapping, 8 scopes, expiry/replay/negative tests | Production IdP, authorization-code/PKCE and JWKS rotation are unqualified |
| P15-02 Public tool schemas | `pass` | exactly 18 closed Draft 2020-12 input/output descriptors and snapshots | Provider registration and live client compatibility are later integration |
| P15-03 Handlers | `pass` | auth -> schema -> policy -> one dispatch -> output validation/correlation, 16 contract tests | Production service adapters are not wired |
| P15-04 Async job UX | `pass` | 6 long-running tools, durable local journal, ordered progress/cancel/terminal receipt | Production queue/database and cross-process writer are unqualified |
| P15-05 Artifact delivery | `pass` | ACL/state/digest recheck, opaque resource link, bounded range and expiry | External object store, CDN and hosted attachment resolution are unqualified |
| P15-06 Error mapping | `pass` | digest-pinned 14-code catalog and exhaustive secret-safe typed mapping | Production HTTP edge and distributed diagnostics are unqualified |
| P15-07 Rate limit/quotas | `pass` | tenant/user/capability/job-class buckets, retry guidance, replay and fairness tests | Distributed persistent quota accounting is unqualified |
| P15-08 Telemetry | `pass` | complete 6-stage traces, process-salted correlations, bounded deterministic dashboards | Exporter, hosted retention, alerting and production SLOs are unqualified |
| P15-09 Inspector/staging | `pass` | clean exact receipt: 18/18 tools and 8/8 fail-closed probes over loopback HTTPS | Public hostname/certificate, remote client and real backend execution are unqualified |
| Common phase constraints | `pass` | versioned generated contracts and supersession locks; typed negative fixtures; unverified claims explicit; source in-place writes 0; handoff recorded below | Other PCs, versions, providers and production remain deferred |

No P15 card introduced a new production database layout. Public schema and error revisions are
versioned, digest-locked and checked through their historical/current supersession validators; every
new boundary has malformed, unauthorized, cross-tenant, expiry, capacity or leakage negatives.

## End-to-end evidence chain

```text
bounded bearer + exact resource/audience
  -> immutable tenant/subject/scopes
  -> exact 18-tool descriptor and closed input schema
  -> tenant/project policy + quota
  -> one typed service dispatch
  -> output schema + request/resource correlation
  -> durable local job or ACL-bound artifact result
  -> stable public error envelope
  -> complete privacy-bounded trace/dashboard
  -> loopback HTTPS SDK transport
  -> MCP Inspector strict discovery + all-tool calls
  -> secret-free digest/status receipt
```

## Validation summary

- Every P15 card has a dedicated report under `implementation/p15/`, a versioned contract/policy,
  exact predecessor binding where applicable, typed negative fixtures and an explicitly scoped
  decision. All nine card reports exist at the audited closure commit.
- The final P15-09 exact clean receipt is 15,051 bytes with SHA-256
  `4cb414b842b24f50a1b9b9bb7705f9d291c260742d4aad1765d27e768d85cf4a`. It binds source commit
  `7ea2f84c244fe5bbd7926ba3f176dc5acafcf624`, exact 18-tool discovery/calls, 8 negative probes,
  temporary configuration deletion and graceful Node/Rust shutdown.
- P15 Python tests are `84/84`, including the final roadmap/contract closure regression. The Rust
  control plane and staging driver are `64/64` on Windows and network-disabled Linux. Node staging
  typecheck/build/tests pass `3/3`; P14 regressions remain `132/132`.
- Runtime/security source commit `81c1ef14f210e78df5bd6658aa6922ce528f4250` passed all five CI
  lanes in both the main checkout and a detached independent checkout. Both security lanes passed
  secret, advisory, license, dependency and SBOM checks with zero failed checks.
- Closure-contract commit `7ea2f84c244fe5bbd7926ba3f176dc5acafcf624` changed only one
  historical-roadmap supersession allowlist entry and its generated digest lock. Its P15 suite passed
  `84/84`, both current/superseding contract validators passed, and a new clean exact Inspector run
  passed before the closure report was updated.
- Offline Linux Rust 1.96.0 used a network-disabled container with read-only source and registry,
  dropped capabilities, `no-new-privileges`, 4 GB/2 CPU/256 PID limits and bounded writable temporary
  filesystems. Tests and Clippy `-D warnings` passed; the container was removed.
- The independent checkout received only four exact digest-pinned current-PC diagnostic JSON files,
  had zero tracked changes after CI, and was removed after its report/SBOM were preserved unchanged.
- Residual P15 containers, independent worktrees and `Hwp.exe` processes are `0/0/0`. No user
  document, original design ZIP, HWPX/PDF, Hangul UI/COM, public endpoint, external account or system
  setting was opened or changed by P15-09 or this Gate.

## Strict review

- Change risk: `high`; this phase defines the public network-facing operation boundary and carries
  authorization, tenant, document/job/artifact references and public diagnostics.
- Verdict: `approve_scoped_current_pc_hancom_2020_local_mcp_reference_and_inspector_staging`.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Remediations across P15 include exact issuer/resource/audience and token-kind separation, closed
  schemas, authentication-before-parse, one-dispatch semantics, immutable terminal receipts,
  generation-bound artifact revocation, stable redacted errors, atomic bounded quota state,
  process-salted/zeroized telemetry correlation, Host/Origin rebinding guards, request-ID exhaustion
  failure, clean child lifecycle and receipt-after-secret-cleanup publication.
- The initial Gate mutation was rejected because P15-08 had locked the mutable roadmap checkbox.
  The repair allows only that roadmap path to be superseded when the complete P15-09 contract passes,
  while all historical P15-08 source locks are still verified against its exact audited commit. The
  Gate was rerun only after generated-lock, 84-test and clean exact Inspector evidence passed.
- Dependency policy pins the official MCP SDK/transport and Inspector versions, disables Inspector
  postinstall, rejects vulnerabilities/forbidden licenses, and limits the MPL exception to the exact
  development-only `lightningcss` package/version graph. Cross-locale dependency diagnostics have a
  dedicated CP949 regression and fail closed without hiding policy errors.
- Component, in-memory, local-journal, synthetic-gateway and loopback HTTPS evidence was not promoted
  to a production identity provider, public service, distributed data plane, real document execution,
  external observability or ChatGPT/Codex attachment.

## Failure fixtures and residual risks

- Malformed/duplicate tokens and JSON, wrong issuer/resource/audience/tenant/scope, expiry, replay,
  inactive principals/keys, schema unknown fields, cross-tenant projects, duplicate dispatch,
  correlation drift, invalid gateway output, illegal job transitions, stale cancellation, artifact
  ACL/revocation/quarantine/range/expiry, unknown error mapping, quota burst/fairness/capacity/clock
  regression, telemetry leakage/eviction, hostile Host/Origin, wrong path/method, oversized body,
  plaintext HTTP and unclean process shutdown remain typed negative fixtures.
- Production authorization server/PKCE/JWKS, PostgreSQL/queue service adapters, object storage/CDN,
  distributed quota/telemetry, public certificate/DNS, hosted MCP deployment, real backend execution,
  ChatGPT/Codex registration and customer operations remain absent or unverified.
- P05 actual render and P10 security-module/production-isolation dependencies remain separate open
  Gates. P15 completion does not waive them or prove real Hangul document mutation.
- Hangul 2022/2024 and other PCs require separate evidence on those machines and are not implied by
  this current-PC decision.

## Phase decision

P15 is complete for current-PC Hangul 2020 local MCP reference development and Inspector-qualified
loopback staging. P16 and P17 may start in the same local scope. No public deployment, provider,
production, customer distribution, other-PC or other-version authorization is implied.

## Next exact task

Start `P16-01 Official docs lock` at reasoning effort `high`. Refresh only authoritative OpenAI/MCP
Apps SDK requirements for the current release point, record immutable source identities and freeze
manifest, resource, tool-metadata, CSP, file-flow and developer-mode obligations before creating a
plugin bundle or widget. Use `max` again for P16 security-sensitive implementation review and its
phase Gate.
