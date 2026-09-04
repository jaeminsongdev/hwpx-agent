# P14-06 worker lease/fencing runbook

## Scope

This runbook validates P14-06's exact worker selection, heartbeat, bounded lease, expiry and fencing
behavior on the current local checkout. It covers the in-memory scheduler and disposable PostgreSQL
v6 schema only. It does not qualify production/multi-host deployment, retry/requeue/takeover,
unknown-outcome reconciliation, cancellation/cleanup or retention. It never opens Hangul or a user
document.

## Static and Rust validation

Run from the repository root:

```powershell
python tools/p14/validate_worker_lease_fencing_migration.py
python -m unittest discover -s tools/p14/tests -p "test_*.py"
cargo fmt --all -- --check
cargo clippy -p job-service -p scheduler-service --all-targets --all-features -- -D warnings
cargo test -p job-service -p scheduler-service --all-features
```

Any source-lock, digest, identity, tenant, subject, profile, capability, expiry, fence, receipt,
privilege, RLS, rollback or side-effect test failure is terminal. Fix the implementation and add a
regression; do not relax the validator or promote a partial result.

## Disposable PostgreSQL evidence

Docker must contain the exact digest-pinned image from
`implementation/p14/postgres/p14-worker-lease-fencing-v1.json`. The harness publishes no host port,
mounts no host volume, uses `--network none`, labels only its owned container and verifies removal.

Commit the reviewed core implementation and require a clean tree before creating a receipt:

```powershell
python tools/p14/test_worker_lease_fencing_migration.py --receipt implementation/p14/evidence/p14-06-postgres-worker-lease-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, `source_revision`
equals the reviewed commit, `container_removed=true`, apply and smoke counts both equal two,
`assertion_count_per_run=20`, v5 preservation is true, all three rollback/duplicate refusals are
true, and the heartbeat/fence/expiry booleans are true.

The fixture covers forced tenant RLS, public privilege revocation, exact worker identity and
capability/profile matching, positive and negative worker heartbeat, ready/draining/stale workers,
job lease bounds, job heartbeat, direct guard bypass refusal, stale fence, live success, early expiry
refusal, late success rejection, unqualified receipt rejection and qualified expiry closure.

## Repository, Linux and security validation

Run all non-security lanes at the exact implementation commit:

```powershell
python tools/p01/run_ci.py --lane linux-core
python tools/p01/run_ci.py --lane windows-worker
python tools/p01/run_ci.py --lane widget
python tools/p01/run_ci.py --lane docs
```

For Linux-specific proof, use the local digest-pinned Rust 1.96.0 image with networking disabled,
source and the existing Cargo registry mounted read-only, and executable tmpfs for Cargo metadata,
target and temporary files. Run both `job-service` and `scheduler-service` Clippy with
`-D warnings` and all tests in `--offline --locked` mode.

Run the unchanged bounded security lane:

```powershell
python tools/p01/run_ci.py --lane security
```

A registry root response or timed-out audit attempt is not a PASS. Accept only a final lane PASS with
every report check at exit code zero, no failed checks, successful timeout cleanup and no residual
audit process.

## Handoff

P14-06 is checked only while the clean PostgreSQL receipt, four non-security lanes, offline Linux
proof, successful security lane and STRICT review remain valid for its locked sources. P14 stays
open. Continue with P14-07 request idempotency, retry policy and unknown-outcome reconciliation at
reasoning effort `max`.
