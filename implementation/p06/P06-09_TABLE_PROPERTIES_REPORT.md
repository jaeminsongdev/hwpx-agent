# P06-09 table and cell properties component report

Result: component_pass

## Implemented

- TABLE-007: exact table-property and selected non-border cell-property replacement bound to the
  complete TableGrid/state identity.
- TABLE-008: per-master-cell top/right/bottom/left and background preserve/clear/set semantics.
- TABLE-009: rectangular selection frame with distinct outer sides and inner horizontal/vertical
  lines, including real merged-cell edge resolution.
- TABLE-047: explicit each-cell or unified-region diagonal values covering both slash directions,
  center lines and line identity, with distinct clear semantics and region-bound shared identity.
- Shared boundaries: complete canonical master-cell state, exact logical-slot sets for TABLE-007/008
  and each-cell TABLE-047, strict rectangular selection for TABLE-009 and unified TABLE-047, full
  merged-cell containment, deterministic bounded
  JSON/SHA-256, before/after state binding, typed errors, actual-change receipts and redacted Debug.

## Verification

- Focused Rust table-properties tests: 21/21 PASS.
- Focused strict Clippy with `-D warnings`: PASS.
- The tests cover table-only and selected properties, per-cell and unified borders, background,
  merged spans, diagonal topology/modes, non-contiguous exact sets, irregular unified/duplicate/out-of-bounds selections,
  strict JSON, stale state, actual change counts, bounded output, deterministic 144-shape corpus and
  privacy.
- Contract validator: PASS; dedicated tamper tests: 4/4 PASS.

## Conformance effect after contract admission

- direct stages: cataloged 9 to 5; unit_passed 34 to 38; integration_passed remains 7;
  oracle_verified remains 11.
- direct evidence missing: 9 to 5.
- validation missing: 214 to 210 because only schema is proven for each row.
- fixture missing: 88 to 72 because only component happy/boundary/negative/preservation fixtures are
  proven; target-build remains absent.
- negative not passed: 9 to 5.
- green rows: remains 0/61.

## Not claimed

There is no direct HWPX adapter, borderFill catalog materialization or diagonal lowering, package mutation, semantic
reopen, formula readback, page-split/render result, Hangul 2020 target build, automation runtime or
differential evidence in this slice. User documents and Hangul were not opened. P06-09, P06 and the
product remain incomplete.

Next reasoning level: max.
