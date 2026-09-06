# P05-07 attempt23: corrected landscape and bounded identity rebinding

- Date: 2026-09-06.
- Scope: the fixed synthetic P05-07 fixture on the current licensed Hangul 2020
  `11.0.0.9136` x86 installation only.
- Decision: `P05-07-H2020-COLPR-ID-ABSENCE-V1` authorizes a fixed-fixture
  `native_automation_bounded_normalization` receipt. It is not the general P12 normalizer.
- Reasoning/review risk: MAX / HIGH-STRICT.

## Actual attempt sequence

Attempt22 reached the user-visible open permission phase but timed out after 600 seconds without
permission. Its failed trace and progress journal remain unchanged. The owned Hwp process was
cleaned and no output or PDF was created.

Attempt23 used the same input bytes. The user granted the three displayed access requests. The
run then passed COM creation, open, input readback, HWPX save, close, saved-output reopen,
output readback, PDF export, both closes and quit. All 21 progress events completed, the watchdog
did not time out, the input digest remained unchanged and zero Hwp processes remained.

| Attempt23 artifact | SHA-256 |
|---|---|
| input HWPX | `37ec3be5f969c5d33fd7ac5e400d69ad24f6b8157220e702d0cbcf9452faa438` |
| saved HWPX | `8a59a4a01f1ce4a4a378223830c21ebea6fd8d31b83cc5dd29526acf59b5d8e6` |
| execution trace | `56c20a15bbff3044fc7a96d7698c789340061a6dc4c3814548c5a311247532aa` |
| progress journal | `0a1bc7da77055450313dee73084d399958253b5b242377801d71ddcc110fa150` |
| exported PDF | `986371a8c67fbb8e03f20beffd735148e17b42501ff36eeae51a833797b273ee` |
| PDF verification | `d76829e7b610c10ed170e0c6e5dd2ae8f590b0c5e9878ca277150da745fed29d` |
| render expectation | `6e4251772d64d799216707d917789f15b2e82f119c8c52692439b866b576ce73` |
| rendered page 1 PNG | `1815c5eccb500605d683f432ffc0d9ce3e425fc32ac1f5bf9b9e1f05ac619eaf` |
| rendered page 2 PNG | `8cd04d18dfef74cc2a66d0a53fb0c7c6dc74f906385eed2c9d498c6783a50aeb` |
| identity receipt | `e752fd21557f06f6fbea6b93489444f97937abb935d2a3f2f862dc55a60a142a` |

The ignored evidence directory is
`fixtures/target-build/p05-07-current-2020-20260906-v4/`. It contains no user document.

## Layout and render result

Both source and saved packages are graph/header/spine-valid two-section documents. Both sections
read as the requested landscape page setup and admit their exact requested column definition at
the actual body width. The source and saved normalized text digests are identical.

The independent PDF verifier returned PASS for two pages. Each page is approximately
`309739 x 229658` milli-mm with rotation zero, within the 500 milli-mm tolerance of the requested
`310000 x 230000` landscape sheet. Each page contains only its expected synthetic marker. At
144 DPI both rendered pages are `1756 x 1302` pixels.

Visual inspection of the two stored PNGs confirmed a landscape canvas and the distinct blue and
brown separator marks. The fixture is intentionally sparse, so this observation does not prove
dense multi-column text flow or balancing.

## Identity decision and implementation

Hangul 2020 rewrote both nonempty `colPr/@id` values to empty strings. The strict fixture inspector
continues to fail this saved output, full `ColumnDefinition` equality still includes `control_id`,
and two empty values are never treated as a shared identity.

The new `rebind-identity` command issues a separate receipt only after all of the following pass:

1. bounded source/saved package admission and exact graph, header and spine closure;
2. exact source target IDs plus equal target page, column, text and section-order semantics;
3. a distinct typed structural/context fingerprint for each section;
4. a saved ID that is either exactly preserved or absent, never a different nonempty ID;
5. exact execution trace, PDF, PDF-verifier, expectation and both rendered-PNG digest bindings.

The attempt23 receipt assigns two distinct logical IDs and records two
`removed_backend_identifier` events. It sets `backend_identifiers_preserved=false`; it does not
claim the backend IDs survived. Raw document text and raw backend IDs are absent from the receipt.
Malformed, stale, reordered, duplicate, changed-context, foreign-ID or render-binding inputs fail
closed. The command cannot rewrite a package or publish a revision.

## Validation and remaining boundary

The fixture example now has 28/28 tests. New regressions cover preserved IDs with zero events,
two absent IDs with two unique logical bindings, semantic/reorder/foreign-ID rejection,
stale trace/PDF/expectation/PNG rejection, duplicate fingerprint rejection and malformed package
rejection. The complete `hwpx-package` all-target suite passes 210/210, and all-target/all-feature
Clippy passes with warnings denied.

This closes only the corrected fixture's current-build layout, save/reopen, PDF and identity
subgate. It does not close dense text flow/balancing, P05-08/P05-09, the full P05 Gate, later
Hangul versions, independent execution attestation, publication, production or the product goal.
