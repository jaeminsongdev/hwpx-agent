# P09-25 native form compatibility regression report

Updated: 2026-10-02. State:
`native_identity_and_anchor_gaps_reproduced_non_green`.

## Outcome and boundary

The original P08-20 saved form capture reproduces a real incompatibility in the
P09-12 existing-form adapter: its native `hp:edit` has no `id`, `instid` or
`instId`, and the production reader rejects it with
`form_control_hwpx_invalid_attribute`. This is a reproduced failure, not a
newly implemented form profile or a native target success. The user requested
offline-only work while away; no new Hangul/COM session or access prompt ran.

The preserved original package is 14,556 bytes, SHA-256
`02e9b5acef95877b6934a6a3131069402138cc2190eff2e68db79aa7e9ac9ce7`.
Its section SHA is
`89a263eff5d4536cc14223e48847a42e65c7e4f97d5b0c12b5cf73dc4bbba2ff`.
The private capture remains at its historical P08 evidence location; public
records expose only bounded metadata and hashes, not document text or private
absolute paths. The original P08 target qualification is unchanged.

## Reproduced gaps

1. The saved native form carries its name/common/character/text properties and
   `sz`, `pos`, `outMargin` geometry, but lacks the ID required by P09-12. The
   insertion contract's reservation ID 8112 is not a saved native ID.
2. A temporary memory-only added-ID diagnostic isolates that rejection: the
   original production reader admits its property projection. That derivative
   is never saved, never called native evidence and reverses exactly to the
   original section. It is not the proposed fix.
3. The same diagnostic also admits intentionally incorrect run/inline anchors
   and shape-state bindings. The old reader's projection is therefore not an
   independent physical-anchor/geometry readback. Old source locks and receipts
   remain unchanged; this finding does not rewrite historical component or P08
   target verdicts.

## Changes and independent evidence

- `crates/hwpx-package/examples/p09_25_native_form_compatibility.rs` runs the real
  P09-12 reader against the bounded, hash-pinned original capture. It refuses
  linked/reparse ancestors, checks exact file size before reading, checks raw
  package and section hashes, and rereads the original after diagnosis.
- `tools/p09/qualify_native_form_compatibility.py` independently parses native
  identity absence, ordered paragraph/run/inline location and geometry inventory,
  binds four unchanged original Rust implementation files and the original
  P09-12/P08-20 receipt identities, and executes the locked/offline Rust probe.
  It rejects unknown/false success claims and publishes exclusively.
- New Rust example tests: 3/3 PASS. New Python tests: 6/6 PASS, including missing
  or changed captures, predecessor source drift, forged/coerced claims and
  privacy/non-Gate assertions. Missing input is an error, not a skipped test.
- `P09-25_NATIVE_FORM_COMPATIBILITY_POLICY.md` defines the immutable diagnostic
  boundary and required explicit successor implementation.

The public receipt is
`implementation/p09/evidence/p09-25-native-form-compatibility-qualification.current-2020.v1.json`,
SHA `a5f86b629ef65d31f3eb49e9cbfacb081aec2165910ed033300b32a80c81e307`.
Exclusive publication and independent `--verify` reproduce identical bytes with
ten source bindings. All new native execution, production routing and phase or
product completion claims are false; green rows remain zero.

## Verification

- Full P09 Python suite: 182/182 PASS, no skips.
- Locked/offline Rust workspace, all targets/features: 1,765 PASS across 269
  test targets/suites; three existing explicitly ignored native/external tests
  remain ignored and are not qualified by this command.
- Locked/offline workspace Clippy with `-D warnings`: PASS.
- `cargo fmt --all -- --check` and `git diff --check`: PASS.
- Original P09-12 validator: genuine PASS, all four raw implementation and four
  source locks unchanged. Its actual target/render/automation/differential
  statuses remain NOT_RUN; static acceptance does not resolve these native gaps.
- P09-23 source v2, P09-22 C01 and P09-24 complete-note receipts independently
  reproduce their prior exact SHA identities. The CLICK_HERE 920-pixel style
  mismatch and pending C02/note targets remain unchanged.
- Read-only process check: no `Hwp` process. No registry/trust/system change,
  network, user-document scan, commit, push, evidence removal or original edit.

## Next implementation, not a completion claim

Implement an explicit successor native identity contract for observed missing-ID
controls. Selection must be source-bound and use a complete ordered anchor map,
namespace/tag and independently observed character, geometry and opaque content.
Logical component IDs must remain distinct from native optional IDs. Seal actual
readback, reject stale/moved/ambiguous controls and preserve all non-delta bytes.
Preserve the frozen P09-12 and additive-export v2 authorities through explicit
successor qualification before modifying their sources. Permanent synthetic-ID
injection or weakening the prior verifier is not acceptable.

Offline implementation and regression work can continue without access prompts.
Actual save/fresh-reopen, semantic, render and differential qualification wait
for explicit user resumption. P09 Gate stays open; no P10 new implementation.
