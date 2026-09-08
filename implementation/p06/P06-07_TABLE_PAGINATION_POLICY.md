# P06-07 table pagination policy v1

Date: 2026-09-08

Decision: **pure, bounded table-pagination observation validator implemented; no renderer claim**

## Purpose

The P06-07 core validates an already observed page layout against one logical `TableGrid`. It does
not predict line breaking or invent page numbers. A target renderer adapter must produce the
observation, and the same target build must later prove it by save, reopen, and PDF readback.

## Policy

`TablePageSplitPolicy` has four semantic values:

- `allow`: the table and eligible rows may split across pages.
- `avoid_row`: the table may split only between complete cells/rows. A page boundary may not cross
  a vertically merged cell.
- `avoid_table`: the whole table must remain on one page.
- `required_keep`: the whole table must remain on one page and an attached caption, when present,
  must carry `keep_with_table=true`.

Every row has an exact positive height and a typed split eligibility: `allowed`, `forbidden`,
`nested_table`, or `unbreakable_object`. These values are policy inputs, not renderer inference.
Nested tables and unbreakable equations/images never degrade to ordinary split rows.

## Repeat header

`repeat_header_rows` is a zero-based contiguous prefix length. A master cell beginning in the
header prefix may not extend into the body. The first page carries the logical header rows as normal
rows; every continuation page must begin with one exact copy of each configured header row in
ascending order. Copies consume page capacity but do not duplicate logical row coverage.
Logical header rows themselves may not fragment across pages.

## Caption and keep

V1 admits vertical captions only:

- `top`: exactly one caption item precedes the first logical row on the first observed page.
- `bottom`: exactly one caption item follows the final logical row on the last observed page.

The caption binds a lowercase SHA-256 of its semantic content, positive block height, nonnegative
gap, and explicit `keep_with_table`. Caption block height plus gap consumes page capacity. Left and
right captions need a two-dimensional flow model and are not silently approximated by V1.

## Observation invariants

- Pages are nonempty and have contiguous indexes beginning at `anchor_page_index`.
- Every logical row appears exactly once as an ordered sequence of one or more fragments.
- Fragment indexes start at zero, `begins_row` and `ends_row` are canonical, and fragment heights
  sum exactly to the declared row height.
- A continued row resumes on the immediately following page before any new logical row.
- Header copies, row fragments, caption block, and caption gap must fit the exact available height.
- The first page and continuation pages have separate positive capacity values.
- Missing rows, duplicate/out-of-order rows, wrong headers, illegal merged/nested/object splits,
  caption drift, arithmetic overflow, and over-limit input fail closed.

## Determinism and bounds

Policy, observation, logical grid, and validation receipt each have deterministic bounded JSON and
SHA-256 bindings. Defaults cap rows at 10,000, pages at 20,000, fragments at 1,000,000, dimensions
at 1,000,000,000 micrometers, and serialized data at 32 MiB. Hard ceilings remain finite.

## Evidence

The Rust boundary suite covers exact page capacity, one micrometer before and after the boundary,
row splitting, repeated headers, vertically merged cells, nested-table and unbreakable-object rows,
top/bottom captions, required keep, malformed JSON, incomplete rows, and public error codes.

## Not claimed yet

- No current Hangul 2020 page count, bounding box, save/reopen, or PDF has been validated by this
  pure component.
- The separate current-PC Hangul 2020 HWPX adapter profile now maps the bounded native attributes,
  but this pure component does not promote adapter or renderer evidence into its receipt.
- No left/right caption layout, arbitrary document compatibility, other PC/version, P06-07
  completion, P06 completion, production, or product completion is claimed.
