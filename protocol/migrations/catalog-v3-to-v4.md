# Protocol catalog v3 to v4

`catalog-v4` adds the private P10 Hancom execution bundle and signed-envelope schemas without
changing any v1, v2 or v3 schema/catalog bytes.

- Existing consumers may continue to pin `schema-catalog-v3.json` unchanged.
- Windows Hancom execution workers opt into `schema-catalog-v4.json`.
- Public operation plans continue to contain semantic capability IDs only. Raw Hancom Action,
  ParameterSet and item identifiers remain confined to the signed private bundle.
- A bundle is usable only for its exact target/build/locale/architecture/executable and capability
  registry digest. Unknown fields, untrusted signatures and target drift fail closed.
