# Selector v0 to v1 migration

`hwpx-agent.selector/v1` is the first executable selector core. The earlier design documents and
`operation-plan-v2.schema.json` remain conceptual wire inputs until P04-04 compiles them into these
validated types.

## Admission changes

- a revision ID and canonical graph digest are mandatory for every resolution;
- text offsets without context anchors are rejected;
- cursor/session and page-position selectors are not admitted by the pure core;
- named slot/field/bookmark values use exact NFC normalization and reserved typed metadata;
- structural paths include node kinds and require an expected final node fingerprint;
- zero, multiple, stale and limit-exceeded results are distinct stable failures;
- deterministic candidate order never implies first-candidate fallback.

Existing clients must not serialize the Rust enum as the final public API. P04-04 must validate the
public OperationPlan v2 schema, reject mixed selector properties and explicitly compile one admitted
wire selector into one v1 typed selector. Any future multi-target selector requires explicit
cardinality and a new additive contract; it cannot weaken `resolve_one`.
