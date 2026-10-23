# P08-09 object conformance report

## Result

Result: `P08_PASS_WITH_TARGET_UNAVAILABLE / 41_SUPPORTED_ROWS_GREEN / P11_DEFERRED`.

P08 is complete for licensed Hancom Hangul 2020 `11.0.0.9136` x86 on this PC. The result is
phase-scoped: it is not P11 completion, arbitrary-document compatibility, another-PC/version,
production readiness or whole-product completion.

## Current matrix

- Required global rows: 58 exactly once; P08 owns 42 and P11 owns 16.
- Direct stages: 5 cataloged, 10 unit-passed, 2 integration-passed, 41 oracle-verified.
- P08: 41 supported rows green; `OBJ-044` non-green and accepted as exact-target unavailable.
- P11: 16 rows remain non-green and deferred to P11.
- Automation bindings: 34 exact-target verified, 9 P11 candidates, 2 policy denied, 13
  unavailable with reason (8 P08 and 5 P11/unbound).
- Differentials: 34 exact semantic-contract matches, 7 not-applicable because only the fallback is
  unavailable, 1 not-applicable because the target capability itself is unavailable, and 16 P11
  not-run.
- Thresholds: asset checks required for 44 rows; render checks required for 53 and calibrated for
  the 41 exact-target direct rows.

## P08-25 closure

The final isolated runtime batch passed 29/29 candidates. It used one x86 STA process and one
disposable document per feature, opened only named project-owned P08-20 readback fixtures when a
selected object was required, never saved a document, and left zero owned HWP processes. P08-24
supplies five separately qualified selected-shape canaries, bringing the exact-target automation
runtime total to 34.

The remaining eight P08 fallback routes are disabled with exact evidence:

- `OBJ-003`: parameterized gallery execution returned false without effect;
- `OBJ-012`: the exact form insertion default parameter set was unavailable;
- `OBJ-025`: the selected-textbox property route produced no semantic effect;
- `OBJ-040`: Hancom 2020 exposed no eligible programmatic multi-shape selection for distribution;
- `OBJ-043`: the known-modal edit-points route produced no semantic effect;
- `OBJ-044`: the exact target capability itself is unavailable;
- `OBJ-046`: no exact per-object printable automation surface exists;
- `OBJ-048`: the complete hyperlink parameter route remained modal, timed out, and its one owned
  HWP process was cleaned with no saved document.

For 34 verified routes, the automation effect and the already-qualified direct effect satisfy the
same pinned capability contract on the same target. This is recorded as
`same_capability_contract_exact_target_semantic_effect_v1`; it does not claim byte-identical
serialization. Seven supported rows keep their verified direct primary route while an unavailable
fallback remains disabled. `OBJ-044` remains non-advertised and non-green.

## Validation and evidence boundary

The public P08-25 receipt exposes only target identity, bounded state, and SHA-256 locks. Its
validator deterministically rebuilds the receipt, qualified overlay, public projection and private
contract from the preserved runtime receipts/traces; tamper tests reject route promotion and
unavailable-route enablement. The 58-row matrix validator also rejects catalog drift, duplicate
rows, evidence-path escape, weakened thresholds, false P08 green promotion and any P11 promotion.

`actual_hwpx=true`, `actual_hangul=true`, `save_reopen=true`, `render=true`,
`automation_runtime_verified=34`, `differential_exact_match=34`, `p08_09_green=true`,
`p08_complete_current_pc=true`, `p11_complete=false`, `production_ready=false`, and
`product_complete=false`.
