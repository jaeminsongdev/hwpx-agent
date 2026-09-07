# P06-05 Table sizing and autofit policy

Date: 2026-09-07

Scope: deterministic pure layout solver component for the current-PC P06 implementation. This is
not a P06-05 card-completion report and does not replace the still-pending P06-04 Hangul readback.

## Exact boundary

`domain_ir::TableLayoutSolver` consumes one already validated `TableGrid`, one finite body width,
one exact table-width specification, exactly one constraint per logical column and exactly one
measurement per canonical master cell. It never opens or rewrites an artifact and never calls
desktop automation.

The width specification implements all four document-model modes:

- `absolute`: an exact micrometer target;
- `percent`: a positive bounded ratio in millionths, resolved against the supplied body width with
  integer half-up rounding;
- `fit_content`: grow from hard minimums toward measured preferred widths without filling unused
  body width;
- `fit_page`: use the body width as an exact target while preserving fixed columns.

Every logical column has positive `minimum_width`, `preferred_width >= minimum_width`, a positive
`previous_width`, and either an automatic width or a positive fixed width not below the column
minimum. All physical values use checked `LengthMicrometers`; negative, zero where prohibited,
over-ceiling, overflowing, mismatched, duplicate and missing inputs fail closed.

## Minimum and preferred constraints

A cell's hard outer minimum is leading margin + trailing margin + unbreakable content width. The
solver first establishes column minimums and fixed widths, then visits the grid's canonical master
cell order. A spanning-cell minimum deficit is distributed evenly, with the one-micrometer remainder
assigned by ascending column index, only across automatic columns in that span. Fixed widths are
never changed and hard minimums are never shrunk to make a result appear to fit.

After the minimum plan is fixed, remaining target capacity is distributed proportionally toward
column and spanning-cell preferred widths. An exact target then moves automatic columns toward their
previous widths before any final even fill. This is a deterministic approximate objective in this
order: body/target/content constraint violations, estimated wrapped row height, then change from
previous column widths.

An over-wide minimum plan is returned with exact `body_overflow` and/or `target_overflow`. A cell
whose fixed-only span cannot meet its hard minimum receives an exact `CellWidthDeficit`. An exact
absolute, percent, or fit-page target with no adjustable capacity receives `target_underfill`.
`require_verified` rejects each of these states; no silent shrink, clipping, fallback or partial
mutation is permitted.

## Font metric evidence and row estimate

Every cell measurement carries `FontMetricEvidence`. `verified` and `estimated` evidence require a
bounded non-control profile ID and an exact lowercase SHA-256 source digest. `missing` evidence must
carry neither. The canonical plan binds the ordered evidence into
`font_metric_evidence_sha256`. A plan is `Verified` only when every cell is backed by `verified`
evidence; estimated or missing metrics always remain `Unverified` and `require_verified` fails.

Wrapped line count uses the measured preferred content width divided by the solved content width.
Each cell's checked line height is distributed over its row span and canonical row heights take the
maximum contribution. These heights are an approximate objective receipt, not a claim about Hancom
line breaking.

## Determinism, limits and evidence

The solver binds the exact canonical `TableGrid` SHA-256, ignores caller ordering of cell
measurements, and emits bounded canonical JSON plus SHA-256. Defaults are 1,024 columns, 1,000,000
master cells, 10,000 rows, 1,000,000,000 micrometers per scalar dimension and 32 MiB serialized
output. Hard ceilings prevent a caller from disabling finite bounds.

The component suite covers fixed and automatic columns, merged spans, body and target overflow,
fixed-only content deficit, exact-target underfill, all four width modes, verified/estimated/missing
font evidence, provenance drift, malformed shapes, output bounds, input-order independence and a
128-case deterministic overflow/metric corpus.

## Not claimed yet

This boundary does not claim actual installed-font extraction, Hancom 2020 line/page equality,
HWPX width/height lowering or readback, row minimum/fixed-height solving, equal-row/equal-column
operations, pagination, formulas, arbitrary documents, another PC or Hangul version, P06-05
completion, P06 completion, production, or product completion. Those require separate target-bound
implementation and evidence.
