# P06-09 table text conversion report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-text-conversion/v1`
- Scope: current repository, pure local delimited-text component
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now parses bounded UTF-8 tab/comma/semicolon text into an exact rectangular semantic
grid and serializes that grid back deterministically. Quoted delimiters, doubled quotes, multiline
cells, empty cells, Unicode, LF and CRLF are covered. Writer output reparses to the same grid.

The parser rejects malformed quotes, bare carriage returns, NUL, invalid UTF-8, ragged records and
all configured size breaches. The validated grid rejects malformed/unknown/duplicate JSON fields,
bounds canonical output and redacts content from Debug.

## Verification

| Check | Result |
|---|---:|
| Dedicated component tests | 9/9 PASS |
| Tab/comma/semicolon semantic roundtrip | PASS |
| Quotes, Unicode, empty and multiline cells | PASS |
| LF/CRLF normalization and deterministic output | PASS |
| Invalid encoding/quote/line/control/ragged negatives | fail closed |
| Input/output/row/column/cell/cell-byte/JSON limits | fail closed |
| Canonical JSON and SHA-256 determinism | PASS |
| Debug cell-content disclosure | redacted |

## Conformance impact

After hash admission, the strict matrix changes only as follows:

- direct `cataloged`: 20 to 18
- direct `unit_passed`: 23 to 25
- direct `integration_passed`: remains 7
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

This is unit-level evidence. No HWPX XML, user document or Hangul process was touched. Document
graph/HWPX lowering, preservation/readback, pagination/rendering, target-build save/reopen,
automation and differentials remain open. P06-09, P06, production and the product remain in
progress.

TABLE-004 subsequently gained separate static direct-HWPX integration evidence under
`P06-09_TABLE_TEXT_TO_TABLE_HWPX_REPORT.md`. That later result does not rewrite this component run;
TABLE-005 subsequently gained its own static direct-HWPX integration evidence under
`P06-09_TABLE_TABLE_TO_TEXT_HWPX_REPORT.md`. Neither later result rewrites this component run, and
licensed Hangul/render evidence remains open.
