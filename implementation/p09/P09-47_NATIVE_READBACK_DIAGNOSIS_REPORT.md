# P09-47 native readback diagnosis — actual defects, no repair/Gate claim

Scope update2026-10-03: the native observations and receipt stay immutable historical
evidence. P09-48's package export changes an immediate source pin; actually running
this current --verify now FAILS diagnosis_fresh_whole_result_changed. Do not relabel
that source drift current PASS. New coupled color preparation is local-only pending
full source/native evidence, and does not erase any old native semantic failures.

Current decision: `15/15 native lifecycle observed / actual public diagnosis
publication + fresh verification PASS / semantic repair NOT QUALIFIED / GREEN 0`.

## Evidence closed on 2026-10-03

- Original r05 native dispatcher/session13013 ended exit1/KeyError AFTER all15
  cases completed. All15 actual traces pass strict lifecycle binding:75 immutable
  native files,30 sequential independent owned sessions, unique process IDs,
  zero remaining Hwp.exe. The dispatcher incorrectly looks for a top-level
  `prior_partial_batch_preserved`; frozen admission contains it only under
  `prior_r04_admission`. No original dispatch/bound success receipt is fabricated.
- Separate r06 recovery publication/session40074 and fresh complete verification/
  session14830 both exited0. Full unchanged r05 admission was reexecuted byte-exact,
  including its original r04/r03/r02 proofs; all30 actual public SDK and independent
  projection stages were attempted. All75 new and35 old files remain preserved.
  Receipt: `evidence/p09-36-native-form-complete-recovery.r06.json`,106751 bytes,
  SHA47df877e392f1ffd0a79f16eb2629db8eedc1f85390f4b75e47a5d77029586cb.
- P09-46 full source publication/session14102 and fresh COMPLETE --verify/session31017
  both exited0. Receipt: `evidence/p09-46-stored-product-request.source-qualified.v1.json`,
  233471 bytes/SHA2d4386dda7efe9a9d9e6ab5efaa301816756818a3cb49c71129408f7fdb398ac,
  31 source pins,8 actual product tests/4 original Python guards/8 full-source guards,
  unchanged original complete P45/P44/P43/P42 reproduction. Authentic original view
  1521 files/50450812 bytes; source qualification is not product/native acceptance.

## Actual cause separation

The new Rust diagnostic calls real public package and section readers on all30
actual outputs, verifies the original15 input state/map/policy hashes, and passes
complete actual bindings and caller policies into the real public domain validator.
Only typed field paths and fingerprint differences are emitted; no raw document
names/values/XML or absolute private paths appear.

| Cases | Actual saved and independently reopened observation |
|---|---|
| C01 | Package and both section readers PASS. Tab orders change from distinct0/1 to1/1. Actual domain validator rejects `form_control_invalid_tab_order`; original combined readback FAIL remains FAIL. Second control name also changes. |
| C02 | Both names and second tab order change; preserved opaque control fingerprints change. Whole target state and bindings remain FAIL. |
| C03/C04/C07 | `common.fore_color_rgb` changes; existing complete target/control failures remain FAIL. |
| C05/C06/C08 | Domain control fingerprints remain exact. Opaque document binding changes; whole document target remains FAIL. |
| C09-C14 | `common.name` changes regardless of which Unicode/metacharacter fixture was used; no stripped-name approximation accepted. |
| C15 | Domain controls remain exact but raw control subtree fingerprint and opaque document binding change. Original strict subtree/package failure remains FAIL. |

All15 cases' opaque document bindings change. C01/C02 reference inventory bindings
also change. The diagnostic does not discard these bindings as harmless volatility;
any normalization acceptance requires separate explicit complete evidence.

The generic old C01 error did NOT prove parser failure. The first new diagnostic
test incorrectly asserted package read FAIL; actual execution gave2 PASS/1 FAIL.
The new diagnostic assertion was corrected to observed package PASS plus actual
domain tab collision rejection. The old authority, old failure and all fixtures
were untouched. First Clippy found4 redundant closures, fixed without suppression.

## Reproducibility and verification

- New actual Rust tests3/3 PASS,0 ignored/filtered; Python boundary/protocol guards5/5 PASS.
- Publication/session73126 and independent fresh --verify both exited0:
  `evidence/p09-47-native-readback-diagnosis.v1.json`,64631 bytes,
  SHA f93d38bd4ef0adceb55af0ee2b1adadbdf29c2081d93b7c6b34ab6db975a7e28.
  Each run executes all3 real Rust tests, warnings-denied Clippy, then all15 real
  public SDK diagnoses, with all75 native files and12 selected immediate source
  hashes checked before/after. Whole canonical fresh result matches publication.
- Selected source pins are immediate-consumer evidence, NOT complete transitive
  source qualification. The separate r06 whole proof is not substituted with hashes.
- Workspace all-target/all-feature Clippy `-D warnings`, workspace formatting and
  `git diff --check` passed after the new diagnostic. Whole workspace locked/offline
  all-target/all-feature Rust regression/session62844 terminated exit0/PASS, with
  existing ignored tests retained. No precise aggregate count is inferred from
  truncated first tool output; the actual command exit/result is the evidence.
- Ordinary P09 Python discovery/session88674 terminated exit1:443 declared,
  389 executed/11 failures/29 errors/0 skipped. New6 recovery and5 diagnosis guards
  add11 executed passes relative to previous432/378/11/29/0. Original failures,
  setUpClass errors and unexecuted bodies remain; no ordinary aggregate PASS.
- After document synchronization, all31 P46,6 r06 and12 P47 source pins were
  independently checked exact. The mutable reports/ledger are outside these pins.

## Exact next implementation boundary

Fix native color/name/tab behavior against the full original intended state, not
expected-value rewrites. The actual existing-blue-style cases preserve blue while
foreColor-only or conflicting-style cases drift, which supports investigating the
native character-style dependency; it does not by itself qualify a general color fix.
Keep full fonts/effects/catalogs/metadata and arbitrary requested colors intact.
Implement and qualify a genuine product preparation before batching new native
permission-dependent runs. Native defaults/input/date/protection/validation,
render/direct-automation differential, signed route/manifest/publication/CAS/
idempotency/CLI/full import and P09 Gate remain open. P10 remains held.

No native session, user permission click, trust/security/registry change, original
edit/deletion/movement, install/network/stage/commit/push occurred in this diagnosis.
