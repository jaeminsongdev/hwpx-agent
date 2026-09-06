# P17 current workspace source qualification v12

Date: 2026-09-07

Scope: current-PC source-binding successor only

Decision: **qualified for the exact PostgreSQL checkpoint-host sources; no phase or product PASS**

The v1-v11 qualification contracts remain byte-for-byte unchanged. This v12 layer composes the
exact v11 contract with SHA-256
`31b7f7f7011136206b9fb699fbe18fb779a968b8972a448b70cd448e8ecf196b` and advances the source view
to clean commit `240f270e09ec8e7576d49430f514dbd29e5ce689`.

Current-host source acceptance run `7b45b92ba5c84ad7a2241b960871a58b` passed all 11 checks. Its
canonical receipt SHA-256 is
`b5112efac6e9a1031da522e2c0e1c4620ad6444aef3307ac0200c0edbdec1ff2`. The fourteen composed
predecessor successors remain exact. Locked/offline Cargo metadata is
`d7dd720fa29a88f5df06dc692b0a56c1d8c70142a88227b4c8ca5f14962bd856` for 25 workspace members.

This successor binds 107 implementation files as exact regular-file bytes and exact Git blobs at
the base commit. It retains the v11 set, advances the changed history and remote-sync sources, and
adds PostgreSQL migration 14, the least-privilege dispatcher, separate-process probes, disposable
database acceptance, private protocol/migration contracts, frozen qualification and the aligned
dependency-license policy. The implementation commit passed the full workspace build and test
suite, formatting, all-target Clippy with warnings denied, targeted PostgreSQL checks and the FULL
repository security lane.

The new sources and their narrower frozen qualification prove current-PC disposable PostgreSQL
checkpoint create, exact replay and rejection paths through separately launched loopback host and
client processes. They do not prove durable atomic mirror role/head admission plus checkpoint,
actual pull/push transitions, persistent credential custody, remote-network TLS, a production
service lifecycle, registered remote app execution, actual Hangul work, P17-06/P17-07 completion,
another PC/version, phase completion, production readiness or product completion. All corresponding
claims remain false.
