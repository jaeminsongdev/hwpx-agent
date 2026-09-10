# P17-06 authenticated durable Git mirror push v14

Date: 2026-09-10
Scope: current-PC PostgreSQL 18.4, authenticated loopback and disposable local bare Git
Decision: **durable push/recovery component PASS; P17-06 remains in progress**

Migration 16 and `LocalPostgresGitMirrorPushCoordinator` now bind one canonical authenticated
`mirror.sync` push to a PostgreSQL effect reservation and an exact local bare-Git ref CAS. The
database stores the complete bounded Git plan before the ref effect, fences each executor with an
expiring lease, and reserves the corresponding branch head. Source and result snapshot digests must
resolve to available, verified artifact rows before an effect can begin.

After Git is observed committed, the finalizer calls the existing revision CAS and updates the
mirror plus effect row in one serializable transaction. A fresh process can reacquire an expired
lease with a higher fence, distinguish `no_effect`, `committed` and `diverged`, and finish without
guessing. Exact replay produces no second Git commit, revision, seal, receipt or audit event. A
competing ref is never overwritten and moves only the mirror/effect to durable manual-merge state.
Any database failure after the Git ref is known committed is returned as unavailable, not rejected.

The current-PC acceptance uses a pinned PostgreSQL 18.4 image, a generated SHA-1 bare repository,
separate authenticated host/client processes and one-time tokens. It deliberately revokes the
finalize function after host admission to interrupt both first- and second-generation pushes after
their Git effects. After introducing a competing ref it also revokes the divergence-transition
function, proves the uncertain attempt remains replayable, and lets only a later fencing lease
commit manual-merge state. The run proves committed-effect recovery, exact replay, idempotency drift
rejection, external-ref divergence preservation, immutable terminal rows, exact branch reservation,
gated empty rollback/reapply, retained-effect rollback refusal, migration/RLS/function admission
drift rejection, PUBLIC execute/search-path/security-definer drift rejection and owned Docker
cleanup. All 27 checks passed in run `9b3ff9b352ec402aab20f1c5a387a8ec`. Its exact receipt is
`artifacts/p17/durable-git-mirror-push/runs/9b3ff9b352ec402aab20f1c5a387a8ec/receipt.json`
(SHA-256 `efca394cc9962da63c3044c1aa4b78fbe9283e8f89d40ce3ae1fbe076146dd4d`) and contains no credential
or authorization value.

This is current-PC component evidence. The transport binds only loopback; Git is a disposable local
bare repository. Durable pull, remote TLS/network Git, persistent credential custody, registered
application lifecycle and production operation were not run. P17-06 therefore remains open. The
next MAX increment is an authenticated durable pull coordinator that observes the same exact Git
state and atomically reconciles the local mirror without weakening push recovery.
