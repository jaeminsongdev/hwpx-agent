# P16-06 PostgreSQL artifact adapter: bounded continuation

- Date: 2026-09-05. Scope: current PC, disposable local PostgreSQL only.
- Worktree: `D:\개발\hwpx-agent-work-p16-plan-service`.
- Implementation HEAD: `217ba56cd8a88e4d3560a5735052b18880481ff4`; clean checkpoint, not integrated in main.
- Independent checkout: `D:\개발\hwpx-agent-audit-p16-postgres-217ba56`, same exact clean source.
- State: actual adapter acceptance PASS in both checkouts; overall FULL still FAIL at source qualification.
- Preserve previous failure reports and historical source contracts. No renderer/host/production PASS.

## Implementation and actual checks

Read `implementation/p16/P16-06_POSTGRES_ARTIFACT_ADAPTER.md` in the implementation checkout for the
product/API changes, exact limitations and complete retained failure sequence. Three repaired causes:
PostgreSQL bigint version decoding incorrectly used i32; a Docker restart reassigned the ephemeral
host port while the harness reused the old endpoint; and owner-role admission omitted SET capability.
All were corrected without weakening source/migration/RLS checks or rerunning business writes blindly.

- Windows and real offline Linux: artifact-service 35/35, formatting and all-target Clippy PASS.
- Harness tests: 5/5. Whole-workspace Rust lane: 485/485 and Clippy PASS in both checkouts.
- Actual DB acceptance: current run `5a68a12751804d6f84df2b42ebed2f11`, session 44354 terminal 0;
  independent run `a06f2d898dd943e89ab6353e0a6f331b`, session 65037 terminal 0.
- Current receipt SHA-256: `36a91a3b60ba27af0218987e7c1cb5b1a824259a76089a2cb8e4d0b71d71e4cc`.
- Independent receipt SHA-256: `abb65588445b5e3fc7446ccdb9e732b1d0a252acb332b4e491e92c88e8a17744`.
- Both cover encrypted store/readback and database restart, deduplication/conflict, stale ACL mutation,
  manager retention, quarantine/wrong key, cross-tenant isolation, exact role/policy/privilege rejection,
  immutable metadata, guarded rollback and exact source hashes unchanged. They do not cover the
  still-unimplemented durable Plan/source/renderer integration or crash-at-every-instruction recovery.

| Actual run | Result | Retained evidence |
|---|---|---|
| `73be1b04dcbc4cd0879de93c5956fe0e` | FAIL guarded empty rollback | Immutable migration-history trigger rejected deleting the v10 registration. |
| `e78573e5a5cc44a38e92e6a7bac5c40e` | FAIL seed, `STORAGE_FAILURE` | Guarded rollback/reapply and predecessor/trigger checks passed. |
| `afee7194223c4389900cfcd5fff57ac9` | FAIL seed, `STORAGE_FAILURE`, probe stage `CONNECT` | Same rollback checks passed; failure narrowed to repository connection/initial database verification, before seed lookup or ingest. |

Reports are under the worktree's `artifacts/p16/postgres-artifacts/runs/<run-id>/report.json`.
The earlier afee719 report SHA-256 remains `6384f387f213002bca3246046de4ca867fbce1500199e219bc9df4d39dbf5358`.
Additional failed runs and the owner-role failing-before/passing-after pair are retained in the
implementation report. None is deleted or reclassified as successful. No actual Hangul/host ran.

## Implemented repair and diagnostic boundary

The v10 down migration now disables the immutable-history trigger only inside the guarded rollback
transaction, removes only its own exact v10 registration, then restores the trigger before commit.
The harness checks identical predecessor rows, exactly nine retained registrations, enabled trigger
state, and a rejected predecessor-history mutation before reapplying v10. These passed twice.
This is not permission to alter any live or production database history.

The additive `connect_diagnosed` returns only TRANSPORT/ROLE/MIGRATIONS/POLICIES/PRIVILEGES and a
stable public category; `connect` preserves its original error interface. No raw backend source chain,
SQL, credentials or private identities are retained in diagnostic values. Negative checks require
the expected stage and ACCESS_DENIED; a network outage is not accepted as a security-control PASS.

Each run reports owned resources removed. A fresh read-only listing found no remaining container or
volume with the exact adapter-test label. Only owned disposable DB resources were removed; retained
reports and encrypted local test objects were not deleted. No Hangul window or user click is pending.

## Whole-checkout audit results and source-qualification hold

All listed handles are terminal. Do not poll or relaunch them unchanged.

| Evidence | Outcome and location |
|---|---|
| First current FULL 84481 | FAIL: four ignored P10 diagnostic JSON pins absent. Exact-hash records were then copied without overwrite; no user documents/keys copied. |
| Current FULL retry 54118 | FAIL: Rust/Windows/widget PASS, docs stops at P14 artifact source lock 3 (`crates/artifact-service/Cargo.toml`); security not reached. |
| Independent FULL 18353 | Same source-lock FAIL after Rust/Windows/widget PASS. Four P10 pins were already present. |
| Actual Linux 69697 | 35/35 + all-target/all-feature Clippy PASS; read-only source/registry, network none, bounded tmpfs; container removed. |
| Security 41295 | PASS: nine checks, no forbidden licenses/findings, SBOM 641 components. Duplicate-dependency warnings retained. |
| Independent P15 Inspector 51120 | PASS at exact clean 217ba56: eighteen tool calls/schema discovery, eight negative probes, graceful shutdown and temporary config deletion. Not actual host or durable Plan evidence. |

Logs live under each checkout's `artifacts/p16/postgres-artifacts/audit-217ba56/`:

- `full-current.log`: `6f577b854d0be182fcf5e9bf302e406cdde9c8908427f66d9b82a97c2b939278`.
- `full-current-retry02.log`: `4004a15f86c1e084a712c09549dae303f2bd920bb7dcad3b04d3347de6137b9d`.
- `full-independent.log`: `695011f5dd305524835ebbf4cd84e7e6e7387b609f4ac05511e2bb436bd02362`.
- `linux-offline.log`: `0384e3f49fa7c133e4d581ce42ac18a9c649c757070fbf22593c85a9bcf417d1`.
- `security-current.log`: `de2990954a204c3fc8337c918c6fa5e289004f5177d85154f28fe9ce763312a9`.

Security receipt: implementation checkout `implementation/p01/evidence/security-runs/1a882a39ca834bcfa3e89c7049683113/report.json`,
SHA-256 `6869dc4de4e8aed8e7bf1c1641ea34febfb7caf319e4ffc84f0e29508d701ecb`.
Inspector receipt: independent checkout `implementation/p15/evidence/staging-runs/3100be43e9fb4b519526ad44250ab1b9/receipt.json`,
SHA-256 `b09342236f32c66c0a37a23e7bb1ed0be92ae6a8ecb9391e039837e9ec49294f`.

The existing P14 artifact contract locks the pre-adapter manifest and source. P15 also locks root
Cargo dependencies and affected service source. Actual successful behavior above does not by itself
change those contracts. No old validator or source hash has been edited to bypass this hold.

## Exact next work

1. Resolve current-source qualification explicitly: preserve the old P14/P15 evidence and bind the
   new v10 adapter, dependency/ACL changes and both actual receipts in a versioned successor contract.
   Inspect the entire affected source-lock chain and run unchanged predecessor regressions; no
   blanket Cargo/source exemptions, blind hash regeneration or runtime-PASS-to-entire-Gate promotion.
2. Resolve the separate main P05 diagnostic dependency hold, then run fresh current/independent FULL
   against the resulting exact integrated source. Original fixture/trace/PDF evidence stays unchanged.
3. Implement authenticated durable PlanSourceRepository/stored-plan storage and actual renderer wiring.
   Source/revision/owner/ACL/expiry checks and formal visual evidence remain required; registered-host,
   actual Hangul layout/identity and later-version qualification are separate Gates.

Recommended reasoning: `max`. No local user action is required for this offline work.
