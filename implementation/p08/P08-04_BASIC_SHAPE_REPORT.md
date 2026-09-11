# P08-04 basic-shape construction report

## Result

Result: `static_shape_component_pass / target_not_run / task_incomplete`.

This checkpoint adds exact domain planning and preserving static HWPX lowering for
`obj.shape_insert` and `obj.textbox_insert`. The implementation covers every P08-04 shape family,
including both freeform encodings, rather than promoting an easier subset.

## Implemented evidence

- Line, rectangle, ellipse, text box, polygon and curve have typed complete payloads with strict
  topology, signed-coordinate and XML-text validation.
- Every request includes complete P08-03 geometry and before/after document-flow state. Planning
  and build both recheck geometry, shape, flow and deterministic request/plan digests.
- The HWPX plan additionally binds the complete package graph, exact selected section/paragraph/run
  and all object, instance, paragraph and sub-list ID sets.
- The lowerer emits one static native shape, changes exactly one spine part, adds no resource, and
  uses the v6 inherited ID profile to reject package-wide collisions.
- Exact readback verifies common geometry plus all shape-specific points, arc/curve semantics and
  text-box state. Removing the emitted span reconstructs the original section byte for byte.
- Text and attributes are escaped once and compared as semantic Unicode. Canonical JSON is bounded
  and duplicate/unknown-field strict; public Debug is redacted.
- The preserving writer reopens every generated synthetic full package through graph, ID and
  integrity validation.

Focused Rust tests: 13/13 PASS (domain 6/6, HWPX package 7/7). They cover all six serialized forms,
deterministic plan/build, package and flow drift, object/instance/paragraph/sub-list collisions,
nonempty and non-spine anchors, topology and text rejection, finite limits, inherited shape-ID
typing, escaped text/name roundtrip, exact preservation, synthetic full-package reopen and redacted
diagnostics.

## Evidence boundary

The passing packages were constructed by tests; none was created, opened, edited, saved or
rendered by licensed Hangul 2020. The public Hancom model establishes static field vocabulary and
inheritance only. P08-05 still owns line/fill/shadow appearance semantics.

`synthetic_full_package_reopen=true`, `actual_target_hwpx=false`, `actual_hangul=false`,
`save_reopen=false`, `render=false`, `direct_automation_differential=false`,
`p08_04_complete=false`, `p08_complete=false`, `production_ready=false` and
`product_complete=false`.

## Next exact task

Continue P08-05 line, fill and shadow appearance semantics at `max`. Keep P06/P07 target evidence
deferred for one correct-plan, complete-capture campaign; failed and incomplete P07-09 attempts
remain unchanged.
