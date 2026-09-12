# P09-02 form-control report

## Result

Result: `eight_capability_typed_component_pass / official_model_qualified /
date_native_binding_unverified / direct_hwpx_not_run / p09_02_non_green`.

P09 now has a complete bounded component model for the six P09 form kinds plus property replacement
and complete tab-order replacement. No result is promoted to actual HWPX, installed Hangul,
semantic reopen, field readback, reference update, save/reopen, render, automation, differential,
production, P09, or product PASS.

## Implemented evidence

- `form_control.rs` models `REF-011/012/013/014/015/017/018/019` as eight exact capability IDs.
- The full ordered inventory binds logical/native identity, paragraph/run/inline anchor, native tag
  status, every qualified common and kind-specific property, inherited shape state, opaque native-payload remainder,
  opaque properties and all unrelated document-state digests.
- Exact pinned-source tags exist for text, checkbox, radio, combo and list. Date has no independent
  tag in the pinned `RunType`; its binding is therefore explicitly unresolved instead of fabricated.
- Current/default inputs, built-in constraints, external-validator digests, radio-group exclusivity,
  unique selection values, Gregorian date bounds, shape protection and atomic contiguous tab order
  fail closed.
- Requests and builds independently reject source-state and document-flow drift. Strict bounded JSON,
  duplicate/unknown-field rejection, sealed plans, preservation checks and redacted diagnostics are
  covered.

Focused Rust: public form-control tests 8/8 PASS; private sealed-plan tamper test 1/1 PASS; total
9/9 PASS. Private contract/qualification/tamper tests: 5/5 PASS.

## Field-model source observation

The same official-source pass found that page and object numbering use separate `autoNum` controls,
while the field enum does not provide a single begin/end representation for all P09-01 definitions.
Consequently P09-01 v1 remains component evidence only. A future native lowering must use an exact
variant identity (`fieldBegin/fieldEnd`, `autoNum`, or separately proven target representation)
instead of forcing every definition into a begin/end pair.

## Evidence boundary

No section XML or HWPX package was created, mutated or reopened. No licensed Hangul process was used,
and no current-target input, protection, date, tab-order, save/reopen or visual behavior was observed.

`unit_model_implemented=true`, `eight_capabilities_unit_passed=true`,
`official_model_source_qualified=true`, `complete_bound_state_preserved=true`,
`input_and_protection_fixtures=true`, and `request_and_build_drift_rejected=true`.
`date_native_binding_verified=false`, `direct_hwpx=false`, `actual_hwpx=false`,
`actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_02_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

## Next exact task

P09-01 must first split native identity by exact representation and prove each supported mapping.
P09-02 HWPX lowering may then cover only the five pinned exact tags, with closed-package readback and
input/protection fixtures. Date stays unrouteable until a Hangul 2020 artifact or a separately
qualified automation binding proves its native representation. P09-03 notes can proceed independently.
