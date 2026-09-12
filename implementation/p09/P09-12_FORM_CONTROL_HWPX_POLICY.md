# P09-12 form-control HWPX policy

## Decision

P09-12 is `two_rows_static_section_integration_pass / target_not_run / p09_incomplete`.
It advances only REF-018 `ref.form_properties` and REF-019 `ref.form_tab_order` from typed unit
models to exact preserving static-section HWPML integration. It does not prove a complete HWPX
package, licensed Hangul behavior, save/reopen, rendering, automation, differential behavior, P09,
production, or product completion.

## Closed native profile

The profile `hwpx-agent.form-control-hwpx.hwpml-2011-existing-native-form-properties/v1` admits an
ordered complete inventory of existing direct `hp:edit`, `hp:checkBtn`, `hp:radioBtn`,
`hp:comboBox`, and `hp:listBox` elements. Each object must match its typed native ID, exact tag,
common attributes, one direct `hp:formCharPr`, and kind-specific payload projection. Boolean values
are canonical `0` or `1`, colors are uppercase `#RRGGBB`, and enum names follow the pinned public
HWPML 2011 writer.

REF-018 may alter one existing object's common native properties except the digest-only active
`command` binding. It preserves identity, anchor, native kind, complete kind-specific payload,
shape state, opaque state, other controls, and document-level state. REF-019 replaces the complete
tab-stop/tab-order assignment atomically while preserving every non-tab field. Control insertion,
payload editing, kind changes, unverified date controls, and incomplete tab assignments fail closed.

## Planning, preservation, and limits

Domain request/plan/build and HWPX plan/lower independently recheck complete source state and
document flow. The HWPX plan additionally seals the section SHA-256, every native form object's
outer-span SHA-256, the domain plan digest, and its own deterministic bounded JSON digest.

Lowering emits only admitted attribute-span replacements or a bounded optional `groupName`
attribute insertion/removal. Every byte outside those deltas is preserved exactly, followed by a
typed target projection readback. Section, element, control, attribute, text, output, and plan sizes
have finite hard ceilings. Public Debug and errors redact names, values, captions, selections,
commands, identities, paths, state, and digests.

## Evidence boundary

`static_section_hwpx=true`, `typed_target_projection_readback=true`,
`outside_delta_byte_preserved=true`, and `REF-018/019=integration_passed` refer only to generated
test section XML. The readback verifies a complete expected typed state against its native
projection; it is not a licensed-Hangul or independent package reconstruction oracle.

`complete_package_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`field_readback=false`, `reference_update=false`, `hancom_open=false`, `render=false`,
`automation=false`, `differential=false`, `green_rows=0`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. Exact field-family qualification and the later combined licensed Hangul
2020 campaign remain `max`.
