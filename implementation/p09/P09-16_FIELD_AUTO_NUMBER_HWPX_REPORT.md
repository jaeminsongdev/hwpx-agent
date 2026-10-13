# P09-16 Field auto-number HWPX report

Decision: `STATIC SECTION INTEGRATION PASS / TARGET NOT RUN / NON-GREEN`.

## Delivered

- Added an exact preserving reader, planner, lowerer and receipt for PAGE, PICTURE, TABLE and EQUATION
  `autoNum` elements using the closed DIGIT profile.
- Added REF-006 and REF-008 insertion plus the exact numeric-result subset of REF-009 update.
- Bound complete field state, source/target flow, section, logical paragraph map, ordered projection,
  domain plan and adapter plan; independently rechecked all bindings before output.
- Added exact target projection readback, one-edit byte preservation, namespace-prefix preservation,
  finite limits, stable errors and redacted Debug surfaces.
- Rejected TOTAL_PAGE, section numbering, non-DIGIT formats, locked/opaque fields, native extensions,
  malformed XML, ambiguous transitions and all source or plan drift.

## Evidence result

Field-engine domain tests are `8/8 PASS`; public adapter tests are `8/8 PASS`; the private sealed-plan
tamper test is `1/1 PASS`; focused total is `17/17 PASS`. Focused package Clippy with `-D warnings`
and repository format check PASS.

The complete Rust workspace all-target/all-feature locked offline test run PASS; only the existing
external P17 PostgreSQL qualification and two synthetic Windows Credential tests remained ignored.
Workspace Clippy with `-D warnings`, deterministic matrix verification, P09 contracts `83/83`,
format and `git diff --check` PASS.

The official pinned OWPML model provides the `autoNum`/`autoNumFormat` grammar and enum set. The
existing Hancom-generated P05-08 section contains PAGE/DIGIT and TOTAL_PAGE/DIGIT examples; only the
PAGE/DIGIT lexical shape is admitted here, and TOTAL_PAGE is an explicit negative boundary.

## Claim boundary

REF-006, REF-008 and REF-009 advance from `unit_passed` to `integration_passed`. This proves exact
static section-byte lowering and typed target readback. It does not prove complete-package HWPX,
installed Hangul execution, application-owned recalculation, save/reopen or rendering.
`actual_hwpx=false`, `actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `green_rows=0`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

## Next exact task

Synchronize P09-11 to the eleven exact static-section integration rows, then continue with the next
dependency-ready direct adapter. Do not promote any target or green claim before generated package
open, semantic reopen, field readback, reference update, render and differential evidence exist.
