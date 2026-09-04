# P14-05 job state-machine runbook

## Scope

This runbook validates P14-05's single-attempt structural job state machine on the current local
development checkout. It covers exact stage edges, active failure, terminal immutability, tenant and
subject authorization, artifact/revision qualification, job-attempt consistency and guarded schema
rollback. It does not qualify production PostgreSQL, remote service wiring, lease expiry takeover,
heartbeat, retry/reconciliation, cancellation/cleanup or retention. It never opens Hangul or a user
document.

## Static and Rust validation

Run from the repository root:

```powershell
python tools/p14/validate_job_state_machine_migration.py
python -m unittest discover -s tools/p14/tests -p "test_*.py"
cargo fmt --all -- --check
cargo clippy -p job-service --all-targets --all-features -- -D warnings
cargo test -p job-service --all-features
```

Any source-lock, digest, unknown-key, transition, identity, ACL, qualification, timestamp, rollback
or side-effect test failure is terminal. Fix the implementation and add a regression; do not relax
the validator or promote a partial result.

## Disposable PostgreSQL evidence

Docker must contain the exact digest-pinned image from
`implementation/p14/postgres/p14-job-state-machine-v1.json`. The harness publishes no host port,
mounts no host volume, uses `--network none`, labels only its owned container and verifies removal.

Commit the reviewed core implementation and require a clean tree before creating a new receipt:

```powershell
python tools/p14/test_job_state_machine_migration.py --receipt implementation/p14/evidence/p14-05-postgres-job-state-machine-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, `source_revision`
equals the reviewed commit, `container_removed=true`, apply and smoke counts both equal two,
`assertion_count_per_run=30`, v4 preservation is true and both rollback refusal checks are true.

The fixture covers function/table privilege boundaries, transaction-local context, reader/editor/
owner roles, subject-bound artifact ACL, qualified revisions/receipts, exact lease and stage binding,
skipped/repeated/backward transitions, active failure, terminal immutability, job/attempt consistency,
immutable job specification, legacy fail-closed behavior and audit events.

## Repository, Linux and security validation

Run all non-security lanes at the exact implementation commit:

```powershell
python tools/p01/run_ci.py --lane linux-core
python tools/p01/run_ci.py --lane windows-worker
python tools/p01/run_ci.py --lane widget
python tools/p01/run_ci.py --lane docs
```

For Linux-specific proof, use the local digest-pinned Rust 1.96.0 image with network disabled,
source and the existing Cargo registry mounted read-only, and executable tmpfs for Cargo metadata,
target and temporary files. Run job-service Clippy with `-D warnings` and all job-service tests in
`--offline --locked` mode.

Run the unchanged bounded security lane:

```powershell
python tools/p01/run_ci.py --lane security
```

A timed-out audit attempt is not a PASS by itself. Accept only a final lane PASS with every report
check at exit code zero, no failed checks, successful timeout cleanup and no residual audit process.

## Handoff

P14-05 is checked only while the exact clean PostgreSQL receipt, all four non-security lanes,
offline Linux proof, security lane and STRICT review remain valid for its locked sources. P14 stays
open. Continue with P14-06 scheduler capability/profile matching, heartbeat, expiry and late-worker
fencing at reasoning effort `max`.
