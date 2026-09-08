# P06-09 whole-table split and join component report

Result: `component_pass`

## Implemented

- TABLE-010: cursor-row whole-table split with first-row rejection, inherited table properties,
  preserved complete master-cell content/property identities, merged-row boundary rejection,
  formula rebasing/cache clearing and cross-table reference rejection.
- TABLE-011: whitespace/paragraph-only vertical join with leading-property precedence, maximum
  source width, removal of the trailing table/gap, and preserved master-cell content/property
  identities.
- Distinct source column layouts are combined through an exact reduced-rational boundary union;
  cell spans and formulas are projected into the common logical grid, while unrepresentable
  HWPUNIT rounding fails closed.
- Shared boundaries: complete state/grid SHA-256 binding, surrounding-flow binding, deterministic
  bounded JSON, typed errors, lowering-ready plans, preservation receipts and redacted Debug.

## Verification

- Focused Rust table-partition tests: 13/13 PASS.
- Focused strict Clippy with `-D warnings`: PASS.
- Tests cover cursor-row split, first-row/out-of-range/stale-state failures, merged row spans,
  formula policy and cross-boundary references, unequal widths and column counts, common-lattice
  span/formula projection, larger-width selection, property precedence, whitespace-only gaps,
  non-content rejection, duplicate identities, HWPUNIT collapse, strict bounded JSON,
  request/build-time document-flow drift rejection, deterministic state and privacy.
- Contract validator: PASS; dedicated tamper tests: 4/4 PASS.

## Conformance effect after contract admission

- direct stages: `cataloged` 5 to 3; `unit_passed` 38 to 40; `integration_passed` remains 7;
  `oracle_verified` remains 11.
- direct evidence missing: 5 to 3.
- validation missing: 210 to 208 because only schema is proven for each row.
- fixture missing: 72 to 64 because only component happy/boundary/negative/preservation fixtures
  are proven; target-build remains absent.
- negative not passed: 5 to 3.
- green rows: remains 0/61.

## Not claimed

There is no section XML lowerer, package mutation, semantic reopen, formula readback,
page-split/render result, Hangul 2020 target-build execution, automation runtime or differential
evidence in this slice. The common-lattice HWPUNIT rounding rule remains subject to exact target
oracle calibration before backend promotion. User documents and Hangul were not opened. P06-09,
P06 and the product remain incomplete.

Next reasoning level: `max`.
