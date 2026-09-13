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
- A create-new, hash-bound 32-case request and one-session surface inventory runner pass exact-target
  execution: 32/32 completed, 22 enabled in the prepared context, 10 disabled in context and 14/14
  documented default reads passed. Configuration-only validation and 25 planner/runner/evidence tests
  pass. The runner probes `IsActionEnable`, `CreateAction` and read-only defaults without executing
  the candidate under probe. The table-create candidate is used 30 times only to construct
  disposable table contexts and 176 fixture-control executions are recorded separately; none can
  qualify runtime support. Redacted evidence is stored at
  `implementation/p06/evidence/target/p06-table-automation-candidate-32-surface.current-2020.attempt01.v1.json`.
- The 22-case direct Hangul attempt 04 timed out at the first `open_input` while waiting for the
  user-owned access approval. It completed 0/22, preserved unchanged inputs and cleaned its owned HWP
  process with 0 remaining. This failure is not replaced by the successful surface inventory.
- Runtime states remain 61 `unverified`; routing remains disabled for 61/61.
- Differentials remain 61 `not_run`.

## Next boundary

Rerun the 22-case direct Hangul lifecycle/render batch when the user can approve access once, then
perform original-detail render review. The 32-case surface inventory remains non-promoting;
target-bound disposable runtime qualification, the remaining 29 unavailable rows and
direct/automation differentials still follow. No row is release-green until its own direct oracle,
runtime binding and exact differential all pass.
