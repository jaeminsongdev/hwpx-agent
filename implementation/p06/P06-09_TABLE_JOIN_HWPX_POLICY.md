# P06-09 TABLE-011 whole-table join HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Exact admitted profile

This profile maps TABLE-011 `table.join_table` from the complete
`hwpx-agent.table-partition/v1` domain result into two adjacent reviewed current-Hangul-2020
top-level `hp:sec/hp:p/hp:run/hp:tbl` wrappers. The wrappers must be consecutive table ordinals and
must have one or more intervening top-level `hp:p/hp:run/hp:t` paragraphs. Each text node is empty
or contains ASCII spaces only; the exact separator bytes and semantic space/paragraph token sequence
are both bound. Text, references, comments, controls, objects, nested elements or a missing paragraph
boundary fail closed.

The selected tables must be formula-free, caption-free and have zero repeat-header rows. Their
supported page-split values must agree. Formula rebasing/cache clearing and repeat-header/caption
ownership after joining require separate native qualification and are not guessed. The leading
logical/native table identity, position and table properties survive; the trailing table object and
the exact separator paragraphs are removed. No new native table or paragraph identity is allocated.

## Common lattice and complete state

Different widths and column counts are admitted through the authoritative reduced-rational boundary
union in the domain plan. The larger source width becomes the output width, cumulative rational
positions use deterministic half-up HWPUNIT materialization, and any collapsed track fails closed.
Every source master span is projected to the common lattice without creating or dropping a cell.

Both source tables are first rendered independently onto that common lattice using their own exact
cell templates. Existing horizontal edges are expanded across projected tracks; existing vertical
edges are mapped to their rational boundary and newly introduced intra-cell boundaries are
nonstructural transparent edges. The leading bottom and trailing top edge must be identical at every
projected track, because one joined shared edge cannot preserve two different line identities.
Mismatch is therefore a typed failure. Row heights are concatenated exactly, and every payload block,
complete cell property, background, diagonal and logical identity remains attached to its master cell.

## Exact request/build/lower binding

`TableJoinHwpxRequest` binds header SHA, section SHA, both wrapper SHAs, separator SHA, both table
ordinals, both complete partition states and grids, table identities, exact separator tokens, formula
policy and document-flow SHA. Request construction and build independently validate source and flow.
The lowerer relifts both sources and rebuilds the authoritative domain and native plan immediately
before any output is returned.

Both projected tables reopen semantically before their row XML is combined. The combined table then
rewrites every cell address/span against the authoritative joined grid, removes only the separator and
trailing wrapper, and reopens through the strict ruling, partition and pagination readers. The receipt
binds source/output parts, both wrappers, separator, joined state, request, plan, before/after flow and
exact preserved/removed counts. JSON is bounded and rejects empty, oversized, malformed, unknown and
recursive duplicate keys. Debug omits hashes, IDs, payloads, formula/cache content and raw XML.

## Preservation and evidence boundary

Sibling tables, sibling formula owner/AST/number-format/display-cache state, trailing document flow
after the removed wrapper, and every non-target package part remain exact. Failure returns no partial
header, section, binding or receipt.

Passing the seven adapter tests and private tamper suite promotes only TABLE-011 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with `schema`, static
`semantic_reopen`, sibling `formula_readback` and `page_split`. This evidence does not prove render
identity, a saved real HWPX, licensed Hangul 2020 execution, target build, formula-bearing join,
repeat-header/caption join, rollback/retry, automation runtime, differential exact match, arbitrary
user documents, another PC/version, P06-09/P06 completion, production or product completion.
