# P17-06 exact Git mirror effect v13

Date: 2026-09-10  
Scope: current-PC disposable local bare Git repositories  
Decision: **exact Git effect and recovery observation component PASS; P17-06 remains in progress**

`GitMirrorEffectHost` accepts only an explicit absolute plain local bare repository, an explicit
absolute plain Git executable, and a typed next-generation mirror input. The caller cannot supply a
Git command or reference. Project, branch and revision identifiers are canonical typed IDs; the
empty head exists only at generation zero; all content bindings are lowercase SHA-256 values; and
the result generation is exactly the expected generation plus one.

Planning validates the current ref's canonical `mirror-state.json` and exact single-entry tree, then
writes deterministic unreachable blob, tree and commit objects. Its bounded canonical plan binds the
input SHA, derived branch reference, old and result OIDs, and state SHA. Publishing performs one
old-OID `update-ref` compare-and-swap. A concurrent ref is never overwritten. Replaying an already
published exact plan returns an explicit replay receipt.

After an uncertain process boundary, the durable plan can be decoded only from its exact canonical
representation and observed as `no_effect`, `committed` or `diverged`. `committed` requires the exact
canonical state bytes and exact one-file tree; `diverged` is never retried automatically. Git runs
with a cleared environment, no credential prompt, no replace objects and an empty hooks directory.
Output is bounded and public `Debug`/errors contain no repository path, identifier or digest.

Six current-PC integration tests use actual Git and disposable bare repositories. They cover
genesis and forward pushes, deterministic plans, exact replay, host restart recovery, noncanonical
plan rejection, input/plan drift, concurrent-ref divergence, ordinary-repository rejection, bounded
typed input validation, exact-tree rejection, semantic pull readback and debug redaction. The
complete `remote-sync-host` target has 19 passing tests and one pre-existing isolated PostgreSQL test ignored;
focused all-target Clippy passes with warnings denied.

This is component evidence only. It does not yet put the effect behind the authenticated loopback
request dispatcher, persist ownership/lease/fencing in PostgreSQL, finalize the revision graph and
mirror atomically, exercise a remote network, or prove production lifecycle. P17-06 remains open.
The next MAX increment is migration 16 plus the authenticated durable pull/push coordinator: persist
the exact Git plan before effect, fence one execution, reconcile the three observations after a
crash, and finalize the PostgreSQL revision/mirror state exactly once.
