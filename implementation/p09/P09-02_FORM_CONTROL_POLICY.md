# P09-02 form-control policy

## Decision

P09-02 is `eight_capability_typed_component_pass / official_model_qualified /
date_native_binding_unverified / direct_hwpx_not_run / target_not_run / task_incomplete`.
The form model covers `REF-011` through `REF-015`, `REF-017`, `REF-018`, and `REF-019`.
It does not include the P11-owned command button or data binding, execute scripts, lower an HWPX
package, or claim installed Hangul, readback, save/reopen, rendering, automation, P09, production,
or product completion.

## Qualified native surface

The official Hancom `hwpx-owpml-model` source is pinned at commit
`1453388472c703a4b299a0834f425cdac16644b9`. Its `RunType` admits `edit`, `checkBtn`,
`radioBtn`, `comboBox`, and `listBox`. The model binds these five semantic controls only to their
matching native tags. No dedicated date-control tag was found in the pinned run model, so date is
represented as `unverified_date_control`; it cannot be silently lowered as `edit` or promoted to
direct-HWPX evidence.

The typed state preserves all qualified common form attributes: name, foreground/background
colors, common group name, tab-stop/order, editable, enabled, border reference, frame, printable,
and a digest-only command reference. It also preserves `formCharPr`, complete button attributes,
edit attributes, ordered combo/list items and their native sizing/selection fields. The raw command
string is neither accepted nor executed. Full inherited shape state, the opaque native-payload
remainder not represented by typed properties, and unknown
properties remain bound by digests.

## Semantic input, validation and protection

Each control separates current and default values from validation. Text input binds length,
multiline, numeric-only, password-character, scroll-bar, tab-key, read-only and alignment state.
Checkboxes bind all three native values, tri-state and checked-required semantics. Radio groups bind
all native button values and reject inconsistent requirements or multiple current/default checked
members. Combo/list controls bind unique item values, current/default selections and selection
requirements; non-editable selections must name an existing item. Date values are strict Gregorian
`YYYY-MM-DD`, bounded by optional earliest/latest values, locale and display format.

`shape_locked` rejects property and tab-order mutation. `SetTabOrder` is an atomic replacement over
the complete control inventory: every identity appears exactly once, disabled tab stops have no
order, and enabled orders form the exact contiguous range `0..n`. Common `editable`, `enabled`,
text `read_only`, and the complete document-protection digest are preserved independently.

## Determinism and failure policy

Requests and builds independently recheck exact source-state and document-flow SHA-256. Plans seal
the operation, capability, request, source/result state and source/result flow. Duplicate or unknown
JSON fields, oversized input/output, zero or colliding IDs, duplicate anchors/names/tab orders,
wrong native bindings, invalid colors/digests/text/dates/items/selections/radio groups, incomplete
tab order, protected targets, kind changes, invalid insertion indexes, missing targets, no-ops,
state/flow drift and plan tampering fail without a partial result. Debug output redacts names,
values, defaults, captions, selections, identities, anchors, commands and digests.

## Evidence boundary

Focused Rust tests passed 9/9: eight public happy/boundary/negative/preservation tests and one
private sealed-plan tamper test. Private contract tests passed 5/5. All tests operate on typed
in-memory component state and pinned source metadata only.

`unit_model_implemented=true`, `eight_capabilities_unit_passed=true`,
`official_model_source_qualified=true`, `complete_bound_state_preserved=true`,
`input_and_protection_fixtures=true`, and `request_and_build_drift_rejected=true`.
`date_native_binding_verified=false`, `direct_hwpx=false`, `actual_hwpx=false`,
`actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_02_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. Exact HWPX lowering/readback and target qualification remain `max`.
