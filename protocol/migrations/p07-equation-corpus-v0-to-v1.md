# P07 equation corpus v0 to v1 migration

There is no stored v0 wire format. Existing adapter-local arrays, screenshots, free-form equation
lists and legacy scripts are evidence inputs only and MUST NOT be relabeled as
`hwpx-agent.equation-corpus/v1`.

A v1 producer must build a strict manifest with unique bounded IDs, explicit A/B/C tier,
source kind, expectation and exact negative code where applicable. It then pins the complete raw
manifest bytes by SHA-256 and runs every case through `EquationCorpusRunner`. Tier counts cannot be
inferred from filenames or documentation.

Legacy scripts migrate only to the opaque exact-preserve boundary after byte digest, UTF-8, size
and NUL checks. They are never normalized to current EqEdit and never count as semantic success.
Tier B component success is not target success; a future target receipt must remain a separate
schema and evidence digest rather than mutating or promoting the v1 component receipt.
