# P06 table split HWPX v0 to v1

Before this profile, `hwpx-agent.table-partition/v1` defined whole-table cursor-row split semantics,
stable logical identities, complete cell movement and exact row rebasing, but no native HWPX adapter
materialized a split result.

`hwpx-agent.table-split-hwpx.hancom-2020-wrapper/1` adds a preserving adapter for one explicitly
bound top-level `hp:p/hp:run/hp:tbl`. It renders the two authoritative output grids independently,
requires one identical header catalog, allocates distinct native IDs, inserts one empty paragraph and
returns only after both tables reopen with exact ruling, partition and page-split semantics.

The request binds source header, section, wrapper, complete table state/grid and document flow. The
lowerer relifts the source and rebuilds the domain result before any output is returned. Every master
cell, span, payload, property, edge and diagonal moves to exactly one partition; sibling formulas and
non-target package parts remain exact.

Formula rebasing, repeat-header ownership and caption ownership are outside this first exact profile
and fail closed. Migration is additive and existing documents are not rewritten in place. Static
synthetic package success may not promote TABLE-010 to licensed Hangul 2020, renderer, automation,
differential, rollback/retry, release, production or product PASS. TABLE-011 is not promoted by this
profile.
