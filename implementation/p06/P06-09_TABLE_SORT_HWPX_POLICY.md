# P06-09 TABLE-056 table sort HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and exact native profile

This profile lowers `hwpx-agent.table-sort/v1` into one explicitly bound current-Hangul-2020
`hp:tbl`. It admits an arbitrary non-empty rectangular table with a complete unmerged grid and an
arbitrary rectangular row-or-column sort region. Every selected-table cell must contain exactly one
plain text paragraph under the shared text-conversion profile. Merged cells, formulas, multiple
paragraphs, controls, fields and opaque text elements fail closed.

The native adapter requires `TableFormulaMovePolicy::Reject`. This is an explicit formula-free profile,
not an implementation of formula move, verbatim-copy or relative-reference rebasing. The
domain model retains all three policies unchanged for a later separately qualified adapter.

## Sort values and relocation semantics

The reader derives comparison values only from exact lifted cell text. Empty text is blank; exact
lowercase `false` and `true` are booleans; canonical signed `i64` syntax is integer; canonical
fixed-decimal syntax is admitted only when scale is at most 18 and the coefficient fits `i64`.
Every other admitted NFC string is text. Date-looking strings remain text because this HWPX profile
has no reviewed native date-type marker. Numeric-looking values that exceed the exact numeric domain
fail closed instead of rounding or using floating point.

The domain sort remains authoritative: ordered keys retain caller precedence, each key binds
ascending or descending order, independent first/last blank placement and binary or
ASCII-case-insensitive text collation, and equal lines stay stable. The adapter moves complete row
or column lines inside the selected region. Master-cell identity, ordered payload blocks and their
exact bytes, complete non-ruling properties, background and both diagonal identities move together.
Table dimensions, physical boundaries, complete unit-edge lattice, table properties, unselected
cells, page-split policy, repeat-header count and caption stay at their physical document positions.

## Exact request, build and lowering binding

`TableSortHwpxRequest` binds the table ordinal, header and section SHA-256, table-content SHA-256,
complete source ruling-state and grid SHA-256, lifted text-grid SHA-256, pagination-policy SHA-256,
table count and current/target document-flow SHA-256. The semantic request is rebuilt from the
source payload identities and exact classified text; caller-supplied comparison snapshots are not
trusted.

The builder repeats source validation, rebuilds the bounded domain sort plan, verifies every
source/destination/payload relocation and constructs exact target grid, ruling state and text grid.
All source and target digests are included in the bounded deterministic plan. A semantic no-op must
keep the document-flow digest unchanged; a real permutation must bind a distinct target digest.

Immediately before mutation the lowerer relifts the source parts, rechecks current flow and rebuilds
the entire plan. It moves the exact native cell templates, regenerates the target binding and returns
nothing until a complete adapter reopen proves target grid, target ruling state, target text grid,
formula absence, table count, page-split policy, repeat headers and caption. No-op lowering returns
the original header and section bytes exactly.

Closed-package tests replace only the coordinated header and section parts, then verify the package
graph and every opaque non-target part byte. Input XML, packages and bindings are never mutated.
JSON, cell selection, text, comparison work, ruling, grid, formula, pagination, serialization and
output growth all retain independent finite ceilings. Debug output omits text, raw XML, logical IDs
and every integrity digest.

## Evidence promotion rule

Passing the seven adapter tests and private contract tamper suite promotes only TABLE-056 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`. The admitted validations are
`schema`, static `semantic_reopen`, formula-free `formula_readback` and `page_split` preservation.

This evidence does not prove renderer equivalence, a saved real HWPX, licensed Hangul 2020
open/save/reopen, target-build execution, rollback/retry, automation runtime, differential exact
match, formula-bearing native sorting, locale-sensitive Hancom collation, native date inference,
rich-content or merged-cell sorting, arbitrary user documents, another PC/version, P06-09 or P06
completion, production readiness or product completion.
