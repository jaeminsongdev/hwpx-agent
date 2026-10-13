# P09-19 complete-object caption-number preparation report

Date: 2026-10-02. Scope: static complete-package preparation, not a target PASS.

## Generated campaign

Primary bundle:
`fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output`.
Independent retry bundle:
`fixtures/target-build/p09-19-object-caption-number-target-20261002-02/output`.
Both manifests SHA-256:
`42a9d18eb18dac2d34185297fb8cf0b18b10658e3e5b327839a14c770fb22a48`.

| Case | Native object | Seed identity | Preparation |
|---|---|---|---|
| P09-19-C01 | rectangle 8101 | P08 margin/caption package | existing caption; NONE -> PICTURE |
| P09-19-C02 | picture 8102 | P08 actual embedded-image insertion package | copy plain seed caption |
| P09-19-C03 | table 1188510574 | P06 complete table-create package | copy caption onto first table; second table preserved |
| P09-19-C04 | equation 1192022476 | captured P07-09 attempt14 output | copy plain seed caption; native script preserved |

Every input contains one object-bound DIGIT field with cached **19**. Saved/reopened
model expectation is **1**, explicitly target-unqualified. A preserved cached value
is rejected as recalculation evidence. No actual Hangul run occurred.

The generator built all cases before publishing. Both complete generation runs
produced identical manifests/packages. Every operation had a deterministic retry,
stale-source rejection and exact insert/preparation reversal to the original section.
Every unrelated expanded package part is unchanged. Complete graphs passed. The
output and the copied equation fixture remain Git-ignored/uncommitted.

## Discovered failures and correction

Earlier generator attempts failed before creating output because the rectangle was
NONE and then because its complete object had root-equal namespace redeclarations.
No failed input or existing fixture was rewritten. The NONE assignment is declared
fixture preparation. Product namespace admission was corrected in the separately
qualified P09-18 v2 source successor, preserving its v1 bytes/receipt. Conflicting
namespace shadowing remains rejected.

Independent Python oracle rejects wrong kind/lock/format/ID, field outside the
selected caption, cached-19-as-recalculation, changed manifests, weakened model
expectations, digest drift, duplicate JSON/ZIP and active XML. A simulated numeric-1
snapshot deliberately still reports `actual_hangul=false`, target-unqualified model
and lifecycle NOT_RUN; it is not recorded as target evidence.

## Verification

- P09-18 focused public Rust tests: **9/9 PASS**; sealed-plan tamper test preserved.
- P09-18 v2 source contract and regression tests: **PASS**, **8/8 PASS**.
- New complete-package oracle tests: **9/9 PASS**.
- Full P09 Python suite: **119/119 PASS**, no skipped test on this PC.
- Rust workspace all-target/all-feature locked offline tests: **PASS**, 264 result
  summaries, zero failed summaries; ignored external checks are not product evidence.
- Workspace Clippy with the same flags and `-D warnings`: **PASS**.
- Format check, `git diff --check`, existing P09 aggregate and frozen P17 v48: **PASS**.
- No new COM/UI run. P08 live shared-lib source hold remains; previous target/failed
  receipts are not refreshed. P09 matrix still 35 unit + 11 static integration,
  7 P11 deferred, zero green.

## Reproduce without starting Hangul

Pinned source/preparation receipt:
`implementation/p09/evidence/p09-19-object-caption-number-target-preparation.current-2020.v1.json`,
SHA-256 `aca01bc5aaac5e3b05896c2d9dee08a6134ed63d08f6878c218b029e227b277c`.
It binds 11 source files, all four original seed packages and both manifests. The
read-only verifier rechecks current P09-18 v2 authority and independently inspects
all eight prepared packages. Result: **PASS**, with lifecycle/target/green claims
still NOT_RUN/false/zero. Exclusive reuse of an existing bundle was rejected and
its manifest hash stayed unchanged. A deliberately incorrect receipt identity was
rejected before any package inspection. No source or prior receipt was overwritten.

```powershell
# Choose another NEW sibling folder; never reuse or overwrite a prior bundle.
cargo run -p hwpx-package --example p09_19_object_caption_number_target_fixture --all-features --locked --offline -- D:\개발\hwpx-agent\fixtures\target-build\p09-19-object-caption-number-target-NEW
py -3 tools/p09/validate_field_object_caption_hwpx_contract.py
py -3 tools/p09/verify_object_caption_number_target_preparation.py
py -3 -m unittest tools.p09.tests.test_field_object_caption_target_oracle -q
py -3 tools/p09/inspect_field_object_caption_target.py fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/p09-19-c01-rectangle-caption-number.hwpx --manifest fixtures/target-build/p09-19-object-caption-number-target-20261002-01/output/fixture-manifest.json --expected-manifest-sha256 42a9d18eb18dac2d34185297fb8cf0b18b10658e3e5b327839a14c770fb22a48 --case P09-19-C01 --stage input
```

## Pause boundary

The preserved target harness `implementation/p09/tools/run-hancom-2020-field-auto-number-target.ps1`
would create a new COM session, register the prescribed path-check module, then Open
one named disposable input and save/reopen in a new private attempt. It has **not**
been invoked for this campaign. Stop before those operations as the user requested.
Do not call the legacy P09-17 qualifier on this different four-package manifest.
After explicit resume, resolve current-source dependency qualification and collect
fresh object-bound semantic, process/lifecycle, render and differential evidence
with a new dedicated successor qualification. Do not relabel the preserved 19 or
model hypothesis as PASS. P09/P09~P20 are not complete; P10 remains held.
