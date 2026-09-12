# P09-01 field core policy

## Decision

P09-01 is `ten_capability_typed_component_pass / direct_hwpx_not_run /
target_not_run / task_incomplete`. The field core covers `REF-001` through `REF-010` as one
bounded state-transition model. It does not claim HWPX lowering, installed Hangul behavior,
field readback, save/reopen, reference update, rendering, automation, P09 completion, production,
or product completion.

## Complete field state

`hwpx-agent.field-engine/v1` binds the complete ordered field inventory. Every field contains a
logical identity, distinct nonzero begin/end-shaped reservation IDs, exact paragraph/run/inline anchor, typed
definition, typed cached result, update policy, cache status, lock state, optional evaluation
context digest, character/paragraph style digests, native field-payload digest, and a unique set of
opaque-property digests. The document state separately binds non-field content, style catalog,
reference inventory, resource inventory, and opaque document state.

The reservation pair is component identity only, not proof that every definition lowers to native
`fieldBegin`/`fieldEnd`. P09-02 source qualification found separate `autoNum` controls for page and
object numbering and no single field-pair representation for the full set. Native lowering therefore
requires a future variant identity and must not reuse the v1 pair as target evidence.

The eight insertion definitions are named, user-defined, click-here, date/time, file name, page
number, section number, and picture/table/equation object number. Their capability IDs are exactly
`ref.field_insert`, `ref.field_user`, `ref.field_click_here`, `ref.field_date_time`,
`ref.field_filename`, `ref.field_page_number`, `ref.field_section_number`, and
`ref.field_object_number`. `ref.field_update` replaces only a compatible cached result and its
explicit evaluation-context digest; `ref.field_lock` replaces only the lock bit.

## Determinism and failure policy

No wall clock, current filename, page count, section count, or object sequence is read implicitly.
A caller supplies an already observed cached result plus a SHA-256 evaluation-context binding.
Numeric fields require a nonnegative numeric value and display string; other fields require a text
result. Update rejects locked fields and `freeze_text` policy. File-name fields store only the
typed `include_path` choice and cached display, not an ambient filesystem path.

Requests and builds independently recheck exact source-state and document-flow SHA-256. Plans seal
the operation, source/result state, source/result flow, capability, and request identity. Duplicate
or unknown JSON fields, oversized input/output, zero or colliding native IDs, duplicate anchors,
invalid names/locale/timezone/text/digests, incompatible result types, invalid insertion indexes,
missing targets, no-ops, stale state/flow, plan tampering, locked/frozen updates, and opaque-key
collisions fail without a partial result. Debug output redacts names, parameters, prompts, cached
results, identities, anchors, digests, and opaque values.

## Evidence boundary

Focused Rust tests passed 9/9: eight public happy/boundary/negative/preservation tests and one
private sealed-plan tamper test. They operate only on typed in-memory component state.

`unit_model_implemented=true`, `ten_capabilities_unit_passed=true`,
`complete_bound_state_preserved=true`, and `request_and_build_drift_rejected=true`.
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `field_readback=false`,
`semantic_reopen=false`, `reference_update=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_01_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. P09-01 direct HWPX and installed-target qualification remain `max`; the
next pure implementation task may use `high` only where no native format or security judgment is
involved.
