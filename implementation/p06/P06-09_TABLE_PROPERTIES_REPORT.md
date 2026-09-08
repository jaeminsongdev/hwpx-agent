# P06-09 table and cell properties component report

Result: component_pass

## Implemented

- TABLE-007: exact table-property and selected non-border cell-property replacement bound to the
  complete TableGrid/state identity.
- TABLE-008: per-master-cell top/right/bottom/left and background preserve/clear/set semantics.
- TABLE-009: rectangular selection frame with distinct outer sides and inner horizontal/vertical
  lines, including real merged-cell edge resolution.
- Shared boundaries: complete canonical master-cell state, exact logical-slot sets for TABLE-007/008,
  strict rectangular selection for TABLE-009, full merged-cell containment, deterministic bounded
  JSON/SHA-256, before/after state binding, typed errors, actual-change receipts and redacted Debug.

## Verification

- Focused Rust table-properties tests: 17/17 PASS.
- Focused strict Clippy with `-D warnings`: PASS.
- The tests cover table-only and selected properties, per-cell and unified borders, background,
  merged spans, non-contiguous exact sets, irregular unified/duplicate/out-of-bounds selections,
  strict JSON, stale state, actual change counts, bounded output, deterministic 144-shape corpus and
  privacy.
- Contract validator: PASS; dedicated tamper tests: 4/4 PASS.

## Conformance effect after contract admission

- direct stages: cataloged 9 to 6; unit_passed 34 to 37; integration_passed remains 7;
  oracle_verified remains 11.
- direct evidence missing: 9 to 6.
- validation missing: 214 to 211 because only schema is proven for each row.
- fixture missing: 88 to 76 because only component happy/boundary/negative/preservation fixtures are
  proven; target-build remains absent.
- negative not passed: 9 to 6.
- green rows: remains 0/61.

## Not claimed

There is no direct HWPX adapter, borderFill catalog materialization, package mutation, semantic
reopen, formula readback, page-split/render result, Hangul 2020 target build, automation runtime or
differential evidence in this slice. User documents and Hangul were not opened. P06-09, P06 and the
product remain incomplete.

Next reasoning level: max.
