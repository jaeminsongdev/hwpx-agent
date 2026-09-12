# P09-08 citation policy

## Scope

This card owns only REF-044 `ref.citation_insert`. REF-043 bibliography management and REF-045
bibliography generation remain P11-owned automation capabilities. The public component schema is
`hwpx-agent.citation/v1`.

## Qualified native boundary

The pinned Hancom OWPML model qualifies the generic `fieldBegin`/`fieldEnd` envelope, the
`CITATION` field type, and the package constants `Custom/bibliography.xml`, manifest id
`bibliography`, and media type `application/xml`. The same implementation leaves bibliography
reading as a stub and writes an already decompressed bibliography part without parsing its record
format. Therefore citation parameter keys, bibliography record XML, provider schemas, display
formatting, field-body serialization, refresh behavior, and generated bibliography layout are not
qualified.

The component must keep these unverified facts explicit as `unverified_opaque_part` and
`unverified_field_parameters`. It must not expose a direct HWPX lowerer until an exact native
fixture and strict reader qualify them.

## Required state

- Bind the complete ordered section inventory and run/inline/page topology.
- Preserve the complete bibliography part digest, exact qualified package identity, provider and
  version digests, locale, style digest, every logical source record and its semantic, display, raw
  and opaque state.
- Bind each citation to one or more distinct existing logical sources in caller-specified order,
  display options, visible cache, native begin/end pair, exact native IDs and all opaque state.
- Bind complete non-citation native control/field/name inventories and all unrelated field,
  reference, note, TOC/index, object, numbering, style, relationship, resource, protection and
  document-state digests.
- Cache projection includes provider/version/locale/style, only selected source records in citation
  order, and display options. An unrelated provider record or raw whole-part byte change alone must
  not invalidate a citation; a selected source, style, provider, locale, order or display-option
  change must.

## Mutation and failure policy

- The only mutation is insertion of one complete current citation at a bounded ordered index.
- Missing/ambiguous/duplicate sources, catalog/provider-key collisions, native ID/name collisions,
  invalid anchors, stale new caches, malformed digests/locales, or inconsistent native pairs fail
  closed without partial state.
- Document and target-section protection fail closed. Catalog/source locks do not block a read-only
  reference and are preserved exactly.
- Request creation, planning and building independently recheck exact source-state and document-flow
  digests. The plan seal binds request, operation and both source/target state and flow.
- JSON is bounded and duplicate/unknown keys are rejected. Output is deterministic and bounded.
- Debug output and error codes must not expose logical IDs, provider keys, source records, field
  names, displayed text, native parameters, document flow or digests.

## Evidence boundary

Passing this card means typed component and pinned structural-source evidence only. It does not mean
`direct_hwpx`, actual HWPX, licensed Hangul execution, semantic reopen, field readback, reference
update, Hancom open, save/reopen, render, automation, differential, P09 green, production readiness,
or product completion.
