# P09-06 Cross-reference report

Decision: `COMPONENT PASS / OFFICIAL STRUCTURE PARTIALLY QUALIFIED /
UNVERIFIED NATIVE CROSSREF PARAMETERS / DIRECT AND TARGET NOT RUN / NON-GREEN`.

## Delivered

- Added `hwpx-agent.cross-reference/v1` for REF-035 `ref.crossref_insert`.
- Added complete bookmark, heading, numbered-paragraph, caption, footnote and endnote target state.
- Added exact target/display projection and current/stale cache classification.
- Added dependency plus containment-derived target DAG validation with dangling, self and cycle
  rejection.
- Added global native-ID and field-name collision, target compatibility, anchor, lock, preservation,
  request/build drift, strict JSON, finite-limit and redacted-Debug checks.
- Added a sealed private plan and tamper test, versioned private contract, migration, pinned-source
  qualification, validator and contract tests.

## Source result

The clean pinned Hancom OWPML checkout proves `CROSSREF` and the generic
`fieldBegin`/`fieldEnd` structure. It does not prove the parameter keys or serialization needed to
bind the typed target/display/cache model to native HWPX. The component therefore keeps those bytes
opaque, labels the binding `UnverifiedFieldParameters`, and exposes no direct lowering.

## Validation

- Rust public cross-reference tests: `10/10 PASS`.
- Rust private sealed-plan tamper test: `1/1 PASS`.
- Focused Rust total: `11/11 PASS`.
- Private contract/source-lock/migration/validator/tamper tests: `5/5 PASS` after the final contract
  run.
- P09 Python suite, affected upstream suites, workspace all-target/all-feature tests, Clippy and
  fmt/diff are recorded only after their final checkpoint runs.

## Claim boundary

`unit_model_implemented=true`, `ref_035_unit_passed=true`, `target_graph_fixtures=true`,
`cache_projection_fixtures=true`, `cycle_and_dangling_fixtures=true`, and
`complete_bound_state_preserved=true`. `native_crossref_parameters_verified=false`,
`ref_036_update_implemented=false`, `direct_hwpx=false`, `actual_hwpx=false`,
`actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_06_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

## Next exact task

Implement P09-07 REF-037 through REF-040 TOC/index insertion, update, style and leader behavior with
an exact target graph and cached generated-body model. REF-036 remains P11-owned automation.
