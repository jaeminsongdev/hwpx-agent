# P06-09 table layout modes HWPX adapter policy v1

Status: direct HWPX integration implemented; no licensed Hangul 2020 oracle claim

## Scope

This evidence profile admits `TABLE-051` (`table.column_fixed_width`), `TABLE-052`
(`table.autofit_content`) and `TABLE-053` (`table.autofit_page`) through the existing
`hwpx-agent.table-layout-hwpx.hancom-2020/2` preserving lowerer. It adds operation-specific static
coverage; it does not introduce a new document format or weaken the predecessor contract.

## Exact mode semantics

- Fixed-column coverage uses a mixed fixed/automatic two-column plan with a 50,800 micrometer
  exact target. The fixed 12,700 micrometer column remains unchanged while the automatic column
  alone grows to 38,100 micrometers.
- Fit-content coverage uses two automatic columns with verified preferred widths totaling 38,100
  micrometers inside a 50,800 micrometer body. It stops at those preferred widths and does not
  fabricate exact-page fill.
- Fit-page coverage starts from the same constraints but treats 50,800 micrometers as exact. The
  residual 12,700 micrometers is deterministically split across the eligible automatic columns,
  producing 21,590 and 29,210 micrometers.
- Every plan must pass `TableLayoutPlan::require_verified()` and exact canonical grid binding
  before source parsing or mutation.

## Lowering and preservation

Only existing selected-table `hp:sz` and master-cell `hp:cellSz` width/height value spans may
change. The output is strictly reparsed and compared against the quantized plan, inner margins and
content-token digest. Merged cells use checked sums of their logical tracks, an unselected sibling
table stays byte-identical, and repeated lowering is deterministic and idempotent.

The disposable closed-package fixture executes all three modes, rebuilds and reopens the package
graph, and requires exact formula AST/cache readback, exact pagination-policy readback, exact
expanded-byte hashes for every non-section part, deterministic package bytes and source
immutability. Estimated font metrics, malformed or drifted shapes, and finite-limit violations
return no output.

## Evidence promotion rule

Passing the seven operation-specific adapter tests and private tamper suite promotes only these
three rows to `direct_hwpx / integration_passed` with `schema`, static `semantic_reopen`,
`formula_readback` and `page_split`. It does not prove renderer identity, licensed Hangul 2020
save/reopen, target-build, automation runtime, differential exact match, rollback/retry,
release-enabled status, arbitrary document compatibility, another PC/version, P06-09/P06 PASS,
production or product completion.
