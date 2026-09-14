# P07 direct/automation differential report

## Result

Result: exact-current-PC scoped differential `pass`.

The P07 phase differential oracle rebuilt all eight P07-07 calibration semantics through the direct
HWPX lowerer and compared them with the independently saved exact-target automation artifacts. Four
inline and four display cases matched normalized semantic SHA, canonical EqEdit script SHA and
layout, with zero silent fallback.

## Evidence chain

- Differential oracle raw SHA-256: `44e54af3...03244`.
- Layout plan file SHA-256: `7244cf6c...5cc8`.
- Exact-target automation evidence SHA-256: `f0c4088e...e048`.
- Separate direct-lowerer exact-target evidence SHA-256: `58d6a359...2a5f`.
- Private eight-case differential receipt SHA-256: `a214cdac...1713`.
- Public redacted qualification:
  `implementation/p07/evidence/p07-equation-differential.current-2020.v1.json`.

Every direct artifact was built and fully reopened by the preserving writer in memory. Every target
artifact was independently reopened through the strict automation-native reader. The inputs and
all eight target artifacts were rehashed after comparison and remained unchanged.

## Equality boundary

This Gate compares the product-level invariants shared by both routes: normalized equation
semantics, canonical EqEdit script and inline/display layout. It intentionally does not require ZIP
byte identity, native object-ID identity, extent equality or line-cache identity because the target
application assigns and normalizes those values. The separate P07-05 evidence proves that the direct
lowerer itself passed licensed Hangul 2020 save/reopen and render; the matched automation side is the
P07-07 exact-target run.

Render is not claimed by this differential receipt. Other Hangul versions, arbitrary documents,
production readiness, full product completion and P07 completion remain separate.
