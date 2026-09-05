# P16-06 PostgreSQL artifact adapter: bounded continuation

- Date: 2026-09-05. Scope: current PC, disposable local PostgreSQL only.
- Worktree: `D:\개발\hwpx-agent-work-p16-plan-service`.
- HEAD: `9c120ac7407c00a7454a195c403330b47ff0524f`; adapter implementation is uncommitted.
- State: actual adapter acceptance FAILED; no renderer, registered-host or production qualification.
- Preserve the dirty adapter files, previous failure reports and historical source contracts.

## Completed checks and current failure

The artifact-service target tests previously passed 32/32. Latest session 51036 completed formatting,
all-target Clippy with warnings denied, probe build and Python syntax compilation before running
`python tools/p16/run_postgres_artifact_checks.py`. That session is now terminal exit 1; do not poll it.

| Actual run | Result | Retained evidence |
|---|---|---|
| `73be1b04dcbc4cd0879de93c5956fe0e` | FAIL guarded empty rollback | Immutable migration-history trigger rejected deleting the v10 registration. |
| `e78573e5a5cc44a38e92e6a7bac5c40e` | FAIL seed, `STORAGE_FAILURE` | Guarded rollback/reapply and predecessor/trigger checks passed. |
| `afee7194223c4389900cfcd5fff57ac9` | FAIL seed, `STORAGE_FAILURE`, probe stage `CONNECT` | Same rollback checks passed; failure narrowed to repository connection/initial database verification, before seed lookup or ingest. |

Reports are under the worktree's `artifacts/p16/postgres-artifacts/runs/<run-id>/report.json`.
Latest report SHA-256: `6384f387f213002bca3246046de4ca867fbce1500199e219bc9df4d39dbf5358`.
Latest probe SHA-256: `cca96f0f24003b3fd7e93ce443e0950e5d520d3c7e7f5027d5e195d8222dbacf`.
The report binds implementation and migration hashes; no actual Hangul or registered host ran.

## Implemented repair and diagnostic boundary

The v10 down migration now disables the immutable-history trigger only inside the guarded rollback
transaction, removes only its own exact v10 registration, then restores the trigger before commit.
The harness checks identical predecessor rows, exactly nine retained registrations, enabled trigger
state, and a rejected predecessor-history mutation before reapplying v10. These passed twice.
This is not permission to alter any live or production database history.

The probe emits a closed set of stage markers; the harness records only a safe stage and public
error category. Raw database errors, SQL, process environment and credentials are not emitted.
`CONNECT` includes both transport establishment and `verify_database`; the specific cause is not
yet established. Do not label this an insert failure or a user/PC permission problem.

Each run reports owned resources removed. A fresh read-only listing found no remaining container or
volume with the exact adapter-test label. Only owned disposable DB resources were removed; retained
reports and encrypted local test objects were not deleted. No Hangul window or user click is pending.

## Exact next work

1. Diagnose connection/initial verification in `crates/artifact-service/src/store/postgres_repository.rs`.
   Keep backend details private and keep role, migration digest, RLS and privilege checks strict.
2. Add a reproducing regression where applicable, fix the actual cause and rerun the same disposable
   DB acceptance. Require restart persistence, tenant isolation, ACL/quarantine, negative security
   controls, immutable metadata and cleanup checks; passing connection alone is not acceptance.
3. Qualify source/dependency changes and run target, FULL/current, FULL/independent and applicable
   Linux/security audits before integrating. Stored Plan, renderer and formal visual evidence remain open.

Recommended reasoning: `max`. No local user action is required for this offline work.
