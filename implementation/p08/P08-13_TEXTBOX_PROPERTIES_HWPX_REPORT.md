# P08-13 text-box properties HWPX report

## Result

Result: `direct_hwpx_integration_pass / target_not_run / task_incomplete`.

`OBJ-025 obj.textbox_properties` now has a preserving static-section HWPML adapter for the complete
typed text-box property operation. This is synthetic integration evidence only, not a licensed
Hangul or release-green result.

## Verified implementation evidence

- One run-level native text box is selected using the same object-ordinal vocabulary as common
  object geometry. The admitted root is an `hp:rect` with a single direct `drawText` and the exact
  `textMargin`, `subList` topology documented by the official HWPML 2011 model.
- All four margins, all three text directions, and all three vertical alignments have typed readback
  and lowering. Canonical number, identity, enum, namespace, topology, and finite-limit errors fail
  closed.
- Request and lowering stages separately recheck complete state and document flow. Section, object,
  `drawText`, margin, sublist, domain-plan, and plan drift are bound.
- Only changed target attribute value spans are emitted. Other root attributes, drawing-text
  attributes, sublist attributes, contained paragraphs and text, neighboring objects, comments,
  and section bytes remain byte-exact.
- Plan JSON is deterministic and bounded; readback, plan, and receipt Debug views are redacted.

Focused execution: `textbox_properties_hwpx` 7/7 PASS and focused `hwpx-package` all-target/all-feature
Clippy with `-D warnings` PASS. Fixture classes cover happy path, all 3x3 enum combinations, numeric
boundaries, malformed/ambiguous inputs, request/build drift, preservation, and finite limits.

## Evidence boundary

Tests use generated section XML. No user document was modified. No complete target HWPX, licensed
Hangul process, save/reopen, object-bounds measurement, render, automation runtime, or differential
was executed.

`static_section_hwpx=true`, `typed_semantic_reopen=true`,
`outside_attribute_spans_preserved=true`; `actual_target_hwpx=false`, `actual_hangul=false`,
`save_reopen=false`, `object_bounds=false`, `render=false`, `automation=false`,
`differential=false`, `p08_complete=false`, `production_ready=false`, and
`product_complete=false`.

## Next exact task

Continue only with P08-10 properties whose entire typed operation has a proven native HWPML map.
Do not infer overlapping geometry flags, two-field alternative-text encoding, six-field image
metadata, link routes, or form-only semantics. Then run the attempt-bound combined licensed Hangul
2020 campaign when manual capture and save approval are available.
