# P08-10 remaining direct object capability report

## Result

Result: fourteen_capabilities_unit_passed / direct_hwpx_not_run /
actual_hangul_not_run / p08_10_non_green.

All fourteen P08-owned rows that were still `cataloged` now have exact typed component models.
This raises the current object matrix implementation coverage from 39 to 53 rows, with
`cataloged=5`, `unit_passed=31`, `integration_passed=22`, `oracle_verified=0`, and
`green=0/58`. The five remaining cataloged rows belong to P11. No component result is promoted to
an HWPX, installed-Hangul, render, automation, differential, production, or product PASS.

## Implemented evidence

- `object_properties.rs` models `OBJ-019`, `OBJ-025`, `OBJ-030`, and `OBJ-044` through `OBJ-048`.
  Operations preserve complete object identity/kind plus geometry, appearance, payload, resource,
  embedded-content and opaque-property bindings. Kind-specific operations, bounded values, safe
  hyperlinks, no-op rejection and exact request/build drift checks are enforced.
- `basic_shape.rs` now routes freeform insertion to exact `obj.freeform` (`OBJ-042`).
  `shape_points.rs` implements `obj.shape_edit_points` (`OBJ-043`) by replacing complete polygon
  or curve topology while preserving every unrelated binding and rejecting degenerate or
  cross-kind edits.
- `object_special.rs` models `OBJ-003`, `OBJ-012`, `OBJ-013`, and `OBJ-014`. It preserves the
  complete document inventory, validates insertion order and target existence, detects object,
  resource and relationship collisions, recomputes the resource inventory digest, limits one
  caption per target, and denies active form content.
- Every model uses bounded duplicate-free strict JSON, deterministic serialization, redacted
  diagnostics, sealed plans and typed fail-closed errors.

Focused Rust tests: 27/27 PASS. Coverage includes every admitted capability, happy paths,
boundaries, malformed and hostile inputs, preservation, identity/resource collisions, unsafe or
active content, request/build state and flow drift, deterministic JSON and redacted diagnostics.

## Evidence boundary

The tests construct typed component state in memory. No HWPX part was written or reopened, no
licensed Hangul process was used, and no save/reopen, property readback, visual render, direct
automation or differential comparison ran.

`unit_model_implemented=true`, `fourteen_capabilities_unit_passed=true`,
`complete_bound_state_preserved=true`, and `request_and_build_drift_rejected=true`.
`direct_hwpx=false`, `actual_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`property_readback=false`, `render=false`, `automation=false`, `differential=false`,
`p08_10_green=false`, `p08_complete=false`, `production_ready=false`, and
`product_complete=false`.

## Next exact task

Implement direct HWPX lowering and strict readback for the eight P08-owned unit rows identified in
the current ledger. The P11-owned cataloged rows stay unimplemented until P11, and all actual
target fields remain false/not_run until the combined licensed Hangul 2020 campaign.
