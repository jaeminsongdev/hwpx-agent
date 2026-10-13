# P09-33 complete native root manifest preparation

## Result and remaining boundary

The actual production source component now performs a sealed, bounded
whole-package packaging transition. It rewrites every declared manifest-item
href that is not expressed as its actual root-relative PackageGraph target.
It is not a raw XML string replacement used as a fake product implementation.
The plan binds the whole input archive, and external output verification
independently re-reads and checks the complete graph and every part.

This checkpoint is explicitly **pending public preparation export**, not a
connected public preparation API, native Open fix, full product route or Gate.
The pending integration target compiles the exact production source, while
the unchanged actual public form package reader independently observes the
complete resulting text and radio packages. No native session was started and
no access/security/registry setting or permission prompt was touched.

## Exact behavior

- Finite archive/part/total/entry ceilings: 32 MiB / 2 MiB / 16 MiB / 256.
- An immutable private plan seals the actual complete source digest and edits;
  there is no deserializer or caller-writable seal.
- The actual PackageGraph resolves root/relative targets and rejects external,
  ambiguous, escaped, duplicate/dangling or open graphs before editing.
- Only OPF manifest-item href VALUE spans are changed; quote style, IDs, comments,
  whitespace, other attributes/metadata bytes and all other expanded parts remain
  unchanged. XML metacharacters and literal percent characters preserve the
  exact declared target, including Unicode/opaque resource paths.
- Original no-op packages are raw byte-exact. Changed packages preserve entry
  order/compression; ZIP headers/streams are rewritten, not byte-exact.
- Deterministic retries, already-prepared no-ops, stale-source rejection and
  actual external candidate verification do not rely on a supplied receipt.
- Complete relationship IDs/targets/media/linear flags/spine remain equal.
  Form controls, IDs, anchors, payloads, referenced styles and flow do not change.
- Debug/errors/receipts contain no document values or absolute private paths.
  Receipt qualification is explicitly package-only; native/typed-reference
  qualification is not manufactured by packaging.

## Actual source/output evidence

The compiled target emits six NEW scratch source/output artifacts. An independent
Python ZIP/XML oracle checks raw source provenance, the exact independently
requested href edit, all expanded parts, every other metadata byte, order,
compression and whole-spine form/style/anchor projections. A second exact compiled
test invocation emits the real typed receipt for independent comparison.

| Actual input | Declared href edits | Output raw SHA-256 |
| --- | --- | --- |
| Original native capture | 0; full raw no-op | `02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7` |
| P09-32 two-section text failure input | 1 | `4a070073dcfb1ab5d48ebca059931a3ab0bd528a1cdc34b6dabd255f4db1107b` |
| P09-32 cross-section radio failure input | 1 | `bcfa8b35ab2baab0b7fd3511d969022ac27c96c88edb5c1ae35dff63513008de` |

Both actual failed input packages change only
`href="section1.xml"` to `href="Contents/section1.xml"`; all other bytes outside
that attribute value and expanded parts are preserved. The complete public form
reader observes both complete sections and identical controls/flow after the
packaging transition. This evidence does not show that Hancom will Open them.

Qualification capsule:
`implementation/p09/evidence/p09-33-native-root-manifest-preparation.current-2020.v1.json`.
SHA-256: `1836e2e3e2b2093edeada1a9681ccd7acb31f6bbc2d0d25c06e306c8e3cd2407`.
All 16 current source pins match; a fresh complete qualification reproduces the
same raw capsule. P09-31/P09-32 capsule/source preservation is independently
checked, including the exact P09-32 observer-only predecessor bridge.

## Verification and failed development steps

- Actual pending-source Rust integration: 12 PASS, zero failures/ignored.
- Independent Python checks: 8 PASS, including rehashed output/metadata/part,
  original/no-op substitution, entry order/compression and test-inventory mutants.
- Full workspace, all targets/features, locked/offline: 1,892 PASS,
  3 existing ignored, 277 suites, zero failures.
- Full P09 Python: 254 PASS, zero skips/failures.
- Strict workspace Clippy, workspace formatting, `git diff --check`: PASS.
- Hwp.exe count: 0. Shared lib remains raw
  `b625b6fb85d9312a3c8a2582e4eff7e0196fac11c059f0b4be4936ce78db8e3b`.

The first compile exposed that NativeFormPackageMap deliberately has no
deserializer. The test now constructs the complete typed map and independently
compares its serialization to the immutable manifest; no deserializer was added.
The first strict Clippy run found excessive receipt booleans. Preservation scope
is now structured separately and qualification is an explicit unqualified enum;
no lint allowance or weakened assertion was introduced.

## Unresolved native behavior and next exact boundary

Preserve all four successful P09-32 lifecycle records and both real first-Open
failures. The relative/root href discrepancy remains a tested packaging
hypothesis, **not** a confirmed native failure cause. No failed case was silently
reclassified as repaired, and neither failed input nor any prior receipt changed.

C02's requested foreground becoming black and C03's literal native-name
metacharacters changing remain unresolved. The original header contains a real
existing colored character style (ID 5, `#2E74B5`), while source style 0 is black.
This is an actual catalog fact, not evidence that native foreground derives from
that style. A safe next diagnostic matrix must isolate foreground from editable
and actual referenced style without approximating the requested arbitrary color
or stripping the requested name to obtain PASS.

Next connect this exact component through a public API with an explicit
source/export successor preserving P09-31/P09-32/P09-33 raw authorities. Then
prepare every genuinely changed dependency-ready complete case, including
corrected two-section admission and meaningful color/name contracts, with their
independent expected-output/native oracles. Dispatch one whole batch only when
all those dependencies are ready, not the two packaging cases alone.

The actual authoritative 53-row P09 inventory remains 35 unit/11 static
integration/0 oracle/0 green (seven rows P11 deferred). Broader input/default/
validation, type/border/protection, routes, metadata/native bindings, note/field,
render and product differential requirements remain in the full objective.
No P10 admission; the goal remains active.

## Preserved checkpoint and P09-34 successor

This report's pending-source evidence remains historical and byte-pinned in the
original P09-33 capsule. P09-34 connects the actual public library API and exposes
a production-build omission: the original hash helper used test-only `hex`.
Its exact archived source is preserved before a std-only hex helper correction;
all preparation/verification logic stays byte-exact outside that helper. The
original pending compilation did not prove a real production-library build.
See `P09-34_NATIVE_ROOT_MANIFEST_PUBLIC_EXPORT_REPORT.md` for actual public
tests, preserved original failures/source chain and current authority. Neither
this correction nor public connection proves native Open repair or P09 Gate.
