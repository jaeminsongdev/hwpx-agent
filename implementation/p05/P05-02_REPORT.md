# P05-02 character-style reader/writer report

- Generated: 2026-09-03
- Implementation and audited source commit: a810aa73930169982f124741303460d27c791b64
- State: pass_current_pc_local_character_styles
- Reasoning/review mode: max / namespace, ID-domain, range, dedup and fail-closed audit

hwpx-package now exposes the executable hwpx-agent.character-style/1 model. It lifts the exact
current-2020 fontface and charProperties structures through the P03 preserving XML tree, types all
seven language-local font domains and character style values, and lowers deterministic escaped XML.
Every output is reparsed for exact typed equality and may be returned with a digest/count receipt.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Source/profile lock | pass | locked KS X 6101 reform-03 Appendix C/F structural source plus exact current generated 2011 head namespace |
| Seven font domains | pass | ordered HANGUL/LATIN/HANJA/JAPANESE/OTHER/SYMBOL/USER groups with independent dense IDs |
| Typed font identity | pass | REP/TTF/HFT, embedded/binary reference, substitute and classification records; bounded escaped strings |
| Typed style values | pass | height, seven font refs/ratios/spacings/relative sizes/offsets, font spacing/kerning, colors and emphasis |
| Effects | pass | italic/bold/underline/strikeout/outline/shadow/emboss/engrave/superscript/subscript and exact defaults |
| ID/reference integrity | pass | counts, dense IDs, per-language font closure and invalid/dangling cases reject |
| Semantic dedup | pass | ID-excluding first-occurrence identity, dense checked allocation and deterministic old-to-new map |
| Typed rewrite | pass | two-pass atomic rewrite changes only typed charPrIDRef/charStyleIDRef; opaque content remains untouched |
| Deterministic lower | pass | typed escaping, bounded output, exact lower-to-re-lift equality and equal SHA/count receipt |
| Privacy | pass | font faces, substitute names and binary references are redacted from Debug; no user/runtime source |

## Validation evidence

- Windows Rust 1.96.0: character-style 11/11, complete hwpx-package 74/74, workspace tests, format and
  Clippy with warnings denied passed.
- Exact current generated header lifted as seven fontface groups, fourteen fonts and seven charPr
  records. The VS-0 text-flow references all resolved within the lifted style catalog.
- Cross-language value/effect/color, XML escaping, embedded/substitute font, semantic dedup,
  atomic typed-reference rewrite, wrong namespace, malformed XML, bad count/ID/reference/range/effect
  and input/output/model limit cases passed.
- The fixed 128-case style-variation lower corpus is byte deterministic with aggregate SHA-256
  5d2a03a19961f26ce46babf6e2d12eac28b23916aff35769fe5a8e0f0dc91e6d.
- Exact commit a810aa7 passed offline Linux Rust 1.96.0 workspace Clippy/tests with network disabled,
  repository and Cargo registry read-only, and only a disposable build directory/Cargo tmpfs
  writable. Pinned validation image digest:
  sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f.
- Current checkout and exact-commit clean clone each passed all 5/5 bootstrap lanes; both Git states
  remained clean. Security scanned 584 files with secrets/vulnerabilities/forbidden licenses 0;
  current/clean-clone SBOM components were 273/231.
- The locked machine-readable source remained SHA-256
  c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4.
- Hangul UI/runtime executed by this task: false. User documents opened or modified: 0.

The generic rust:1.96.0-bookworm image lacked rustfmt/Clippy, and Docker Desktop forced tmpfs noexec.
Those environment attempts stopped before product validation and are not counted as PASS. The
successful Linux run used the pinned Clippy image and an explicit disposable executable build mount;
that build directory was deleted after completion.

## Strict self-review

- Change risk: high; later paragraph/layout and package patching will trust font-domain and style-ID
  semantics from this boundary.
- Review added deterministic receipts and atomic typed text-reference rewrite after identifying that
  a dedup map alone did not satisfy reference-update integrity.
- A new embedded substitute-font path exposed one missing closing quote in the lowerer; the defect was
  fixed and the path now passes lower/re-lift equality on Windows and Linux.
- Boolean properties became explicit binary enums, public mutable models are fully revalidated, and
  all sensitive font/binary strings remain redacted from diagnostics.
- No raw XML fragment, installed-font query, COM/HAction string, arbitrary path or platform fallback
  is accepted.
- Final blocker/major/minor findings after remediation: 0/0/0.

## Scope and remaining boundary

P05-02 does not prove installed-font availability/substitution, visual fidelity, arbitrary existing
documents, package-wide binary/border-fill closure by itself, paragraph/tab/list/page/section
semantics, Hangul save/render behavior, another PC, or Hangul 2022/2024 compatibility. Full-package
external-reference closure remains the P03 IdIndex gate. Runtime/render claims remain later exact
target-oracle evidence.

## Next exact task

Start P05-03 Paragraph styles at reasoning effort max. Lock the exact current-2020 paraProperties and
referenced border/fill profile against the official Appendix C/F structures. Implement bounded typed
alignment, margins/indentation, spacing, line spacing, border/fill references and keep/widow/page
break behavior with deterministic lower/readback and layout-semantic negative tests. No Hangul UI is
required until a later layout vertical-slice oracle explicitly requests it.
