# P06 table join HWPX v0 to v1

Before this profile, `hwpx-agent.table-partition/v1` defined whitespace-only whole-table join,
leading identity/property precedence and reduced-rational common-column projection, but no native HWPX
adapter materialized the joined table.

`hwpx-agent.table-join-hwpx.hancom-2020-wrapper/1` adds a preserving adapter for two consecutive
top-level `hp:p/hp:run/hp:tbl` wrappers and the exact whitespace-only paragraph sequence between them.
It relifts both sources and rebuilds the domain result, renders each source onto one common lattice,
reopens both projected states, combines their rows, removes the exact separator and trailing wrapper,
and reopens the final joined table before publication.

Every master cell, projected span, payload, property, edge and diagonal remains bound. A leading-bottom
and trailing-top edge disagreement fails because one joined native shared edge cannot preserve both.
Sibling formulas and all non-target package parts remain exact.

Formula rebasing, different junction edges, repeat-header ownership and caption ownership are outside
this first exact profile and fail closed. Migration is additive and existing documents are not
rewritten in place. Static synthetic package success may not promote TABLE-011 to licensed Hangul
2020, renderer, automation, differential, rollback/retry, release, production or product PASS.
