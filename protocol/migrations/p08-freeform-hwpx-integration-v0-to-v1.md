# P08 freeform HWPX integration v0 to v1 migration

There is no accepted v0 representation. The v1 integration classification is additive and does
not reinterpret the P08-04 basic-shape or P08-10 shape-points domain contracts.

Freeform insertion requires the admitted complete synthetic-package profile. Point editing requires
a complete validated polygon or curve state, exact before/after document-flow digests and exactly
one contiguous native point or segment payload island. All bytes outside that island remain exact.

Any missing or ambiguous identity, unsupported topology, noncanonical payload, stale state/flow,
section/object/payload/plan mismatch, target reopen failure or bounded-limit violation must fail closed.
There is no legacy fallback and no partial output.
