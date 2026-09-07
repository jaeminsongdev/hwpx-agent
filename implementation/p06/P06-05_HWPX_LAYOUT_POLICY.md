# P06-05 HWPX table-layout adapter policy

Date: 2026-09-07

Scope: current-PC Hangul 2020 HWPX width/height lowering and semantic readback component. This is a
successor to the pure `domain_ir::TableLayoutSolver`. The active exact-build contract is
`hwpx-agent.table-layout-hwpx.hancom-2020/2`; immutable `/1` remains its hash-bound predecessor.
This component is not P06-05 completion.

## Admission boundary

`hwpx_package::TableLayoutHwpxLowerer` first requires `TableLayoutPlan::require_verified()` and an
exact canonical `TableGrid` digest match. Estimated or missing font evidence, nonfit receipts,
column/row cardinality drift, inconsistent plan totals, and a plan generated for another grid all
fail before source mutation.

The HWPX reader accepts a standalone `hp:tbl` or one zero-based table in an exact `hs:sec`. The
current profile requires absolute table width and height, `cellSpacing="0"`, positive bounded
dimensions, declared row and column counts, and direct `hp:tr`/`hp:tc` structure. Each cell must
contain exactly one `cellAddr`, `cellSpan`, `cellSz`, `cellMargin`, and `subList`; their existing
source order is preserved because layout owns none of that ordering. Addresses and spans must form
one gap-free, nonoverlapping grid exactly equal to the requested `TableGrid`. Unknown direct shape,
wrong namespaces, duplicate or unknown owned attributes, malformed values, gaps, overlaps and
out-of-range spans reject without repair.

V2 also reads the exact inherited `hp:inMargin` values into `TableInnerMarginReadback`. Left,
right, top and bottom are unsigned HWPUNIT values; zero is valid and every value is bounded by the
configured scalar dimension ceiling. The product solver converts the exact left/right values into
its per-cell margin input instead of assuming a default.

## Quantization and mutation

Every solved logical column width and estimated row height is converted independently from checked
micrometers to HWPUNIT using the domain unit conversion. The stored table width and height are exact
checked sums of those quantized vectors. Each master cell, including merged cells, receives the
exact checked sum of the columns and rows covered by its span. This keeps every cell boundary on the
same quantized grid and prevents independent table/cell rounding drift.

Only existing `hp:sz` `width`/`height` and every selected table cell's `hp:cellSz`
`width`/`height` attribute value spans may change. No element, attribute, row, cell, margin,
formatting, paragraph, text, field, sibling table or package part is created, removed, reordered or
normalized. Standalone and full-section entry points share the same parser, validator and edit
engine.

## Readback, receipt and limits

The complete output is reparsed under the same finite limits. Table dimensions, all four inherited
inner margins, every canonical master-cell address/span/dimension and the pre-edit content-token SHA-256
must match exactly. A
receipt binds the profile, source, output, grid, verified plan and content digests plus bounded
counts and dimensions; it contains no visible cell text.

Defaults are 8 MiB input and output, 131,072 XML elements, 4,096 tables, 32,768 cells, 10,000 rows,
1,024 columns, 1,000,000 grid slots, and 100,000,000 HWPUNIT per scalar dimension. Hard ceilings,
checked allocation, arithmetic and edit spans prevent callers from disabling the bounds.

The component suite covers exact ordinary and merged-cell lowering, selected-table isolation,
idempotence, deterministic output, unverified-plan rejection, exact grid binding, gap/overlap/span
drift, relative sizing, nonzero spacing, unknown shape, malformed values, every finite limit,
stable diagnostics, exact readback and proof that no unrelated source byte changes.

## Exact target fixture

The bounded target builder binds the exact current-PC synthetic source, the exact installed
`함초롬바탕` 10 pt metric receipt, the four target text hashes and the verified 70,000 micrometer
layout plan. Three independent create-new outputs are byte-identical. `Preview/PrvText.txt` is
rewritten to the target strings. The source-derived `Preview/PrvImage.png` remains preserved and is
explicitly not visual evidence; only a fresh Hangul save and exported PDF can refresh and validate
the rendered preview.

## Not claimed yet

The current target fixture's actual Hangul 2020 readback and PDF comparison are **NOT RUN**. This
boundary does not claim actual Hangul 2020 line/page/render equality,
row minimum or fixed-height solving, equal-row/equal-column operations, pagination, formulas,
arbitrary shape repair, arbitrary user documents, another PC or Hangul version, P06-05 completion,
P06 completion, production, or product completion. Those remain separate gates.
