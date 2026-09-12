# P09 citation v0 to v1 migration

There is no accepted predecessor wire model. Callers must construct a complete
`hwpx-agent.citation/v1` state and request; implicit upgrade from free-form citation parameters,
raw XML, provider objects, field payloads, arbitrary paths, or partial bibliography records is
forbidden.

Required migration work:

1. Snapshot the exact bibliography part and its qualified package identity without parsing or
   normalizing the unverified native record format.
2. Assign stable logical IDs to the catalog, every provider record, and every existing citation.
3. Bind provider/version/locale/style and per-record semantic, display, raw and opaque digests.
4. Bind complete section, native-ID/name and unrelated document inventories.
5. Construct a citation with distinct existing source IDs in display order, complete display
   options, a current selected-source projection and the full generic native field pair.
6. Recompute source state and document flow at request, plan and build boundaries.

REF-043 management and REF-045 generation are not migration fallbacks; they remain P11-owned.
No migration may claim native citation parameters, direct HWPX, licensed-target or render evidence.
