# P06 table-pagination pure v1 to HWPX adapter v1

Date: 2026-09-08

This is an additive current-PC Hangul 2020 adapter boundary. It does not mutate or replace
`hwpx-agent.table-pagination/v1` or its renderer-observation schema.

The adapter maps `allow`, `avoid_row`, and `avoid_table` to native `CELL`, `TABLE`, and `NONE`
respectively. `required_keep` has no exact table-level native representation and rejects. Repeated
headers are lowered to the table `repeatHeader` flag plus a contiguous prefix of rows whose direct
cells carry `header="1"`; mixed or non-contiguous source flags reject.

Existing top/bottom captions may change only their bounded native attributes while their semantic
content digest stays fixed. Caption creation/removal and left/right placement have no automatic
migration in V1. Unknown shapes, enum values, namespaces, or inconsistent flags reject without a
fallback.

The static adapter does not supply renderer observations. P06-07 remains open until the boundary
page suite and exact licensed Hangul 2020 save/reopen/PDF oracle pass. Other PCs and Hangul
versions remain unclaimed.
