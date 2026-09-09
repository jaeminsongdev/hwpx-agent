# P06-09 TABLE-005 table-to-text HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope and exact native profile

This profile converts one explicitly bound top-level current-Hangul-2020 table wrapper into both a
bounded deterministic delimited UTF-8 result and one replacement HWPX text paragraph. It admits any nonzero bounded rectangular unmerged grid whose master cells each contain exactly one empty scaffold
or one complete supported plain-text paragraph. Text spans, tabs and line breaks across runs are read
completely and normalized to NFC. Multiple paragraphs, fields, opaque controls, nested tables,
captions, merged cells and formulas/caches fail closed because V1 has no reviewed lossless flattening
semantics for them.

The source table may carry arbitrary admitted ruling edges, cell properties, payload identities,
physical tracks, page-split policy and a valid contiguous repeat-header prefix. Those values are not
silently ignored: the complete typed source state/grid, exact table bytes and pagination readback are
bound before the intentionally destructive table removal. The caller supplies one output text-block
logical ID that must be distinct from the table, every master and every payload ID.

The complete `TableTextGrid` writer supports tab, comma and semicolon delimiters, minimal quoting,
doubled quotes, multiline cells, empty cells and LF or CRLF output without a final record ending. The
returned byte vector preserves the selected line ending exactly. HWPX represents both LF and CRLF
record endings as typed `hp:lineBreak` semantic atoms; CRLF is therefore intentionally normalized to
one document line-break atom while its returned external bytes remain exact.

## Exact binding, lowering and reopen

The request binds source header/section, table and containing paragraph ordinals, exact wrapper and
table bytes, wrapper context, full typed state/grid/text grid, serialized bytes, target paragraph,
source table count, delimiter, line ending, current/target document-flow SHA-256 and output identity.
Request admission and build independently recheck all bindings. The plan carries the complete source
state and private exact grid, returned bytes, target flow and target paragraph alongside their hashes.

Immediately before mutation the lowerer rereads the source, reconstructs the text grid and serialized
bytes, revalidates the wrapper and current flow, and rebuilds the plan. It replaces only the bound
top-level wrapper paragraph, preserving that paragraph's admitted ID/property/style and run character
property identity. Output is returned only after exact paragraph-byte and typed-flow reopen, NFC
visible-text comparison and an exact one-table count decrement.

Closed-package tests preserve header bytes, every opaque non-target part, manifest/spine/container
relationships, the unrelated table and every byte outside the selected wrapper. Inputs are borrowed
and never mutated. XML, allocation, text, state, grid, JSON and output work is finite. Duplicate and
unknown JSON fails closed. Debug omits text, hashes, logical IDs, raw XML and document content.

## Evidence promotion rule

Passing the seven adapter tests and private contract tamper suite promotes only TABLE-005 from
`component_only / unit_passed` to `direct_hwpx / integration_passed` with `schema`, static
`semantic_reopen`, formula-free `formula_readback` and source-pagination classification.

It does not prove merged-cell expansion, formula/cache flattening, caption/nested-table conversion,
render equivalence, a saved real HWPX, licensed Hangul 2020 execution, target-build, rollback/retry,
automation, differential exact match, arbitrary wrappers or user documents, another PC/version,
P06-09/P06 completion, production or product completion.
