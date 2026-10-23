# P08-09 object conformance policy

## Scope

This policy owns the current-target matrix for `OBJ-001` through `OBJ-058`. Catalog ownership is
preserved: 42 rows belong to P08 and 16 rows belong to P11. P08 closure never promotes a P11 row.

The exact target is licensed Hancom Hangul 2020 `11.0.0.9136`, x86, `ko-KR`, on the current
personal development PC. No other build, PC or arbitrary user document inherits this state.

## P08 phase rule

For a supported P08 capability, the catalog declares `direct_hwpx` as the preferred backend and
desktop automation as a fallback. A supported row is green only when its preferred direct route is
`oracle_verified`, all required validations and fixture classes pass, negative and rollback/retry
evidence pass, and one of these exact fallback states is recorded:

1. the fallback is exact-target runtime verified, routing is enabled for that row, and the direct
   and automation effects match the same capability contract; or
2. the fallback is unavailable with an exact reason, routing is disabled, and the differential is
   explicitly not applicable because the verified preferred route remains authoritative.

The second state is not a skipped test or an inferred PASS. It is a fail-closed fallback result.
An unavailable fallback cannot be routed. `OBJ-044` is different: the capability itself is absent
from the exact target, so it remains non-green and non-advertised as
`CAPABILITY_UNAVAILABLE_FOR_TARGET`. P08 may close as `pass_with_target_unavailable` only when the
other 41 supported P08 rows are green and this negative result remains current.

## Current evidence projection

- P08-20 proves 41/41 supported direct routes on the exact target with save/reopen, independent
  semantic/resource/bounds checks, 96-DPI render checks and three declared retries.
- P08-21 proves that `OBJ-044` has no persistent exact native or automation aspect-lock surface on
  this build. Fixed-size protection is not an equivalent.
- P08-22 binds 40 source-backed automation candidates and records two exact missing surfaces.
- P08-23 confirms 38 non-known-modal surfaces without candidate execution.
- P08-24 proves five selected-shape canaries with semantic Undo and no file open/save.
- P08-25 isolates the remaining safe candidates by feature. Together with P08-24, 34 routes have
  exact-target semantic effects and bounded rollback. Eight routes are unavailable with exact
  reasons and remain disabled. The 34 runtime effects match the corresponding direct route under
  `same_capability_contract_exact_target_semantic_effect_v1`.

The current 58-row matrix therefore has 41 green P08 rows, one non-green accepted target-
unavailable P08 row, and 16 non-green deferred P11 rows. The global matrix is not a P11 or product
PASS.

## Thresholds and privacy

Resource checks require exact payload/media/length/reference identity. The single-image Hancom
normalization is admitted only by the P08-20 target profile. Render checks require the same build,
font inventory and DPI, an explicit affected region, zero changes outside it, zero structural
mismatches, zero missing glyphs, and strict object placement/size.

`OBJ-046` additionally binds security fixtures that reject printability on a generic non-form
object and reject source/flow drift before output. Public evidence contains repository-relative
paths and hashes only; raw Action/parameter identifiers, document content, absolute private paths
and probe values remain private.

Current claims: `p08_rows=42`, `p08_supported_rows=41`, `p08_green_rows=41`,
`p08_target_unavailable_rows=1`, `automation_runtime_verified=34`,
`automation_unavailable_with_reason=8`, `differential_exact_match=34`,
`p08_phase_gate=pass_with_target_unavailable`, `p08_complete_current_pc=true`,
`p11_complete=false`, `production_ready=false`, and `product_complete=false`.
