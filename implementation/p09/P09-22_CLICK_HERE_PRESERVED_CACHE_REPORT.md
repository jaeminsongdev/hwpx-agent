# P09-22 CLICK_HERE preserving cache report

Updated: 2026-10-02. Scope: the licensed current-PC Hangul 2020
`11.0.0.9136` x86 `ko-KR`; not other versions/PCs or general product readiness.

## Outcome

Current source boundary: P09-28/v3 adds separate native-form exports without
changing this CLICK_HERE production module or either native receipt. The old
full-lib source pin remains the archived v2 lib; it cannot qualify the new live
lib. Historical target mutation tests explicitly use preserved source inputs,
while v3 checks the current exact additive source chain independently. This is
not a new native execution or comparator promotion.

Current successor update: the resumed P09-26 batch also executes C02. Its scoped
cache/style save/reopen and PDF stability qualify in the new C02 receipt; see
`P09-26_NATIVE_BATCH_REPORT.md`. The original preparation/hold history below is
preserved. The user now requires whole ready-case batches for future access work.

An actual production preserving adapter updates a single existing plain-text
CLICK_HERE cache through the typed field engine. Eight Rust tests pass, including
three exact native-captured packages. Two complete disposable HWPX cases are
generated deterministically. C01 completes actual open/save/PDF/fresh-session
reopen/save/PDF and independent cached-field/style readback. The full selected
section is identical before save, after save and after reopen. Their PDFs have
zero pixel drift. This is `bounded_cached_semantic_non_green`, not a P09 Gate.

The independently captured same-value PutFieldText outcome has the same value
but different character styling: the preserving direct path retains red italic
style reference 7; PutFieldText produces black non-italic style reference 0.
Unmasked 96-DPI PDF comparison finds 920 changed pixels and RGB delta sum 215567
within `[113,132,273,145]`. Keep `observed_mismatch_non_gate`; no differential
PASS, tolerated mask, fabricated visual equivalence or style-policy change.

C02 (replace an already filled cache, including non-BMP text) passes static,
complete-package and deterministic checks only. Its native target run has NOT_RUN
status. The user asked to avoid access-allow prompts while away, so no new Hangul
or COM session was started after that request. Hwp process count is currently 0.

## Implementation and boundaries

- `crates/hwpx-package/src/click_here_hwpx.rs`: reader/builder/lowerer, sealed
  source/state/flow/map/domain plan binding, bounded single cache update, exact
  selected pair/opaque parameters/run/style and non-selected byte preservation.
- `crates/hwpx-package/tests/click_here_hwpx.rs`: eight Rust tests for literal
  Unicode/XML, empty cross-run instructions, multiple/self-closing text spans,
  native captures, unknown/rich/invalid shapes, stale bindings and redaction.
- `crates/hwpx-package/examples/p09_22_click_here_update_target_fixture.rs`:
  production lowerer, bounded original seed identities, complete package graph,
  expanded non-section part identity and repeated full-package equality.
- `implementation/p09/tools/run-hancom-2020-click-here-discovery.ps1`: separate
  fixed dummy native discovery via documented CreateField/GetFieldList/
  PutFieldText/GetFieldText; no synthesized field Command, arbitrary HAction,
  user documents, automated UI clicks, registry edits or route activation.
- `tools/p09/qualify_click_here_update_target.py`: independent read-only oracle,
  declared-edit reconstruction, actual trace/artifact/API/helper/source binding,
  native pair/cache/character definitions and Poppler PDF comparisons.
- `tools/p09/tests/test_click_here_update_target_qualification.py`: 14 tests,
  including retained semantic failure, identity/claim coercion, rehashed edits,
  source/authority drift, privacy and independently fresh process rejection.

Native IDs `1210042100` and field ID `627272811` are observed HWPX identities;
domain begin/end reservations 1/2 are not falsely relabeled native IDs. This
profile supports existing text-cache update only, not field creation/locking,
general fields/rich text, reference recomputation, opaque Command execution,
qualified product routing or automation fallback.

## Evidence identities

| Item | SHA-256 |
|---|---|
| Native discovery trace | `257f98e1629e547e515a5f4eaf136064b80f5a5960c9a9ef1fc0d475b905a900` |
| Captured empty seed | `60a646f488941bad203d1c1d8bab43a36f2ae5c4712396eeeb3c1acb81d50747` |
| Captured filled seed | `ab6d2d2d8f9d4375c30b16b80e963a71c31c3b3ed6c7466f5bc3da872b00ebaf` |
| Both fixture manifests (01 and 02) | `d61d28d10aff3e9b7ee4e73a397ba0e96e97630737ff9718862b6ddb12387876` |
| C01 generated input | `0eaf3e6a8959bed7d6e64c507c3259486a735a1aa3f56bf73792d1cd72946f7c` |
| C01 lifecycle trace | `9d34161d5181cf5d374843a09aee985db7f89b884bc4280275e5e14604b18f3f` |
| C01 saved HWPX | `daa1f0eb985bb899952a72a1dec7dc4509420647164e8a1a060f3fcac0df2ae1` |
| C01 reopened HWPX | `bda749ea1208bda38c06cbf4dfcdb144f4fd102fdb7d3e1995506adce46b4c70` |
| C01 input/saved/reopened section | `423ff6b0bd24d760a908e2909465417458e19062e13bd4c46cb31ad1bca504d5` |
| Independent public C01 qualification | `f17c6386af5a3b1dfa35c7cff0507cd4ac8ef61a05c560824f640f5c85890e9b` |
| P09-23 source successor | `70806cbec581e50a5a4a419ce73e8a1ab32c09c930f7aae915c7b0d47bac38f1` |

Public record:
`implementation/p09/evidence/p09-22-click-here-update-target-c01-20261002-attempt01.v1.json`.
Private captures stay under the named P09-22 discovery and C01 target attempt
directories; raw text, absolute private paths and original user materials are
not copied into the public receipt. Permission acceptance is `user_attested`
only and never a substitute for target evidence.

Both actual C01 session `RegisterModule` returns are false, preserved verbatim.
The existing security DLL preflight and exact licensed executable identity passed.
Two independent process IDs were observed; finalizer left zero Hwp processes.
Application save/reopen changed `Contents/content.hpf`, `Contents/header.xml`,
`Preview/PrvImage.png` and `Preview/PrvText.txt`; these are reported, not hidden
as complete package byte parity. Referenced character definitions remained exact.

## Verification

- Focused production adapter Rust tests: 8/8 PASS.
- New independent target qualification tests: 14/14 PASS; no synthetic receipt
  published as actual evidence and no corpus absence converted to a skip.
- P09 Python suite: 161/161 PASS.
- `cargo test --workspace --all-targets --all-features --locked --offline`:
  1759 PASS across 267 test targets/suites, 3 existing explicitly ignored
  native/external tests. The ignored cases are not newly qualified by this command.
- Workspace Clippy, all targets/features, locked/offline, `-D warnings`: PASS.
- `cargo fmt --all -- --check` and `git diff --check`: PASS.
- Exclusive C01 receipt publication followed by `--verify`: identical SHA PASS.
- P09-23 source receipt `--verify`: identical SHA PASS, all 25 current validators
  audited with preserved legacy failures and the exact source projection chain.
- Current authoritative P09 aggregate unchanged: 46 owned, 7 P11 deferred,
  35 unit, 11 static integration, zero oracle/green rows. These new bounded
  target observations do not silently rewrite its historical evidence levels.

## Remaining work

1. While the user is away, only offline/pure implementation, tests and analysis;
   no new Hangul/COM sessions, permission prompts or UI actions.
2. When explicitly resumed, run C02 from the pinned 02 manifest into a new
   attempt directory, then independently qualify its exact output.
3. Resolve preservation versus native PutFieldText style behavior with an
   explicit field formatting contract and matched comparator evidence. Do not
   silently change this frozen preserving profile to discard source styles.
4. Complete missing field insertion/locking/reference families, qualified
   direct/fallback routes, render/differential and combined document campaign.
5. Preserve older object-caption failures and rectangle/equation visual gaps;
   close authoritative P09 Gate before starting any new P10 implementation.
