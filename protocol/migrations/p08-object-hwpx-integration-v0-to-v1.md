# P08 object HWPX integration v0 to v1 migration

There is no accepted v0 representation. The v1 profile is additive and does not reinterpret the
P08-06 or P08-08 domain contracts.

Migration requires a complete validated source state, exact before/after document-flow digests and
an admitted closed HWPML 2011 section island. Generated objects must satisfy the standardized empty
binding and supported-kind rules. Existing opaque fragments are preserved byte-for-byte except for
the exact planned attributes or children.

Any missing identity, ambiguous topology, unsupported payload/resource/effect, stale state/flow,
plan mismatch or semantic-reopen failure must fail closed. There is no legacy fallback and no
partial output.
