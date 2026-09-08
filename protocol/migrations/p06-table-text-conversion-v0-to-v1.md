# P06 table text conversion migration: v0 to v1

`v0` had no independently versioned text-grid conversion boundary. Callers must now use
`hwpx-agent.table-text-conversion/v1` and choose one of the admitted tab, comma or semicolon
delimiters.

## Required migration

1. Treat input as bounded UTF-8, not locale-dependent bytes.
2. Use doubled quotes for quotes inside quoted fields and reject malformed quote transitions.
3. Normalize LF/CRLF inside quoted cells to semantic LF; reject bare CR.
4. Preserve empty fields and require a nonempty rectangular grid.
5. Bound input/output bytes, rows, columns, total cells, per-cell bytes and canonical JSON.
6. Serialize with an explicit LF or CRLF policy, minimal quoting and no final record ending.
7. Treat syntax, allocation and limit errors as atomic failures with no partial output.

This migration may not promote document-graph, HWPX or licensed Hangul 2020 support. Those require
a separately versioned preserving adapter and target-backed oracle evidence.
