# P14-09 retention and local-mirror runbook

## Scope

This runbook validates P14-09 artifact-retention, legal-hold, fenced purge and digest-only local
project mirror behavior on the current checkout. It covers a bounded Rust reference service and a
disposable PostgreSQL v9 schema. It does not qualify production object storage, a production
database, multi-host failover or later Hangul versions. It never opens Hangul or a user document.

## Static and Rust validation

Run from the repository root:

```powershell
python tools/p14/validate_retention_local_mirror.py
python -m unittest discover -s tools/p14/tests -p "test_*.py"
cargo fmt --all -- --check
cargo clippy --locked -p retention-sync-service --all-targets -- -D warnings
cargo test --locked -p retention-sync-service
```

Any digest, identity, tenant, subject, legal-hold, shared-reference, lease, fence, retry, receipt,
head-CAS, operation-plan, conflict, RLS, privilege or rollback failure is terminal. Fix the
implementation and add a regression. Do not rewrite an older contract digest to make drift pass;
the P14-07 Cargo locks are verified against their exact historical Git blobs and a valid P14-09
superseding contract.

## Disposable PostgreSQL evidence

Docker must contain the exact digest-pinned image from
`implementation/p14/postgres/p14-retention-local-mirror-v1.json`. The harness publishes no host
port, mounts no host volume, uses `--network none`, labels only its owned container and verifies
removal.

Commit the reviewed implementation and require a clean tree before creating a receipt:

```powershell
python tools/p14/test_retention_local_mirror_migration.py --receipt implementation/p14/evidence/p14-09-postgres-retention-mirror-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, `source_revision`
equals the reviewed commit, `container_removed=true`, all three v9 smoke and v7 regression runs
pass, the legal-hold/shared-reference/fence checks are true, all three conflict resolutions pass,
new references are blocked after tombstone, expired push recovery requires a new identity,
single-generation reservation and active push-identity uniqueness pass, unsafe rollback is refused,
clean rollback restores v8, and reapply succeeds.

The P14-09 fixture creates a transaction-local `pg_temp` helper solely to seed the already-proven
P14-07 revision receipt shape. It is never installed in the product schema. The unchanged P14-07
fixture runs in the same v9 database to prove that the prerequisite idempotency/revision contract
still holds.

## Repository, Linux and security validation

Run all non-security lanes at the exact implementation commit:

```powershell
python tools/p01/run_ci.py --lane linux-core
python tools/p01/run_ci.py --lane windows-worker
python tools/p01/run_ci.py --lane widget
python tools/p01/run_ci.py --lane docs
```

For Linux-specific proof, use the local digest-pinned Rust 1.96 image with networking disabled,
source and the existing Cargo registry mounted read-only, and executable tmpfs for Cargo metadata,
target, temporary and Rustup temporary files. Run retention-sync-service Clippy with `-D warnings`
and all tests in `--offline --locked` mode.

Run the unchanged bounded security lane:

```powershell
python tools/p01/run_ci.py --lane security
```

A timed-out or unreachable advisory request is not a PASS. Accept only a completed security report
with every check at exit code zero and no residual audit process.

## Handoff

P14-09 may be checked only while the exact clean PostgreSQL receipt, four non-security lanes,
offline Linux proof, successful security lane and strict review remain valid for the reviewed
commit. P14 then requires a separate phase-gate audit before P15 begins. Continue that audit at
reasoning effort `max`.
