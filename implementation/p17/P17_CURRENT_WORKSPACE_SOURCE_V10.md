# P17 current workspace source qualification v10

Date: 2026-09-06
Scope: current-PC source-binding successor only
Decision: **qualified for the exact checkpoint-intent-bound sync sources; no phase or product PASS**

The v1-v9 qualification contracts remain byte-for-byte unchanged. This v10 layer composes the
exact v9 contract with SHA-256
`6f6beada33d8d73ba372781cff40507071d3ee754697241a983865b8e42617c2` and advances the source view
to clean commit `02ce014fe739dd51de347ba71313c042ace76621`.

Current-host source acceptance run `ff13d539c1f64cbc988dbddac859529a` passed all 11 checks. Its
canonical receipt SHA-256 is
`e89ec763b27c27afad21977e34145ddae49b0f0a3752c793f17a509273db5e95`. The fourteen composed
predecessor successors remain exact. Locked/offline Cargo metadata remains
`d956979b62019ff5b89a3c6b2ab506a7f102ae0fcb4f86ce70717ac2fca2d51d` for 23 workspace members.

This successor binds sixty implementation files as exact regular-file bytes and exact Git blobs at
the base commit. It retains the v9 set, replaces the changed `local-sync` core, CLI, adapter and
tests, and adds the store, private v3 checkpoint request contract, private v4 CLI contract, private
v2 conflict contract, v3/v5 migration notes and implementation reports. All 39 `local-sync` tests,
the full workspace build and test suite, formatting, and all-target Clippy with warnings denied
passed before the implementation commit.

The new sources prove only that checkpoint label and optional note are included in the exact private
v3 request, that its SHA-256 is paired durably with the pending idempotency key in local-mirror v5,
and that changed retry metadata fails closed without exposing label or note in the journal, CLI
output or debug representation. Clean legacy snapshots migrate and ambiguous legacy pending state
fails closed.

They do not prove a credential provider, host transport, remote service, private-to-public checkpoint
mapping, registration of `project_conflict_resolve`, a concurrent Web/Codex conflict, an actual
Hangul operation, P17-06 or P17-07 completion, another PC/version, phase completion or product
completion. All corresponding claims remain false.
