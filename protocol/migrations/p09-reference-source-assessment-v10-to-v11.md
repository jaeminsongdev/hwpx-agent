# Reference source assessment v10 to v11 migration

`reference-source` emits `hwpx-agent.product.reference-source-assessment/v11`.
The new `note_selections` array allows clients to construct typed note-kind
requests from actual source observations without importing Form or Note data
again. Existing result fields and their qualifications remain unchanged.

## New selection fields

Each array item has exactly three fields:

- `note_id`: the source-generated logical ID bound to document, package, part and source position.
- `source_note_sha256`: the marker subtree fingerprint as a JSON array of 32 byte values.
- `kind`: `footnote` or `endnote`, reflecting the actual source tag.

The array follows source XML order. It does not expose note text, raw XML,
native attributes, marker characters or native instance IDs. No notes yields
an empty array, not a successful zero-reference validation. Selection count
and serialized response size retain the original finite limits.

## Client migration

Clients must recognize the v11 schema before using these selectors. Historical
v10 responses are not rewritten; do not manufacture selectors from their
absence or interpret native numeric IDs as substitutes. There is no stored
document or database migration.

Use `note_id`, `source_note_sha256` and an explicit target NoteKind to construct
`NoteKindConversion`. Changing the document or any package content requires
new selectors. A response, digest or retained candidate is not authorization:
the stored provider rechecks current scope, head, ACL, quarantine, AEAD and
the complete source before preparation and each output exposure. Final head
verification still precedes the consumer callback.

## Preserved incomplete state

`status=incomplete`, four unresolved stages, `validation_report=null` and CLI
exit code 3 remain. This migration does not qualify database persistence,
issuer authority, atomic CAS, execution, publication, Native numbering,
save/reopen, rendering or the P09 Gate. Existing executable-route denial stays.

## Verification

The source API suite passes five new tests and 46 affected regressions. The
stored target separately passes the API JSON join and the strengthened
three-lane historical-input contract. Foreign/stale selectors, fingerprint
tampering, revoked access, hidden notes and finite output limits retain their
rejection behavior. See
`implementation/p09/evidence/p09-361-source-note-api-components016.v1.json`.
