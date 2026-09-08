# P06-09 whole-table split and join policy

- Features: TABLE-010 `table.split_table`, TABLE-011 `table.join_table`
- Model contract: `hwpx-agent.table-partition/v1`
- Scope: pure bounded semantic component for the current-PC local-development branch
- Current direct stage: `component_only / unit_passed`

## Source meaning and feature boundary

These operations change whole-table and surrounding paragraph topology. They are deliberately
separate from TABLE-016/017 cell split/merge. Hancom's official help defines whole-table split at
the row containing the cursor: that row becomes the first row of the second table, and the first
row cannot be used as a split boundary. Both resulting tables inherit the original table
properties.

Whole-table join searches below the leading table and admits only spaces and forced paragraph
breaks between the two tables. Text, drawings, text boxes or other non-table content block the
operation. The trailing rows are appended below the leading table, the joined table retains the
leading table properties, and its width becomes the larger source width.

References:

- https://help.hancom.com/hoffice110/ko-KR/Hwp/table/table(dividing).htm
- https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/table(attach).htm
- https://help.hancom.com/hoffice/multi/ko_kr/hwp/toolbox/object_table.htm

## Complete state and exact bindings

`TablePartitionState` contains the table logical identity, exact canonical `TableGrid` digest,
table-property digest, HWPUNIT table width, one positive width per logical column and one complete
record for every master cell. Each cell record binds its logical identity and master coordinate to
payload, cell-property and optional validated `FormulaCell` state. Missing, duplicate, extra or
coordinate-mismatched cells, invalid digests, inconsistent column sums and formula-owner drift fail
before a request exists.

Both requests bind the exact pre-state SHA-256 and surrounding document-flow SHA-256. A split also
binds the cursor, new table identity and separating paragraph identity. A join binds both table
states plus the exact intervening token sequence. IDs, document text and digests are redacted from
Debug surfaces.

## TABLE-010 split semantics

The cursor row is the only split boundary; caller-supplied row/column counts or a vertical split are
not accepted as whole-table semantics. The leading table retains its identity and rows before the
boundary. Rows from the cursor row onward move to a newly identified second table, with master-cell,
payload and cell-property identities preserved and row coordinates rebased.

A row-spanning merged cell that crosses the boundary is rejected rather than cut or duplicated.
Validated formulas are either rejected explicitly or rebased into their resulting table while
their caches are cleared. Any formula reference that would cross the new table boundary fails
closed. Both table states retain the original width, column tracks and table-property identity. The
plan creates exactly one second table and one separating paragraph; it never mutates the source.

## TABLE-011 join semantics

The separator grammar admits only positive space runs and paragraph breaks and requires at least
one paragraph break. Content/object tokens, empty tokens and over-limit gaps are typed failures.
The leading table identity and table-property identity survive; the trailing table object and gap
are removed, while every master cell, payload and cell-property identity survives.

Different source column counts and widths are supported by constructing the union of their exact
reduced-rational column boundaries. Source spans are projected onto that common lattice and the
larger source width becomes the output width. Rational boundaries are deterministically rounded to
HWPUNIT at half-up cumulative positions; if two boundaries collapse, the direct plan is rejected
instead of inventing or losing a column. Formulas are projected through inserted common-lattice
columns and appended rows with cleared caches.

## Determinism, preservation and failure behavior

States, requests and lowering-ready plans use deterministic compact bounded JSON and SHA-256.
Receipts bind before/after state and flow identities, row/column/width outcomes, preserved master
cells, payloads and cell properties, formula/cache changes, property inheritance, and created or
removed topology counts. Invalid limits, versions, JSON, identifiers, state/grid drift, separator
content, merged boundaries, formula transforms, output size or allocation return typed errors with
no partial plan or receipt.

No user document, HWPX package, Hangul process, registry, printer, trust store, network service or
system setting is read or changed by this component.

## Evidence boundary

This slice proves only the bounded logical planner for TABLE-010/011. It does not prove HWPX
section XML lowering, package mutation/preservation, semantic reopen, formula readback, pagination,
rendering, licensed Hangul 2020 execution, desktop automation or differential equivalence. Both
rows move only from `cataloged` to `unit_passed`; they remain non-green and P06-09, P06 and the
product remain in progress.

The next HWPX/preservation/oracle work remains at reasoning level max.
