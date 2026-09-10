# P17 durable Git mirror pull v1

Migration 17 adds an exact observed-snapshot binding to `project_local_mirrors` and an immutable,
tenant-RLS `git_mirror_pull_observations` ledger. The new security-definer reconciliation function
accepts only the application role's authenticated tenant and subject, the canonical v4 pull request,
the mirror's exact observed revision/generation/snapshot tuple, and one read-only local bare-Git
observation whose revision, generation, artifact snapshot, commit OID and state digest agree with
the PostgreSQL revision chain.

For a clean mirror, a strict descendant atomically advances the observed head and snapshot. For an
ahead mirror, the same descendant creates one durable conflict while preserving the local snapshot
and pending operation plan. Same-head/same-snapshot is unchanged. Older heads, rewritten chains,
snapshot disagreement, unauthorized artifact state, unsupported mirror states and Git/database
drift fail closed. A canonical replay returns the immutable prior observation without a second
observation or conflict.

Rollback requires an explicit session gate, exact schema version 17, no later migration and an
empty observation ledger. It restores schema version 16 and removes only migration-17 objects. A
ledger containing accepted observations blocks rollback.

The implementation reads an explicit local SHA-1 bare repository without mutation and derives the
Git reference from typed project/branch identities. It accepts no caller command or reference and
performs no remote network operation. The current evidence covers only disposable PostgreSQL 18.4,
local bare Git and authenticated loopback processes on this PC. Persistent credential custody,
registered-host lifecycle, remote network transport, production, Hangul execution, P17-06
completion and product completion remain outside the claim.
