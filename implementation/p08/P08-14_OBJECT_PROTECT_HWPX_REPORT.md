# P08-14 object protection HWPX report

## Result

Result: `direct_hwpx_integration_pass / target_not_run / task_incomplete`.

`OBJ-045 obj.object_protect` now has an exact preserving static-section HWPML adapter over the
common root `lock` field. This is synthetic integration evidence only, not a licensed Hangul or
release-green result.

## Verified implementation evidence

- All twelve reviewed direct run-level common object kinds read and lower the same canonical root
  `lock` field inherited from the official `AbstractShapeObjectType` model.
- A protection transition changes exactly one attribute value span. Complete common geometry,
  transforms, identity, object-specific payload, opaque children, neighboring objects, comments,
  whitespace, and namespaces remain byte-exact.
- Request and build independently recheck complete state and document flow. The section, selected
  object, state, flow, domain plan, and HWPX plan bindings reject drift or tampering.
- No-op requests, noncanonical booleans, wrong identity/kind/order, missing or duplicate required
  structures, nested-only targets, finite-limit violations, preservation failure, and semantic
  readback failure all fail closed without partial output.
- Deterministic JSON is bounded and public Debug output is redacted.

Focused execution: domain `object_geometry` 7/7 PASS and preserving HWPX `object_geometry_hwpx`
12/12 PASS. Fixture classes cover all twelve kinds, happy path, boundary, negative, preservation,
request/build drift, no-op rejection, deterministic planning, and redacted diagnostics.

## Evidence boundary

Tests use generated section XML. No user document was modified. No complete target HWPX, licensed
Hangul process, save/reopen, object-bounds measurement, render, automation runtime, or differential
was executed. The official source review establishes static vocabulary and inheritance only.

`static_section_hwpx=true`, `typed_semantic_reopen=true`,
`outside_attribute_span_preserved=true`; `actual_target_hwpx=false`, `actual_hangul=false`,
`save_reopen=false`, `object_bounds=false`, `render=false`, `automation=false`,
`differential=false`, `p08_complete=false`, `production_ready=false`, and
`product_complete=false`.

## Next exact task

Continue only with P08-10 operations whose complete typed state has a one-to-one reviewed native
HWPML map. Keep `OBJ-044 obj.aspect_lock` at unit evidence until its exact UI/native semantics are
proven. Run the attempt-bound licensed Hangul 2020 campaign only after implementation closure.
