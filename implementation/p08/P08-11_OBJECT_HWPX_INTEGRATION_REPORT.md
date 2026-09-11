# P08-11 object HWPX integration report

## Result

Result: `static_section_hwpx_integration_pass / target_not_run / task_incomplete`.

Direct static HWPML lowering now exists for OBJ-010, OBJ-031 and OBJ-036 through OBJ-041. This is
integration evidence, not licensed-target or release-green evidence.

## Verified implementation evidence

- Composition lowering preserves a closed native island while implementing group/ungroup, all
  z-order and alignment/distribution modes, and all nine connector kinds with endpoint subjects,
  indexes and ordered control points.
- Canvas lowering preserves existing opaque container/picture/shape content, rewrites an exact
  embedded-picture clip, and appends a fully reserved generated container/rectangle subtree.
- Both request and lowering paths bind source/target state, document flow and section digests;
  target semantic reopen and bytes outside the island are mandatory.
- Unsupported visibility/printability, generated nonempty payloads, OLE/linked/effects profiles,
  malformed native identity/topology/geometry/resource references and bounded-limit violations
  fail closed. Debug output redacts digest material.

Focused Rust execution: object composition 6/6 PASS and drawing canvas 7/7 PASS. The tests cover
happy, boundary, negative and preservation fixtures, source/flow drift, native tampering and strict
reopen. Focused Clippy with `-D warnings` passed.

## Evidence boundary

The tests operate on synthetic section XML. They did not build or reopen a complete package, verify
package relationship targets or media bytes, run Hangul, save/reopen a document, measure object
bounds, render, route automation or compare a differential.

`static_section_hwpx=true`, `semantic_reopen=true`, `outside_island_preserved=true`;
`full_package=false`, `resource_integrity=false`, `actual_target_hwpx=false`,
`actual_hangul=false`, `save_reopen=false`, `object_bounds=false`, `render=false`,
`automation=false`, `differential=false`, `p08_complete=false`, `production_ready=false` and
`product_complete=false`.

## Next exact task

Extend HWPX lowering to the fourteen P08-10 typed models without weakening their complete-state
contracts. Then run the combined licensed Hangul 2020 target campaign; only attempt-bound package,
readback and render evidence may advance rows beyond integration.
