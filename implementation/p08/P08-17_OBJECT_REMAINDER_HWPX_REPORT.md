# P08-17 object remainder HWPX and target route report

## Result

Result: `eight_bounded_direct_profiles_integration_passed / one_exact_reason_fail_closed /
actual_target_not_run / rows_non_green`.

The nine remaining P08-10 rows were handled together. Eight now have bounded direct-HWPX compiler
or adapter profiles and one has a typed exact-target rejection reason instead of a speculative
native or desktop fallback.

## Implemented direct profiles

- `OBJ-003`: the exact installed `FG_Basic_Shapes/Rectangle.drt` is admitted only when its path,
  12,288-byte size, CFB signature and SHA-256 all match, then compiled to the qualified native
  rectangle representation. Other gallery templates remain outside this profile.
- `OBJ-012`: one hash-qualified native static `edit` control is inserted with its complete ordered
  attributes and children; other form kinds, active content, profile drift and XML drift fail closed.
- `OBJ-013`: one plain-static caption subtree is inserted under the exact selected rectangle while
  preserving all bytes outside the insertion span; numbered and duplicate captions fail closed.
- `OBJ-014`: a rectangle is lowered to the fixed paragraph-band profile with paragraph-relative
  anchoring, behind-text wrapping, `39600 x 1200` HWPUNIT geometry and pinned solid fill.
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

`OBJ-044` retains `unit_passed` evidence and the stable internal reason maps publicly to
`CAPABILITY_UNAVAILABLE_FOR_TARGET`. Size protection is not promoted to aspect-ratio lock.

## Verification

- common-property adapter tests: 6/6 PASS;
- exact-target route tests: 5/5 PASS;
- form insertion adapter tests: 4/4 PASS;
- caption insertion adapter tests: 4/4 PASS;
- deterministic 41-case bundle generation: 2/2 PASS with identical manifest SHA-256
  `2d8bfcbf9fe32092614c8d2cd27a3eee2c56d123b0ae956b27544b819bf71a4b`;
- exercised happy, negative, preservation and drift cases;
- no Hangul process was launched and no document was opened or saved in this checkpoint.

The eight direct rows advance from `unit_passed` to `integration_passed` in the P08 conformance
matrix. They remain non-green because licensed-target validation is not run. The one unavailable
row remains `unit_passed` and non-green.

## Evidence boundary

`direct_hwpx_profiles=8`, `unavailable_with_reason_profiles=1`, `rust_tests=19/19 PASS`,
`deterministic_bundle_generations=2/2 PASS`, `bundle_cases=41`,
`schema=true`, `semantic_reopen=true`, `negative=true`, `preservation=true`.

`actual_target_hwpx=false`, `hancom_open=false`, `save_reopen=false`,
`resource_integrity=false`, `object_bounds=false`, `render=false`,
`automation_runtime_binding=false`, `differential=false`, `release_green_rows=0`,
`p08_complete=false`, `production_ready=false`, and `product_complete=false`.

## Next exact task

Execute one licensed Hangul 2020 41-case open/save/reopen/readback, resource-integrity,
bounds/render, differential and rollback/retry campaign. Keep `OBJ-044` visibly unavailable until
a real aspect-lock field or a source-backed negative target result is qualified.
