# P06-09 table style and transpose component report

Result: component_pass

## Implemented

- TABLE-020: versioned table-style definitions, fixed region precedence, explicit row/column band
  precedence, complete master-cell bindings, merged-region reject/anchor policy, deterministic
  per-master style mutations and preservation receipts.
- TABLE-021: complete rectangular grid transpose including merged spans, logical cell identities,
  payload/style state, FormulaAst coordinates and row/column anchor kinds, explicit formula rejection
  or transpose-with-cache-clear policy, deterministic relocation and preservation receipts.
- Shared boundaries: strict bounded JSON, finite work/output limits, canonical SHA-256 identities,
  typed fail-closed errors, redacted Debug and no partial result.

## Verification

- Focused Rust table-style tests: 14/14 PASS.
- Focused Rust table-transpose tests: 14/14 PASS.
- The transpose tests include merged spans, formula owner/reference/anchor mapping, cache clearing,
  unsupported output dimensions, strict JSON, deterministic fixed-shape corpus and privacy checks.
- Contract validator and dedicated tamper tests: validator PASS and 4/4 PASS.
- Full P06, workspace, Clippy and formatting results are recorded in the implementation ledger and
  commit verification; they do not promote either row beyond unit evidence.

## Conformance effect

- direct stages: cataloged 11 to 9; unit_passed 32 to 34; integration_passed remains 7;
  oracle_verified remains 11.
- direct evidence missing: 11 to 9.
- validation missing: 216 to 214 because only schema is proven for each row.
- fixture missing: 96 to 88 because only component happy/boundary/negative/preservation fixtures are
  proven; target-build remains absent.
- negative not passed: 11 to 9.
- green rows: remains 0/61.

## Not claimed

There is no direct HWPX adapter, package mutation, style-catalog materialization, semantic reopen,
formula readback, page-split/render result, Hangul 2020 target build, automation runtime or
differential evidence in this slice. User documents and Hangul were not opened. P06-09, P06 and the
product remain incomplete.

Next reasoning level: max.
