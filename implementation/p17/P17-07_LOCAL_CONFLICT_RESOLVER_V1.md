# P17-07 local conflict resolver v1

Date: 2026-09-06
Scope: current PC, durable local stale-head resolution core and CLI surface
Decision: **first bounded increment implemented; P17-07 remains in progress**

`local-sync` now resolves a durably recorded conflict through three explicit paths. Rebase requires
the exact recorded conflicting head and its validated snapshot digest. A mirror with pending local
work must also supply a complete rebased snapshot/operation-plan pair; a clean checkpoint conflict
may adopt the exact remote snapshot. Branch resolution accepts only a new bounded branch identity
whose supplied base head and snapshot exactly equal the mirror's old observed base, then preserves
the local snapshot and pending plan. Manual merge requires the exact conflict head plus the merged
snapshot and replacement operation-plan digests and remains ahead until a normal push succeeds.

All inputs are validated before mutation. A valid resolution is one immutable journal append using
the existing exact revision CAS; a stale writer cannot overwrite it. The mirror snapshot advances
to `hwpx-agent.local-mirror/v4` and records only the selected resolution enum. Valid v1-v3 states
migrate to v4; an older schema carrying the new field or an unresolved conflict carrying a prior
resolution marker fails closed.

The real `local-sync` process exposes `resolve-rebase`, `resolve-branch`, and `resolve-manual`. Its
v2 public output adds a stale-head surface containing only current generation, generation delta and
an ordered allowed-resolution enum list. It emits no path, project/branch/mirror/revision identity, digest,
credential or idempotency key. The exact private contract is
`protocol/private/p17-local-conflict-resolver-v1.json`.

The crate passes 37 tests: thirteen state-machine, five durable-store, eight durable
remote/resolution, four authenticated-adapter and seven real-process CLI tests. These prove the
local resolver, migrations, zero-change rejection, durable CAS and bounded CLI surface only. The
compiled remote port still fails closed, branch evidence is not an authenticated remote receipt,
and no concurrent Web/Codex run or graphical stale-head UI has been executed. P17-07 therefore
remains open; the next increment must extend the qualified host protocol and wire this resolver to
the widget before collecting actual concurrent evidence.
