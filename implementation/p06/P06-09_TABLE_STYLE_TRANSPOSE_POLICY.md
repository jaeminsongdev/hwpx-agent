# P06-09 table style and transpose policy

- Features: TABLE-020 table.table_style, TABLE-021 table.transpose
- Model contracts: hwpx-agent.table-style-definition/v1, hwpx-agent.table-style/v1,
  hwpx-agent.table-transpose/v1
- Scope: pure bounded semantic components for the current-PC local-development branch
- Current direct stage: component_only / unit_passed

## Table-style semantics

A style definition is a backend-neutral, digest-bound table-properties state plus one mandatory
whole-table cell-style rule and up to twelve optional region rules. The admitted regions are header
rows, footer rows, first and last columns, odd and even row bands, odd and even column bands, and the
four corner cells. Caller input order never controls precedence.

The resolver uses this fixed order:

1. an enabled corner rule;
2. header or footer rows;
3. enabled first or last column;
4. row/column bands in the request's explicit rows_first or columns_first order;
5. the mandatory whole-table rule.

Corner rules are active only when both their corresponding header/footer region and first/last
column flag are enabled. Band sizes are finite positive values and header plus footer rows may not
overlap.

Every master cell is bound by logical ID, top-left coordinate, prior cell-style digest, payload
digest and optional formula digest. A merged cell either resolves from its master anchor under an
explicit policy or every covered slot must resolve to the same style digest. Mixed resolution fails
before a plan exists. The plan preserves payload and formula digests and changes only the declared
table-properties and cell-style identities.

## Transpose semantics

Transpose consumes exactly one record for every master cell in an already validated TableGrid. It
emits a new grid with:

- rows' = columns and columns' = rows;
- master (row, column) changed to (column, row);
- (row_span, column_span) changed to (column_span, row_span);
- master logical ID, payload digest, style digest, and table-properties digest preserved.

Merged rectangles are transposed rather than rejected. The resulting grid is rebuilt through the
normal TableGrid invariant checker, so overlap, gaps, capacity and dimension violations still fail
closed.

Formula-bearing cells require transpose_and_clear_cache; reject returns no request. Formula owners,
every reference coordinate, ranges, relative/absolute row and column anchor kinds are transposed
through the typed FormulaAst. The unverified cache is cleared and number format is preserved. A
transposed table that would exceed the exact grid or formula column ceiling is rejected rather than
truncated.

## Determinism, privacy and failure

Definitions, requests, plans and receipts use compact bounded JSON and SHA-256 identities. Cell
sets are complete, unique and coordinate-canonical. Debug surfaces redact table/style/master IDs,
payloads, formulas and all digests. Invalid limits, versions, JSON, identifiers, digests, bindings,
regions, master-cell coverage, formula ownership, merged-style conflicts, output size and allocation
all return typed errors with no partial plan or receipt.

No user document, HWPX package, Hangul process, registry, printer, trust store, network service or
system setting is read or changed by these components.

## Evidence boundary

This slice proves deterministic table-style resolution and semantic grid/formula transposition only.
It does not prove HWPX lowering, border-fill/style catalog materialization, package preservation,
semantic reopen, formula readback, pagination, rendering, licensed Hangul 2020 execution, desktop
automation or differential equivalence. TABLE-020/021 therefore move only from cataloged to
unit_passed; both rows remain non-green and P06-09, P06 and the product remain in progress.

The next implementation and all HWPX/preservation/oracle Gates remain at reasoning level max.
