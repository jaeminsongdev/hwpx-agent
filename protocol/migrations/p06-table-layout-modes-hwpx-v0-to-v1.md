# P06 table layout modes HWPX evidence v0 to v1

This additive evidence contract admits the already-versioned
`hwpx-agent.table-layout-hwpx.hancom-2020/2` lowering path for three previously unit-only catalog
operations: fixed column width, fit to content and fit to page. It does not replace or reinterpret
the immutable layout component contract.

The three modes are not coerced into one semantic result. A mixed fixed/automatic plan keeps the
fixed track exact while the automatic track receives eligible remainder. `FitContent` stops at
verified preferred widths and may leave unused body width. `FitPage` treats the body width as an
exact target and distributes all eligible remainder across automatic tracks.

The adapter returns bytes only after the existing strict HWPX readback succeeds. The new closed
package fixture additionally requires formula, pagination and all non-section parts to remain
semantically or byte-for-byte identical as appropriate. It never writes a real document and never
invokes Hangul.

Static component evidence may not promote these rows beyond `direct_hwpx / integration_passed`.
Licensed Hangul target-build, render comparison, automation runtime, rollback/retry and exact
direct/automation differential evidence remain independent requirements.
