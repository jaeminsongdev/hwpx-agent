# P06 table automation binding overlay v0 to v1 migration

The P02 automation binding registry is immutable and remains the parent evidence. P06 adds
`hwpx-agent.p06-table-automation-binding-overlay/v1` as a target-scoped restricted derivative and
`hwpx-agent.p06-table-automation-binding-overlay-contract/v1` as its redacted tracked proof.

The exact official ActionTable review changes only the table binding disposition snapshot from six
candidate-unverified and 55 unavailable rows to 32 candidate-unverified and 29 unavailable rows.
All 61 runtime states remain unverified, all routing flags remain false and all direct/automation
differentials remain not run. No existing canary is inherited by a newly admitted candidate.

The tracked contract contains hashes rather than raw Action or ParameterSet identifiers. The public
`hwpx-agent.table-automation-projection/v1` wire shape is unchanged; its current snapshot receives a
new source digest and dispositions through this explicitly reviewed successor update. A checkout
without private P02 evidence can still validate the committed redacted projection and conformance
report. When private evidence is present, the validator reconstructs and byte-compares the contract,
private overlay and public projection.

Ambiguous, partial, generic-dialog or multi-action matches are not coerced. They remain unavailable
until a separately reviewed successor supplies an exact mapping or explicit composed binding. This
migration does not qualify runtime execution, enable routing, run a differential or complete P06.
