# P17 current workspace source qualification v1

Date: 2026-09-06
Scope: current-PC source-binding successor only
Decision: **qualified for the exact current source; no phase or runtime PASS**

The immutable P15 Inspector, P16 PostgreSQL and P16 main-integration contracts remain byte-for-byte
unchanged. Their exact SHA-256 values are prerequisites. A new successor maps only the historical
hashes those contracts already authorize to the source blobs at clean commit
`3b575dbb47d2e93a9825f7982d1a47d287600d3c`. It cannot admit an unknown path, an unlisted historical
hash or working-tree content that differs from that commit.

Acceptance run `72027184ccae49c784362e57a3d11b95` passed all 11 checks in an independent clean
worktree. The canonical receipt SHA-256 is
`642d5a60eb0b37d65b2f52e699849597017f5b79cccac02b98fb4611f7797297`. Exactly fourteen current
successors were required: root Cargo manifest/lock, the later PostgreSQL repository and harness,
the later MCP control-plane manifest/library, the integration/source/widget successor validators,
the composed-successor test, the pnpm lock and widget build script. Every current digest equals its
exact Git blob at the audited commit. The exact P16 widget contract is now a fourth immutable
predecessor.

`cargo metadata --locked --offline --no-deps` resolved 23 declared workspace members. The projected
metadata digest is `8071ba0ee448f663054c4786cc646ebf2bf49307dc773d71b1e347dbd1b43403`.
The audit also requires `hwpx-package` to keep exact workspace `serde` and `serde_json` development
edges and requires both names in its Cargo.lock dependency list. This qualifies the P05 diagnostic
dependency integration without rewriting the P15 source lock.

The P16 integration validator reconstructs its immutable predecessor contract using the successor
only after this qualification verifies. Its outward replacements are then composed to current
digests for the existing P14/P15 validators. Any contract, source, history, path or claim mutation
fails closed.

This evidence does not claim P05 layout correctness, actual Hangul execution, registered-host work,
production readiness, another PC/version or phase completion. Targeted regressions, both FULL runs,
security and actual landscape evidence remain separate requirements.
