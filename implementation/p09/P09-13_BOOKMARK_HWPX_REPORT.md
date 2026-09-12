# P09-13 bookmark HWPX report

## Result

Result: `REF-031/032 static-section integration PASS / target NOT RUN / P09 INCOMPLETE`.

The exact point-bookmark subset now has a preserving HWPML section adapter. REF-031 and REF-032
advance to `integration_passed`; the other 42 P09-owned rows retain their prior unit stage, the
seven P11-owned rows remain cataloged, and all 53 rows remain non-green.

## Verified implementation evidence

- The reader verifies one section, exact paragraph and direct-run placement, every bookmark wrapper,
  the required name-only empty marker, complete order, and point boundaries against typed state.
- REF-031 inserts one namespace-compatible escaped `ctrl/bookmark` wrapper. REF-032 deletes only the
  selected complete wrapper. Same-boundary insertion follows target inventory order.
- Request/build and lower bind complete state and flow. Section, every wrapper, domain plan, and
  HWPX plan are sealed; source, state, flow, projection, and plan drift fail before output.
- Non-point, locked, opaque, malformed, duplicated, ambiguous, unmodeled, and out-of-range inputs
  are rejected. Default and explicit paragraph namespaces are both covered.
- Exactly one admitted byte span changes, target projection is reread, JSON is bounded, allocation
  failures are typed, and public diagnostics redact bookmark content and bindings.

Focused Rust execution: `link_reference` 10/10 PASS, public `bookmark_hwpx` 8/8 PASS, private sealed
plan tamper 1/1 PASS, and `hwpx-package` all-target Clippy with `-D warnings` PASS. Fixture coverage
includes happy path, boundary, negative, preservation, exact state/flow/source drift, finite limits,
same-boundary ordering, namespace spelling, and redaction.

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

Qualify and implement the next closed P09 HWPML subset without inferring unsupported field identity.
Keep licensed UI execution deferred until all intended P09 implementation slices are ready for the
combined P06/P07/P09 target campaign.
