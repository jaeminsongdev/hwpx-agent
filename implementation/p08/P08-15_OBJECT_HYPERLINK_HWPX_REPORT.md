# P08-15 object hyperlink HWPX report

## Result

Result: `direct_hwpx_partial_profile_pass / row_unit_only / target_not_run / task_incomplete`.

The shape-component subset of `OBJ-048 obj.object_hyperlink` now has an exact preserving
static-section HWPML adapter over the common root `href` field. The complete row remains
`unit_passed`: official `ChartType` has no common root `href`, so chart is rejected. This is partial
synthetic profile evidence only, not complete-row, complete-package, licensed-Hangul, render,
differential, or release-green evidence.

## Verified implementation evidence

- Eleven native tags covering five admitted IR kinds read and lower the same common root `href`
  field inherited from the official `AbstractShapeComponentType` model. Text boxes are
  distinguished from plain rectangles by exactly one direct `drawText` child.
- HTTPS, `mailto:`, `#bookmark`, and link removal have typed semantic readback. XML-sensitive HTTPS
  query characters are escaped on write and decoded on read.
- A transition changes exactly one attribute value span. Object-specific payload, opaque children,
  neighboring objects, comments, whitespace and namespaces remain byte-exact.
- Request and build independently recheck complete property state and document flow. The section,
  selected object, href, state, flow, domain plan and HWPX plan bindings reject drift or tampering.
- Unsafe or unsupported schemes, missing/duplicate/qualified hrefs, zero or noncanonical identity,
  chart, nested-only and unreviewed targets, ambiguous text boxes, no-op requests, finite-limit
  failures, preservation failures and semantic readback failures all fail closed without partial
  output.
- Deterministic JSON is bounded and public Debug output redacts link targets and bindings.

Focused execution: preserving HWPX `object_hyperlink_hwpx` 7/7 PASS. Fixture classes cover all
admitted kinds, all four transitions, happy path, boundary, negative, preservation, request/build
drift, deterministic planning, XML escaping and redacted diagnostics.

## Evidence boundary

Tests use generated section XML. No user document or complete HWPX package was modified. No
package resource-integrity validator, licensed Hangul process, save/reopen, object-bounds
measurement, render, automation runtime, or differential was executed. The official source review
establishes only the static shape-component `href` vocabulary and inheritance, plus chart's absence
from that inheritance branch.

`shape_component_static_section_hwpx=true`, `typed_semantic_reopen=true`,
`outside_attribute_span_preserved=true`, `obj_048_complete=false`,
`chart_direct_hwpx=false`; `resource_integrity=false`,
`actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`object_bounds=false`, `render=false`, `automation=false`, `differential=false`,
`p08_complete=false`, `production_ready=false`, and `product_complete=false`.

## Next exact task

Continue only with P08-10 operations whose complete typed state has a one-to-one reviewed native
HWPML map. Do not collapse two-field alternative text into one `shapeComment`, omit native caption
subtree state, or infer `obj.aspect_lock` from `hp:sz@protect`. Run the attempt-bound licensed
Hangul 2020 campaign only after implementation closure.
