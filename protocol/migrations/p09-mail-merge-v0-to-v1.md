# P09 mail merge v0 to v1 migration

There is no accepted predecessor wire model. Callers must construct a complete
`hwpx-agent.mail-merge/v1` state and request. Free-form field parameters, raw XML, provider
objects, plaintext rows, filesystem paths, credentials and partial source schemas are forbidden.

Required migration work:

1. Move the data source into an encrypted artifact outside the document and bind its digest.
2. Bind provider/version/locale, schema, exact record count, row-identity manifest, access policy
   and PII policy without copying row values into the model.
3. Assign stable logical IDs to every data source, schema column and existing mail-merge field.
4. Classify every column's type, nullability and sensitivity and bind provider/display/semantic/
   format digests.
5. Bind complete section, native-ID/name, preview, batch-output, label-layout and unrelated document
   inventories.
6. Construct a current field with one exact source/column pair and the full generic native pair.
7. Recompute source state and document flow at request, plan and build boundaries.

REF-047 generation is not a migration fallback. No migration may claim preview, batch output, label
rendering, native parameter semantics, direct HWPX, licensed-target or render evidence.
