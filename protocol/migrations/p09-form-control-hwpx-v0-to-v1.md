# P09 form-control HWPX v0 to v1 migration

There is no accepted v0 wire contract and no implicit migration.

Only `hwpx-agent.form-control-hwpx.hwpml-2011-existing-native-form-properties/v1` is accepted.
Unknown profiles, fields, native tags, enum spellings, control insertions, payload mutations,
unverified date controls, incomplete tab assignments, stale state/flow/section/object bindings, and
unsealed plans fail closed with no partial output. Producers must reconstruct and validate a fresh
v1 typed state and plan; no older or partial payload is upgraded in place.
