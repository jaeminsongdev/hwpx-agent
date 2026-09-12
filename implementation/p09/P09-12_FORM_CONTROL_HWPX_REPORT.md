# P09-12 form-control HWPX report

## Result

Result: `REF-018/019 static-section integration PASS / target NOT RUN / P09 INCOMPLETE`.

The existing-native-form subset now has an exact preserving HWPML section adapter. REF-018 and
REF-019 advance to `integration_passed`; the other 44 P09-owned rows retain their prior unit stage,
the seven P11-owned rows remain cataloged, and all 53 rows remain non-green.

## Verified implementation evidence

- The reader verifies all five official native tags and their exact common, `formCharPr`, text,
  button, combo, list-item, and list payload lexicals against the complete typed state.
- REF-018 changes one control's admitted native common-property attributes while preserving its
  payload, identity, kind, anchor, shape/opaque state, other controls, and document state.
- REF-019 replaces the complete tab-stop/tab-order assignment, including canonical `-1` for a
  non-tab-stop object, without changing non-tab properties.
- Request/build and lower both bind state and flow; section, every form object, domain plan, and
  HWPX plan are sealed. Source, object, projection, flow, and plan drift fail before output.
- Unsupported insertion, payload mutation, kind change, date binding, malformed structure,
  duplicate attributes, noncanonical values, and finite-limit failures are rejected.
- Only admitted attribute spans change. Surrounding payload, neighboring forms, comments,
  whitespace, and namespace bytes remain exact. JSON is bounded and diagnostics are redacted.

Focused Rust execution: `form_control_hwpx` 6/6 PASS; `hwpx-package` all-target Clippy with
`-D warnings` PASS. Fixture coverage includes five-tag vocabulary, happy paths, boundary,
negative, preservation, state/flow/source drift, nonrepresentable operations, limits, and redaction.

## Evidence boundary

All HWPX fixtures are generated section XML. No user document, complete package, installed Hangul
process, save/reopen cycle, field/reference update, render, automation runtime, or differential was
executed. `static_section_hwpx=true` and `typed_target_projection_readback=true` do not imply
`actual_hwpx`, `actual_hangul`, or release-green evidence.

`complete_package_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`field_readback=false`, `reference_update=false`, `hancom_open=false`, `render=false`,
`automation=false`, `differential=false`, `green_rows=0`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

## Next exact task

Qualify and implement the next closed field-family HWPML subset. Do not infer unsupported native
identities or start licensed UI execution until all intended P09 implementation slices are ready
for the combined P06/P07/P09 target campaign.
