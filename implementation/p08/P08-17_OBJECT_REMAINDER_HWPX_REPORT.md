# P08-17 object remainder HWPX and target route report

## Result

Result: `four_bounded_direct_profiles_integration_passed / five_exact_reasons_fail_closed /
actual_target_not_run / rows_non_green`.

The nine remaining P08-10 rows were handled together. Four now have preserving section-level
direct-HWPX adapters and five have typed exact-target rejection reasons instead of speculative
native or desktop fallbacks.

## Implemented direct profiles

- `OBJ-019`: four `outMargin` attributes plus side, gap, width, lastWidth and simple caption text
  are patched as bounded spans for an already present `numbering=none` caption.
- `OBJ-030`: original pixels, horizontal/vertical DPI and millionth scales are checked and lowered
  to `imgDim`, `orgSz` and `curSz` with checked integer arithmetic.
- `OBJ-046`: only an existing `edit`, `checkBtn`, `radioBtn`, `comboBox` or `listBox` form root can
  change its `printable` attribute.
- `OBJ-047`: only an existing single-string `shapeComment` with empty IR title is admitted; title
  loss and presence changes fail before mutation.

Each profile binds the exact source section, selected object, property span, complete domain plan,
native identity and document flow. Source drift, flow drift, object-kind mismatch, ambiguous XML,
unsupported lexical forms and plan tampering return no output. The preservation check proves all
bytes outside the declared edited spans are identical.

## Fail-closed routes

`OBJ-003`, `OBJ-012`, `OBJ-013`, `OBJ-014` and `OBJ-044` retain `unit_passed` evidence and now have
stable internal reasons that all map publicly to `CAPABILITY_UNAVAILABLE_FOR_TARGET`. In
particular, size protection is not promoted to aspect-ratio lock and a one-string shape comment is
not promoted to a two-field title/description representation.

## Verification

- common-property adapter tests: 6/6 PASS;
- exact-target route tests: 5/5 PASS;
- exercised happy, negative, preservation and drift cases;
- no Hangul process was launched and no document was opened or saved in this checkpoint.

The four direct rows advance from `unit_passed` to `integration_passed` in the P08 conformance
matrix. They remain non-green because complete-package and licensed-target validation is not run.
The five unavailable rows remain `unit_passed` and non-green.

## Evidence boundary

`direct_hwpx_profiles=4`, `unavailable_with_reason_profiles=5`, `rust_tests=11/11 PASS`,
`schema=true`, `semantic_reopen=true`, `negative=true`, `preservation=true`.

`actual_target_hwpx=false`, `hancom_open=false`, `save_reopen=false`,
`resource_integrity=false`, `object_bounds=false`, `render=false`,
`automation_runtime_binding=false`, `differential=false`, `release_green_rows=0`,
`p08_complete=false`, `production_ready=false`, and `product_complete=false`.

## Next exact task

Generate the complete fixture bundle for all P08-owned direct profiles and execute one licensed
Hangul 2020 open/save/reopen/readback, resource-integrity, bounds/render, differential and
rollback/retry campaign.
