# P08-08 drawing-canvas, clip and effects report

## Result

Result: `exact_canvas_transition_component_pass / successor_static_hwpx_integration_pass /
security_corpus_not_run / target_not_run / task_incomplete`.

The current-ledger prerequisite now has one exact model for container topology, picture clip,
picture effects and closed resource preservation. The historical WBS active-content/security scope
remains explicit and open rather than being silently replaced by this checkpoint.

## Implemented evidence

- Complete ordered container trees bind logical/native identity, parent/depth/order, bounds,
  visibility, printability, protection and five separate semantic/opaque state bindings.
- Resource inventory closure covers embedded/linked images, image fills, opaque OLE binaries and
  passive previews. Linked targets are digest-bound; OLE activation is unrepresentable except as
  `blocked` preservation state.
- Picture clip uses exact original-pixel coordinates and fails on empty, reversed or out-of-bounds
  rectangles. Effects reuse the already qualified P08-05 typed shadow/glow/soft-edge/reflection
  model.
- Canvas insert binds the complete new subtree and every new logical/native/resource ID. Clip and
  effects operations permit exactly one semantic field plus its corresponding payload or
  appearance digest to change.
- Request construction, plan and build independently recheck complete source state and document
  flow. The sealed plan recomputes all digests and rejects internal tampering.
- JSON is deterministic, bounded, duplicate-key-free and unknown-field strict; diagnostics redact
  identity, content, geometry and digests.

Focused Rust tests: 10/10 PASS (external contract 9/9 plus private-plan tamper 1/1). Coverage
includes nested containers, exact ID reservation, existing-state preservation, bounded clip and
effects transitions, opaque OLE blocking, topology/identity/resource negatives, no-op and coupled
mutation rejection, source/flow drift, JSON limits and Debug redaction.

The private contract tamper suite passed 4/4 and all P08 Python contract tests passed 32/32. The
workspace all-target/all-feature locked offline suite and Clippy with `-D warnings` passed; its three
pre-existing isolated qualification tests remained ignored. Format and diff checks passed.

P08-11 adds a separate static-section HWPX adapter for `obj.drawing_object_insert` and `obj.crop`.
Its focused tests pass 7/7 with strict semantic reopen, native identity/geometry/resource-reference
checks, source/flow drift rejection and outside-island preservation. Picture effects and active
content remain deliberately unsupported by that adapter.

## Evidence boundary

Synthetic HWPX section XML was generated and modified; no complete package was built. No real OLE/media corpus was opened or
activated, and no security scanner ran. No document was opened, saved, reopened, property-read or
rendered by licensed Hangul 2020. The pinned Hancom source qualifies field ownership and tree shape
only.

`exact_canvas_state_component_pass=true`, `insert_clip_effect_transitions=true`,
`opaque_ole_activation_blocked_by_model=true`, `static_section_hwpx=true` and
`semantic_reopen=true` for insert/crop; `synthetic_package=false`,
`security_corpus=false`, `actual_hangul=false`, `save_reopen=false`, `property_readback=false`,
`render=false`, `automation=false`, `differential=false`, `p08_08_complete=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false`.

## Next exact task

Continue lowering the remaining P08-10 typed models. The existing package-level opaque
OLE/multimedia preservation and security evidence remains separate, and the licensed-target
campaign must still close package/readback/render requirements.
