# P06 table merge/split HWPX v0 to v1

Before this profile, `hwpx-agent.table-merge-split/v1` defined exact rectangular merge and evenly
divisible split semantics, stable master identities and all content policies, but no native HWPX
adapter materialized those domain results.

`hwpx-agent.table-merge-split-hwpx.hancom-2020/1` adds a preserving adapter for one explicitly
bound `hp:tbl`. Merge removes precisely the shared edges made internal by the authoritative target
grid. Split adds precisely the newly structural edges using a caller-bound line identity that must
already exist in the source header edge-line catalog. Reverse topology transitions fail closed.

The request binds complete source ruling state, grid, content ownership and document flow. The
lowering binding additionally covers header, section, request and complete plan. The lowerer
relifts the source and rebuilds the domain result before any output is returned.

All merge policies and split keep/distribute policies retain their domain meaning. `First`
discards only with explicit receipt evidence, and `RejectIfMultiple` never guesses. Selected
formulas, visible diagonals or unequal complete merge-cell properties are not representable by this
direct profile and fail closed. Unselected supported formulas and caches remain exact even when a
different region changes topology; this is preserving readback, not a broader formula mutation
profile.

Migration is additive and existing documents are not rewritten in place. Static synthetic package
success may not promote TABLE-016/017 to licensed Hangul 2020, renderer, automation, differential,
rollback/retry, release, production or product PASS.
