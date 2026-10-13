# P09-26 resumed native validation batch report

Updated: 2026-10-02. Target: licensed current-PC Hangul 2020
`11.0.0.9136`, x86, `ko-KR`, not general release qualification.

## Outcome

The user resumed access-allow-dependent validation and then required future
ready cases to be collected/preflighted/executed as a whole batch rather than
isolated one/two-case dispatches. This supersedes the temporary offline hold.
The prepared CLICK_HERE C02, footnote, endnote and mixed footnote/endnote cases
all completed real open/save/PDF and independently fresh reopen/save/PDF.
Each case used two distinct identified Hangul processes: eight native sessions
total, with zero remaining Hwp processes in each finalizer. No agent permission
click/typing, registry/trust/system change, network or user-document scan occurred.
No new user click attestation was received; public records say `not_attested`.

Independent validation establishes CLICK_HERE C02 cache/style preservation and
zero saved/reopened PDF drift. The note batch preserves bounded typed body text,
character/paragraph/style references, instance identities and anchor order, and
all four saved/reopened note PDF pages have zero changed pixels at 96 DPI.
However, native note raw body/style bindings changed and body numbering remains
unqualified. The note receipt intentionally remains `failed_semantic_non_green`;
verification of that failure record is not conversion of the failed case to PASS.
The P09 authoritative matrix and Gate remain non-green/open.

## Batch and identities

All original fixture packages, manifests, predecessor policies/source locks and
receipts are unchanged. The existing P09-17 native lifecycle harness raw SHA is
`30341f7a7ff5106e4c3ac74331abdd9b612ec4d88eb060387b506809399338a9`.
Every attempt was create-new under the private evidence boundary. The remaining
two note cases were preflighted together and run in one sequential queue; the
harness's preexisting-process refusal prevents simultaneous ambiguous sessions.

| Case | Lifecycle trace SHA-256 | Saved/reopened PDF pages | Scope |
|---|---|---:|---|
| P09-22-C02 | `37439edebb8fba24e36fa4932fe514eb735e1baea30d29626944624e77307780` | 1/1 | Existing filled cache replacement, including Korean/non-BMP text |
| P09-24-C01 | `1170c77a093728b784cfa47fb6d1cc8dc483017cbaed86189e06bce5cfb576d9` | 1/1 | Footnote before main text |
| P09-24-C02 | `b2b95139955b0454eff102be10eae8db4a15f062285078db87b7851a18b3977c` | 1/1 | Endnote after main text |
| P09-24-C03 | `ebb916efc52d52fb0c4ef85e5280cccc40c2630ca8f6caed4654dfb0e9a9629e` | 2/2 | Footnote and endnote with distinct anchors |

CLICK_HERE C02 public receipt:
`implementation/p09/evidence/p09-22-click-here-update-target-c02-20261002-attempt01.v1.json`,
SHA `27db328b1a4c14d73c5a6b4cef75c8ccaa2306e5d87853c7b4656f7a29fcffb9`.
State `bounded_cached_semantic_non_green`; full render, matched automation
comparator, qualified routing and P09 completion remain false/NOT_RUN.
The earlier C01's 920-pixel preserving-versus-PutFieldText style mismatch remains.

Note batch public receipt:
`implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json`,
SHA `a03e6461d94010d7b1ccfbf9eecdb8e1d06389f3a690363e7b414d4cda9f2347`.
State `failed_semantic_non_green`, with each original trace/artifact/package,
frozen preparation/source identity, typed readback, real native additions,
projection hash differences and multi-page PDF comparison bound independently.

## Real note changes and retained failures

- Native save adds `suffixChar="41"` (`)`) to each marker and derived
  `linesegarray` data. The actual frozen P09-24 preparation oracle rejects that
  native marker with `note_marker_shape_invalid`; that failure is retained.
- The new separate observation profile validates and hashes those closed native
  additions, then performs an explicitly declared memory-only semantic comparison.
  It does not change captured bytes or weaken the frozen preparation oracle.
- Hangul also removes the redundant `xmlns:hp` declaration on the body subList.
  The body-graph and raw start-tag style digests therefore differ from the input.
  The new record retains `saved_raw_body_or_style_binding_changed` and
  `reopened_raw_body_or_style_binding_changed` for every note case. It never
  equates canonical/typed comparison with raw byte parity.
- Complete typed note text, body paragraph/run/style attributes, actual main-text
  markers, instance IDs and anchors match the generated input. Referenced
  charPr 0/3, paraPr 10 and style 14/15 definitions are unchanged. Main text is
  unchanged. Saved and reopened complete section bytes are identical to each
  other, but not to the generated section. Changed non-section parts are listed.
- Visual inspection of all four note pages confirms bottom-of-page footnote
  placement, endnote content and mixed two-page pagination, with Korean/XML
  literals and the rocket glyph present. It also shows no number prefix in the
  note body. Actual bodies contain zero `hp:autoNum` fields. Main reference
  markers are visible, but native body numbering/full render acceptance remains
  unqualified and requires a production contract/implementation fix.
- The old CLICK_HERE single-page PDF comparator correctly rejects the mixed
  two-page profile. It is not relaxed. The separate note comparator validates
  exactly 1/1/2 pages, 794x1122 pixels, every page nonempty, zero changed pixels,
  and no image masks/tolerances.

## Changes and verification

- Added `tools/p09/qualify_note_native_batch.py`: independent bounded read-only
  native note artifact/source/projection/PDF qualifier; never opens Hangul.
- Added `tools/p09/tests/test_note_native_batch.py`: 11/11 PASS, including exact
  native corpus, genuine frozen-oracle failure, suffix/layout/body/style/source
  damage, mixed instance drift, independently fresh session/type enforcement,
  two-page comparison, retained failure/privacy/non-Gate assertions.
- Added the batch policy and this report; updated PLANS and predecessor reports
  with explicit successor pointers, not rewritten source authorities.
- Full P09 Python suite: 193/193 PASS, no skips. No Rust production source,
  library export or frozen module was changed this turn; its preceding locked/
  offline 1,765-test Rust checkpoint remains the preceding result, not a new run.
- New note/C02 receipt `--verify`: byte-identical. P09-23 source v2, P09-24 static
  preparation and P09-25 form regression receipts also reproduce unchanged SHA.
- Formatting/diff checks pass; final read-only process check finds zero Hwp.
  No original edit, evidence deletion/move, staging, commit or push.

## Next work and future access requests

Continue the explicit native-form identity/anchor/geometry implementation and
resolve note body-numbering/source-to-native binding plus field formatting and
remaining reference-family contracts. Prepare complete cases and independent
expected outputs before any new native dispatch. Collect all dependency-ready
native tests into one preflighted queue; announce the whole scope and then run
it to completion, with user-only permission dialogs appearing sequentially.
Do not retry these unchanged cases just to raise additional prompts. No P10 new
implementation before the authoritative P09 Gate closes.
