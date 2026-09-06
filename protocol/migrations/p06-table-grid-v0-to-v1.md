# P06 table-grid implicit v0 to v1

`hwpx-agent.table-grid/v1` is the first executable standalone logical-grid contract. The earlier
`DocumentGraph` v2 `TableNode` shape stored row/column/span values and rejected overlap or incomplete
coverage, but it did not expose a canonical slot-to-master-cell mapping or the P06-specific typed
failure taxonomy. That implicit shape is not relabeled as v1 evidence.

Migration is explicit and fail closed: copy only bounded logical dimensions, master-cell logical IDs,
top-left coordinates and nonzero spans into a v1 draft; validate every identifier, checked capacity,
rectangle, overlap and slot; then emit canonical v1 bytes. Any zero span, overflow, out-of-bounds
rectangle, duplicate ID, overlap, uncovered slot, unknown field or unsupported version rejects the
whole conversion without a partial grid. No HWPX numeric ID, raw XML, cell content or style is guessed.

P06-02 may consume only a validated v1 `TableGrid`. P06-03 owns merge/split content distribution,
and direct HWPX or desktop-automation bindings remain unqualified until their later task evidence.
