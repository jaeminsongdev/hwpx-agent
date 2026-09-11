# P08-06 object composition policy

## Decision

P08-06 is `pure_object_graph_component_pass / direct_hwpx_not_run / task_incomplete`. The v1
checkpoint implements all six requested composition capabilities as one exact, bounded graph
transition model. It does not lower a graph into HWPX and has not been opened, saved, reopened or
rendered by licensed Hangul 2020, so neither P08-06 nor P08 is complete.

## Complete graph state

The schema is `hwpx-agent.object-composition/v1`. Every object binds a distinct logical ID,
nonzero distinct native object and instance IDs, kind, parent group, contiguous sibling z-order,
exact group depth, world-coordinate bounds, visibility, printability and a content-addressed
binding for its complete non-composition state. That binding contains the exact SHA-256, byte
length and a strictly ordered resource-reference set; operations may not rewrite it.

Groups are nonempty containers with at least two direct children. Their bounds must equal the
union of their direct children. Parents must exist and be groups, cycles and excess depth fail,
and every sibling list is exactly `0..n-1`. Group and ungroup preserve every existing child ID,
native ID, world-coordinate bound, visibility, printability, payload/property binding and resource
reference. Grouping requires at least two siblings and a fresh three-part identity. Ungrouping
removes only the selected group node and splices its children into the exact former z-order slot.

## Exact operations

- `obj.group` and `obj.ungroup` implement the closed containment transitions above. Connector
  subjects and their connector must cross the boundary together; a dangling or cross-parent edge
  fails closed.
- `obj.z_order` implements bring-to-front, send-to-back, forward-one and backward-one. The selected
  object moves only among its siblings and every other field is preserved. An edge no-op is an
  explicit failure.
- `obj.align` implements left, horizontal-center, right, top, vertical-middle and bottom against
  the selected siblings' envelope. Half-HWPUNIT centers use deterministic Euclidean-floor
  placement. Moving a group translates its complete subtree.
- `obj.distribute` implements horizontal and vertical equal-gap distribution for at least three
  siblings. The first and last objects remain fixed. Integer remainders are assigned one HWPUNIT
  at a time to the earliest gaps, so gap sizes differ by at most one.
- `obj.connector` creates and updates straight, stroke and arc connectors in no-arrow, one-way and
  both-arrow forms. Endpoints bind world coordinates and optional same-parent non-connector
  subjects plus bounded connection indexes; control points are ordered and bounded. Connector
  bounds are derived from every endpoint/control point and cannot drift.

Align/distribute reject connector roots. Moving a subject while leaving its attached connector
outside the transition also fails the final closure check. This is a deliberate exact-state
boundary until one native HWPX profile establishes how installed Hangul rewrites attached
connector points during those operations.

## Planning, limits and diagnostics

Graph and request JSON is compact, deterministic, bounded, duplicate-key-free and unknown-field
strict. Requests bind the exact source graph SHA and before/after document-flow SHA. Admission,
planning and build each recompute the operation and all graph invariants; build additionally
recomputes the complete target and sealed plan digest. Limits independently cover input/output
bytes, objects, selection, resources, control points, depth, identifiers, coordinates, content
bytes and connection indexes. Debug output redacts IDs, coordinates, resource references, content
digests and flow/state/plan digests.

## Evidence boundary

The static vocabulary is grounded in the archived KS X 6101 source and Hancom's OWPML model at
pinned commit `1453388472c703a4b299a0834f425cdac16644b9`, specifically `ContainerType`,
`AbstractShapeObjectType`, `AbstractShapeComponentType`, `ConnectLineType` and
`ConnectPointType`. Those sources establish names and field types only, not installed-target
serialization, action behavior or rendering.

`pure_object_graph_component_pass=true`, `graph_invariant_tests=true` and
`complete_noncomposition_state_binding=true`. `direct_hwpx=false`, `resource_integrity=false`,
`semantic_reopen=false`, `actual_target_hwpx=false`, `actual_hangul=false`, `save_reopen=false`,
`object_bounds=false`, `render_diff=false`, `automation=false`, `differential=false`,
`p08_06_complete=false`, `p08_complete=false`, `production_ready=false` and
`product_complete=false` remain explicit.

Reasoning level: `max`; P08-07 charts and the later combined target campaign also remain `max`.
