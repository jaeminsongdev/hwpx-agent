# P08-03 object geometry and transform policy

## Decision

P08-03 is `common_component_pass / target_not_run / task_incomplete`. The v1 checkpoint admits the
complete HWPML 2011 common geometry state for one existing run-level picture or drawing component
and lowers exact protection, position, size, anchor, wrap, rotation and flip transitions into
preserving section bytes. Licensed-Hangul serialization, full-package reopen and rendering have not
run, so P08-03 and P08 remain incomplete.

## Admitted object and state model

The reviewed profile covers the public OWPML-model descendants exposed as run-level `pic`, `rect`,
`ellipse`, `line`, `arc`, `polygon`, `curve`, `connectLine`, `container`, `ole`, `video` and
`textart`. Nested group members are not independently addressable in v1. Graph/chart controls,
unknown drawing extensions and objects missing any required common child fail closed.

The typed state includes logical/native object identity, object kind, z-order, numbering type, lock,
absolute or relative width/height, protection, all five anchor flags, horizontal/vertical reference,
alignment and offsets, wrap/flow, four outer margins, component offset, original/current size,
horizontal/vertical flip, rotation angle/center/image flag and all 18 coefficients of translation,
scale and rotation matrices. The profile changes none of the object-specific payload.

OWPML FLOAT matrix values are represented as signed fixed millionths. Source decimals with more
than six fractional digits, exponents, noncanonical signs or out-of-bound magnitudes are rejected.
Rotation and flip operations require the caller to provide the complete target transform matrices;
the component does not infer target-specific trigonometric normalization.

## Exact planning and lowering

The private domain schema is `hwpx-agent.object-geometry/v1`. Request construction binds the exact
canonical source state and document-flow SHA-256. Planning rechecks both. The HWPX plan then binds
the full section bytes and selected object bytes; final lowering rechecks the plan digest, section,
object, state and flow before returning output.

The lowerer edits only value spans for common attributes whose typed value changed. Unchanged
lexemes, namespaces, whitespace, sibling objects and every object-specific child remain byte-exact.
Semantic readback must equal the planned target state. The six original geometry/transform
operations retain byte-identical no-op lowering; `obj.object_protect` rejects a no-op before plan
construction. No failure returns partial bytes.

## Limits and diagnostics

JSON input/output, HWPUNIT extents, matrix coefficients, section bytes, XML elements, object count,
output bytes and matrix lexemes have independent finite hard ceilings. State and request JSON reject
duplicate, unknown, missing and malformed fields. Native booleans require `0` or `1`; identifiers and
integers require canonical bounded forms. Public `Debug` hides identities, geometry, paths and
digests.

## Evidence boundary

The vocabulary and inheritance are grounded in the local archived KS X 6101 material and Hancom's
public OWPML model at pinned commit `1453388472c703a4b299a0834f425cdac16644b9`. Those sources are a
static type reference, not an installed-Hangul runtime oracle. All current fixtures are synthetic
section components.

`full_package_hwpx=false`, `exact_current_2020_serialization=false`, `actual_hangul=false`,
`save_reopen=false`, `render=false`, `automation=false`, `differential=false`,
`p08_03_complete=false`, `p08_complete=false`, `production_ready=false` and
`product_complete=false` remain explicit.

Reasoning level: `max`; the next P08 implementation task and later target qualification remain
`max`.
