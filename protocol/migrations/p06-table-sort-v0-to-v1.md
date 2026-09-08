# P06 table sort v0 to v1

`hwpx-agent.table-sort/v1` is an additive pure-domain contract for TABLE-056. Existing documents,
table grids and prior P06 schemas are not rewritten.

Callers must now provide an exact merge-free region, complete cell payload/formula digests, typed
sort values, ordered keys and an explicit formula movement policy. V1 emits a bounded whole-cell
relocation plan and hash-bound receipt or fails with no partial plan.

Native HWPX lifting/lowering, locale-sensitive collation, formula rebasing, Hangul 2020 execution
and renderer evidence remain separately versioned successor boundaries.
