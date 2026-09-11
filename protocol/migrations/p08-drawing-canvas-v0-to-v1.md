# P08 drawing-canvas v0 to v1

There is no accepted v0 wire shape. Callers must construct
`hwpx-agent.drawing-canvas/v1` from a complete document projection.

- Inventory every drawing node and resource; do not infer omitted siblings or resources.
- Assign distinct logical, native object and native instance IDs and exact parent/ordinal/depth.
- Bind geometry, payload, appearance, composition and opaque state separately.
- Convert picture crop to an in-bounds nonempty original-pixel rectangle.
- Reuse the v1 P08-05 picture-effects representation without lossy conversion.
- Represent OLE bytes as opaque content plus optional passive preview and set activation policy to
  `blocked`. Creation, activation and semantic mutation have no v1 migration.
- Bind source state and before/after flow digests. Clip/effects changes must keep flow unchanged.

Partial legacy inputs, implicit defaults, duplicate IDs, dangling or extra resources, unblocked
active content and guessed target serialization fail closed.
