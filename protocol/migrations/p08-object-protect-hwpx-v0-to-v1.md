# P08 object protection HWPX v0 to v1 migration

There is no accepted v0 representation. The v1 adapter is additive: it extends the complete common
geometry operation vocabulary with `obj.object_protect` and does not reinterpret any existing
geometry, appearance, object-property, or object-specific field.

V1 requires one exact direct run-level common object, its complete typed geometry state, exact
before/after document-flow digests, and one canonical root `lock` attribute. A real transition edits
only that attribute value span; a no-op request is rejected.

Any wrong identity, kind, ordinal, missing, duplicate, nested, qualified, ambiguous or noncanonical
target field, stale state/flow, section/object/plan mismatch, target readback failure, preservation
failure, or bounded-limit violation must fail closed. There is no legacy fallback, no migration
switch, and no partial output.
