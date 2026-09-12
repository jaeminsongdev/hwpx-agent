# P09-05 Link/reference report

Decision: `COMPONENT PASS / OFFICIAL STRUCTURE PARTIALLY QUALIFIED /
UNVERIFIED NATIVE HYPERLINK PARAMETERS / DIRECT AND TARGET NOT RUN / NON-GREEN`.

## Delivered

- Added `hwpx-agent.link-reference/v2` for REF-031 through REF-034, including a required native
  parameter-state digest on hyperlink edits.
- Added exact bookmark insert/delete and hyperlink insert/edit transitions.
- Added internal-bookmark, HTTPS, email and path-free managed-document targets.
- Added a bound policy revision with exact external target approval digests.
- Added dangling-reference, external-policy, global occupied-native-ID collision, anchor, lock, no-op,
  preservation, request/build drift, strict JSON, finite-limit and redacted-Debug checks.
- Added a sealed private plan and tamper test, versioned private contract, migration, source
  qualification, validator and contract tests.

## Source result

The clean pinned Hancom OWPML checkout proves the standalone `bookmark/name` structure and the
generic `fieldBegin`/`fieldEnd` HYPERLINK envelope. It does not prove the meanings of the generic
parameter list entries. The component therefore keeps all hyperlink parameter semantics opaque and
labels the general binding `UnverifiedFieldParameters`; P09-14 separately qualifies only the exact
Hangul 2020 HTTPS/current-tab subset.

## Validation

- Rust public link/reference tests: `10/10 PASS`.
- Rust private sealed-plan tamper test: `1/1 PASS`.
- Focused Rust total: `11/11 PASS`.
- Private contract/source-lock/migration/validator/tamper tests: `5/5 PASS`.
- P09 Python suite, workspace all-target/all-feature tests, Clippy and fmt/diff are recorded only
  after their final runs in the checkpoint ledger.

## Claim boundary

`unit_model_implemented=true`, `four_capabilities_unit_passed=true`,
`official_structure_source_qualified=true`, `external_policy_fixtures=true`,
`dangling_reference_fixtures=true`, and `complete_bound_state_preserved=true`.
`native_hyperlink_parameters_verified=false`, `direct_hwpx=false`, `actual_hwpx=false`,
`actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_05_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

## Next exact task

Implement P09-06 REF-035 cross-reference insertion as a typed target graph. REF-036 update remains
P11-owned automation unless a target-pinned direct identity and update oracle are independently
qualified.
