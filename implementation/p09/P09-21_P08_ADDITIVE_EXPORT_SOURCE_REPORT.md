# P09-21 preserved P08 additive-export source qualification

Date: 2026-10-02. State: `source_qualified_non_gate`. No target or row promotion.

## Result

New exclusive receipt:
`evidence/p09-21-p08-additive-export-source-qualification.current-2020.v1.json`.
SHA-256 `e62e69a558683d41eb6bb29663f86781ec7b324f07520f8b29126975ca7d21f6`.
Publication and read-only byte-for-byte reproduction passed.

The current shared lib matches its pinned raw digest. Removing exactly two named
module declarations and two named public-export blocks, uniquely and in memory
only, reproduces the complete predecessor raw digest. Both P09 module sources,
all 25 required validator sources and the bridge's code/test/policy/migration
are independently bound. Other byte changes or caller-selected hashes are not
admitted. No old validator, contract, source receipt or target receipt was edited.

All 23 old upstream validators and both current P09 numeric/caption validators ran:
16 genuinely passed. Nine still failed with only `implementation_digest`, exit 1,
valid old source qualification and the complete implementation count. Each has
the same predecessor lib digest; every other implementation/test file matches
its old raw lock. Their actual failed verdicts remain failed in the new receipt.
The old full P08 aggregate is not reported as PASS.

## Initial failure and official source restoration

The initial bridge assumed only the asset validator locked the shared lib and
its integration test failed on the image validator. Exhaustive diagnostics found
eight additional full-lib locks and missing official-reference roots in drawing
canvas/active content. These were real failures, not ignored checks.

The absent reference checkout was restored at
`D:\개발데이터\Temp\hwpx-owpml-model-probe-20260912` from the existing clean
repository-local official source cache. Its HEAD is the original pinned commit
`1453388472c703a4b299a0834f425cdac16644b9`; the two unchanged validators verify
their required raw official-source hashes. Drawing canvas genuinely passes;
active content now retains only its lib-lock failure. Source cache and data roots
were not moved, deleted, linked or edited. The initial obsolete official repo URL
fetch failed; the newly created checkout's origin was corrected to the official
`hancom-io/hwpx-owpml-model` name, and source restoration itself used local Git
objects, not a new reference version. No registry/trust/environment changes occurred.

## Verification

- Bridge tests: **9/9 PASS**, including unique-span/unknown-byte rejection,
  predecessor/module/validator tamper, additional-error/missing-proof rejection,
  genuine-PASS requirement, live integration and false-Gate/privacy assertions.
- Unchanged Rust asset pipeline regression: **10/10 PASS**, current linked workspace,
  `cargo test -p hwpx-package --test asset_pipeline --locked --offline`.
- Complete P09 Python suite: **146/146 PASS**, no skips.
- P09 conformance validator: **PASS**, unchanged 35 unit + 11 static integration,
  7 P11-deferred, zero oracle/green. `git diff --check`: **PASS**.

## Boundaries and next work

This is exact additive source compatibility, not historical target reexecution,
general ABI compatibility, new full P08/P09 Gate or production proof. The old
object target receipts' `held_shared_lib_identity` field is preserved; this new
orthogonal source record supplies current source evidence without relabeling them.
P09-20 canonical picture now has separately bound current target evidence. Render
acceptance, product field-update API, fallback and differential remain open.
New shared-lib exports or module changes need a distinct bounded source successor;
this receipt must not be overwritten or have its expected digests silently refreshed.
