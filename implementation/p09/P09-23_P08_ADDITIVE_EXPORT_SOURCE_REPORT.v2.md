# P09-23 P08 additive-export source bridge v2 report

Updated: 2026-10-02. State: `source_qualified_non_gate`.

Current successor: P09-28/v3 adds only observed-native form public exports and
recovers this exact v2 lib from its preserved archive. This v2 current verifier
actually fails on the new lib; its original capsule is not refreshed or claimed
current. The result below remains the historical v2 checkpoint. See
`P09-28_NATIVE_FORM_PUBLIC_EXPORT_REPORT.md` for the current source chain.

## Result

The new CLICK_HERE preserving cache module and exports have an explicit exact
source successor. Current lib SHA `1eae8f6896cb5bb70762ac41e00d0fa017af794cb6dfaec8463879eb1f366d09`
removes exactly one new module declaration and one public export block in memory
to reproduce the archived P09-21 lib bytes. Its predecessor projection reproduces
the P08 lib. No legacy expected hash, source receipt or verdict was refreshed.

P09-21's original live checker correctly rejects the newer current lib with
`current_shared_lib_identity_changed`. This actual failure is retained in v2.
The exact old lib and original bridge-test bytes were archived before their
successors. The new live bridge test explicitly verifies the predecessor failure
and tests its pure projection against the real archived baseline, not a monkey-
patched current source or fabricated source digest.

All 25 current component validators were executed. Exactly nine historical full-
lib-lock failures are qualified through the byte-exact additive chain and their
independently unchanged other implementation locks; the other 16 run successfully.
All actual validator verdicts and the original aggregate failure remain preserved.
The historical P08 matrix/privacy/source rules run without target promotion.

## Evidence

- Public v2 receipt:
  `implementation/p09/evidence/p09-23-p08-additive-export-source-qualification.current-2020.v2.json`
  SHA `70806cbec581e50a5a4a419ce73e8a1ab32c09c930f7aae915c7b0d47bac38f1`.
- Preserved P09-21 predecessor receipt SHA
  `e62e69a558683d41eb6bb29663f86781ec7b324f07520f8b29126975ca7d21f6`.
- Adapter raw SHA `5252ed2bafc7f6d311fe2368e4287ea5afd8f54dd85a0d2a15e5a99fc63fb213`;
  its Rust test SHA `e16c15ecf2ca6eaf9fc615f92ded493d8280d55ff8150af4f4ae3d70947e2c35`.
- Exact predecessor archive:
  `implementation/p09/source-archive/p09-21-additive-exports-v1/`.
- Source-bound successor policy and migration:
  `P09-23_P08_ADDITIVE_EXPORT_SOURCE_POLICY.v2.md` and
  `protocol/migrations/p09-p08-additive-export-source-bridge-v1-to-v2.md`.

Exclusive publication and independent `--verify` reproduce the same receipt SHA.
The live bridge tests are 10/10 PASS, the full P09 Python suite is 161/161 PASS.

## Boundaries

This qualifies exact current source lineage only, not field target behavior,
general HWPX semantics, product routes, fallback, render/differential, P09 Gate,
other PCs/versions or product completion. The separately qualified actual C01
target observation is in P09-22; it cannot rewrite this source receipt's non-
target claims. P08 legacy aggregate is still not PASS. Unknown source/export
changes require another preserved successor, not mutation of this v2 identity.
