# P17-06 atomic mirror checkpoint v12

Date: 2026-09-10
Scope: current-PC disposable PostgreSQL with separate loopback host and clients
Decision: **atomic durable mirror admission sub-increment PASS; P17-06 remains in progress**

Migration 15 adds `create_mirror_history_checkpoint_v3`. In one serializable transaction it checks
the authenticated tenant/subject, locks the durable project role, locks the exact local mirror,
requires `clean` with no pending plan or active push, locks the exact branch head, and requires the
same revision/generation at mirror, branch and checkpoint intent. Only then does it invoke the
existing immutable v2 checkpoint operation. Role, head or mirror drift is rejected with `P1702` and
leaves no new history request, checkpoint or audit row.

`LocalPostgresAtomicMirrorCheckpointDispatcher` accepts exact migrations 1-15, exact forced tenant
RLS on all nine participating tables, and a bounded role that can execute v3 but neither v1 nor v2
and cannot write tables directly. It sets authenticated context transaction-locally, performs one
v3 call, verifies the returned immutable fields before commit, and does not retry an uncertain
result. Public diagnostics redact connection credentials and tenant/subject/client identity.

Current-PC run `7c508c3590914b0eabb169477b633fc7` used the pinned PostgreSQL 18.4 image,
one separately launched host and seven separately launched clients. It passed 20/20 checks,
including exact migration rollback/reapply, least privilege, create/replay, changed-payload
rejection, durable ACL/head/mirror drift rejection despite unchanged process-local state, restored
exact replay, immutable rows, and startup refusal after migration, RLS-policy and execute-privilege
tampering. The receipt contains no secret material and all run-owned resources were removed. Four
earlier failed runs remain failed evidence and were not edited or relabeled.

This closes the earlier process-local mirror-admission gap. It does not implement or prove an actual
pull or push transition, persistent credential custody, remote-network TLS, production lifecycle,
registered application, or Hangul behavior. The product and P17-06 therefore remain open. The
machine contract is `protocol/private/p17-atomic-mirror-checkpoint-v1.json`; migration constraints
are in `protocol/migrations/p17-atomic-mirror-checkpoint-v1.md`.

The next MAX increment is a bounded durable pull/push state machine behind the same authenticated
host boundary, including ownership, lease/fencing, crash recovery, idempotent replay and exact Git
effects, without promoting local or synthetic evidence to production.
