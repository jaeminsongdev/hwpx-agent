# P08-08 drawing-canvas, clip and effects policy

## Decision

This checkpoint is `exact_canvas_transition_component_pass / direct_hwpx_not_run /
security_corpus_not_run / task_incomplete`. It implements the current ledger's drawing-canvas,
image-clip and effects prerequisite as one complete state transition. It does not close the older
P08-08 WBS requirement for the full OLE/media active-content policy and security corpus.

## Complete state

The schema is `hwpx-agent.drawing-canvas/v1`. A state binds one document identity, all drawing
nodes, all referenced resources and a digest of unmodelled document state. Nodes have distinct
logical, native object and native instance IDs; exact parent, ordinal and group level; bounds;
visibility, printability and protection; and separate geometry, payload, appearance, composition
and opaque byte bindings. Root nodes are containers. Every other node has a container parent,
cycles and excess depth fail, and each sibling list is exactly `0..n-1`. Empty containers are not
admitted.

Resources have distinct logical and relationship IDs, typed disposition, MIME, content digest and
byte length. The inventory is closed: every node reference resolves and every inventory entry is
referenced. Embedded and linked images are distinguished; linked targets are digest-bound and are
never fetched by this model. An OLE node binds exactly one opaque OLE resource and optional passive
preview resources. Its only admitted active-content policy is `blocked`; no creation, activation,
CLSID dispatch or semantic property edit exists.

Picture state binds its exact image resource, original pixel dimensions, optional clip and the
complete P08-05 `PictureEffects`. A clip is an ordered, nonempty pixel rectangle wholly inside the
original image. Effects reuse the P08-05 shadow, glow, soft-edge and reflection validation instead
of introducing a second approximation.

## Exact transitions and preservation

- `obj.drawing_object_insert` appends one new root canvas and its complete connected subtree. The
  request reserves every new logical node, native object, native instance and resource ID and
  binds an allocator proof digest. Every existing node and resource must remain exactly equal.
- `obj.crop` replaces only one picture clip and that node's payload binding. It preserves all other
  picture fields, bindings, nodes, resources and document flow.
- `obj.picture_effects` replaces only one picture effects value and that node's appearance binding.
  It preserves all other state and document flow. This is an internal exact checkpoint name, not a
  newly published catalog row; P08-05 remains the owner of the individual effect capabilities.

No-op targets, coupled clip/effect edits, unrelated flag or digest mutations, incomplete ID
reservations and flow changes during clip/effect operations fail closed.

## Request, plan and build

Requests carry complete source and target states, the exact operation, source-state SHA-256 and
before/after document-flow SHA-256. Construction validates both states and proves the named delta.
Planning rechecks current state and flow, then seals canonical request, source, target, flow and
capability digests. Build repeats every check, recomputes the target digest and rejects private
plan-field tampering. The result is a pure domain receipt; it is not an execution observation.

All state/request JSON is bounded, duplicate-key-free, unknown-field strict and NFC canonical.
Counts, depth, identifiers, media types, resources, opaque bytes, image dimensions and coordinates
have independent finite limits. Debug output redacts document/node/resource IDs, relationship IDs,
MIME values, dimensions, coordinates, clip/effect values and digests.

## Evidence boundary

The static vocabulary is grounded in the local Hancom OWPML model at pinned commit
`1453388472c703a4b299a0834f425cdac16644b9`. `ContainerType` admits nested containers, drawing
objects, pictures and OLE; `PictureType` owns `imgClip` and `effects`; `OLEType` references opaque
binary content. These files establish static structure only and do not prove installed Hangul 2020
serialization, preservation, activation behavior or rendering.

`exact_canvas_state_component_pass=true`, `insert_clip_effect_transitions=true`,
`opaque_ole_activation_blocked_by_model=true`. `direct_hwpx=false`, `synthetic_package=false`,
`security_corpus=false`, `actual_hangul=false`, `save_reopen=false`, `property_readback=false`,
`render=false`, `automation=false`, `differential=false`, `p08_08_complete=false`,
`p08_complete=false`, `production_ready=false` and `product_complete=false`.

Reasoning level: `max`; the remaining active-content/security checkpoint and P08-09 are also
`max`.
