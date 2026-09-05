# P16-06 PostgreSQL encrypted durable plan store v12

- Date: 2026-09-06; scope: current-PC disposable PostgreSQL and synthetic plans only.
- Decision: durable compiled-plan persistence successor PASS; renderer and P16-06 remain open.
- Base: `5166fe5a684415534af920d55b06043168302d37`; review risk HIGH / STRICT.

Migration 0012 adds a create-once, tenant-isolated compiled-plan table. Canonical plan JSON is stored
only as AES-256-GCM ciphertext with a random 96-bit nonce. Authenticated data binds tenant, project,
plan, revision, graph, owner, plaintext digest/length, timestamps, algorithm and key reference.
Every lookup decrypts and revalidates exact canonical bytes through `CompiledOperationPlan`, then
reauthenticates and rechecks current project/source authorization. Missing historic keys, metadata,
nonce or ciphertext drift fail closed. Active limits remain 256 entries, 1 MiB per plan, 16 MiB per
tenant and 900 seconds. A least-privilege, database-time, 256-row bounded purge removes only expired
ciphertext through a security-definer function; updates and direct deletes remain rejected.

Actual disposable PostgreSQL run `1828b246e92746789fa5d6501e7f1ac2` passed 39 ordered checks.
It proves process and database restart recovery, ciphertext-only storage, v1-to-v2 key rotation,
wrong-key rejection, expiry and configured capacity, owner isolation, bounded expiry purge,
ciphertext/nonce/AAD tamper rejection, unbound-source insert rejection, fresh ACL/source checks,
cross-tenant RLS, role/policy/privilege/owner/migration drift rejection, immutability and nonempty
rollback refusal. The pinned PostgreSQL 18.4 container and volume were UUID-owned and removed.
The retained receipt is `qualification/durable-plan-v12-20260906-v1/current-db.json`; its runtime
source digests are re-read by `tools/p16/postgres_durable_plan_qualification.py`.

Successor regressions also passed after schema v12: authoritative plan source run
`3892ae2fcf3c4b0289e649cd84110e0c` and encrypted artifact repository run
`02cf829ee0a244bb816fcd96ba8dfb63`. These transient runs are supporting regression evidence, not
additional claims in the durable-plan qualification.

No Hangul process, COM operation, user document, registered host, renderer, route receipt, dry-run,
diff receipt or production service was used. This increment does not authorize document execution.
Next implement a renderer that accepts only the exact stored plan digest plus route, dry-run, diff
and signature receipts. Recommended reasoning: `max`.
