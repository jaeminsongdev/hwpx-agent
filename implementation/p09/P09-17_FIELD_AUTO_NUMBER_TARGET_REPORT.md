# P09-17 Field auto-number target report

Updated: 2026-10-02. Decision: `FAILED SEMANTIC / HISTORICAL LIFECYCLE PASS / GREEN 0 / P09 OPEN`.

## Result

The preserved 2026-09-15 attempt successfully opened, saved, exported PDF, quit, reopened in a
different exact-target process, saved and exported again. Its trace recorded zero remaining HWP
processes. Both `RegisterModule` returns were false; the prescribed security preflight was pass.
These facts are retained without promoting them to field correctness or render acceptance.

| Case | Feature | Native type/effect | Input | Saved | Reopened | Cached-result preservation |
|---|---|---|---:|---:|---:|---|
| P09-17-C01 | REF-006 | PAGE insert | 9 | 9 | 9 | pass, non-green |
| P09-17-C02 | REF-008 | PICTURE insert | 2 | 0 | 0 | fail, non-green |
| P09-17-C03 | REF-008 | TABLE insert | 3 | 0 | 0 | fail, non-green |
| P09-17-C04 | REF-008 | EQUATION insert | 4 | 0 | 0 | fail, non-green |
| P09-17-C05 | REF-009 | direct numeric PAGE update | 9 | 9 | 9 | pass, target recalculation not run |

The input contains zero native `pic`, `tbl` or `equation` controls; none of its four auto numbers has
a caption ancestor. Thus the experiment does not qualify a numbered-object/caption association.
The observed zero values and missing objects motivate that next implementation; they do not by
themselves prove the exact internal Hangul recalculation mechanism.

## Implemented correction

- Reused and strengthened the existing inspector rather than adding another native field parser.
- Split structural inspection from expected-value verification; no-expectation output is now
  `structural_only`, and `9/2/3/4 -> 9/0/0/0` is `semantic_projection_mismatch`.
- Added bounded hash/state/operation-chain qualification of input, lifecycle, saved/reopened and
  PDF artifacts. Published an exclusive-create, redacted successor receipt with five case decisions.
- Added regression tests for historical zero recalculation, weakened expectations, altered hashes,
  stale lifecycle identities, fake fresh sessions, duplicate JSON, boundary escape, linked files,
  excessive package/ZIP size, active XML and caption-context observation.
- Preserved the private attempt, fixture and preliminary public receipt; no source artifact was
  rewritten, no COM/UI action ran, and no P09 matrix row was promoted.

Authoritative successor:
`implementation/p09/evidence/p09-17-field-auto-number-target-qualification.current-2020.20261002-r02.v1.json`.
Its SHA-256 is `5aa1565adffa24b6f7e3fce8e69fce44d81de9ac0706d29f115f15d990d27af7`.
It locks the inspector, qualifier, tests, fixture generator and existing target harness.

Immutable input locks:

- Manifest: `e682518000d7f931fb364de8433c5d9d853825c68a4e2251d189d94e3c55a878`.
- Lifecycle trace: `6a2b15ece549f7f4864e9b440b05e5ec0e12e541dedc961043eee1b8ab25ce0b`.
- Input package: `b0efd3e4aed47849eb719bb3090385a139c52d8ce15129b15e168e11861bcb36`.
- Saved package: `b1dd458e523cfd716d9846762d7cdd1575b3b5b9e2b53b6d98fa3b50168c7817`.
- Reopened package: `bfcc0723c06fd8e5e6b3bdd6690df8aad4d98f656d17be5872185781bdfa7356`.

Reproduce the receipt without changing the attempt:

```powershell
py -3 tools/p09/qualify_field_auto_number_target.py `
  --manifest fixtures/target-build/p09-17-field-auto-number-target-20260915-04/output/fixture-manifest.json `
  --expected-manifest-sha256 e682518000d7f931fb364de8433c5d9d853825c68a4e2251d189d94e3c55a878 `
  --attempt implementation/p09/evidence/private/p09-17-field-auto-number-target-20260915-attempt01 `
  --expected-trace-sha256 6a2b15ece549f7f4864e9b440b05e5ec0e12e541dedc961043eee1b8ab25ce0b `
  --verify implementation/p09/evidence/p09-17-field-auto-number-target-qualification.current-2020.20261002-r02.v1.json
```

CLI `state=pass` means the failed qualification receipt was reproduced/verified; its separately
reported `qualification_state=failed_semantic_non_green` and `semantic_failures=3` remain failures.

## Same-turn checks

Focused target inspector/qualifier tests: `19/19 PASS`. Field-domain Rust tests: `8/8 PASS`;
static-section adapter tests: `8/8 PASS`; sealed-plan tamper test: `1/1 PASS`. Package all-target,
all-feature locked offline Clippy with `-D warnings`: `PASS`. P09 matrix deterministic verification,
P09 aggregate contract and frozen P17 source-v48 contract: `PASS`.

Final P09 Python suite: `102/102 PASS`. Rust workspace all-target/all-feature locked offline tests:
`PASS` across 262 test-result summaries; ignored external/synthetic qualification tests remain
ignored, not product evidence. Workspace all-target/all-feature locked offline Clippy with
`-D warnings`: `PASS`. Repository format check and `git diff --check`: `PASS`. Receipt deterministic
rebuild/byte comparison: `PASS`; attempted exclusive-create collision was rejected with the
existing receipt hash unchanged. `PLANS.md` is 82 lines. No HWP process remained at final inspection.

The current P08 aggregate failed at `tools/p08/validate_asset_pipeline_contract.py` with
`implementation_digest`. Of its six implementation locks, only shared
`crates/hwpx-package/src/lib.rs` differs. Its expected digest is
`a22f9f73f04e17ac3439022fcf6aaa0fb5f5ddb02d48257d10998bd01bdf2e12`; current bytes hash to
`2c39dfb041a3f470f382e7dfe148c2ff3f78ad416bcfaede8ba7e70e05f6aa76`.
An in-memory removal of only the P09 auto-number module declaration and export block exactly
reproduced the P08 expected digest. No Rust source or P08 authority was modified in this turn.
This isolates the source-lock drift but does not make the failing aggregate a PASS.

## Remaining work

P09-11 remains 35 unit + 11 static-section integration rows, 7 P11 deferred and zero green.
REF-008 requires actual object association/numbering implementation and a fresh exact-target
campaign. REF-006/009 need application-owned field/reference update evidence; preserved cached
numbers alone do not suffice. Render/visual, direct/automation differential, full reference-family
integration and P09 Gate closure remain open. A new access-allow validation is held at the user's
requested pause boundary; this turn did not start that validation.
