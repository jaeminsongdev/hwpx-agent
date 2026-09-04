# P14-02 artifact service report

- Date: 2026-09-04
- Implementation commit: `95f40ad`
- Decision: `pass_scoped_p14_02_local_disposable_postgres_and_local_blob_adapter`
- Review: `STRICT / max`, blocker/major/minor after correction `0/0/0`

## Delivered

- A Rust `artifact-service` crate with bounded, validated tenant/artifact/content/subject/media/file,
  encryption-key, scanner and quarantine types. Public serialization is canonical and cannot bypass
  constructor invariants.
- Tenant-scoped content-addressed object keys and a no-overwrite local encrypted blob adapter built
  on `SecureWorkspace`. Published and quarantined namespaces are separate, stored reads are
  containment checked, and quarantine relocation/restore uses create-new atomic hard links.
- AES-256-GCM encryption with a fresh random nonce and AAD that binds tenant, plaintext digest,
  plaintext size, media type, artifact kind and key reference. Plaintext, ciphertext and AAD
  digests are verified; key material is zeroized and only a bounded key reference is persisted.
- HMAC-SHA256 signed-URL policy that is HTTPS-only and binds tenant, artifact, content digest,
  subject, ACL generation, operation and expiry. Maximum TTL is 300 seconds, verification is
  constant-time, and an ACL change invalidates an older URL.
- Tenant-scoped ACLs with read/manage/quarantine permissions, last-manager protection and
  indistinguishable cross-tenant absence. Audit events exclude payload bytes and signed URLs.
- Scanner outcomes for clean, suspicious and unavailable states. Suspicious or unverified input is
  quarantined fail closed and cannot receive a normal download URL.
- PostgreSQL v2 artifact columns and `artifact_acl` with forced RLS, revoked public privileges,
  immutable encryption/scanner identity, deferred final-manager enforcement and ACL-generation
  invalidation. Legacy available/quarantined rows fail closed to orphaned while rollback-only state
  is retained for exact restoration.
- A guarded down migration that refuses destructive rollback unless the same session sets
  `hwpx_agent.allow_destructive_rollback=on`, plus a digest-pinned PostgreSQL 18.4 harness and 22
  SQL assertions per application.

## Actual PostgreSQL evidence

The authoritative Git-ignored receipt is
`implementation/p14/evidence/p14-02-postgres-artifact-audit-20260904T034433Z.json`:

- bytes: `1824`
- SHA-256: `4402f7bebd71e54996768b33e48ec202cae974e8d5e4d59fb5cf9145ccb36226`
- exact clean source revision: `95f40adb1d4112ff1e7a995302ec7c0164332164`
- migration contract SHA-256:
  `4ec7a76e861994c21769624524c91c87cfc0823d1c3fcebfac2c34b2ca1fb563`
- test harness SHA-256:
  `961ad7a8ef198e77ff5e5e8948260ec0fbda7f8761d017763c0d3cdaf4ec6416`
- prerequisite v1 migration SHA-256:
  `7c00f744993581448acb4b6d4d8a46f1ff03d108750da0afc671c3b5e2b0a78d`
- v2 up migration SHA-256:
  `202753fbd6f20f181b09bd6227766dfb808811bd4e734a4a418cb5bae4eaee56`
- v2 down migration SHA-256:
  `af04b1198d7c6f153cfc576036807bd1749746fcc17f480cd6d2d29d6a49f5ae`
- smoke fixture SHA-256:
  `26ed06c05035af1086d4657ecaa758197916db062e4f4e609abcce5aa5e2e59c`
- validator SHA-256:
  `7ed5e2e985bacb7cb9a14495a9c6d6104537857a7a142cdc3352abde853a5a5f`
- PostgreSQL: `18.4 (Debian 18.4-1.pgdg12+1)`
- image:
  `postgres:18.4-bookworm@sha256:7e6103cf85f88f7a0eddb3ec0b1ba8940eba098ed118ade25a729ca9daee5568`

The clean run applied v1 then v2 twice and ran all 22 SQL assertions after each v2 application. It
proved NOBYPASSRLS cross-tenant read/write denial, transaction-local tenant context, encryption and
scanner identity immutability, ACL-generation changes, last-manager rejection, quarantine state,
legacy fail-closed conversion and exact legacy state restoration. Rollback without the explicit
session gate was rejected; two explicitly gated disposable rollbacks and both reapplications
succeeded. No host port, host volume or container network was used, and the exact labeled container
was removed.

## Validation

| Check | Result |
|---|---|
| Contract validator | pass, 14 v2 columns / exact digests / 22 assertions |
| P14 negative/unit tests | pass, 12/12 artifact-contract tests; 25/25 combined P14 tests |
| Rust artifact service | pass, 21/21 |
| Rust secure-workspace regression | pass, 12/12 |
| Actual PostgreSQL apply and reapply | pass, 2/2 |
| Actual SQL smoke | pass, 22/22 per run, 2 runs |
| Cross-tenant denial | pass under NOBYPASSRLS and service repository tests |
| Rollback without gate | pass, refused 1/1 and schema retained |
| Explicit disposable rollback and legacy restore | pass, 2/2 |
| Current checkout `linux-core`, `docs`, `widget`, `windows-worker` | pass |
| Exact-commit clean clone lanes | pass after hydrating four Git-ignored, digest-pinned current-PC P10 evidence files |
| Offline Linux target tests/Clippy | pass, network disabled, source and Cargo registry read-only, `21+12` tests |
| Secret scan | pass, 835 files, findings 0 |
| Cargo deny/audit, pnpm audit/license, .NET vulnerable, SBOM | pass |
| Residual P14 containers / `Hwp.exe` | pass, 0 / 0 |

The exact-commit security report is Git-ignored at
`implementation/p01/evidence/security-runs/b1368be1158d450c9c5f544e3f33f096/report.json`, bytes
`1644`, SHA-256 `1276675843931667f6d7ccd1f9a7899b0eeb74ef6c0c00d3b86f65c9fd7a981b`.
All checks passed. `pnpm audit` timed out twice with successful cleanup and succeeded on attempt 3.
The SBOM contains 674 components.

An initially bare source clone correctly failed the P10 policy test because its four current-host
runtime evidence files are private and Git-ignored. The same exact commit passed after only those
digest-pinned files were hydrated into ignored paths. This is recorded as a local current-PC
evidence dependency, not treated as proof that a bare clone contains runtime qualification.

## Strict task decision and limits

P14-02's required artifact service exists and cross-tenant denial has both service-level and actual
PostgreSQL evidence, so only the P14-02 roadmap checkbox is checked. This does not close P14 and does
not qualify a production object store, production KMS/HSM, production HTTP download edge, malware
vendor, backup/restore, multi-host deployment or any P14-03 through P14-09 behavior.

The in-memory metadata repository and local filesystem blob adapter are deliberate current-stage
adapters. The SQL contract proves persistence invariants independently; wiring the service to a
production PostgreSQL transaction manager and external object store remains later integration work.
No Hangul process, user document, source fixture, registry/system setting or production database was
used by P14-02.
