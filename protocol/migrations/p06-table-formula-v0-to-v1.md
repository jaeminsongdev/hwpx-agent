# P06 table formula v0 to v1

There was no executable FormulaAst contract before `hwpx-agent.table-formula/v1`. Existing formula
strings, cached display text, target XML, automation actions, and spreadsheet-like assumptions are
therefore untrusted v0 inputs; they are not silently reclassified as v1.

Migration parses only the bounded ASCII grammar admitted by v1 and then emits a typed AST with
zero-based cell coordinates and independent relative/absolute row and column anchors. Unknown
functions, locale separators, exponent notation, malformed or reversed ranges, out-of-grid
references, excessive precision, and over-limit trees fail closed. A formula that cannot be parsed
must remain opaque or be routed to a separately qualified backend; guessing is forbidden.

Cached results migrate separately from the source formula. This pure v1 component admits only
`absent` or `unverified`; it cannot mint an oracle-qualified value from a digest-shaped string.
A later receipt-verifying adapter must own any target-oracle promotion. Preservation after a
structural edit is allowed only if the canonical formula digest is unchanged; otherwise an explicit
clear or update policy is required.

V1 supports `SUM`, `AVG`, `PRODUCT`, arithmetic, general/number/percent/scientific formats, and
deterministic insert/delete and copy-rebase reference transforms. Currency, date, custom formats,
additional functions, evaluator semantics, HWPX lowering, and target-specific readback require a
new contract version or a separately versioned adapter. Adding them in place would weaken the
fail-closed boundary.
