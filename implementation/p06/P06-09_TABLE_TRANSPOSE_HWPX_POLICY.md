# P06-09 TABLE-021 table transpose HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and exact native profile

This profile lowers the complete `hwpx-agent.table-transpose/v1` TABLE-021 grid relocation into
one explicitly bound current-Hangul-2020 `hp:tbl`. It admits arbitrary non-empty rectangular
dimensions, rectangular merged cells and nonuniform physical row and column tracks. The target
swaps dimensions, every master coordinate and span axis, the table width and height, physical
boundary axes and every complete unit-edge axis.

Master-cell, payload-block and table logical IDs do not change. Ordered payload paragraphs,
complete non-ruling cell properties, background and both diagonal identities move with their
master cells. Slash and back-slash diagonal directions remain the same under x/y reflection;
horizontal unit edges become vertical and vertical unit edges become horizontal. Table properties,
position, page-split policy and caption are preserved.

The domain model continues to support typed formula transposition and cache clearing. This native
v1 adapter is intentionally narrower only where HWPX has no exact preserving representation:
formula-bearing source cells and nonzero repeat-header rows fail closed. It does not silently copy,
drop or approximate formulas, and it does not invent a repeat-header-column concept.

## Exact request and build binding

`TableTransposeHwpxRequest` carries the complete domain request plus the selected table ordinal,
header and section SHA-256, source ruling-state SHA-256, source grid SHA-256, current document-flow
SHA-256 and caller-bound target document-flow SHA-256. Payload and style digests are recomputed from
the complete typed cell payload/property values, not caller labels.

Admission validates every digest and every master record against a fresh readback. The builder
repeats those checks, rebuilds the authoritative domain plan and target grid, constructs the full
transposed physical state and binds all results into a bounded plan. A semantic no-op requires an
unchanged flow digest; every real grid or state transition requires a distinct target flow digest.

Immediately before mutation the lowerer relifts the same source, checks current flow and rebuilds
the plan. Source part, state, grid, payload, property, formula-free, pagination or plan drift returns
no output.

## Lowering, semantic reopen and preservation

The existing-table renderer reorders cells by target row-major master coordinates while retaining
their exact native content templates. It rewrites table dimensions, frame size, every cell address,
span and physical extent, and resolves the transposed four-sided edge state through the typed
border-fill catalog. New catalog entries, if required, are append-only and deduplicated.

The output binding is regenerated from the target state and grid. Publication occurs only after
header and section reparse proves the exact target `TableGrid` and `TableRulingState`, swapped
pagination dimensions, zero repeat headers, unchanged page-split policy and caption, unchanged
payload count and zero formulas. The table count must remain exact. A double-transpose test proves
the complete grid/state returns to the original value.

Closed-package tests replace only coordinated header/section parts and verify the package graph and
opaque non-target bytes. The source XML, package and caller binding are never mutated. Work,
serialization and output use the finite transpose, ruling, layout, style, formula, grid and
pagination limits. Debug surfaces omit all digests, logical IDs, payloads, formulas and raw XML.

## Evidence promotion rule

Passing the seven adapter tests and private contract tamper suite promotes only TABLE-021 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`. The validations are `schema`,
static `semantic_reopen`, formula-free `formula_readback` and `page_split` preservation.

This evidence does not prove renderer equivalence, a saved real HWPX, licensed Hangul 2020
open/save/reopen, target-build execution, rollback/retry, automation runtime, differential exact
match, formula-bearing native transpose, repeat-header conversion, arbitrary user documents,
another PC/version, P06-09 or P06 completion, production readiness or product completion.
