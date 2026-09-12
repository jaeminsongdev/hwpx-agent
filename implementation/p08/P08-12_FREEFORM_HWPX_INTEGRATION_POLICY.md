# P08-12 freeform HWPX integration policy

## Decision

P08-12 is `direct_hwpx_integration_pass / target_not_run / task_incomplete`. It records the
existing synthetic full-package lowering for `obj.freeform` (`OBJ-042`) and adds a preserving
static-section payload-island lowering for `obj.shape_edit_points` (`OBJ-043`). The two rows advance
to integration evidence only; neither row is licensed-target or release-green evidence.

## Exact native profiles

- `hwpx-agent.basic-shape-hwpx.hwpml-2011-static/v1` inserts a complete polygon or curve with typed
  common geometry, native points or segments, distinct object and instance IDs, package-part
  preservation and strict synthetic-package reopen. This is the existing P08-04 `OBJ-042` path.
- `hwpx-agent.shape-points-hwpx.hwpml-2011-payload-island/v1` selects exactly one run-level native
  polygon or curve and replaces only its contiguous `hc:pt` or `hp:seg` payload island. Polygon
  points and curve start/LINE/CURVE segments are exact; noncontiguous, nested, namespaced,
  noncanonical, mismatched-kind and ambiguous payloads fail closed.
- Point editing reopens the whole common geometry through the object-geometry reader and binds the
  complete `ShapePointsState`, including object identity, payload/properties/formula/cache/resource
  digests and opaque-byte count. Bytes before and after the payload island remain byte-exact.

## Planning, preservation and limits

The `OBJ-043` request and lowering paths independently rebuild the domain plan and recheck complete
source state, target state and document-flow SHA. The HWPX plan additionally seals the source
section, selected object, payload and domain-plan SHA values. Lowering computes the exact output
section digest and requires strict semantic reopen before returning output.

Section, payload, output, plan, element and object counts have finite configurable limits below hard
ceilings. JSON plans are deterministic and bounded. Debug views expose only counts, kinds and
booleans and do not reveal state, flow, payload or plan digests.

## Evidence boundary

For `OBJ-042`, `synthetic_full_package=true` and `resource_integrity=true` refer only to the P08-04
generated fixture. For `OBJ-043`, `static_section_hwpx=true`, `semantic_reopen=true` and
`outside_island_preserved=true`; no complete package or resource payload was tested.

For both rows `actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`object_bounds=false`, `render=false`, `automation=false`, `differential=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false`.

Reasoning level: `max`; exact native mapping of the remaining P08-10 property/special-object models
and the later licensed-target campaign remain `max`.
