# P06-09 TABLE-060 absolute-reference HWPX adapter policy v1

Status: direct static HWPX integration implemented; no licensed Hangul 2020 target claim

## Exact operation

`hwpx-agent.table-absolute-reference-hwpx/v1` applies
`table.formula_absolute_ref` to one explicitly selected formula cell in one current-Hangul-2020
table. The source field may use the complete bounded locale-neutral `FormulaAst` grammar. The
target must keep every literal, operator, function, argument, range endpoint and referenced cell
coordinate unchanged. Each reference axis may remain unchanged or move from `relative` to
`absolute`; changing an absolute axis back to relative or changing formula meaning fails closed.

The selected native formula is the exact `=`-prefixed canonical AST. Row and column anchors are
independent, so `A2`, `$A2`, `A$2` and `$A$2` remain distinct. A target must contain at least one
absolute axis. An already-absolute target is an admitted byte-exact no-op.

## Cache and native field semantics

The exact direct profile retains `General` number format. `Preserve` requires the target cache to
equal the source cache, which is safe because referenced coordinates and the formula body cannot
change. `Update` requires an explicitly bound unverified decimal cache and writes it to the native
command, last-result and visible-result slots. `Clear` requires an absent target cache and empties
those slots. No cache is labeled verified, and `recalculate=true` fails closed because this static
adapter does not execute a formula engine.

The reader selects the formula by table ordinal plus owner coordinate. Other formula fields may be
present. Their bytes are included in the selected-field unowned digest and are never interpreted or
rewritten by this operation. Duplicate formula fields in the selected cell, field identity drift,
noncanonical formula/cache text and visible/cache mismatch are rejected.

## Binding, preservation and publication

The request binds header and section SHA-256, selected table-content SHA-256, selected source
formula SHA-256, all bytes outside its four owned native text slots, exact table and formula-field
counts, pagination policy and current/target document-flow SHA-256. The builder repeats these checks,
validates the reference-only transition and binds the complete target formula and cache.

Immediately before mutation the lowerer relifts the source and rebuilds the plan. A real change
rewrites only the selected formula, command, last-result and visible-result spans; the general
result-format slot stays unowned. Header bytes, all other section bytes, cell grid/spans, table and
cell properties, payloads, other formulas/caches, page split, repeat headers, caption and table
count are preserved exactly. No result is returned until the target formula/cache and every
preservation invariant reopen. Closed-package tests additionally preserve the package graph,
compression class and opaque non-target parts.

JSON and XML parsing, formulas, fields, cells, tables, serialization and output are bounded.
Duplicate JSON keys and unknown fields fail. Debug output omits formulas, caches, document text,
hashes and native field contents.

## Evidence boundary

Eight Rust adapter tests plus the private contract/tamper suite promote only TABLE-060 from
`component_only / unit_passed` to `direct_hwpx / integration_passed`, with static `schema`,
`semantic_reopen`, `formula_readback` and `page_split` evidence.

This does not prove that Hangul recalculates or saves the synthetic canonical field, render equality,
a licensed Hangul 2020 target build, rollback/retry, automation, differential equality, arbitrary
user documents, another PC/version, P06-09, P06, production or product completion.
