# P06-09 table sort component policy v1

Status: pure bounded component implemented; no HWPX or Hangul 2020 oracle claim

## Scope

This policy covers `TABLE-056` / `table.sort_cells`. The component accepts one exact logical table
ID, one canonical `TableGrid`, one rectangular merge-free region, ordered sort keys and a complete
cell snapshot. It produces a destination-ordered whole-cell relocation plan; it does not patch an
HWPX package, automate Hangul or claim renderer behavior.

## Sort semantics

Rows or columns are sorted as complete lines. Every selected cell carries the SHA-256 of its full
payload, an optional formula SHA-256 and a typed sort value. Relocations therefore bind the whole
cell rather than rebuilding only visible text or leaving style/formula state behind.

Sort keys retain caller order as semantic precedence. Each key has its own ascending/descending
direction, first/last blank placement and either binary or ASCII-case-insensitive text collation.
Blank placement is not reversed by descending order. Lines equal under every key retain original
order through an explicit original-index tie break.

Nonblank values use a deterministic total order: boolean, numeric, date-day and text. Integer and
fixed-decimal values share one exact numeric domain; trailing-zero decimals are canonicalized,
scale is limited to 18 and comparison uses checked-width integer arithmetic, never floating point.
Text collation is explicitly limited and
does not pretend to implement locale-sensitive Hancom collation.

Merged selections fail closed. A later HWPX adapter must either reject formulas, move their
expression verbatim, or rebase relative references according to the request's explicit
`TableFormulaMovePolicy`. This component binds that policy and each formula digest but does not
claim formula readback.

## Safety and determinism

- JSON is exactly `hwpx-agent.table-sort/v1`; empty, oversized, malformed, duplicate and unknown
  input fails closed.
- The region must be ordered, inside the exact grid and covered once by the supplied cell set.
- Payload and formula digests must be lowercase canonical SHA-256 values.
- Cell count, key count, individual text bytes, estimated comparison work and serialized bytes all
  have independent finite ceilings.
- The source grid SHA-256, request SHA-256 and relocation SHA-256 are bound into the receipt.
- No partial plan is returned after any validation, work or output-limit failure.
- Debug output redacts logical IDs, cell values, payload/formula digests and receipt hashes.

## Evidence promotion rule

Passing Rust and contract/tamper tests promotes only TABLE-056 to
`component_only / unit_passed` with `schema` evidence and happy, boundary, negative and
preservation fixtures. It cannot promote direct HWPX integration, semantic/formula/page readback,
render diff, licensed Hangul 2020 target-build, automation, differential exact match,
release-enabled, P06-09/P06 PASS, production or product completion.

The next boundary is a preserving HWPX adapter that lifts comparison values from exact cell
content, verifies payload/formula hashes, applies the relocation atomically and reopens every
formula and page policy. Recommended reasoning remains `max`.
