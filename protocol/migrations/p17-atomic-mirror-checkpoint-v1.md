# P17 atomic mirror checkpoint v1 migration policy

Migration 15 adds only `hwpx_agent.create_mirror_history_checkpoint_v3` and schema-version
metadata. It does not alter durable rows. The function admits an immutable history checkpoint only
after the authenticated role, exact clean mirror and exact branch head have been read and locked in
the same serializable transaction.

The v3 function is `SECURITY DEFINER`, fixes `search_path`, is revoked from `PUBLIC`, and is the sole
function executable by the bounded host role. It requires exact tenant and subject context, an
active project, a durable `editor` or `owner` ACL row, an idle clean mirror, and matching positive
revision/generation state for the mirror and branch. A durable state conflict uses `P1702`; the
existing v2 function retains checkpoint idempotency and immutable audit behavior.

All current PostgreSQL consumers admit exactly migrations 1 through 15 and query one extra row so a
later migration fails closed. The v11 dispatcher remains an immutable historical qualification for
schema 14; the v12 dispatcher is the current schema-15 route.

Rollback requires `hwpx_agent.allow_p17_atomic_mirror_checkpoint_rollback=yes`, exact latest version
15, and no later migration. Because migration 15 adds no data column, rollback drops only v3 and the
exact version row. It must never be presented as reversing a checkpoint already created through v3.

This migration proves no pull, push, remote TLS, persistent credential custody, production
lifecycle, registered application, or Hangul behavior. Those require separate evidence.
