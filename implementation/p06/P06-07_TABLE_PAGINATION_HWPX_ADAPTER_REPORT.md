# P06-07 current-PC Hangul 2020 table-pagination HWPX adapter report

Date: 2026-09-08

Decision: **PASS for the bounded static adapter component; P06-07 remains in progress**.

## Exact native boundary

Profile `hwpx-agent.table-pagination-hwpx.hancom-2020/1` reads a standalone `hp:tbl` or a table
selected by zero-based document order from one current-profile section. It maps native
`pageBreak` values exactly: `CELL` to `allow`, `TABLE` to `avoid_row`, and `NONE` to
`avoid_table`. Unknown enum values reject. The stronger pure `required_keep` policy has no exact
table-attribute mapping and rejects instead of being approximated.

Repeated headers are represented by both the table `repeatHeader` flag and a contiguous prefix of
rows whose direct cells all carry `header="1"`. The reader rejects mixed-header rows,
non-contiguous header rows, and flag/cell disagreement. The lowerer updates both layers and admits
any header-prefix count bounded by the source row count. This preserves the pure model's explicit
row count instead of silently reducing it to a Boolean.

An existing top or bottom `hp:caption` can have its `side`, `fullSz`, `width`, `gap`, and
`lastWidth` attributes updated. Its content is bound by a semantic-content SHA-256 and must remain
identical. Caption creation/removal and left/right caption flow are excluded from V1 because they
require structural insertion/deletion or a two-dimensional layout model.

## Preservation and failure policy

The adapter parses with the preserving XML layer, enforces finite input/output, element, table,
row, column, and HWPUNIT limits, and admits only the current paragraph and section namespaces. It
validates table child order, exact row count, direct cell/header shape, caption position and
cardinality, numeric and Boolean syntax, and known owned attributes.

Lowering edits only changed attribute-value spans. Source bytes are immutable; untouched markup,
whitespace, text, references, comments, and attribute quote/order remain byte-exact. The output is
reparsed and exact-compared with the expected typed readback. A repeated lower is byte-idempotent
and reports zero modified attributes.

Ten integration tests cover all three split mappings, one- and multi-row header prefixes,
idempotence, caption preservation, section selection, source/target mismatch, malformed shape,
enum/number/Boolean drift, and finite limits. The full package test and Clippy gates are recorded
in the repository plan ledger.

## Gate boundary

This component does not claim renderer behavior. The required boundary-page suite—one line before,
exactly at, and one line after the page boundary, plus merged cells, nested tables, and long
equation/image rows—has not yet run in licensed Hangul 2020. Save/reopen, PDF geometry, repeated
header rendering, row split/keep behavior, and caption placement therefore remain `NOT_RUN`.
P06-07, P06, production, other PCs, and other Hangul versions remain incomplete and unclaimed.
