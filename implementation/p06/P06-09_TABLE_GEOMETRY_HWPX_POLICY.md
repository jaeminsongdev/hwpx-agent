# P06-09 table geometry HWPX adapter policy v1

Status: direct HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope

This adapter lowers the validated `hwpx-agent.table-geometry/v1` state for `TABLE-018`,
`TABLE-019` and `TABLE-050` into the current-PC Hancom 2020 HWPX XML profile. It accepts either a
standalone `hp:tbl` fragment or one table selected by zero-based document order in an `hs:sec`
part. Selection by application cursor or private automation identifier is outside this contract.

## Admission and lowering

- The geometry state must match the supplied canonical `TableGrid` SHA-256 and exact logical
  row/column counts.
- Source XML must use the reviewed Hancom 2020 paragraph/section namespaces, absolute table size,
  zero cell spacing, a complete nonoverlapping cell grid and the supported five-child cell shape.
- Integer micrometers are converted with the existing official HWP-unit conversion. Zero,
  overflowing and configured-over-limit dimensions fail before publication.
- Only the selected table's `hp:sz` width/height and each `hp:cellSz` width/height value may change.
  Master-cell sizes are checked sums of their covered logical tracks.
- The output is reparsed through the strict reader. Exact table/cell size readback, cell text/comment
  digest and inner margins must match the expected result before bytes or a receipt are returned.
- The disposable full-package fixture reopens a closed HWPX package graph after each of the three
  operations. It requires exact formula AST/cache and pagination-policy readback, exact hashes for
  every non-section part, source immutability and deterministic rebuilt package bytes.

## Integrity and failure behavior

The receipt binds profile, source/output, logical grid, geometry state, counts, dimensions and the
preserved content digest. Its Debug surface omits all hashes and raw dimensions. Standalone and
section lowering are deterministic and idempotent. A malformed source, wrong table ordinal, grid
drift, unsupported XML shape, content/readback drift, allocation failure or size-limit failure
returns no output.

## Evidence promotion rule

Passing the adapter and tamper suites promotes only `TABLE-018`, `TABLE-019` and `TABLE-050` to
`direct_hwpx / integration_passed` with `schema`, static `semantic_reopen`, `formula_readback` and
`page_split` evidence. It does not prove renderer identity, licensed Hangul 2020 save/reopen,
automation runtime, differential exact match, release-enabled status, P06-09/P06 PASS, production,
other-PC/version compatibility, or product completion.
