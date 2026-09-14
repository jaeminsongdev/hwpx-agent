# P08-17 object remainder HWPX and target route policy

## Decision

P08-17 is `four_bounded_direct_profiles_integration_passed / five_exact_reasons_fail_closed /
actual_target_not_run / rows_non_green`. It handles the nine P08-10 remainder rows as one batch
without treating similarly named HWPML fields as equivalent semantics.

The bounded direct-HWPX profiles are:

- `OBJ-019 obj.margin_caption`: exact `hp:outMargin` mutation and mutation of an already present,
  single-text-run caption with `numbering=none`; caption insertion/removal is not admitted;
- `OBJ-030 obj.image_properties`: exact `hp:imgDim`, `hp:orgSz`, and `hp:curSz` mutation when pixel,
  DPI and millionth-scale values have a finite checked HWPUNIT representation;
- `OBJ-046 obj.printable`: exact root `printable` mutation on an already present admitted form
  control only;
- `OBJ-047 obj.alt_text`: description-only mutation of an already present `hp:shapeComment` when
  the IR title is empty; title and presence changes are not collapsed into one string.

The exact current-target unavailable reasons are:

- `OBJ-003`: the typed gallery payload has no complete qualified native object template;
- `OBJ-012`: the typed special-object payload does not carry the complete native form-control
  state required by the existing form-control HWPX adapter;
- `OBJ-013`: inserting/removing a caption subtree has no qualified preservation profile;
- `OBJ-014`: no distinct paragraph-band HWPML native construct has been qualified;
- `OBJ-044`: `hp:sz@protect` is size protection and is not inferred to mean aspect-ratio lock.

All unsupported paths return `CAPABILITY_UNAVAILABLE_FOR_TARGET` before effect. A rejected direct
preflight never widens to unverified desktop automation and no backend switch occurs after partial
mutation.

## Source qualification

The pinned Hancom OWPML model commit
`1453388472c703a4b299a0834f425cdac16644b9` defines common `outMargin`, optional `caption`, and
single-string `shapeComment` under `AbstractShapeObjectType`; `PictureType` adds `imgDim` while the
shape component supplies `orgSz` and `curSz`; `AbstractFormObjectType` supplies `printable`.

The official automation archive commit `213c7faad552b4853b525887e36accb6025e837b`
documents `ShapeCaption`, `ShapeComment`, `ProtectSize`, image original size and form-property
surfaces. It does not establish that `ProtectSize` is aspect lock or that the nine typed IR
operations all have unattended target bindings.

## Exactness and failure rules

Planning binds the complete domain plan, exact section and selected object digests, exact native
identity, property span digest and source document-flow digest. Lowering re-runs the domain build,
re-parses the source, applies bounded non-overlapping byte-span edits, verifies every untouched
byte, and performs target-state semantic readback. Integer conversion uses checked arithmetic and
rejects zero, overflow, lossy profile shape, ambiguous elements or noncanonical values.

Caption label and text are rendered together only for the explicit `numbering=none` existing
caption profile and are checked against the complete expected state. Alternative-text titles are
never discarded. Generic shapes never receive a form-only `printable` attribute. Target, source,
plan, state, object-kind, identity or document-flow drift produces no output.

## Evidence boundary

`direct_hwpx_profiles=4`, `fail_closed_unavailable_profiles=5`, `rust_tests=11/11 PASS`,
`schema=true`, `semantic_reopen=true`, `negative=true`, and `preservation=true`.

`complete_native_coverage_for_all_nine=false`, `actual_target_hwpx=false`, `hancom_open=false`,
`save_reopen=false`, `resource_integrity=false`, `object_bounds=false`, `render=false`,
`automation_runtime_binding=false`, `differential=false`, `release_green_rows=0`,
`p08_complete=false`, `production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. The next task is one combined complete-package target campaign for all
P08-owned direct profiles, while keeping the five unavailable reasons visible.
