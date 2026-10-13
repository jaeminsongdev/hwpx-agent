# P09-50 private native form control worker — implementation progress, not native qualification

Updated: 2026-10-03. State: `PRIVATE IMPLEMENTATION + NINE PURE/METADATA TESTS PASS /
ACTUAL NATIVE BINDING, SETTERS, SAVED/REOPENED PACKAGES AND RENDER NOT_RUN`.

## Evidence that changes the next implementation step

All 15 original P09-35 package identities contain 17 form controls (two cases have
two sections). Every form lacks `id` and `instid`. The domain reservations90001/90002
are NOT native object IDs. Original P09-27 evidence already records that distinction.
Do not bind by reservation, form collection index, CharShapeID or invented IDs.

The separately extended read-only installed-typelib reader observes IDHwpCtrlCode
HeadCtrl/Next walking, Properties GET/PUT, and GetAnchorPos DISPID15000 returning
DISPATCH with one I4 argument whose actual parameter flags are0 (not fabricated FIN).
Actual IDHwpParameterSet declares Clone, Item, ItemExist, SetItem and IsEquivalent.
HShapeObject declares ShapeFormCommonAttr; HFormCommonAttr declares literal lowercase
name BSTR, TabOrder I4 and Color UI4. IHwpObject.RGBColor DISPID30007 returns I4 from
three UI1/FIN arguments. The new test actually re-reads the installed TLB and checks
11 exact signatures, not mocks of the installed metadata.

Official local HwpAutomation_2504.pdf pages64/68/69 were fully text-read and visually
reviewed; they specify existing-item checks, type codes +edt/+rbt, corresponding
ShapeObject properties and three anchor scopes. Page69's printed LispParaPos spelling
is preserved as source wording, not a new runtime type claim. ParameterSetTable_2504.pdf
pages85/129 were fully read and visually reviewed; ListParaPos defines List/Para/Pos,
and ShapeObject lists nested ShapeFormCommonAttr. Manual2504 remains distinct from
actual installed2020 runtime acceptance. Official developer forum examples also use
HeadCtrl/Next and GetAnchorPos(0/2), not current caret GetPos as an object identity:
https://forum.developer.hancom.com/t/2010-2014-2018-2020-2024/1728/8

## Actual new implementation

- `tools/p09/native_form_control_plan.py` compiles every original pinned complete
  fixture into exact names, globally unique tabs and full24-bit RGB intents. Keeps
  source package/section hashes and physical paragraph/run/inline coordinates.
  Rejects source substitution, protected/unsupported forms, nested body profiles,
  duplicate target keys/names/tabs, XML declarations/entities and bounded ZIP/XML
  violations. No fixture or private source is rewritten; no public action added.
- `implementation/p09/tools/native-form-control-binding.ps1` is a function-only
  library. Dot-sourcing does NOT activate COM or open/save documents. Intended runtime
  walks HeadCtrl with finite bounds and cycle guards, observes three anchor scopes,
  and matches the COMPLETE target set before any write. Root body paragraph ordinal
  is an explicitly UNQUALIFIED candidate; Pos is observed, never guessed from XML.
  Every root/local/top scope must agree; missing, extra or ambiguous targets reject.
  Generic/unknown form type codes fail closed; +edt/+rbt runtime identity still needs
  observation. THIS IS NOT PROOF that XML paragraph ordinals equal native Para values.
- Intended application clones separate complete ShapeObject/CommonAttr objects,
  checks COM identity is not aliased, edits ONLY name/TabOrder/Color, and verifies all
  exact managed values after all writes. Only declared peer managed changes may
  occur between writes; complete unmanaged parameter sets are checked against their
  original baselines. Final name/tab/color expectations are NOT weakened. Rollback
  includes all target peers, checks complete runtime parameters and separately records
  rollback failure. This code has NOT executed against native COM objects yet.
- `implementation/p09/tools/run-hancom-2020-native-form-control-binding.ps1` is an
  exclusive byte-copy successor of the original owned-exit-wait harness, modified
  only here. Original SHA7463b70fce52407f5173da8ccff75344ce740ab88f664620796d591edd3ec1a3
  remains exact. Plan/library hashes, same fixture directory, exact case name, regular
  file/ancestor checks and pure plan validation precede COM activation. First open
  applies the private worker; after first save, fresh reopen and second save only
  verify, never repair. Private trace retains type-count/anchor mismatch observations
  and rollback state without names/text/payload. Owned process cleanup, existing user
  process rejection, exact executable/security-module/read-only registry checks and
  user-owned permission clicks remain. This successor has NOT been launched.

## Actual checks and retained failures

`python -E -B -X utf8 -m unittest -v tools.p09.tests.test_native_form_control_plan`
latest session41984 TERMINATED exit0:9 tests,0 failures,0 errors,0 skips,18.658s.
This invokes real original15 fixtures/17 controls, installed metadata, and BOTH pwsh
and the actual x86 Windows PowerShell parser/pure matching functions. Reversed
observations still match by candidate anchor/type, not index; Unicode/metachar names
are independently UTF8-SHA compared across the JSON boundary. Negative cases reject
wrong scopes/positions/list/type, missing/extra/duplicate targets, coercions, invented
IDs, protection, nested profiles and global conflicts. No actual COM setter, rollback,
native process, package save/reopen, render or semantic acceptance is tested here.

Initial session86442 FAILED2/8: fixture protection test accidentally changed the
preceding rectangle, and JSON delivery failed before parsing the ampersand-name case.
The new test alone was corrected to edit the actual form; explicit Console.InputEncoding
UTF8 fixed delivery without changing source names or dropping cases. Intermediate
sessions60266/82638/4937/81483 and final41984 terminal PASS remain execution history.
Old tests, locks, expectations and failed native runs are untouched.

After final implementation/tests, actual hash checks confirm original native harness,
all P48's23 sources/1551 current inputs/original native evidence/archives and P49's9
sources remain exact. This preservation check does not reexecute P48's whole workflow.
`git diff --check` PASS. No whole ordinary Python/legacy/Rust rerun or new Gate claim.
Five derived review PNGs786458 bytes were removed from the exact owned temporary
directory after inventory/reparse checks; official original PDFs were unchanged.

Implementation source checkpoint (mutable until complete batch admission; NOT a
published full-source qualification receipt):

| Source | SHA256 |
|---|---|
| tools/p09/inspect_native_form_binding_typelib.ps1 | 8fe98a096a2aa943d0e977b22858c45a5b85e07da0524a8ac518185e994c9534 |
| tools/p09/native_form_control_plan.py | bab544538de45a95628b3caea43a9c98c641e50752147a9674fda29fd96dca78 |
| tools/p09/tests/test_native_form_control_plan.py | c1b64c85c562ac06ad49efb0799cfafa7a956a5174b6ed3dc73c36f64d6da98d |
| implementation/p09/tools/native-form-control-binding.ps1 | c0534e9bfdcb0d4e93cd8535585d462df59813c7d9788f7b55afcf4d23c48183 |
| implementation/p09/tools/run-hancom-2020-native-form-control-binding.ps1 | 2777a290bc6b8442d125c6920a9ce68b851ef0500e8f86121fc9459e7204035f |

## Remaining required work — no narrowed success criterion

Update2026-10-03: item2's protected admission/dispatcher dependency is now CLOSED by
P09-52 publication45588+independent WHOLE fresh57013 terminal PASS/14209/f3394852,
ALL15 actual no-COM prefixes/three hash rejections/15 guard tests. All frozen P50/
P51 source identities remain exact. Item3 native execution is NOT_RUN: latest user
forbids access-permission prompts; continue only permission-free work. See
`P09-52_NATIVE_FORM_BINDING_BATCH_REPORT.md`.

Update2026-10-03: item1 below is now CLOSED by P09-51's actual SDK15/17 candidate
generation and immutable progress publication29675+independent whole fresh73435
PASS/8860/925ce0c7/9 source pins/31 persisted files261216 bytes. See
`P09-51_NATIVE_FORM_CANDIDATES_REPORT.md`. Do not regenerate/overwrite its r01 inputs
or repeat completed preparation instead of the remaining protected admission,
dispatcher and native batch. Original statements below remain historical requirements.

1. Prepare ALL15 complete candidates through the actual P48 coupled foreground/style
   SDK API, preserving exact original intents, full non-form/document state, map and
   explicit fixture policies. Connect exact worker plans to those output identities.
   Neither raw original input-only execution nor hand-written XML substitutes for
   the newly implemented production color preparation.
2. Qualify the complete protected source/admission path and dispatcher before native
   activation. Preserve P48/P49 frozen chains and all previous failures. No original
   capsule/current lock is updated to conceal an additive-export failure.
3. Run ONE genuinely changed COMPLETE15-case permission batch, user alone clicks.
   Observe actual type/anchor/property bag bindings and record mismatches. Native
   scalar checks are not package/opaque/field/reference/render/differential proof.
   Independently verify full saved/reopened packages and renders, then fix real failures.
4. Input/default/date/protection/validation, field-numbering/style discrepancies,
   signed form route, manifest/publication/CAS/idempotency/CLI/full import and final
   P09 Gate remain required. No P10 before P09 Gate. Goal ACTIVE; green rows0.
