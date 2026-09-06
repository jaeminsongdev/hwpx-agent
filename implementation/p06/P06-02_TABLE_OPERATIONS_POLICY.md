# P06-02 Table operations policy

- Contract: `hwpx-agent.table-operations/v1`
- Contract record: `protocol/private/p06-table-operations-v1.json`
- Implementation: `domain_ir::TableGrid` create/insert/delete operations
- Scope: current-PC pure IR, personal local development only

## Source boundary

The P06 table model, table-layout implementation guide, 61-feature table contract and P06 roadmap are
the only product-design sources used by this task. Their UTF-8 text is normalized to LF before exact
SHA-256 comparison so LF and CRLF checkouts are equivalent while semantic content drift fails closed.
P06-02 does not infer HWPX XML names or desktop automation identifiers.

## Creation

`TableGrid::create_unmerged` accepts nonzero bounded rows and columns plus exactly `rows * columns`
caller-owned `LogicalId` values in row-major order. Each identifier becomes one 1x1 master cell. The
operation never invents identity, accepts a partial initializer or creates merged cells. Duplicate,
oversized or malformed identifiers are rejected by the P06-01 invariant before a result is returned.

## Insertion

Row insertion accepts a boundary in `0..=rows`; column insertion accepts `0..=columns`. Count is
nonzero and the resulting dimensions, slot product, master-cell count and serialization must fit the
existing finite `TableGridLimits`. The caller supplies exactly one new unique master ID for every
inserted slot. New cells are 1x1 and ordered row-major.

An insertion boundary strictly inside an existing span fails with `SpanBoundaryConflict`. Insertion
at a span edge is allowed: masters before the boundary stay fixed and masters at or after it shift by
the exact count without changing identity or span. Span expansion is deliberately not guessed; it is
owned by P06-03 merge/split policy.

## Deletion

Deletion accepts a nonempty in-bounds half-open axis interval. Removing the final row or final column
fails. A master intersecting the interval must be fully contained and is then deleted as one identity.
Any partial span intersection fails with `SpanBoundaryConflict`; P06-02 never shrinks or splits a
master implicitly. Surviving masters after the interval shift backward by the exact count and retain
identity and span.

## Atomic result and receipt

Every operation borrows the source grid and constructs a new validated `TableGrid`; failure never
publishes or mutates a partial result. `TableOperationReceipt` records the version, operation,
before/after dimensions, every survivor's old/new top-left coordinate, inserted IDs and deleted IDs in
deterministic canonical order. Receipt and remap fields are private and exposed through read-only
getters so consumers cannot mutate evidence in place. Debug output exposes only dimensions and
counts, not logical IDs.

Validation order is count, index/range, result dimensions and slots, exact new-ID count, span
boundary, fallible allocation and final P06-01 invariant/serialization. Stable typed errors preserve
the underlying `TableGridError` code where the base invariant rejects the result.

## Deferred semantics

Cell content/style/formula ownership is not represented by `TableGrid`. Style inheritance,
content redistribution, span expand/shrink/split, merge/split, FormulaAst reference movement, HWPX
lift/lower, desktop automation, semantic reopen and render verification remain later P06 tasks. This
task does not qualify a public tool, arbitrary documents, another PC/version or production.
