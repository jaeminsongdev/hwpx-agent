# P14-02 artifact service runbook

## Scope

This runbook validates the P14-02 artifact service on the current local development checkout. It
does not qualify a production object store, KMS, malware scanner, OAuth/OIDC verifier, PostgreSQL HA
deployment or a later P14 task. It never opens Hangul or a user document.

The service boundary is implemented by `crates/artifact-service`. It accepts only validated typed
metadata, hashes the authenticated subject identifier, scans before publication, encrypts the
payload with AES-256-GCM, uses a tenant/kind/state/content-addressed object key, grants the creator
the first manager ACL, and keeps quarantined ciphertext in a separate namespace. Signed download
URLs bind the tenant, artifact, subject digest, content digest, ACL generation, operation and a
maximum 300-second lifetime.

The checked PostgreSQL v2 migration extends the P14-01 metadata schema. Existing v1
`available`/`quarantined` rows have no P14-02 ciphertext identity, so migration forces them to
`orphaned` while retaining their original security state in rollback-only recovery columns. A v2
rollback restores those exact v1 fields before removing the v2 columns.

## Static and Rust validation

Run from the repository root:

```powershell
python tools/p14/validate_artifact_service_migration.py
python -m unittest tools.p14.tests.test_artifact_service_migration
python -m py_compile tools/p14/validate_artifact_service_migration.py tools/p14/test_artifact_service_migration.py tools/p14/tests/test_artifact_service_migration.py
cargo fmt --all -- --check
cargo clippy -p hwpx-agent-foundation -p artifact-service --all-targets --all-features -- -D warnings
cargo test -p hwpx-agent-foundation -p artifact-service
```

Any source-lock, migration digest, exact-key, required invariant, unsafe path, unpinned image,
rollback scope or test failure is terminal. Reconcile the reviewed source; do not edit the contract
only to silence the validator.

## Disposable PostgreSQL validation

Docker must already contain the exact image pinned in
`implementation/p14/postgres/p14-artifact-service-v1.json`. The harness publishes no host port,
mounts no host volume, uses `--network none`, labels its one owned container and verifies removal in
all exit paths.

For an evidence run, first commit the complete P14-02 implementation and require a clean tree. Then
use a new receipt path:

```powershell
python tools/p14/test_artifact_service_migration.py --receipt implementation/p14/evidence/p14-02-postgres-artifact-audit-<UTC>.json
```

Accept the receipt only when `state=pass`, `source_tree_clean_before_run=true`, `source_revision`
equals the reviewed commit, `container_removed=true`, and all exercised booleans are true. The run
applies v1 and v2, verifies two pre-v2 legacy rows fail closed, runs 22 SQL assertions, refuses an
ungated rollback, restores both legacy rows during the gated rollback, reapplies, repeats the smoke
and removes v2 and v1.

## Failure handling

- Contract or digest mismatch: stop before Docker and review the changed source.
- PostgreSQL version/image mismatch: stop; do not fall back to a tag or `latest`.
- Migration, smoke or rollback failure: keep the terminal output, allow only the harness-owned
  container cleanup, fix the source and rerun from a new container.
- Audit publication, encryption, storage relocation or metadata failure: fail closed. Never promote
  an unscanned, unencrypted or inconsistent record to `available`.
- Scanner unavailable: use `FailClosedScanner`; the artifact remains quarantined and unverified.
- Production credentials: pass only vault/KMS handles. Never put raw keys, signed URLs or document
  bodies into receipts, metadata or audit events.

## Handoff

After the clean receipt and repository-wide validation are recorded, P14-02 may be checked only in
its task row. P14 remains open. Continue with P14-03 Revision CAS at reasoning effort `max`; P14-08
owns orphan reconciliation and P14-09 owns retention/purge. Production adapters remain unqualified
until their independent Gates.
