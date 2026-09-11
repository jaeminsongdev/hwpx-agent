# P08-05 object appearance report

## Result

Result: `static_appearance_component_pass / visual_target_not_run / task_incomplete`.

This checkpoint adds exact domain planning and preserving section-level HWPX lowering for all
eleven P08 appearance capability rows. It covers the complete reviewed static shape/picture
boundary rather than promoting a line/fill-only subset.

## Implemented evidence

- Typed state covers line, four mutually exclusive fill forms, classic shape shadow, picture
  shadow/glow/soft-edge/reflection, transparency channels and picture image adjustment.
- All public-model line/fill/image/shadow enums and ordered RGB color transforms have explicit
  HWPML mappings. Unsupported color-source families and unknown native fields fail closed.
- Requests bind full before/after state, exact single-component delta, native identity and document
  flow. Domain request, plan and build each repeat validation and deterministic digest checks.
- HWPX plans additionally bind section bytes, selected direct-run object bytes, object ordinal,
  object family/native IDs and the complete domain plan.
- Lowering changes only appearance children or the four reviewed picture-image adjustment
  attributes. Strict reparse must equal the complete target appearance.
- Original-object replacement reconstructs the complete original section byte for byte. Bounded
  JSON/XML handling, finite vectors, canonical native numbers and redacted diagnostics are enforced.

Focused Rust tests: 13/13 PASS (domain 6/6, HWPX integration 6/6, private-plan tamper 1/1). They
cover every shape appearance family, every picture effect, picture line and color adjustment,
alpha-only transparency, strict readback, exact outside-object preservation, source/identity/flow
drift, duplicate components, unknown attributes, unsupported effect colors, output limits,
duplicate/unknown JSON and redacted Debug.

## Evidence boundary

The tests use synthetic section XML. No current output was created, opened, edited, saved, reopened
or rendered by licensed Hangul 2020, and no visual diff ran. The image-fill relationship ID is
lexically validated but not yet resolved through a full package graph in this section-level
profile. The public Hancom model is static source qualification, not a runtime oracle.

`static_appearance_component_pass=true`, `synthetic_section_roundtrip=true`,
`package_image_fill_resource_integrity=false`, `actual_target_hwpx=false`,
`exact_current_2020_serialization=false`, `actual_hangul=false`, `save_reopen=false`,
`visual_diff=false`, `render=false`, `direct_automation_differential=false`,
`p08_05_complete=false`, `p08_complete=false`, `production_ready=false` and
`product_complete=false`.

## Next exact task

Continue P08-06 composition at `max`: group/ungroup, z-order, align/distribute and connector graph
operations with exact identity, topology and geometry preservation. Keep incomplete P06/P07 target
attempts unchanged until one coherent, fully captured campaign is available.
