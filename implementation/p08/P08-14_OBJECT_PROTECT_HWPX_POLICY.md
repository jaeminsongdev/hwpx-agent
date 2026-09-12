# P08-14 object protection HWPX policy

## Decision

P08-14 is `direct_hwpx_integration_pass / target_not_run / task_incomplete`. It advances only
`OBJ-045 obj.object_protect` from typed component evidence to preserving synthetic section-HWPX
integration. It does not prove licensed Hangul, visual equivalence, automation, production, P08, or
product completion.

## Exact native profile

The profile `hwpx-agent.object-protect-hwpx.hwpml-2011-root-lock/v1` admits one existing direct
run-level `pic`, `rect`, `ellipse`, `line`, `arc`, `polygon`, `curve`, `connectLine`, `container`,
`ole`, `video`, or `textart` selected by bounded document order. The official HWPML 2011
`AbstractShapeObjectType` model exposes one root `lock` boolean for this common base type. The
adapter maps that exact field to the complete typed state's `locked` value and changes no other
field.

Native `lock` accepts only canonical `0` or `1`. The root `id` and `instid`, object kind, and every
required common geometry child must be unambiguous and must equal the complete typed source state.
Nested-only, unknown, missing, duplicate, qualified-target, or noncanonical forms fail closed. The
distinct `hp:sz@protect` field is not admitted as `obj.aspect_lock`; its UI meaning is not inferred
from a similarly named native flag.

## Planning, preservation, and limits

Request planning and lowering independently bind and recheck the complete source and target
`ObjectGeometryState` plus before/after document-flow SHA-256. The HWPX plan additionally seals the
exact section, selected object, domain plan, and plan SHA-256. A real transition changes exactly one
root `lock` value span, proves every byte outside that span exact, and requires typed target
readback. A no-op protection request is rejected before a plan is built.

JSON, section, element, object, matrix, edit, output, and plan sizes remain under finite hard
ceilings. Plans are deterministic bounded JSON. Public Debug output redacts identities, geometry,
paths, state, and all binding digests.

## Evidence boundary

`static_section_hwpx=true`, `typed_semantic_reopen=true`, `all_twelve_common_kinds=true`, and
`outside_attribute_span_preserved=true` refer only to generated test XML. The pinned public Hancom
model is a static type reference, not an installed-target runtime oracle.

`actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`, `object_bounds=false`,
`render=false`, `automation=false`, `differential=false`, `p08_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. The remaining exact native adapters and later combined licensed Hangul
2020 campaign remain `max`.
