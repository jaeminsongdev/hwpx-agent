# P08 text-box properties HWPX v0 to v1 migration

There is no accepted v0 representation. The v1 adapter is additive and does not reinterpret the
P08-10 complete object-property state or the P08-04 text-box insertion profile.

V1 requires exactly one run-level rectangle text box, one exact `drawText` child topology, a complete
typed source state, exact before/after document-flow digests, and canonical reviewed margin,
direction, and alignment attributes. It edits only changed values in those six attribute spans.

Any wrong identity or ordinal, unsupported root, missing, duplicate, nested, qualified, ambiguous or
noncanonical target field, stale state/flow, section/object/payload/plan mismatch, target readback
failure, preservation failure, or bounded-limit violation must fail closed. There is no legacy
fallback and no partial output.
