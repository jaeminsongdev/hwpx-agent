# P09-09 mail-merge policy

## Scope

This card owns only REF-046 `ref.mailmerge_field`, insertion of a mail-merge template field.
REF-047 `ref.mailmerge_generate` is P11-owned automation. Preview execution, record expansion,
single/multiple document output and label rendering are generation effects and are not admitted by
this component schema, `hwpx-agent.mail-merge/v1`.

## Qualified native boundary

The pinned Hancom OWPML model qualifies `MAILMERGE` as a field type and the generic
`fieldBegin`/`fieldEnd` envelope. It provides no mail-merge-specific parameter keys, provider
schema, source-column encoding, placeholder-body rule, preview rule, record iteration rule or
output/label behavior. The component therefore uses `unverified_field_parameters`, exposes no
direct HWPX lowerer, and never guesses provider-native bindings.

## Required state

- Bind the complete ordered section and run/inline/page topology.
- Represent each data source only as a distinct encrypted external artifact plus exact provider,
  version, locale, schema, record-count, row-identity-manifest, access-policy and PII-policy state.
- Record every source column with stable logical identity, provider-key, display-name, type,
  nullability, sensitivity, semantic definition, format, lock and opaque state.
- Bind every template field to exactly one existing source and column, a current projection,
  placeholder digest, generic native pair, exact native IDs and opaque state.
- Preserve complete preview, batch-output and label-layout inventories as digests. Their existence
  is not evidence that preview, generation, output or rendering is implemented.
- Bind complete non-mail-merge native IDs/names and all unrelated field, reference, note, TOC,
  citation, object, numbering, style, relationship, resource, protection and opaque document state.

## Mutation and failure policy

- The only mutation is insertion of one complete current template field at a bounded index.
- Plaintext or unencrypted source admission is forbidden. No row value, address, email, name or
  provider credential belongs in this public model, receipt, error or Debug output.
- Missing/ambiguous source or column, duplicate provider key, invalid locale/digest, excessive
  record count, native ID/name collision, invalid anchor or stale new field fails without output.
- A locked document or target section rejects insertion. Source/column locks are read-only and are
  preserved exactly.
- Request, plan and build independently recheck exact source-state and document-flow digests; the
  sealed plan binds the operation and both source/target state and flow.
- JSON is duplicate/unknown-key rejecting and bounded; output is deterministic and bounded.

## Evidence boundary

Passing this card means typed component and pinned structural-source evidence only. It does not
mean native parameters, provider mapping, direct HWPX, actual HWPX, licensed Hangul, semantic
reopen, field readback, reference update, preview, batch output, label layout execution,
save/reopen, render, automation, differential, P09 green, production readiness or product
completion.
