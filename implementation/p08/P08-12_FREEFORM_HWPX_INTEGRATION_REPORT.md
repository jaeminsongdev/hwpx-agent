# P08-12 freeform HWPX integration report

## Result

Result: `direct_hwpx_integration_pass / target_not_run / task_incomplete`.

`OBJ-042` is now correctly classified from the already verified P08-04 synthetic full-package
freeform insertion path. `OBJ-043` now has a preserving static HWPML payload-island adapter. This is
integration evidence, not licensed Hangul or release-green evidence.

## Verified implementation evidence

- `obj.freeform` inserts every admitted polygon and curve family using the existing full synthetic
  package builder and strict package reopen.
- `obj.shape_edit_points` changes only one contiguous native point/segment island while preserving
  complete geometry, identity, properties, formula/cache/resource bindings, opaque bytes and all
  section bytes outside that island.
- Request planning and lowering both recheck source state and document flow. Section, object,
  payload, target-state and plan drift fail closed.
- Wrong object ordinal or kind, ambiguous/noncontiguous/nested payloads, duplicate/extra attributes,
  noncanonical integers/enums, namespace declarations and finite-limit violations are rejected.
  Debug output is redacted.

Focused execution: domain shape-points 6/6 PASS, basic-shape HWPX 7/7 PASS and shape-points HWPX
5/5 PASS. Fixture classes cover happy path, boundary, negative and preservation behavior. Focused
Clippy with `-D warnings` passed for the new adapter test target.

## Evidence boundary

The `OBJ-042` fixture is a generated synthetic package; `OBJ-043` tests are synthetic section XML.
No user document was modified. No licensed Hangul process, target save/reopen, object-bounds
measurement, render, automation runtime or differential was executed.

`OBJ-042 synthetic_full_package=true`, `OBJ-043 static_section_hwpx=true`,
`semantic_reopen=true`, `outside_island_preserved=true`; `actual_target_hwpx=false`,
`actual_hangul=false`, `save_reopen=false`, `object_bounds=false`, `render=false`,
`automation=false`, `differential=false`, `p08_complete=false`, `production_ready=false` and
`product_complete=false`.

## Next exact task

Map only the P08-10 properties with proven native HWPML fields while preserving unsupported fields
fail-closed. Do not infer aspect-lock, two-field alternative text, image-property or link encodings.
Then execute the combined licensed Hangul 2020 target campaign from attempt-bound fixtures.
