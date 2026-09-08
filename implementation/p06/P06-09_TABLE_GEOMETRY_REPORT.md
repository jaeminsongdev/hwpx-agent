# P06-09 table geometry component report

- Generated: 2026-09-08
- Model schema: `hwpx-agent.table-geometry/v1`
- Scope: current repository, pure local IR component
- Result: `component_pass`
- Recommended next-step reasoning: `max`

## Result

The repository now contains deterministic implementations for `TABLE-018` equal row height,
`TABLE-019` equal column width and `TABLE-050` row minimum height. Each operation is bound to one
validated `TableGrid`, preserves tracks outside the selected range, enforces positive bounded
dimensions and content minima, and emits source/output state hashes in a bounded receipt.

This is deliberately unit-level evidence. The backend remains `component_only`; no HWPX XML was
changed and no Hangul process, save/reopen, PDF render or automation action was invoked.

## Validated behavior

| Area | Evidence | State |
|---|---|---|
| Row equalization | ceiling-average distribution with maximum selected minimum | PASS |
| Column equalization | same bounded semantics without changing rows | PASS |
| Row minimum | grows undersized rows and never shrinks larger rows | PASS |
| Merged extent | checked sum across canonical master-cell spans | PASS |
| Atomic failure | invalid range/dimension/grid leaves source digest unchanged | PASS |
| Determinism | repeated source and operation yield equal state and receipt | PASS |
| Strict input | version, duplicate/unknown JSON, counts, minima and limits fail closed | PASS |
| Privacy | Debug excludes hashes and raw dimensions | PASS |

## Verification

- `cargo test -p domain-ir --test table_geometry`: 13/13 PASS.
- `cargo clippy -p domain-ir --tests -- -D warnings`: PASS.
- Fixed-seed boundary corpus: 256/256 deterministic and minimum-preserving cases PASS.
- Contract validator checks exact source locks, semantic policy, implementation markers and
  non-claims; its tamper suite covers source drift, implementation drift, duplicate keys,
  traversal, semantic drift, limits and non-claim promotion.

## Conformance impact

After this report is hash-admitted into the P06-09 direct evidence registry, the strict 61-row
matrix changes only as follows:

- direct `cataloged`: 33 to 30
- direct `unit_passed`: 13 to 16
- direct `integration_passed`: remains 4
- direct `oracle_verified`: remains 11
- green rows: remains 0/61

The unchanged green count is expected: unit evidence is insufficient for the release rule.

## Preserved boundaries

No direct HWPX adapter, semantic reopen against modified package XML, formula preservation,
page-split behavior, Hangul 2020 target-build readback/render, automation runtime, differential,
arbitrary user document, other PC/version, P06 completion, production or product completion is
claimed. User-provided source documents and the original design archive were not modified.

The next exact task is the direct HWPX geometry adapter and package-level semantic reopen tests;
recommended reasoning remains `max`.
