# P04-02 Unit and ID model report

- Generated: 2026-09-02
- Audited source commit: `6790fa9b558785c35d569947ec58101786061a81`
- State: `pass_current_pc_local_pure_model`
- Reasoning/review mode: `high / exact unit conversion, rounding and typed identity boundaries`

`domain-ir`에 backend-independent fixed-point unit, checked rational conversion, coordinate
space/anchor와 typed identity 경계를 구현했다. 모든 canonical 값은 integer로 저장하며 binary
floating-point를 core input, equality 또는 hash에 사용하지 않는다. 한글 runtime, filesystem,
network, process와 사용자 문서는 이 task에서 사용하지 않았다.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Pure unit/identity boundary | `pass` | `#![forbid(unsafe_code)]`; backend/runtime/filesystem/network/process dependency 0 |
| Fixed-point canonical types | `pass` | micrometer, point-milli, ratio-millionths, angle-microdegree, HWPUNIT, sparse z-order |
| Exact conversion | `pass` | bounded rational input, checked `i128` intermediate, checked `i64` publication |
| Explicit rounding | `pass` | half-away-from-zero; reduced signed rounding delta in every `ConversionReceipt` |
| Source-locked HWPUNIT | `pass` | official HWP 5.0 revision 1.3: `1/7200 inch`; `10 pt = 1000 hwpunit` |
| Legacy unit separation | `pass` | HWPML `hunit` `1/1800 inch` is explicitly rejected as a v1 HWPUNIT assumption |
| Coordinate safety | `pass` | page/content/anchor/object-local require compatible typed anchor; translation is checked |
| Typed identity | `pass` | 10 non-interchangeable newtypes with shared validated parse/deserialize boundary |
| Compatibility | `pass` | P04-01 canonical digest remains `2ab9ffef0263e14609afa148e412ba2915820e54e365c9a420c734f908a6f3c6` |
| Privacy | `pass` | identity, receipt and error Debug output does not reveal values |

The authoritative conversion source is the locked Hancom document
`implementation/p00/source-archive/original/format/HWP_5.0_revision1.3.pdf`, source ID
`hancom-hwp-5-rev1.3`, SHA-256
`1d1da9e6fe22563ae2c5285bbbfc6762974fb7f002278084cbc11e5266bdc782`. The source-lock
entry and archived file digest agree. This task does not reinterpret the older HWPML `hunit` as
HWPUNIT; any future legacy adapter must name that source unit and issue a separate receipt.

## Validation evidence

- Windows Rust 1.96.0: `domain-ir` `18/18`, doc tests and Clippy `-D warnings` passed.
- Linux Rust 1.96.0: derived image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`,
  network off, source/registry read-only, Cargo offline, target/toolchain temp on `tmpfs`;
  `18/18` and Clippy passed.
- Unit/identity-specific tests: `9/9`; official constants, positive/negative tie symmetry,
  `7200 HWPUNIT = 25400 um`, `10 pt = 1000 HWPUNIT`, `210 mm = 59528 HWPUNIT`, invalid DPI,
  rational bounds, overflow, validated deserialization, coordinate mismatch and privacy passed.
- Fixed-seed property corpus: 10,000 signed HWPUNIT round trips passed without unchecked wrap or
  nondeterministic rounding.
- Current checkout FULL bootstrap: `5/5` lanes passed.
- Exact implementation commit clean clone FULL bootstrap: `5/5` lanes passed; post-run Git changes 0.
- Current security: 522 files scanned, secrets/vulnerabilities/forbidden licenses 0, SBOM 271 components.
- Clean-clone security: secrets/vulnerabilities/forbidden licenses 0, SBOM 229 components.

## Strict self-review and remediations

- Change risk: `high` because selectors, planner defaults and backend lowering will trust normalized
  units and identity kinds.
- The official HWPUNIT and legacy HWPML `hunit` definitions were initially easy to conflate; the
  policy now records their distinct denominators and forbids implicit legacy admission.
- Binary floating-point admission would make NaN/infinity and platform-dependent rounding possible;
  the core accepts only bounded exact rational input.
- Derived deserialization initially could bypass constructor checks for `RationalInput` and
  `Position2D`; custom validated `Deserialize` implementations and negative JSON tests closed it.
- All multiplication/addition and publication paths use checked arithmetic; no saturation, wrap or
  silent coordinate-space conversion exists.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P04-02 proves pure deterministic unit and identity primitives. It does not prove actual HWPX
lifting/lowering, page-layout fidelity, public JSON adapter behavior, Hancom automation or source ID
stability across a real save. No user document was opened or modified. Other Hancom releases and
PCs remain deferred and do not affect the current-PC sequence.

## Next exact task

Start `P04-03 Selector engine` with reasoning effort `high`. Implement deterministic ID, named
slot/field/bookmark, structural path plus fingerprint and text-context resolution against an
immutable graph snapshot. Zero, multiple and stale candidates must fail closed; arbitrary first
candidate fallback is forbidden. P04 final Gate remains `max`. No user local operation is required
for P04-03.
