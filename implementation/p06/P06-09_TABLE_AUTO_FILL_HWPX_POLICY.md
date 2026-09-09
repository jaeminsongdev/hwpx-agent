# P06-09 TABLE-057/058 table auto-fill HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and exact native profile

This profile lowers `hwpx-agent.table-auto-fill/v1` and its bound
`hwpx-agent.table-auto-fill-series/v1` into one explicitly identified current-Hangul-2020
`hp:tbl`. It admits any finite nonempty rectangular region whose cells are all unmerged and contain
exactly one paragraph and one run. Plain cells contain one text span without an inline text style.
Formula cells must match the existing exact native formula reader, including visible/cache parity.
Multiple paragraphs or runs, merged cells, opaque content and inline-styled spans fail closed.

## Scalar, series and formula semantics

The domain model remains authoritative for explicit cycles, exact linear fixed-decimal numbers and
linear civil-date days, row-major or column-major traversal, start index and overflow. The adapter
renders booleans as lowercase, integers canonically, decimals at their bound scale, and generated
dates as proleptic-Gregorian ISO `YYYY-MM-DD`. Visible source date-looking text is not inferred as a
date. When visible text equals the requested generated rendering, target-series typing wins; this
makes a text value such as `"true"` a byte-exact no-op instead of silently changing its type.

`Reject` refuses a selected formula. `ReplaceBound` removes the selected exact formula and replaces
its one run content. No formula engine is claimed. Before target construction, the adapter walks
cell, range, unary, binary and function expressions; if an unselected formula references any
actually changed selected cell, the operation fails closed rather than preserving a stale cache.

## Exact identity, preservation and lowering

Every request binds header and section SHA-256, selected table-content SHA-256, complete ruling
state and grid, selected scalar/style/formula state, pagination policy, source table count, series
SHA-256, and current/target document-flow SHA-256. Existing nonempty selected cells must retain
their logical payload ID. A blank or formula cell becoming nonempty requires a new explicit ID that
does not collide with the table, master-cell or payload namespace. Blank targets carry no payload.

The builder repeats all source and series checks, rebuilds the domain plan and constructs complete
target ruling and scalar states. A semantic no-op requires unchanged flow; a real change requires a
different target flow. Immediately before mutation, the lowerer relifts the source and rebuilds the
entire plan. It edits only the selected run-content spans with canonical escaped XML, preserving the
paragraph/run wrapper, cell properties, background, diagonals, complete edge lattice, grid,
unselected payload bytes, table properties, page split, repeat headers, caption and table count.

No output is returned until the same readers reopen the exact target state, grid, scalar values,
formula count, payload identities and pagination. Closed-package tests prove the package graph and
opaque non-target parts stay intact. JSON, XML, text, series work, formula traversal, allocation and
output growth remain independently bounded. Debug output omits content, values, logical IDs and all
integrity hashes.

## Evidence promotion rule

Passing the eight adapter tests and private contract tamper suite promotes only TABLE-057/058 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`. Admitted validations are
`schema`, static `semantic_reopen`, `formula_readback` and `page_split` preservation.

This does not prove render equivalence, a saved real HWPX, licensed Hangul 2020 execution,
target-build behavior, rollback/retry, automation, differential equality, native formula
recalculation, source date typing, rich/merged fill, arbitrary user documents, another PC/version,
P06-09 or P06 completion, production readiness or product completion.
