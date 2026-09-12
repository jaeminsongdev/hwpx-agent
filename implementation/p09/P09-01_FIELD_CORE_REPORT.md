# P09-01 field core report

## Result

Result: `ten_capability_typed_component_pass / direct_hwpx_not_run /
field_readback_not_run / p09_01_non_green`.

P09 now has its first implementation checkpoint. All ten `REF-001` through `REF-010` field-core
capabilities have exact typed unit models. No result is promoted to direct HWPX, installed Hangul,
semantic reopen, field readback, reference update, save/reopen, render, automation, differential,
production, P09, or product PASS.

## Implemented evidence

- `field_engine.rs` models named, user, click-here, date/time, filename, page, section and object
  number definitions plus update and lock as ten distinct capability IDs.
- State includes complete field order, component reservation pairs, anchors, typed definition/result, update and
  cache policy, lock, explicit evaluation context, style/payload bindings, opaque properties, and
  all unrelated document-state digests.
- Insertion rejects field/native-ID/anchor collisions. Result update rejects missing, locked,
  frozen, no-op and definition-incompatible targets. Ambient time, filename and numbering state are
  never sampled by the component.
- Request and build independently reject source-state and document-flow drift. Deterministic bounded
  JSON, duplicate/unknown-field rejection, sealed plans, typed errors, preservation checks and
  redacted diagnostics are covered.

Focused Rust: public field tests 8/8 PASS; private sealed-plan tamper test 1/1 PASS; total 9/9 PASS.

## Evidence boundary

The tests construct field state in memory. No section XML or HWPX package was mutated or reopened,
no licensed Hangul process was used, and no current-target field result, pagination, object
sequence, reference update, save/reopen, or visual behavior was observed.

Later official-source qualification found that page and object numbering use separate `autoNum`
controls. The v1 pair-shaped reservation is therefore not a universal native identity; exact lowering
must migrate to a representation variant rather than interpreting the component IDs as HWPX proof.

`unit_model_implemented=true`, `ten_capabilities_unit_passed=true`,
`complete_bound_state_preserved=true`, and `request_and_build_drift_rejected=true`.
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `field_readback=false`,
`semantic_reopen=false`, `reference_update=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_01_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

## Next exact task

Qualify the official HWPML field-begin/end/control structures and implement preserving section-level
lowering plus strict readback for all eight insert definitions, update and lock. If a definition has
no exact native map in the pinned source or Hangul 2020 output, keep that row at unit evidence and
route it only after a separately verified automation binding exists. In parallel, P09-02 may start
as a complete inert-form state model without claiming active script execution.
