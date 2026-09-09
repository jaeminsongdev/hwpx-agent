# P06-09 TABLE-054 nested-table HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 target claim

## Exact operation

`hwpx-agent.table-nested-table-hwpx/v1` applies `table.nested_table` to one explicitly selected
master cell and one exact empty direct paragraph in that cell. The nested table comes from a
caption-free inline HWPX wrapper using the same bound header catalog. Its complete typed grid,
merged spans, ruling edges, cell properties, ordered text payloads, formula/cache state, pagination
policy and placement are retained.

The parent cell may already contain other payload paragraphs. The insertion index is derived from
the exact direct-paragraph order, and the new wrapper receives a distinct logical payload identity.
A covered coordinate inside a merged cell is rejected instead of silently canonicalized. The
parent may itself be nested; selection remains the global table ordinal plus exact master-cell
coordinate.

## Formula and identity isolation

Formula ownership is the nearest ancestor table. A formula inside the new nested table is therefore
read only as nested state and never as a parent formula. Formula/cache paragraphs remain excluded
from the nested table's ordinary payload list, while the whole nested-table wrapper is one typed
payload block of the parent.

Parent and nested logical table, master-cell and payload identifiers must be globally distinct for
the operation. The inserted parent payload identity is also distinct. Native table IDs and formula
begin/field IDs are checked against the destination before mutation. A template must be
`treatAsChar=1`, have no caption, contain exactly one table root in its wrapper, and contain no
external resource-bearing picture, OLE, chart, video or audio payload.

## Binding, preservation and publication

The request binds header and source section SHA-256, complete parent state/grid/content, complete
template state/grid/content, exact wrapper bytes, insertion context, source table count, and
current/target document-flow SHA-256. The builder constructs the full target parent state with one
ordered payload insertion and retains the complete nested state.

Immediately before mutation the lowerer relifts both inputs, repeats identity checks and rebuilds
the plan. Only the selected empty paragraph span is replaced. Header, parent grid/spans/edges/cell
properties/formulas/cache/pagination, other payload order, all other document bytes, nested
formula/cache/pagination/placement and table count must reopen. Closed-package tests preserve the
package graph, compression classes and every non-target part.

JSON/XML, grids, tables, formulas, payloads, serialization and output are bounded. Duplicate JSON
keys and unknown fields fail. Debug output omits logical IDs, hashes, formula/cache values, native
text and document content.

## Evidence boundary

Seven Rust adapter tests plus the private contract/tamper suite promote only TABLE-054 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with static `schema`,
`semantic_reopen`, `formula_readback` and `page_split` evidence.

This does not prove licensed Hangul save/reopen, render equality, target-build behavior,
rollback/retry, automation, differential equality, external resource portability, arbitrary user
documents, another PC/version, P06-09, P06, production or product completion.
