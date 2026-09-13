# P06-09 exact ActionTable binding overlay report

Date: 2026-09-14

Decision: **PASS for exact-source candidate review; runtime, routing, differential and P06 remain
unverified/in progress**.

## Scope and result

The immutable P02 automation registry remains unchanged. A P06-specific restricted derivative now
reviews the official ActionTable extraction against all 61 table capabilities. Only exact, unique,
single-action matches are admitted. Ambiguous, partial, generic-dialog and composed behaviors stay
`unavailable_with_reason`.

- Exact-source `candidate_unverified`: 32.
- `unavailable_with_reason`: 29.
- Runtime `verified_current_target`: 0.
- Routing enabled: 0.
- Direct/automation differential executed: 0.

The prior six candidates remain candidates; 26 additional rows advance only from no reviewed mapping
to exact-source candidate. This review does not reuse the six-case disposable canary as evidence for
the other 26 rows.

## Evidence chain and privacy

`protocol/private/p06-table-automation-binding-overlay-v1.json` pins the parent registry, official
ActionTable records, candidate graph, canonical matrix and private review by SHA-256. Each admitted
mapping retains only hashes of the source record, graph node, Action identifier, description,
ParameterSet signal and locator in the tracked contract. Raw Action and ParameterSet identifiers
remain in Git-ignored private inputs and the Git-ignored runtime overlay.

`tools/p06/build_table_automation_binding_overlay.py` rebuilds the private overlay and the public
projection fail closed. It rejects source drift, duplicate official Actions, non-unique graph nodes,
capability mismatch, demotion of an existing candidate, any pre-promoted runtime state and any
enabled routing. The public projection contains only feature/capability IDs, binding disposition,
runtime state and routing Boolean.

## Validation

- Synthetic fail-closed overlay tests: 4/4 PASS.
- Actual private-source reconstruction: PASS, 32 candidate / 29 unavailable.
- Public conformance matrix regeneration: PASS, 61 rows, 0 green.
- Private overlay/contract/projection cross-check: PASS.
- Runtime states remain 61 `unverified`; routing remains disabled for 61/61.
- Differentials remain 61 `not_run`.

## Next boundary

First complete the already prepared 22-case direct Hangul lifecycle/render batch. Then execute
target-bound disposable runtime qualification for the 32 candidates, continue exact review or
explicit unavailable evidence for the remaining 29, and run direct/automation differentials. No row
is release-green until its own direct oracle, runtime binding and exact differential all pass.
