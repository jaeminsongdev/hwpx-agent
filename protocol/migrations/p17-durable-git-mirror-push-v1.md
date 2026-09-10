# P17 durable Git mirror push v1 migration policy

Migration 16 adds an authenticated current-PC push coordinator; it does not claim remote-network
Git, pull, credential custody or production lifecycle. The authoritative effect row contains the
canonical bounded Git plan, request/idempotency bindings, expected and result database/Git state,
verified source/result artifact identities, receipts, lease owner and monotonic fencing token.
The row is stored and committed before the local bare-Git reference compare-and-swap runs.

The only mutable effect state machine is `executing -> finalized|diverged`. Terminal rows and all
plan/identity fields are immutable. Forced tenant RLS applies to the effect table. A branch trigger
rejects head movement while an executing reservation exists unless the exact push ID and current
fencing token are transaction-locally presented by the finalizer. The revision receipt trigger
admits that same exact Git capability without weakening the pre-existing job/idempotency path.

Five `SECURITY DEFINER` functions with fixed `search_path` and no public execute privilege provide
inspect, plan-store, lease-acquire, divergence and finalization boundaries. Finalization calls the
existing revision CAS and updates the mirror/effect in one serializable PostgreSQL transaction.
If Git is already committed after a process interruption, a later execution may acquire only an
expired lease with a higher fence, observe the stored plan, and finalize once. An unrelated ref is
classified `diverged`, preserved, and moves the mirror to `manual_merge_required`.

Current PostgreSQL metadata/plan consumers require migrations 1 through 16 and look one row past
the admitted set. The atomic-checkpoint dispatcher retains exact v15 admission for its historical
qualification and also accepts the complete exact v16 set when used in the current workspace.

Rollback requires
`hwpx_agent.allow_p17_durable_git_mirror_push_rollback=yes`, exact latest version 16, no later
migration, and an empty effect table. It never deletes retained plans, committed/diverged evidence,
Git objects, refs, revisions or receipts. The down migration restores the exact pre-v16 revision
receipt guard before removing the empty effect table.

This migration proves no durable pull, remote TLS/network behavior, registered application,
persistent credential custody, production lifecycle or Hangul behavior. Those remain separate
Gates.
