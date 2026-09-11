# P08-03 object geometry and transform report

## Result

Result: `common_component_pass / target_not_run / task_incomplete`.

This checkpoint adds a deterministic domain planner and preserving HWPX section lowerer for the six
catalog operations `obj.position`, `obj.size`, `obj.anchor`, `obj.wrap`, `obj.rotate` and `obj.flip`.
It models every reviewed common geometry field instead of implementing an easier partial subset.

## Implemented evidence

- The domain request, plan and build path binds complete state and before/after document-flow
  digests, with request-time and build-time drift rejection.
- The HWPX plan additionally binds the exact full section and selected run-level object bytes.
- Twelve public-model component kinds are admitted through confirmed inheritance; nested-only,
  unknown, missing and duplicate common structures fail closed.
- Page, paragraph and inline-style anchors, all wrap/flow values, relative/absolute size references,
  outer margins, original/current sizes, offsets, rotation, flip and three six-coefficient matrices
  have typed exact readback.
- Matrix FLOAT syntax is converted to deterministic signed fixed millionths without floating-point
  JSON. More than six fractional digits and unsupported syntax fail closed.
- Only changed common-attribute value spans are replaced. Opaque shape payload, unchanged numeric
  lexemes, sibling objects, text, XML formatting and namespaces remain byte-preserved.
- Canonical JSON is bounded and duplicate/unknown-field strict; public debug output is redacted.

Focused Rust tests: 17/17 PASS (domain 6/6, preserving HWPX 11/11). They cover all six operations,
all twelve object kinds, deterministic plan/build, source/state/flow drift at both boundaries,
page/paragraph anchor fixtures, inline flags, wrap/margins, complete size/component transitions,
rotation/flip with caller-supplied matrices, no-op byte identity, sibling and opaque-payload
preservation, matrix exactness, finite limits, malformed/missing/duplicate/nested rejection and
redacted diagnostics.

## Evidence boundary

The passing inputs are synthetic section XML, not an HWPX package produced by or reopened in the
installed licensed Hangul 2020 target. No visual or automation differential has run. The public
Hancom model establishes static field vocabulary and inheritance only.

`full_package_hwpx=false`, `actual_hangul=false`, `save_reopen=false`, `render=false`,
`direct_automation_differential=false`, `p08_03_complete=false`, `p08_complete=false`,
`production_ready=false` and `product_complete=false`.

## Next exact task

Continue P08-04 basic-shape semantic construction at `max`, reusing this common geometry lowerer.
Keep the combined P06/P07 licensed-target campaign deferred until a complete attempt-specific
capture set can be collected without combining failed or incomplete attempts.
