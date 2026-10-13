# P09-10 REF-053 product API verification note

## Scope

This is a supplemental work-in-progress note. It does not replace or promote the pinned
`P09-10_REFERENCE_AUXILIARY_REPORT.md`; REF-048 through REF-053 retain their existing unit-only and
native/target `NOT_RUN` classification.

## Implemented library surface

- Added `crates/product-cli/src/reference_validation_product.rs` and exported its library module.
- The operation accepts only the typed `ref.reference_validate` request, delegates strict bounded
  request parsing and plan/build to `ReferenceAuxiliaryBuilder`, recomputes the report digest, and
  checks the domain receipt plus unchanged source/target state and document-flow pins.
- It performs no filesystem/package read or write, native action, reference repair, field update, or
  external data-source access. It is a library API; no executable CLI dispatch or package lowering
  is claimed.
- Added four integration tests for a missing-target report, rejection of mutation capabilities,
  malformed capability-envelope classification, and duplicate-key rejection through the domain
  parser. The product response carries the fixed qualification
  `caller_supplied_typed_state_only_source_completeness_unverified` so callers cannot mistake the
  API result for a fully imported document report.

## Verification boundary

- After adding the qualification field, `CARGO_BUILD_JOBS=1 cargo test -p hwpx-agent-cli --test
  reference_validation_product --locked --offline`: `4 passed, 0 failed`.
- `rustfmt --edition 2024 --check` on the new API and test files: `PASS`.
- This incremental one-target build began at CPU `38%`, available RAM `6,013 MiB`; after completion
  the sample was CPU `80%`, available RAM `5,869 MiB` of `31,861 MiB`. No full suite was started.
- Actual HWPX write/readback, Hangul open/save, render, external source handling, P09 queue
  acceptance, and Gate closure remain `NOT_RUN`/unverified. P09 remains 104/249, next111, Gate
  `OPEN`; P10 implementation remains unstarted.

## Next boundary

The next implementation needs a qualified product-side reader that derives the complete reference
state and flow pins from the actual HWPX package. The current product API accepts already-typed state
and does not provide that reader, CLI dispatch, or package output. Do not promote REF-053 beyond the
tested library contract until that path is implemented and verified. Do not infer target or Gate
acceptance from these unit tests.

## Source-reader audit (2026-10-10)

- `hwpx-package`/`product-cli` search found no `ReferenceAuxiliary` HWPX reader or reference-validation
  CLI dispatch.
- The existing `ImportedDocumentStructure` exposes bookmark observations. The existing field-semantic
  import recognizes only `HYPERLINK` and `FORMULA` in its closed scope; it does not produce the complete
  cross-reference edge inventory required by `ref.reference_validate`.
- Therefore the tested library operation still depends on caller-supplied typed state. Deriving a
  full-document report from these partial observations would overstate coverage; no such projection
  was added. HWPX source binding remains `NOT_RUN`.
