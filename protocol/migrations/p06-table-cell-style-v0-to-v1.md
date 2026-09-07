# P06 table cell style v0 to v1

P06-04 introduces private contract `hwpx-agent.table-cell-style.hancom-2020/1`. There was no
accepted v0 wire format and no legacy cell-style payload is migrated automatically.

The v1 model requires finite optional HWPUNIT margins, one exact `borderFillIDRef`, one exact
`paraPrIDRef` whose catalog entry proves the requested horizontal alignment, typed vertical
alignment and text-direction tokens, and an exact pair of `protect`/`editable` bits. A missing,
ambiguous, dangling or semantically different header reference must fail closed.

The lowerer accepts either a standalone `hp:tc` fragment or one zero-based cell in full section XML.
It updates only existing style attribute value spans, rewrites every direct cell paragraph to the
validated paragraph-property reference, reparses the result and verifies that cell content bytes did
not drift. An absent margin is canonical only as `hasMargin="0"` with four zero values.

Unknown shapes, inferred IDs, mixed paragraph references, implicit catalog insertion, silent
normalization and compatibility aliases are not migrated. Later changes require a new version,
migration and negative tests.
