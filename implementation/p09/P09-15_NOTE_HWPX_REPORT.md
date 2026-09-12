# P09-15 note HWPX report

## Result

Result: `REF-021/022 closed plain-text static-section integration PASS / target NOT RUN / P09
INCOMPLETE`.

Footnote and endnote insertion now have a preserving HWPML section adapter. REF-021 and REF-022
advance from `unit_passed` to `integration_passed`. The matrix becomes seven cataloged, 40 unit,
six integration and zero oracle/release-green rows.

## Verified implementation evidence

- The reader verifies one section, a complete top-level paragraph logical-ID map, direct run/inline
  anchors, every native note wrapper, semantic/native kind, positive `instId`, the complete marker
  state, and ordered source/target note inventory.
- The exact closed body graph supports multiple paragraphs, runs, character/paragraph/style IDs and
  decoded text while rejecting incomplete attributes, objects, fields, tables, change tracking,
  special-character children, arbitrary XML and foreign namespaces.
- Body bytes, decoded text, length-framed body-style projection and enclosing marker-run style each
  have distinct bindings. Raw body XML is supplied separately and only its SHA/length enters the
  sealed plan.
- REF-021 and REF-022 each insert exactly one namespace-compatible native wrapper with escaped BMP
  marker characters. Non-BMP WCHAR values, opaque/locked notes, wrong payload/state/flow/map,
  malformed wrappers, out-of-range anchors and plan tampering fail before output.
- Exactly one admitted byte span changes; all other bytes are compared, and the complete typed
  target projection is reread. JSON and all inputs are bounded and public diagnostics redact body,
  identity, anchor, state and digest data.

Focused execution: domain note engine public 8/8 and private tamper 1/1 PASS; public `note_hwpx`
7/7 PASS; private adapter tamper 1/1 PASS; `hwpx-package` all-target/all-feature Clippy with
`-D warnings` PASS. Fixtures cover both note families, multi-paragraph/multi-run body style,
boundary placement, preservation, malformed/native/namespace negatives, exact section/payload/
state/flow/map drift, finite limits and redaction.

## Evidence boundary

All HWPX fixtures are generated section XML. No user document or complete package was modified, and
no installed Hangul save/reopen, field/reference update, rendering, automation runtime or
differential was executed. The exact profile deliberately does not admit arbitrary rich-note body
objects.

`arbitrary_rich_note_body=false`, `complete_package_hwpx=false`, `actual_hwpx=false`,
`actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`, `reference_update=false`,
`hancom_open=false`, `save_reopen=false`, `render=false`, `automation=false`,
`differential=false`, `green_rows=0`, `p09_complete=false`, `production_ready=false`, and
`product_complete=false`.

## Next exact task

Finish the already-open P09-14 hyperlink native discovery without treating its manually produced
file as PASS by itself. Then implement only the exact qualified field parameters and preserve this
note profile's rich-body limitation until independently qualified.
