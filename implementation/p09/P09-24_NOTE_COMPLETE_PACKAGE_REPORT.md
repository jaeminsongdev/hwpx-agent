# P09-24 complete note package preparation report

Updated: 2026-10-02. State: `complete_package_static_non_green`.

## Outcome

Current successor update: the user resumed the P09-26 native batch. All three
note cases complete actual two-session lifecycle and PDF stability; typed text,
style and anchor readback match, but raw body/style bindings change and note-body
numbering remains unqualified. The new receipt retains `failed_semantic_non_green`.
See `P09-26_NATIVE_BATCH_REPORT.md`. This report's original static preparation
and offline-hold history, and its immutable receipt/source authority, are preserved.

The unchanged P09-15 note engine and preserving HWPX adapter now have complete
disposable packages for footnote insertion, endnote insertion and their combined
use. Three independent generator runs produced identical seed, case and manifest
bytes. No Hangul/COM process or access-allow prompt was started; the user requested
offline-only work while away. Actual target, save/reopen, render, automation and
differential remain NOT_RUN, all authoritative rows remain non-green.

This fills the missing complete-package preparation step before the actual target
campaign; it does not replace that campaign with synthetic success. Existing note
style/convert/export and arbitrary rich-note bodies remain outside the direct
profile. P09 Gate and all P10-dependent implementation remain open/held.

## Changes

- `crates/hwpx-package/examples/p09_24_note_target_fixture.rs`: real typed domain
  request/plan/build and production reader/builder/lowerer, complete package graph,
  seed/header/settings/resource bindings and exclusive SecureWorkspace publication.
  A prospective build derives actual output bytes; the final sealed plan uses
  that actual section hash and must reproduce the same bytes. Each final insertion
  rejects stale source and body and rereads the complete ordered native inventory.
- New example tests: deterministic complete packages and all non-section parts,
  mixed insertion's real section/state chain and preservation of the first note,
  duplicate-anchor rejection without partial progress; 3/3 PASS.
- `tools/p09/inspect_note_complete_fixture.py`: independent bounded package and
  XML oracle, safe ZIP names/aliases/count/size, manifest/spine targets, exact native
  kind/instance/marker/anchor, decoded text, raw body and length-framed body style
  hashes, existing header style references, full reversal to the seed and all
  intermediate sections. It imports no COM or GUI runner and makes no network calls.
- `tools/p09/tests/test_note_complete_fixture.py`: 15/15 PASS covering normal
  packages, repeated generation, false claim/coercion, rehashed main/body damage,
  kind/ID/marker/unknown/rich/stray-content errors, missing style/graph targets,
  moved mixed-note anchors, non-section damage, ZIP aliases/traversal, broken
  operation/state chains, source drift, boundaries/hash/duplicate JSON keys.
- New independent policy and public static qualification receipt. No predecessor
  expected source hash, note module, shared lib export, contract, matrix, policy,
  source receipt or authority was rewritten. P09-23 v2 remains byte-identical.

## Case identities

The target fixture directories are direct children of `fixtures/target-build`:
`p09-24-note-target-20261002-01`, `-02` and `-03`; each has an `output` subdirectory.
Use the final `-03/output/fixture-manifest.json` for later target work. The original
generated seed and all predecessor fixture directories are preserved.

| Case | Scope | Package SHA-256 | Bytes |
|---|---|---|---:|
| Seed | Original main paragraph/default note styles, no notes | `494f62f4b5e996bd241c09b16e17a8323cb17fe0974fcdf36af230dad73763d5` | 7411 |
| P09-24-C01 | REF-021 footnote, before main text | `587cc310e952d5424b5803ef01beb8668481c0dbbe503bebad4dfd901a1102dd` | 7609 |
| P09-24-C02 | REF-022 endnote, after main text | `0121bb13948ce67393c8c3909e7a4c192ce83d00bc0b3899e119f62f982b7c88` | 7597 |
| P09-24-C03 | Footnote then endnote, distinct before/after anchors | `e876d566f85f03461b1a7cb9e56f53cd6a3d065989ed2e60356b6043bb0fede9` | 7646 |

All manifest bytes have SHA
`ef2e30388827c40e02b99017350f434b33840ce5564c2d46b2bae9c10dac9150`.
The exclusive public static qualification is
`implementation/p09/evidence/p09-24-note-complete-fixture-qualification.current-2020.v1.json`,
SHA `3aaa98e189fa155129bc348e31367f9a06f2b81b7bd7386c3cecc36076a85ce2`.
Independent `--verify` reproduces identical bytes and all 15 pinned sources match.

Bodies use existing header note style 14/15, paragraph style 10 and character
definitions 3/0, with two paragraphs and three runs, escaped XML-special text,
Korean and non-BMP plain text. Instance IDs are distinct 24001/24002. Marker
number 1 is input state only, not application recalculation proof. The unchanged
writer omits zero flag and absent optional marker WCHAR attributes; the independent
oracle requires precisely that emitted shape, not a looser guessed attribute set.

## Verification and preserved authority

- New Rust example tests: 3/3 PASS; existing note adapter/component tests unchanged.
- New independent Python note-package tests: 15/15 PASS.
- Full P09 Python suite: 176/176 PASS.
- Locked/offline Rust workspace, all targets/features: 1762 PASS across 268
  test targets/suites; 3 existing explicitly ignored native/external tests remain
  ignored, not qualified by this command.
- Locked/offline workspace Clippy, all targets/features, `-D warnings`: PASS.
- `cargo fmt --all -- --check` and `git diff --check`: PASS.
- Original P09-15 validator: genuine PASS, all four raw implementation and four
  source locks unchanged; target/render/differential still NOT_RUN.
- P09-23 current-source v2 and P09-22 C01 actual-target receipts both reproduce
  their previous exact SHA. The 920-pixel CLICK_HERE style mismatch remains.
- Authoritative P09 aggregate: unchanged 46 owned/7 P11 deferred, 35 unit,
  11 static integration, 0 oracle/green. No old evidence level was promoted.
- Final read-only process inventory: Hwp=0. No cleanup, registry/trust changes,
  user-document scans, external push or new target session occurred.

## Next work

Continue other dependency-ready pure/complete-package integration while the user
is away. Do not start any target/native session that could require access approval.
When the user explicitly resumes native work, first complete the held CLICK_HERE
C02 campaign, then bind all three note cases to independent disposable exact-target
save/fresh-reopen, body/marker/style/numbering/resource readback and visual results.
The plain-text body profile intentionally lacks body auto-number/rich controls;
preserve any resulting native failure or appearance gap and qualify an explicit
successor if actual evidence requires expansion. Do not silently rewrite this
receipt, field formatting policy or earlier source identities to obtain a PASS.
