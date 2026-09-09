# P06-09 table text conversion policy v1

Status: pure bounded component implemented; TABLE-004/005 have separately governed static HWPX adapters; no Hangul 2020 oracle claim

## Scope

This policy covers the semantic text-grid boundary for:

- `TABLE-004` / `table.text_to_table`
- `TABLE-005` / `table.table_to_text`

V1 admits UTF-8 tab, comma and semicolon delimiters. It implements double-quote escaping, exact
rectangular rows, semantic LF inside cells and deterministic LF or CRLF output. It does not mutate a
document graph, create HWPX table XML or invoke Hangul.

## Semantics

Text-to-table accepts LF and CRLF record endings and standard doubled quotes inside quoted fields.
Record endings inside quoted fields normalize to semantic LF. A single final record ending is
accepted without inventing an additional row. Empty leading, middle and trailing fields remain
real cells.

Table-to-text minimally quotes fields containing the chosen delimiter, a quote or semantic LF,
doubles embedded quotes and uses the requested line ending both between records and inside quoted
fields. It emits no final record ending. Parsing the emitted bytes with the same delimiter restores
the exact semantic grid.

## Safety and determinism

- Input/output bytes, rows, columns, cells, per-cell bytes and canonical JSON are independently
  bounded under hard ceilings.
- Invalid UTF-8, bare CR, NUL, quotes in unquoted fields, trailing bytes after a closing quote,
  unterminated quotes and ragged rows fail closed.
- Allocation uses fallible reservations and errors return no partial grid or byte vector.
- Grid JSON rejects unknown and duplicate fields; canonical JSON and SHA-256 are deterministic.
- Debug output exposes only dimensions and redacts cell content.

## Evidence promotion rule

Passing Rust and contract/tamper tests promotes only TABLE-004 and TABLE-005 to
`component_only / unit_passed` with `schema` evidence. It cannot promote direct document-graph or
HWPX integration, merged-cell/style/formula preservation, semantic reopen, formula readback, page
split, render diff, licensed Hangul 2020 target-build, automation, differential exact match,
release-enabled, P06-09/P06 PASS, production or product completion.

TABLE-004 and TABLE-005 now have separately governed preserving adapters at
`P06-09_TABLE_TEXT_TO_TABLE_HWPX_POLICY.md` and `P06-09_TABLE_TABLE_TO_TEXT_HWPX_POLICY.md`.
This component report itself remains unit evidence and does not inherit either adapter's integration
result. Recommended reasoning remains `max` for the remaining P06-09 HWPX and target-oracle work.
