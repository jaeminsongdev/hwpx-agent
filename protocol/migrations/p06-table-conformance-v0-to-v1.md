# P06 table conformance v0 to v1 migration

P06-09 introduces `hwpx-agent.table-automation-projection/v1`,
`hwpx-agent.table-conformance-evidence/v1`, and
`hwpx-agent.table-conformance-report/v1` as additive contracts. There is no predecessor wire
payload to coerce.

These public schemas first appear in additive `schema-catalog-v5.json`. Catalog v2, v3 and v4
remain byte-for-byte immutable; consumers pinned to those catalogs do not receive the new schemas.

The report joins exactly 61 `TABLE-001` through `TABLE-061` rows across the canonical feature
catalog, generated capability contracts, one redacted exact-target automation projection, and
hash-bound direct evidence. Missing records are interpreted as `cataloged`, never as tested.

A row becomes `green` only when its direct HWPX route is oracle verified, every contract validation
and required fixture class passes, negative and rollback/retry evidence passes, the exact current
target automation binding is runtime verified, and the direct/automation differential is an exact
match. Existing component, static adapter, or unrelated runtime evidence may not promote a row.

The projection removes raw Action, ParameterSet, default and probe values. Future current-PC
evidence advances by an additive evidence/projection successor and regenerated report. A later
Hangul build or another PC requires a new target-scoped projection and report; v1 evidence is not
coerced or inherited across targets.
