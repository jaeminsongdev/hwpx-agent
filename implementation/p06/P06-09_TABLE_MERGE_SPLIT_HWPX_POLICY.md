# P06-09 TABLE-016/017 merge/split HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and topology authority

This profile maps the complete `hwpx-agent.table-merge-split/v1` domain result for TABLE-016
`table.split_cell` and TABLE-017 `table.merge_cells` into the reviewed current-Hangul-2020 HWPX
table shape. The domain grid remains authoritative. The adapter never infers a convenient subset
from cursor position or raw XML coordinates.

Merge requires an exact rectangular logical slot set, preserves the top-left master identity and
retires every other fully selected master. Split requires one exact master, an evenly divisible
row/column subdivision and the exact row-major new identities. Every normalized unit edge is
classified from before/after slot ownership: merge removes only edges that become internal, and
split adds only edges that become structural. An inverse transition is a plan mismatch.

## Content and native admission

All four content policies are delegated to the domain result. Merge `Concatenate` and `Distribute`
retain every selected block in stable row-major cell/block order; `First` keeps only top-left
content and receipts every discard; `RejectIfMultiple` fails when more than one selected cell is
nonempty. Split `Distribute` assigns stable balanced contiguous chunks; the other policies keep all
content in the preserved top-left result.

A split line is an explicit SHA-256 identity already present in the source header edge-line
catalog. It is not guessed or synthesized from a caller label. Split cells inherit the exact source
cell properties. Merge is admitted only when every selected complete cell-property value is
identical. Selected formulas or visible diagonals fail closed because combining or subdividing them
would require semantics outside this reviewed profile.

## Exact request/build/lower binding

`TableMergeSplitHwpxRequest` binds table ID, complete source ruling-state SHA, grid SHA, content
ownership SHA, document-flow SHA and the complete operation. Construction and build both validate
those bindings and rebuild the authoritative domain result. The plan binds domain receipt, complete
target state and target grid/content/state digests.

`TableMergeSplitHwpxPartBinding` additionally binds header, section, source state/grid/content,
request and plan. Immediately before mutation the lowerer verifies all part and flow identities,
relifts the source, rebuilds the plan and compares it exactly. Output exists only after the same
strict reader reproduces the target grid, ruling state and content ownership.

## Preservation, formula boundary and privacy

Paragraph blocks are carried as their original byte spans and are only reordered, redistributed or
explicitly discarded as required by the selected policy. Unselected cell properties, formula
owner/AST/number-format/display cache, diagonal state, physical boundaries, table properties,
pagination, sibling tables and other package parts remain exact. A merged topology containing one
unselected supported formula is read only through the preserving ruling path; the public formula
mutation profile remains unchanged and selected formula mutation remains rejected.

JSON input/output, XML work, layout, formula, grid, ruling and catalogs remain finite. Custom Debug
surfaces omit hashes, logical IDs, payloads, formulas, caches and raw XML. No partial header,
section, binding or receipt is returned on failure.

## Evidence promotion rule

Passing the six adapter tests and private tamper suite promotes only TABLE-016 and TABLE-017 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, `formula_readback` and `page_split`. It does not prove render identity, licensed
Hangul 2020 save/reopen or target build, rollback/retry, automation runtime, differential exact
match, arbitrary user documents, another PC/version, P06-09/P06 completion, production or product
completion.
