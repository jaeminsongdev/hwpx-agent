# P08-07 chart automation report

## Result

Result: `exact_chart_automation_component_pass / installed_target_not_run / task_incomplete`.

This checkpoint implements all nine chart catalog rows together. It supplies the exact state and
sealed automation/readback contract needed by a later licensed-target adapter, without treating
synthetic bindings as installed-Hangul evidence.

## Implemented evidence

- Exact target profiles require all nine capability mappings and digest-bind type/style mappings,
  parameter schemas and readback schemas without publishing raw action identifiers.
- Complete chart state covers collision-safe identity, numeric/blank data and row/column labels,
  orientation and provenance, series, axes, legend, labels, title, style, geometry, composition,
  appearance, opaque semantics and the non-chart object inventory.
- Insert, type, data, series, axis, legend, labels, title and style operations preserve every
  untargeted component and reject invalid or no-op results.
- Request, plan and build independently recheck exact profile/state/flow bindings. Build recomputes
  the entire target, validates the capability mapping and verifies the private plan seal.
- Execution observations require one complete open/save/reopen/readback/export attempt whose
  reopened state exactly equals the sealed target; partial, repeated, drifted and empty exports
  fail closed.
- Profile, state, request and observation parsing is bounded, deterministic, duplicate-key-free,
  unknown-field strict and diagnostics redact identity, content and digest material.

Focused Rust tests: 10/10 PASS (external contract 9/9 plus private-plan tamper 1/1). They cover exact
profile membership/order, grid and label coherence, distinct insertion identity and allocator
transition, all eight edit capability mappings, cross-chart preservation, series/axis/presentation
negative cases, strict JSON and limits, request/plan/build drift, no-op rejection, complete
observation admission, incomplete/tampered observation rejection and Debug redaction.

## Evidence boundary

No chart HWPX part was generated or modified and no automation adapter executed. No document was
opened, saved, reopened, property-read, exported or rendered by licensed Hangul 2020. The pinned
Hancom source and help pages qualify vocabulary and architecture only; synthetic unit bindings are
not an actual target profile or runtime oracle.

`exact_chart_state_component_pass=true`, `all_nine_chart_rows_modelled=true` and
`automation_plan_and_observation_contract=true`, while `actual_target_profile=false`,
`direct_hwpx=false`, `resource_integrity=false`, `semantic_reopen=false`, `actual_hangul=false`,
`save_reopen=false`, `full_property_readback=false`, `export=false`, `render_diff=false`,
`direct_automation_differential=false`, `p08_07_complete=false`, `p08_complete=false`,
`production_ready=false` and `product_complete=false`.

## Next exact task

Continue P08-08 draw/clip/effects at `max`, keeping P08-07 installed-target evidence not run. The
later combined P06/P07/P08 campaign must create a real target profile, execute each chart operation
on disposable copies, read back the full chart state after reopen, verify resources and compare
exports/renders before any chart row or P08 can become release-green.
