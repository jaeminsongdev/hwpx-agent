# P09 link/reference v0 to v1

- There is no accepted v0 wire representation.
- Producers must emit `hwpx-agent.link-reference/v1` and all complete state fields.
- Raw XML, HAction names, filesystem paths, untyped URLs and implicit external approvals are not
  migratable inputs.
- Bookmark names must be non-empty, exact NFC strings and unique in the bound document state.
- Internal targets migrate only with a live logical bookmark ID.
- External targets migrate only as safe HTTPS, plain email, or path-free managed-artifact targets
  with an exact kind-and-target SHA-256 approval under the bound policy revision.
- Generic HWPX hyperlink parameters remain opaque under `unverified_field_parameters`; v1 does not
  imply direct HWPX lowering or installed-Hangul support.
- Missing identities, occupied non-hyperlink native-ID inventories, native field-pair bindings,
  topology/preservation digests, policy approvals, locks, or opaque state fail closed. No defaults
  are synthesized.
