# P05-01 text-flow reader/writer report

- Generated: 2026-09-03
- Implementation and audited source commit: `08de88a0d6745398e8141190f204a93b009f770a`
- State: `pass_current_pc_local_text_flow`
- Reasoning/review mode: `max / Unicode, preservation, field-boundary and fail-closed audit`

`hwpx-package` now exposes the first executable `hwpx-agent.text-flow/v1` model. It lifts one bounded
current-profile paragraph through the P03 preserving XML tree and types paragraph/run/text ordering,
Unicode text, tabs, line breaks and nested field boundaries. It lowers only fully typed non-opaque
flows, escapes deterministically, reparses and requires exact typed equality before returning bytes.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Source/profile lock | `pass` | locked KS X 6101 reform-03 Appendix E structural source plus exact 2011 namespace from current 2020 VS-0 |
| Ordered typed model | `pass` | paragraph properties, runs, text spans/atoms, tabs, line breaks and field begin/end remain distinct |
| Field integrity | `pass` | duplicate, misnested, unclosed and over-depth boundaries reject the complete flow |
| Unicode/boundaries | `pass` | Hangul/Latin/CJK/emoji/combining corpus; NFC comparison does not mutate stored text or merge runs |
| Opaque safety | `pass` | digest-only non-editable record; possible visible content blocks semantic extraction and all opaque blocks lowering |
| Deterministic lower | `pass` | typed escaping, bounded output and exact lower→re-lift equality |
| Finite failure | `pass` | input/elements/runs/items/text/field depth/output, allocation and malformed/profile errors are typed |
| Preservation boundary | `pass` | reader is non-mutating; existing P03 surgical package/untouched-part regressions remain green |
| Privacy | `pass` | Debug redacts text, field names and opaque names/content; no user document or runtime input |

## Validation evidence

- Windows Rust 1.96.0: text-flow `12/12`, complete `hwpx-package` `63/63`, workspace tests, format and
  Clippy `-D warnings` passed.
- The fixed 128-case Unicode/run-boundary lower corpus is byte deterministic with aggregate SHA-256
  `e7fefa652acf7139c29ee29e7e2d5f90f0758850c01d6be9a0834c62f0c70c60`.
- The generated current-2020 VS-0 paragraph lifted as 2 ordered runs, exact visible text and 3 opaque
  layout records. Opaque layout prevented normalized lowering; it was not silently discarded.
- Exact commit `08de88a` passed offline Linux Rust 1.96.0 workspace Clippy/tests with network disabled,
  repository and Cargo registry read-only, and only tmpfs writable. Derived image digest:
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`.
- Current checkout and exact-commit clean clone each passed all `5/5` bootstrap lanes; both Git states
  remained clean. Security scanned 579 files with secrets/vulnerabilities/forbidden licenses 0;
  current/clean-clone SBOM components were 273/231.
- The locked machine-readable source remained SHA-256
  `c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`.
- Hangul UI/runtime executed by this task: false. User documents opened or modified: 0.

## Strict self-review

- Change risk: `high`; later editing and style modules will trust run ordering, text identity and field
  nesting from this boundary.
- Review remediations made unknown-namespace layout lookalikes conservative, blocked semantic text
  when opaque descendants can contain text, rejected nonsemantic document envelopes, applied a total
  element limit, made collection growth fallible and kept Debug output redacted.
- No raw XML fragment, COM/HAction string, path or executable markup is accepted by the writer.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Scope and remaining boundary

P05-01 does not resolve character-style records; it preserves their numeric references for P05-02.
It does not implement paragraph styles, full tab definitions, lists, page/section/header/footer
structures, arbitrary package editing, actual field creation/readback, save/render fidelity, another
PC, or Hangul 2022/2024 compatibility. The official 2024 schema is structural reference evidence and
was not promoted to current-runtime compatibility evidence.

## Next exact task

Start `P05-02 Character styles` at reasoning effort `max`. Lock the exact current-2020 header
fontface/charPr profile, implement bounded typed language font slots, size/scale/spacing/effects/color,
deterministic style dedup/lowering and package readback tests. Do not claim installed-font rendering or
actual Hangul fidelity until the later target-oracle task supplies that evidence.
