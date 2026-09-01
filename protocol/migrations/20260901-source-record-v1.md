# SourceRecord v1 additive contract

P02-01 adds `source-record-v1.schema.json` without changing any P01 foundation v1 schema or protobuf descriptor. The existing `schema-catalog.json` remains the immutable P01 foundation catalog. `schema-catalog-v2.json` is the additive catalog for the P02-01 contract.

Compatibility rules:

- Consumers that only know the P01 foundation catalog continue to receive byte-identical generated artifacts.
- P02 consumers opt into `SourceRecordV1` and must reject missing source identity, invalid locator/source-kind combinations, unknown properties and unqualified runtime observations.
- A future additive schema uses the next catalog version. A breaking SourceRecord change also requires a new schema version, a new generated type and explicit migration/negative tests. The v1 schema is not edited in place after this Gate.
