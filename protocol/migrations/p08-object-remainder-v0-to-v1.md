# P08 remaining object capabilities v0 to v1

There is no accepted v0 object-remainder state. A caller must not reinterpret a generic shape,
generic property bag, cursor-only insertion, partial object list, filename-only resource list, or
automation candidate as one of the fourteen exact v1 capabilities.

`obj.freeform` is distinct from `obj.shape_insert`, and `obj.shape_edit_points` requires a complete
existing freeform topology. The property transitions require the complete bound object state.
Special insertion requires the complete document order, object/caption/paragraph inventory,
resource and relationship ID sets, and their digests. Active form behavior cannot be enabled by a
migration flag.

Unknown or duplicate fields, missing state, kind mismatch, invalid topology, unsafe links,
identity/resource/relationship collisions, active content, state or flow drift, plan tampering and
no-op transitions fail closed. There is no migration switch that weakens these requirements or
promotes unit evidence to HWPX, Hangul, render, automation, differential or production evidence.
