# P08-02 static image HWPX report

## Result

Result: `static_component_pass / target_not_run / task_incomplete`.

The second P08 checkpoint adds a bounded embed-only image request, exact empty-run source binding,
HWPML picture lowerer, strict static reader and picture/manifest ID-reference profile. It composes
the existing P08-01 asset plan with the preserving patch engine in one transaction.

## Implemented evidence

- Complete ordered package state, section, paragraph, run, object-ID set, instance-ID set, insertion
  ordinal, asset plan and before/after document flow are bound and rechecked.
- Nonzero distinct object/instance IDs and resource IDs are typed independently; the new `pic` and
  `instid` declarations and `img/@binaryItemIDRef` manifest reference are indexed.
- Embedded PNG insertion and exact existing-asset reuse both pass relationship/content closure,
  strict picture readback, byte restoration and full synthetic package writer reopen.
- Display extent, X/Y DPI, nonempty rectangular pixel crop and XML-safe alternate text are emitted
  and read back exactly. Pixel coordinates use bounded deterministic HWPUNIT conversion.
- Unsupported link modes, nonempty/ambiguous anchors, ID collisions, source/flow/asset drift,
  malformed geometry/text, strict JSON violations and shape/resource tampering fail closed.
- Bounded canonical JSON is deterministic and public debugging is redacted.

Focused Rust tests: 9/9 PASS. They cover new/reused assets, atomic package counts, writer reopen,
crop/DPI/alternate-text semantics, strict native-shape tamper, link refusal, geometry/text limits,
request and build-time drift, object collision, target shape, JSON duplicate/unknown/limit checks,
picture-to-manifest ID closure and debug redaction.

## Evidence boundary

All passing archives and picture controls are synthetic component fixtures. The installed licensed
Hangul 2020 target has not opened, saved, reopened or rendered this output. The public OWPML model
documents vocabulary and types but is not a current-target runtime oracle. Linked images are not
implemented, so the full P08-02 WBS row remains incomplete.

`actual_hwpx_image=false`, `actual_hangul=false`, `save_reopen=false`, `render=false`,
`direct_automation_differential=false`, `p08_02_complete=false`, `p08_complete=false`,
`production_ready=false` and `product_complete=false`.

## Next exact task

Continue P08-03 shape geometry at `max` without consuming licensed UI time. Batch P06/P07 exact
target validation later, preserving each fixed-plan attempt boundary and requiring its own complete
evidence set before promotion.
