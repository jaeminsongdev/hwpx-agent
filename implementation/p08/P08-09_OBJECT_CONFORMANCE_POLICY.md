# P08-09 object conformance policy

## Scope

This policy owns one current-target matrix for all `OBJ-001` through `OBJ-058` rows. The canonical
catalog and generated capability contracts define row identity, support level, owning phase,
validators and fixture classes. P08 implementation evidence may advance a row only to the exact
stage it proves; P11 ownership remains visible and is not pulled forward by this ledger.

Target: licensed Hancom Hangul 2020 `11.0.0.9136`, x86, `ko-KR`, current personal development PC.
No other Hangul release inherits this target state.

## Stage policy

The ordered direct stages are `cataloged`, `unit_passed`, `integration_passed`, and
`oracle_verified`. Component-only graph or automation models stop at `unit_passed`. Synthetic XML
or package lowering can reach `integration_passed`. Only direct current-target evidence can reach
`oracle_verified`.

`green` additionally requires every generated-contract validator and fixture class, negative and
rollback/retry evidence, applicable target binding/runtime, a passed direct/automation or provider
differential, exact asset policy, and calibrated current-target render policy. Missing evidence is
a blocker; it is never treated as skipped success.

## Current evidence projection

- Static image insertion, six geometry operations, two basic-shape operations and eleven
  appearance operations have synthetic HWPX/XML integration evidence.
- Six composition operations, nine chart operations, drawing-canvas insertion and crop have exact
  component evidence without direct HWPX execution.
- Fourteen formerly cataloged P08-owned operations now have complete typed unit models: drawing
  gallery, inert form, caption and paragraph-band insertion; margin/caption, text-box and image
  properties; freeform insertion and point editing; aspect lock, protection, printability,
  alternative text and safe hyperlinks.
- Both preserve-only OLE rows have synthetic package inventory, activation denial, security and
  byte-preservation evidence. This does not claim OLE creation or semantic editing.
- The five remaining `cataloged` rows are P11-owned. P08 unit models still do not prove direct
  HWPX lowering, installed-target behavior or automation routing.

## Asset thresholds

Every `resource_integrity` row binds package path, relationship target, media type, expanded
length and payload SHA-256 exactly, with zero dangling or ambiguous references. Every
`binary_preservation` row uses the same exact identity plus zero payload mutations and
`activation_allowed=false`. A section-only image-fill relationship is not package integrity.

## Render thresholds

Each `render_diff` row requires the same target build, font inventory and DPI, an explicit affected
region, zero changed pixels outside that region, zero structural mismatches, zero missing glyphs,
and strict object placement/size. The narrow antialias/color allowance must be bound per fixture;
there is no global permissive pixel threshold. Since no exact-target fixture has calibrated it,
all 53 render rows remain `not_run` and non-green.

## Evidence and privacy boundary

The matrix contains only repository-relative evidence paths and normalized SHA-256 locks. It
contains no document content, raw action/parameter identifiers, private absolute paths or probe
values. Existing failed attempts and user documents remain immutable.

Current claims: `matrix_implemented=true`, `threshold_definitions_complete=true`,
`implementation_covered_rows=53`, `actual_hwpx=false`, `actual_hangul=false`, `render=false`,
`automation=false`, `differential=false`, `green_rows=0`, `p08_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. The next row implementation work and the later current-target campaign
remain `max` because a weaker subset would produce misleading conformance totals.
