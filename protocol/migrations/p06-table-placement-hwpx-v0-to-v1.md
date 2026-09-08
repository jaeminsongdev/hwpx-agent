# P06 table placement HWPX v0 to v1

Before this profile, `hwpx-agent.table-placement/v1` modeled position, attachment, wrapping and
outside margins but had no native HWPX read/lower boundary.

`hwpx-agent.table-placement-hwpx.hancom-2020/1` adds a preserving adapter for one standalone
`hp:tbl` or one zero-based table selected inside `hs:sec`. The strict layout reader admits the full
grid/cell shape first. The adapter then reads every required current-profile `hp:tbl`, `hp:pos` and
`hp:outMargin` value. Missing, duplicate, unknown, noncanonical or over-limit values are not coerced.

Migration is additive. Existing documents are not rewritten. A caller supplies exact source and
target `hwpx-agent.table-placement/v1` states with the same logical table ID. Native source
readback must match the active source state. It returns bytes only after strict output reparse,
target-state readback and content-digest preservation succeed.

Inline and floating modes intentionally preserve their respective inactive native fields. Older
callers must not synthesize defaults for those fields. Static adapter success may not promote any
row to a licensed Hangul oracle, automation, differential, release, production or product PASS.
