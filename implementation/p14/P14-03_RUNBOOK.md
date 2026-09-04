# P14-03 revision CAS runbook

## Scope

This runbook validates the P14-03 immutable revision DAG and expected-head compare-and-swap
boundary on the current local development checkout. It does not qualify a production PostgreSQL
deployment, distributed transaction manager, remote artifact store, history API or a later P14
task. It never opens Hangul or a user document.

The Rust boundary is implemented by `crates/revision-service`. It accepts only validated, typed
tenant/project/branch/revision/commit identifiers, a verified revision request and an authenticated
subject digest. A successful commit atomically seals one immutable node, records a digest-bound
receipt and advances the exact branch generation. A stale expected head returns a typed conflict
without inserting a node or receipt. Cross-tenant reads and commits are indistinguishable from
absence.

The PostgreSQL v3 migration extends the P14-01/P14-02 schema with branch and project head
generations, immutable graph seals, immutable commit receipts and a `SECURITY DEFINER` CAS
function with a fixed search path. The function requires matching transaction-local tenant and
subject context, project owner/editor authorization, available verified artifacts and a verified
revision. Existing non-null heads receive generation `-1` plus a `legacy_unqualified` seal and
cannot be used as qualified CAS roots.

## Static and Rust validation

Run from the repository root:

```powershell
python tools/p14/validate_revision_cas_migration.py
python -m unittest tools.p14.tests.test_revision_cas_migration
python -m py_compile tools/p14/validate_revision_cas_migration.py tools/p14/test_revision_cas_migration.py tools/p14/tests/test_revision_cas_migration.py
cargo fmt --all -- --check
cargo clippy -p revision-service --all-targets -- -D warnings
cargo test -p revision-service
```

Any source-lock, migration digest, schema object, exact-key, unsafe SQL, rollback scope or test
failure is terminal. Reconcile the reviewed implementation; do not alter the contract merely to
silence the validator.

## Disposable PostgreSQL validation

Docker must already contain the exact image pinned in
`implementation/p14/postgres/p14-revision-cas-v1.json`. The harness publishes no host port, mounts
no host volume, uses `--network none`, labels its one owned container and verifies removal in every
exit path.

For an evidence run, first commit the complete P14-03 implementation and require a clean tree. Use
a new receipt path:

```powershell
python tools/p14/test_revision_cas_migration.py --receipt implementation/p14/evidence/p14-03-postgres-revision-cas-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, `source_revision`
equals the reviewed commit, `container_removed=true`, both smoke and race counts equal two, and all
exercised booleans are true.

Each application runs 20 SQL assertions covering authorization, request-context binding,
verified/available artifacts, root and child commits, default-branch/project mirroring, immutable
seals and receipts, audit publication, stale conflict side-effect freedom, invalid parents,
cross-tenant denial and independent branch heads. A real two-session row-lock race must yield
exactly one commit and one conflict, persist only the winner, and advance the generation once. The
harness also verifies legacy heads fail closed, refuses an ungated rollback, preserves the v2
schema after a gated v3 rollback, reapplies v3 and repeats the smoke and race.

## Failure handling

- Contract or digest mismatch: stop before Docker and review the changed source.
- PostgreSQL version/image mismatch: stop; do not fall back to a mutable tag or `latest`.
- Race produces two commits, two conflicts, a fast non-waiting contender or more than one candidate
  node/receipt: treat atomicity as failed and retain the terminal output for diagnosis.
- Stale conflict inserts any graph, receipt or audit state: fail closed; never repair the head by a
  second unguarded update.
- Legacy head generation `-1`: migrate or rebuild it through a separately reviewed path; never
  promote it to a qualified generation by inference.
- Production credentials or identities: persist only hashes and opaque handles. Never put subject
  identifiers, document bodies, URLs or secret values in receipts or audit records.

## Handoff

After the clean receipt and repository-wide validation are recorded, only the P14-03 roadmap row
may be checked. P14 remains open. Continue with P14-04 History/checkpoints at reasoning effort
`max`; production deployment, multi-host concurrency and remote service wiring remain unqualified
until their independent Gates.
