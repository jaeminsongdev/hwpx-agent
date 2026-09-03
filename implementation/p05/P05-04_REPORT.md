# P05-04 tab-definition reader/writer report

- Generated: 2026-09-03
- Implementation commits: 1a8723c4430a93f597fc9e4a3c53ace9dec84ea5, 5cb4fe74c1ffe8795ceb535324667660897c3d63
- State: pass_current_pc_local_tabs
- Reasoning/review mode: max / namespace, unit, compatibility, target-canonicalization and fail-closed audit

hwpx-package now exposes the executable hwpx-agent.tab-definition/1 model. It lifts the exact
current-2020 tabProperties through the P03 preserving XML tree, types automatic flags and ordered
left/right/center/decimal stops, preserves direct and HwpUnitChar compatibility forms, and lowers
deterministic escaped XML. Every output is reparsed for exact typed equality and paragraph-reference
closure and is bound to a digest/count receipt.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Source/profile lock | pass | locked KS X 6101 reform-03 Appendix C/F plus exact current generated 2011 head/paragraph namespaces |
| Exact current header | pass | three dense definitions with automatic flag pairs 0/0, 1/0 and 0/1 |
| Typed custom stops | pass | LEFT/RIGHT/CENTER/DECIMAL, twelve LineType2 leaders, checked non-negative positions and optional CHAR/HWPUNIT |
| Compatibility preservation | pass | exact current/fallback HwpUnitChar branches preserve both 2x and 2x+1 input pairs |
| Ordering and units | pass | strict effective-position ordering and one effective unit per definition; ambiguous mixed units reject |
| Semantic dedup | pass | ID-excluding first-occurrence identity with checked dense allocation |
| Typed rewrite | pass | complete-map validation before mutation; only typed P05-03 tabPrIDRef values change |
| Deterministic lower | pass | bounded fragment, exact lower-to-re-lift equality and stable SHA/count receipt |
| Actual Hangul 2020 target readback | pass | disposable HWPX open/read/save/reopen/read/close/quit, text digest preserved, input unchanged, residual process 0 |

## Validation evidence

- Windows Rust 1.96.0: tab-definition 13/13, complete hwpx-package 101/101, workspace tests,
  format and Clippy with warnings denied passed.
- Exact generated current-2020 header lifted all three tab records. Direct alignment/leader/unit
  variants, automatic tabs, compatibility pairs, dedup, typed reference rewrite and malformed/count/
  ID/reference/order/range/enum/namespace/limit cases passed.
- The fixed 128-case tab lower corpus is byte deterministic with aggregate SHA-256
  f1f8d6822de68ca5824cef00cca89e753c61aac5b5956d9b7d5a4ccbdbdd0a92.
- Exact correction commit 5cb4fe7 passed offline Linux Rust 1.96.0 workspace Clippy/tests with
  network disabled, repository and Cargo registry read-only, and only a disposable build directory
  writable. Pinned validation image digest:
  sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f.
- Current checkout and exact-commit clean clone each passed all 5/5 bootstrap lanes; both Git states
  remained clean. Security scanned 600/597 files with secrets/vulnerabilities/forbidden licenses 0;
  current/clean-clone SBOM components were 273/231.
- The locked machine-readable source remained SHA-256
  c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4.
- Licensed Hangul 2020 11.0.0.9136 x86 actual run trace state was pass. Input/output visible-text
  SHA-256 both equal 96ab746862b4a90b2d0f3e3f2f39593e9c28b9f04ab97db662ecf46eee2d60cf;
  input SHA-256 d823ed8c2eb4f748b715135668d505d2c362f2f9c30a9402286e096f419dee4b
  remained unchanged; output SHA-256 was
  835c703c8b745a81424b39b0f6bc3db65011ed37f786b5f4a0569a732c83cb94. The product inspector
  reported four definitions, four conceptual stops and exact semantic pass. The trace records no raw
  document text, user-document scan, network, Registry/system change or Computer Use click/type.
- User documents opened or modified: 0. All target material was a disposable generated fixture.

The actual target run exposed two implementation assumptions before closure. Hangul 2020 canonicalized
the valid odd fallback position 4001 to 4000, and section tab occurrences use required numeric width,
leader and type attributes rather than tab-definition enum names. The public definition reader/writer
continues to preserve either valid 2x or 2x+1 input exactly; only the target-fixture oracle accepts the
one observed save canonicalization. P05-01 occurrence typing and the target fixture were corrected,
and all validation above was rerun at commit 5cb4fe7.

## Strict self-review

- Change risk: high; paragraph layout and the next list/page/section engines trust these IDs, units,
  compatibility branches and rewrite atomicity.
- Unsupported VERTBAR/legacy variants, unknown typed content, sparse IDs, ambiguous units, unordered
  stops and malformed public remap tables fail closed.
- Actual target evidence proves semantic save/reopen on this exact installation, not visual tab
  placement, table/column interactions, arbitrary user documents, another PC or another release.
- No raw XML fragment, arbitrary path, COM/HAction string or platform fallback is accepted by the
  public model.
- Final blocker/major/minor findings after remediation: 0/0/0.

## Scope and remaining boundary

P05-04 does not prove rendered alignment, pagination, arbitrary-document editing, list/page/section
semantics, another PC, or Hangul 2022/2024 compatibility. Those targets remain deferred until their
machines are available and receive independent exact-build qualification.

## Next exact task

Start P05-05 Lists and numbering at reasoning effort max. Lock the exact current-2020 numbering and
bullet records plus paragraph heading references. Implement bounded typed definitions, deterministic
sequence/nesting, continuity/restart semantics, level transitions, reference closure and lower/readback
fixtures before requesting the next disposable Hangul 2020 target run.
