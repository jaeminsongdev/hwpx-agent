# Semantic diff v0 to v1

P04-07 replaces conceptual text-only or raw-value comparisons with
`hwpx-agent.semantic-diff/v1`. Callers must provide two validated DocumentGraph v2 instances,
their exact revision identities and canonical graph SHA-256 values.

The v1 result contains only typed categories, entity kinds, change kinds, hashed subject/value
references, finite structural paths and reference-impact counts. Raw document text, property values,
logical IDs and backend identifiers are intentionally absent. Consumers must reject unknown schema
versions and must not infer rename or move from unrelated remove/add pairs.

This migration is additive. No P04-01 DocumentGraph bytes or prior route/transaction receipt bytes
change.
