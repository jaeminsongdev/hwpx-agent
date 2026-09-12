# P09 reference auxiliary v0 to v1 migration

There is no accepted predecessor wire model. Callers must construct a complete
`hwpx-agent.reference-auxiliary/v1` state. Free-form field parameters, raw XML/actions, raw external
paths, partial caption inventories and inferred validation results are forbidden.

Required migration work:

1. Assign stable logical IDs to sections, caption targets/sequences/bindings, fields, literals,
   correction marks, data-link identities and reference graph nodes.
2. Bind every caption target, document order and deterministic resolved number; preserve the full
   official caption envelope and keep sub-list numbering semantics explicitly unverified.
3. Lift DATE/DOC_DATE format state separately from display cache and opaque native parameters.
4. Replace any path-bearing filename insertion with a frozen leaf string plus its exact digest and
   source revision.
5. Map proofreading fields to one of the 19 closed correction-mark kinds without guessing native
   parameter meanings.
6. Replace raw linked-document paths with encrypted artifact, allowlist-location and relationship
   digests and an explicit inheritance enum.
7. Supply the complete validation target/edge graph and bind the deterministic report digest.
8. Recompute canonical source state and document flow at request, plan and build boundaries.

Migration does not prove native parameters, direct HWPX, reference refresh/repair, licensed-target,
render, automation or differential evidence.
