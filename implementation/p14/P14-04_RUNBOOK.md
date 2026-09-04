# P14-04 history/checkpoints runbook

## Scope

This runbook validates the P14-04 bounded revision-history, semantic-diff cursor, immutable
checkpoint and branch-creation boundary on the current local development checkout. It does not
qualify a production PostgreSQL deployment, HTTP API, remote KMS, multi-host service or a later P14
task. It never opens Hangul or a user document.

The Rust boundary is implemented by `crates/history-service`. History cursors are HMAC-SHA256
signed, tenant/subject bound, short lived and size limited. The first page fixes a qualified branch
head; continuations keep that head even if the branch advances. The service orders the reachable DAG
child-before-parent, rejects more than 10,000 reachable nodes, validates every adapter projection and
returns semantic-diff artifact identities only after cursor verification and reauthorization.

The PostgreSQL v4 migration adds immutable checkpoint idempotency claims and fixed-search-path
`SECURITY DEFINER` functions for history queries, checkpoints and branches. It requires transaction-
local tenant/subject context, an active project, role authorization and `service_v1` revision seals.
Reachable legacy nodes, inconsistent parent generations and more than 10,000 reachable nodes fail
closed. Public function/table privileges are revoked and destructive rollback is explicitly gated.

## Static and Rust validation

Run from the repository root:

```powershell
python tools/p14/validate_history_checkpoints_migration.py
python -m unittest discover -s tools/p14/tests -p "test_*.py"
cargo fmt --all -- --check
cargo clippy -p history-service --all-targets --all-features -- -D warnings
cargo test -p history-service --all-features
```

Any source-lock, digest, exact-key, bounded-input, cursor-binding, authorization, graph, rollback or
test failure is terminal. Fix the implementation and its regression test; do not weaken the
contract or promote a partial result.

## Disposable PostgreSQL evidence

Docker must already contain the exact image pinned in
`implementation/p14/postgres/p14-history-checkpoints-v1.json`. The harness publishes no host port,
mounts no host volume, uses `--network none`, labels its owned container and verifies removal.

Commit the reviewed implementation and require a clean tree before creating a receipt:

```powershell
python tools/p14/test_history_checkpoints_migration.py --receipt implementation/p14/evidence/p14-04-postgres-history-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, `source_revision`
equals the reviewed commit, `container_removed=true`, both smoke and race counts equal two and every
exercised boolean is true.

Each smoke run has 26 numbered assertions. They cover bounded stable pagination, merge parents,
reader/editor/owner roles, tenant/subject context, unqualified and generation-invalid graphs,
checkpoint create/replay/drift/immutability, branch qualification/uniqueness, diff identities,
forced RLS, public revocation, schema version and audit events. The two-session race must yield one
created checkpoint plus one replay, with one claim, one checkpoint and one audit event.

## Repository and Linux validation

Run all four non-security CI lanes at the exact commit. For the Linux-specific crate proof, use the
digest-pinned local Rust 1.96.0 image with no network, read-only source and Cargo registry, and only
executable disposable tmpfs for Cargo home/target/temp. Run history-service Clippy with
`-D warnings` and all history-service tests.

Run `python tools/p01/security_checks.py` without suppressing or relaxing any check. A registry
timeout is not a vulnerability finding, but it is also not a PASS. Retain the exact failed report,
verify cleanup and rerun later under the same bounded policy.

## Handoff

Only check P14-04 in the roadmap after the exact clean PostgreSQL receipt, all four CI lanes,
offline Linux validation, security checks and STRICT review pass. P14 remains open. Continue with
P14-05 job state machine at reasoning effort `max`; production deployment and remote wiring remain
unqualified until their own Gates.
